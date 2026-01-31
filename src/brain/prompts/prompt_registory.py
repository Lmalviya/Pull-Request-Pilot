from src.brain.prompts.reviewer_prompt import PERFORMANCE_FOCUSED_PROMPT
from src.config import settings

PROMPT_REGISTRY = {
    "performance": PERFORMANCE_FOCUSED_PROMPT
}

def get_system_prompt() -> str:
    system_prompt_name = settings.system_prompt_name
    print(f"sysmtem prompt: {system_prompt_name}")
    if system_prompt_name not in PROMPT_REGISTRY:
        raise ValueError(f"Unknown prompt: {system_prompt_name}")
    return PROMPT_REGISTRY.get(system_prompt_name)