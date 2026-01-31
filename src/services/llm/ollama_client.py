import requests
from typing import List, Dict
from fastapi import HTTPException
from src.config import settings
from src.services.llm.base import LLMClient

class OllamaLLM(LLMClient):
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response from the Ollama model given a conversation history.
        Uses /api/chat endpoint.
        """
        url = f"{self.base_url}/api/chat"
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        try:
            response = requests.post(url, json=data, timeout=120) 
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Ollama API Error: {response.text}")
            
            # Response format for chat is {"message": {"role": "assistant", "content": "..."}}
            return response.json().get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to Ollama: {str(e)}")