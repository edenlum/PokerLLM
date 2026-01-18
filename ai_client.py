"""
Simple AI client that uses OpenAI SDK for all providers.
Supports OpenAI, Google (via OpenAI-compatible API), and other providers.
"""

import os
import json
from datetime import datetime
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
    elif provider == "openrouter":
        return OpenAI(
            api_key=os.getenv(f"{provider.upper()}_API_KEY"), 
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        raise ValueError(f"Invalid provider: {provider}")

class AIClient:
    """Simple AI client using OpenAI SDK with configurable base URLs."""
    
    def __init__(self, provider: str, model: str, log_file: Optional[str] = None):
        """
        Initialize AI client.
        
        Args:
            provider: Provider name ('openai', 'google', 'anthropic')
            model: Model name
            log_file: Optional path to log file for prompts and responses
        """
        self.provider = provider
        self.client = get_client(provider)
        self.model = model
        self.log_file = log_file
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
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
        response = None
        error = None
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                response_format=response_format,
            )
            response = completion.choices[0].message.parsed
            if response is None:
                raise ValueError("No response received from the model")
            return response
        except Exception as e:
            error = str(e)
            raise Exception(f"AI API error ({self.provider}): {error}")
        finally:
            if self.log_file:
                self._log(messages, response, error)
    
    def _log(self, messages: list, response=None, error: Optional[str] = None):
        """Log input messages, response (optional), and error (optional) to file."""
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"\n{'='*80}\n")
            f.write(f"[{timestamp}] Provider: {self.provider}, Model: {self.model}\n")
            f.write(f"{'='*80}\n")
            
            # Log input messages
            f.write("INPUT MESSAGES:\n")
            for msg in messages:
                f.write(f"  {msg['role'].upper()}: {msg['content']}\n")
            
            # Log response if available
            if response:
                f.write("\nRESPONSE:\n")
                if hasattr(response, 'model_dump'):
                    f.write(json.dumps(response.model_dump(), indent=2))
                elif hasattr(response, 'dict'):
                    f.write(json.dumps(response.dict(), indent=2))
                else:
                    f.write(str(response))
                f.write("\n")
            
            # Log error if available
            if error:
                f.write(f"\nERROR: {error}\n")
            
            f.write(f"{'='*80}\n\n")
    