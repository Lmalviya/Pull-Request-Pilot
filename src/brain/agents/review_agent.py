import json
import logging
import time
from src.config import settings
from src.brain.agents.utils import (
    llm_output_parser, 
    llm_call, 
    execute_tool, 
    validate_required_keys, 
    validate_tool_structure, 
    validate_content_structure
)
from src.brain.agents.base_agent import BaseAgent
# Configure logging
logger = logging.getLogger("review_agent")

class ReviewAgent(BaseAgent):
    def __init__(self, llm_client, scm_client):
        super().__init__(llm_client, scm_client)

    def llm_output_validator(self, response_text: str) -> tuple[bool, dict | None, str]:
        try:
            generated_content = llm_output_parser(response_text)
            if generated_content is None:
                return False, None, "LLM returned invalid JSON"
            
            if not isinstance(generated_content, dict):
                return False, generated_content, "LLM returned valid JSON but not a dictionary"
            
            # 1. Validate Keys
            is_valid, error = validate_required_keys(generated_content, ["reasoning", "model", "content", "tool_call"])
            if not is_valid:
                return False, generated_content, error

            # 2. Validate based on model type
            model_type = generated_content["model"]
            if model_type == "tool":
                is_valid, error = validate_tool_structure(generated_content)
                if not is_valid: return False, generated_content, error

            elif model_type == "answer":
                is_valid, error = validate_content_structure(generated_content)
                if not is_valid: return False, generated_content, error
            
            else:
                return False, generated_content, f"Invalid model type: {model_type}"

            return True, generated_content, ""
        except Exception as e:
            logger.error(f"Error processing comments: {e}")
            return False, None, "Error processing comments"

    def run(self, system_prompt: str, user_message: str) -> list:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        while True:
            response_text = llm_call(self.llm, messages)
            if response_text is None:
                raise Exception("LLM call failed")
            
            messages.append({"role": "assistant", "content": response_text})
            is_valid, generated_content, error = self.llm_output_validator(response_text)
            
            if not is_valid:
                logger.error(f"Invalid LLM output: {error}")
                messages.append({"role": "user", "content": error})
                continue
            
            model_action = generated_content["model"]
            
            if model_action == "tool":
                tool_data = generated_content["tool_call"]
                tool_name = tool_data["tool"]
                tool_args = tool_data["args"]
                logger.info(f"Agent requesting tool: {tool_name}")
                
                is_success, tool_result, tool_error = execute_tool(
                    tool_name, 
                    tool_args, 
                    self.registered_tools, 
                    self.tool_call_max_retries, 
                    self.tool_call_retry_delay
                )
                
                if not is_success:
                    error_msg = tool_error if tool_error else "Tool call failed"
                    logger.error(f"Tool call error: {error_msg}")
                    messages.append({"role": "user", "content": f"Tool execution error: {error_msg}"})
                    continue
                
                # Success
                messages.append({"role": "tool", "content": tool_result})
                continue
            
            elif model_action == "answer":
                logger.info("Agent returned final answer")
                return generated_content["content"]

            break

        return []
