import os

_cache: str | None = None

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "business_prompt.md")


def get_business_prompt() -> str:
    global _cache
    if _cache is None:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            _cache = f.read()
    return _cache
