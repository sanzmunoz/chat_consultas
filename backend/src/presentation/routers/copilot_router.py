from fastapi import APIRouter, Depends, HTTPException, status
from src.presentation.schemas.copilot_schemas import (
    CopilotQueryRequest,
    CopilotQueryResponseSchema,
    CopilotCitationSchema,
    CopilotUsageResponseSchema
)
from src.presentation.middleware.auth_middleware import get_current_user
from src.domain.entities.user import User
from src.application.copilot.query_copilot_use_case import QueryCopilotUseCase
from src.application.copilot.get_copilot_usage_use_case import GetCopilotUsageUseCase
from src.infrastructure.database.pg_message_repository import PgMessageRepository
from src.infrastructure.database.pg_copilot_log_repository import PgCopilotLogRepository
from src.infrastructure.llm.openai_llm_service import OpenAILlmService

router = APIRouter(prefix="/api/copilot", tags=["Copiloto IA (RAG)"])

message_repo = PgMessageRepository()
copilot_log_repo = PgCopilotLogRepository()
llm_service = OpenAILlmService()

query_copilot_uc = QueryCopilotUseCase(message_repo, copilot_log_repo, llm_service)
get_usage_uc = GetCopilotUsageUseCase(copilot_log_repo)

@router.post("/query", response_model=CopilotQueryResponseSchema, summary="Consultar Copiloto RAG con citas")
async def query_copilot(
    req: CopilotQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Consulta al Copiloto RAG recuperando contexto EXCLUSIVAMENTE de los canales
    donde el usuario autenticado es miembro (con citas y negativas explícitas).
    """
    try:
        res = await query_copilot_uc.execute(
            actor_id=current_user.id,
            user_name=current_user.display_name,
            user_position=current_user.position,
            user_email=current_user.email,
            query=req.query
        )
        return CopilotQueryResponseSchema(
            query=res.query,
            response=res.response,
            citations=[
                CopilotCitationSchema(
                    msg_ref=c.msg_ref,
                    channel_name=c.channel_name,
                    author_name=c.author_name,
                    content_snippet=c.content_snippet,
                    similarity_score=c.similarity_score
                )
                for c in res.citations
            ],
            prompt_tokens=res.prompt_tokens,
            completion_tokens=res.completion_tokens,
            total_tokens=res.total_tokens,
            model=res.model,
            prompt_version=res.prompt_version
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error procesando la consulta del copiloto: {str(e)}"
        )

@router.get("/usage", response_model=CopilotUsageResponseSchema, summary="Consumo de tokens del usuario")
async def get_copilot_usage(current_user: User = Depends(get_current_user)):
    """
    Consulta 4: Retorna el consumo acumulado de tokens del usuario autenticado.
    """
    usage = await get_usage_uc.execute(current_user.id)
    if not usage:
        return CopilotUsageResponseSchema(
            user_id=current_user.id,
            display_name=current_user.display_name,
            email=current_user.email,
            total_queries=0,
            total_prompt_tokens=0,
            total_completion_tokens=0,
            total_tokens_used=0,
            last_query_at=None
        )
    return CopilotUsageResponseSchema(
        user_id=usage.user_id,
        display_name=usage.display_name,
        email=usage.email,
        total_queries=usage.total_queries,
        total_prompt_tokens=usage.total_prompt_tokens,
        total_completion_tokens=usage.total_completion_tokens,
        total_tokens_used=usage.total_tokens_used,
        last_query_at=usage.last_query_at
    )
