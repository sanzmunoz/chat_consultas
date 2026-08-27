import yaml
from pathlib import Path
from typing import Optional, List
from uuid import UUID
from src.domain.entities.copilot_log import (
    CopilotQueryResponse,
    CopilotCitation
)
from src.domain.ports.message_repository import MessageRepositoryPort
from src.domain.ports.copilot_log_repository import CopilotLogRepositoryPort
from src.domain.ports.llm_service import LlmServicePort

PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "v1.yaml"
if not PROMPT_PATH.exists():
    PROMPT_PATH = Path(__file__).resolve().parents[4] / "backend" / "prompts" / "v1.yaml"

class QueryCopilotUseCase:
    def __init__(
        self,
        message_repo: MessageRepositoryPort,
        copilot_log_repo: CopilotLogRepositoryPort,
        llm_service: LlmServicePort
    ):
        self.message_repo = message_repo
        self.copilot_log_repo = copilot_log_repo
        self.llm_service = llm_service
        self._prompt_config = self._load_prompt_config()

    def _load_prompt_config(self) -> dict:
        if PROMPT_PATH.exists():
            with open(PROMPT_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {
            "version": "v1",
            "model_default": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 600,
            "system_template": "Eres el Copiloto de Riwi Co. Responde con citas basadas en el contexto."
        }

    async def execute(
        self,
        actor_id: UUID,
        user_name: str,
        user_position: str,
        user_email: str,
        query: str
    ) -> CopilotQueryResponse:
        """
        Executes RAG flow strictly scoped to messages in channels where actor is a member.
        Provides citations and explicit transparent negative answers.
        """
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Query cannot be empty.")

        # 1. Generate query embedding
        query_embedding = await self.llm_service.generate_embedding(clean_query)

        # 2. Retrieve context messages strictly filtered by PostgreSQL RLS / memberships
        context_messages = await self.message_repo.retrieve_copilot_context_embeddings(
            actor_id=actor_id,
            query_embedding=query_embedding,
            raw_query=clean_query,
            similarity_threshold=0.65,
            limit=5
        )

        # 3. Format system prompt with user identity
        sys_template = self._prompt_config.get("system_template", "")
        system_prompt = sys_template.format(
            user_name=user_name,
            user_position=user_position,
            user_email=user_email
        )

        # 4. Build user prompt and citations
        citations: List[CopilotCitation] = []
        if not context_messages:
            user_prompt = (
                f"PREGUNTA DEL USUARIO: {clean_query}\n\n"
                f"ESTADO DEL CONTEXTO: NO SE ENCONTRARON MENSAJES EN TUS CANALES AUTORIZADOS.\n"
                f"Responde de forma transparente indicando que no tienes acceso a información sobre esta consulta."
            )
        else:
            context_blocks = []
            for msg in context_messages:
                channel_info = msg.author_position or "Canal"
                ref_str = msg.msg_ref or str(msg.id)[:8]
                block = f"[{ref_str}] De {msg.author_name} en {channel_info}:\n\"{msg.content}\""
                context_blocks.append(block)
                
                citations.append(
                    CopilotCitation(
                        msg_ref=ref_str,
                        channel_name=channel_info.split(" | ")[0] if " | " in channel_info else channel_info,
                        author_name=msg.author_name or "Desconocido",
                        content_snippet=msg.content[:150] + ("..." if len(msg.content) > 150 else ""),
                        similarity_score=round(msg.search_rank or 0.0, 4)
                    )
                )

            user_prompt = (
                f"CONTEXTO RECUPERADO DE TUS CANALES AUTORIZADOS:\n"
                + "\n\n".join(context_blocks)
                + f"\n\nPREGUNTA DEL USUARIO: {clean_query}\n\n"
                f"Instrucción: Responde a la pregunta citando las referencias [msg-xxxx] del contexto."
            )

        # 5. Generate completion via LLM
        model_name = self._prompt_config.get("model_default", "gpt-4o-mini")
        temperature = float(self._prompt_config.get("temperature", 0.1))
        max_tokens = int(self._prompt_config.get("max_tokens", 600))
        prompt_version = self._prompt_config.get("version", "v1")

        response_text, p_tokens, c_tokens, t_tokens = await self.llm_service.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # 6. Audit log in database
        try:
            await self.copilot_log_repo.log_copilot_interaction(
                user_id=actor_id,
                query=clean_query,
                response=response_text,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=t_tokens,
                model=model_name,
                prompt_version=prompt_version
            )
        except Exception:
            pass  # Logging should not block response delivery

        return CopilotQueryResponse(
            query=clean_query,
            response=response_text,
            citations=citations,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=t_tokens,
            model=model_name,
            prompt_version=prompt_version
        )
