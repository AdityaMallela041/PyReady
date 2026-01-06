"""Groq LLM client implementation."""

import os
from typing import Optional
import httpx

from .client import LLMClient, LLMError


class GroqClient(LLMClient):
    """Groq LLM client using OpenAI-compatible API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key (reads from GROQ_API_KEY env var if not provided)
            model: Model to use for generation
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1"
        
    def is_available(self) -> bool:
        """Check if Groq API key is configured."""
        return self.api_key is not None and len(self.api_key) > 0
    
    def generate(self, prompt: str, max_tokens: int = 200) -> str:
        """
        Generate text using Groq API.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If API call fails
        """
        if not self.is_available():
            raise LLMError("Groq API key not configured. Set GROQ_API_KEY environment variable.")
        
        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are a technical assistant that explains development commands. "
                                    "Provide clear, concise explanations in 3-6 lines. "
                                    "Do not speculate or add information beyond what is provided. "
                                    "Focus on what the command does, not recommendations."
                                )
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.3,  # Low temperature for consistency
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                if "choices" not in data or len(data["choices"]) == 0:
                    raise LLMError("No response from Groq API")
                
                return data["choices"][0]["message"]["content"].strip()
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise LLMError("Invalid Groq API key")
            elif e.response.status_code == 429:
                raise LLMError("Groq API rate limit exceeded")
            else:
                raise LLMError(f"Groq API error: {e.response.status_code}")
        
        except httpx.TimeoutException:
            raise LLMError("Groq API request timed out")
        
        except Exception as e:
            raise LLMError(f"Unexpected error: {str(e)}")
