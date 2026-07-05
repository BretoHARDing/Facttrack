import os
from functools import lru_cache
from openai import AsyncOpenAI
from app.config import settings

@lru_cache(maxsize=1)
def get_llm_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.LLM_API_KEY or "dummy-key",
        base_url=settings.LLM_BASE_URL
    )

@lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "nsw_evidence_matrix_v2.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

async def extract_nsw_matrix(text: str) -> str:
    client = get_llm_client()
    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": _load_system_prompt()},
            {"role": "user", "content": f"[DOC_START]\ntext:\n{text[:50000]}\n[DOC_END]"} # Cap at 50k chars for safety
        ],
        temperature=0.0
    )

    return response.choices[0].message.content or ""
