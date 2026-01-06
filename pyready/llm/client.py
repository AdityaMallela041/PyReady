"""Abstract LLM client interface."""

from abc import ABC, abstractmethod
from typing import Optional


class LLMError(Exception):
    """Exception raised when LLM call fails."""
    pass


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 200) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt for the LLM
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if LLM client is available and configured.
        
        Returns:
            True if client can be used, False otherwise
        """
        pass
