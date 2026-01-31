from src.brain.prompts.reviewer_prompt import PERFORMANCE_FOCUSED_PROMPT
from src.config import settings

PROMPT_REGISTRY = {
    "performance": PERFORMANCE_FOCUSED_PROMPT
}

def get_system_prompt(**kwargs) -> str:
    system_prompt_name = settings.system_prompt_name
    if system_prompt_name not in PROMPT_REGISTRY:
        raise ValueError(f"Unknown prompt: {system_prompt_name}")
    
    prompt_template = PROMPT_REGISTRY.get(system_prompt_name)
    
    # Default values for common keys if not provided
    defaults = {
        "previous_feedback": "None"
    }
    defaults.update(kwargs)
    
    return prompt_template.format(**defaults)