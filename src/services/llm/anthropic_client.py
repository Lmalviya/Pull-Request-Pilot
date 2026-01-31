import requests
from typing import List, Dict
from fastapi import HTTPException
from src.config import settings
from src.services.llm.base import LLMClient

class AnthropicLLM(LLMClient):
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        # Using the generic 'model_name' from settings which defaults to Claude
        self.model = settings.model_name 
        self.api_url = settings.anthropic_base_url

    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # Extract system prompt if present, as Anthropic handles it separately
        system_prompt = None
        filtered_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)

        data = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": filtered_messages
        }
        
        if system_prompt:
            data["system"] = system_prompt

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Anthropic API Error: {response.text}"
                )
            
            result = response.json()
            return result["content"][0]["text"]
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to Anthropic: {str(e)}")
