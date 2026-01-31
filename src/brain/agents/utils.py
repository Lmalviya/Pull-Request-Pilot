from typing import Dict, Any, Callable
import json
import logging
import time

logger = logging.getLogger("agent_utils")

def llm_output_parser(text: str) -> Dict | None:
    try:
        # Clean response if it contains markdown code blocks
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        comments = json.loads(clean_text)
        return comments
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response as JSON. Raw response: {text}")
        return None
    except Exception as e:
        logger.error(f"Error processing comments: {e}")
        return None

def llm_call(llm_client, messages: list[dict[str, str]]) -> str | None:
    try:
        response_text = llm_client.generate_response(messages)
        logger.info("LLM response received")
        return response_text
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return None

def execute_tool(tool_name: str, tool_args: Dict[str, Any], available_tools: Dict[str, Callable], max_retries: int, retry_delay: int) -> tuple[bool, Any | None, str | None]:
    for _ in range(max_retries):
        try:
            if tool_name in available_tools:
                result = available_tools[tool_name](**tool_args)
                return True, result, None
            else:
                return False, None, f"Tool '{tool_name}' not found"
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            time.sleep(retry_delay)
            continue    
    return False, None, "Max retries reached for tool execution"

def validate_required_keys(data: Dict, keys: list[str]) -> tuple[bool, str]:
    for key in keys:
        if key not in data:
            return False, f"Missing required key: {key}"
    return True, ""

def validate_tool_structure(data: Dict) -> tuple[bool, str]:
    if not isinstance(data.get("tool_call"), dict):
        return False, "tool_call must be a dictionary"
    if "tool" not in data["tool_call"] or "args" not in data["tool_call"]:
        return False, "tool_call missing tool or args"
    return True, ""

def validate_content_structure(data: Dict) -> tuple[bool, str]:
    if not isinstance(data.get("content"), list):
        return False, "content must be a list"
    for item in data["content"]:
        if not isinstance(item, dict):
            return False, "content items must be dictionaries"
        if "file" not in item or "line" not in item or "comment" not in item:
            return False, "content item missing required fields"
    return True, ""