from typing import Protocol, List, Tuple, Optional

class LlmServicePort(Protocol):
    """
    Interchangeable LLM provider interface (ADR-08).
    Abstracts embeddings and chat completions from specific vendor implementations (OpenAI, Anthropic, local mock/fallback).
    """
    async def generate_embedding(self, text: str) -> List[float]:
        """Generates 1536-dimensional vector embedding for text."""
        ...

    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 600
    ) -> Tuple[str, int, int, int]:
        """
        Generates completion given system and user prompts.
        Returns: (response_text, prompt_tokens, completion_tokens, total_tokens)
        """
        ...
