"""Utility for loading prompt templates."""

from pathlib import Path

from kiwi_video.core.exceptions import ResourceNotFoundError
from kiwi_video.utils.logger import get_logger

logger = get_logger("prompt_loader")

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "config" / "prompts"


def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts directory.
    
    Args:
        prompt_name: Name of the prompt file (with or without .txt extension)
        
    Returns:
        Prompt content as string
        
    Raises:
        ResourceNotFoundError: If prompt file not found
    
    Example:
        >>> prompt = load_prompt("story_loader")
        >>> prompt = load_prompt("veo_prompt.txt")
    """
    # Add .txt extension if not present
    if not prompt_name.endswith(".txt"):
        prompt_name = f"{prompt_name}.txt"
    
    prompt_path = PROMPTS_DIR / prompt_name
    
    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        raise ResourceNotFoundError("prompt", prompt_name)
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        logger.debug(f"Loaded prompt: {prompt_name}")
        return content
        
    except Exception as e:
        logger.error(f"Failed to load prompt {prompt_name}: {e}")
        raise


def load_prompt_with_variables(prompt_name: str, **variables: str) -> str:
    """
    Load a prompt template and replace variables.
    
    Args:
        prompt_name: Name of the prompt file
        **variables: Key-value pairs for variable substitution
        
    Returns:
        Prompt with variables replaced
        
    Example:
        >>> prompt = load_prompt_with_variables(
        ...     "veo_prompt",
        ...     plan_name="Scene 1",
        ...     vo_script_cue="Hello world"
        ... )
    """
    template = load_prompt(prompt_name)
    
    # Replace variables in the format <<variable_name>>
    for key, value in variables.items():
        placeholder = f"<<{key}>>"
        template = template.replace(placeholder, str(value))
    
    return template


def list_available_prompts() -> list[str]:
    """
    List all available prompt templates.
    
    Returns:
        List of prompt file names
    """
    if not PROMPTS_DIR.exists():
        logger.warning(f"Prompts directory not found: {PROMPTS_DIR}")
        return []
    
    prompts = [f.name for f in PROMPTS_DIR.glob("*.txt")]
    logger.debug(f"Found {len(prompts)} prompt templates")
    
    return prompts

