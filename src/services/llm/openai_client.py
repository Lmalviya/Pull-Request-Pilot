import requests
from typing import List, Dict
from fastapi import HTTPException
from src.config import settings
from src.services.llm.base import LLMClient

class OpenAILLM(LLMClient):
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.api_url = settings.openai_base_url

    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"OpenAI API Error: {response.text}"
                )
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to OpenAI: {str(e)}")
