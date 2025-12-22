"""
Simple AI client that uses OpenAI SDK for all providers.
Supports OpenAI, Google (via OpenAI-compatible API), and other providers.
"""

import os
from openai import OpenAI
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel
load_dotenv()

def get_client(provider) -> OpenAI:
    if provider == "openai":
        return OpenAI(
            api_key=os.getenv(f"{provider.upper()}_API_KEY"), 
            base_url=None
        )
    elif provider == "google":
        return OpenAI(
            api_key=os.getenv(f"{provider.upper()}_API_KEY"), 
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    elif provider == "anthropic":
        return OpenAI(
            api_key=os.getenv(f"{provider.upper()}_API_KEY"), 
            base_url="https://api.anthropic.com/v1/openai/"
        )
    else:
        raise ValueError(f"Invalid provider: {provider}")

class AIClient:
    """Simple AI client using OpenAI SDK with configurable base URLs."""
    
    def __init__(self, provider: str, model: str):
        """
        Initialize AI client.
        
        Args:
            provider: Provider name ('openai', 'google', 'anthropic')
            model: Model name
        """
        self.provider = provider
        self.client = get_client(provider)
        self.model = model
    
    def get_completion(self, messages: list, response_format: BaseModel) -> str:
        """
        Get completion from AI provider.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Randomness (0.0-1.0)
            max_tokens: Maximum response tokens
            
        Returns:
            AI response text
        """
        try:
            completion = self.client.beta.chat.completions.parse(  # type: ignore
                    model=self.model,
                    messages=messages,
                    response_format=response_format,
                )  # type: ignore
            if completion.choices[0].message.parsed is None:
                raise ValueError("No response received from the model")
            return completion.choices[0].message.parsed
        except Exception as e:
            raise Exception(f"AI API error ({self.provider}): {str(e)}")
    