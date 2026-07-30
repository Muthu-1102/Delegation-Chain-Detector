"""Thin wrapper around the Groq API used by all agent nodes."""

from __future__ import annotations

from groq import AsyncGroq

from app.core.config import get_settings

settings = get_settings()

_client: AsyncGroq | None = None


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _client


async def complete(system_prompt: str, user_prompt: str) -> str:
    """Single-turn completion helper shared by every agent node."""
    client = get_client()
    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""
