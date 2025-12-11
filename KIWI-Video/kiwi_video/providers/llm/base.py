"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM client implementations must inherit from this class.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int | None = None
    ) -> str:
        """
        Generate text completion.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        pass

    @abstractmethod
    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float = 0.7
    ) -> dict[str, Any]:
        """
        Generate response with tool calling support.
        
        Args:
            messages: Conversation history
            tools: List of available tools
            temperature: Sampling temperature
            
        Returns:
            Dictionary containing response and tool calls
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text with streaming.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        pass

