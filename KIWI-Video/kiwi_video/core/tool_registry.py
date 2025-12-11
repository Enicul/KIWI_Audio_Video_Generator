"""Tool registry for managing agent tools and their specifications."""

from collections.abc import Callable
from typing import Any

from kiwi_video.utils.logger import get_logger


class ToolRegistry:
    """
    Registry for managing tools available to agents.
    
    Tools are functions that agents can call to perform specific actions.
    Each tool has a specification defining its name, description, and parameters.
    """

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self.tools: dict[str, Callable] = {}
        self.tool_specs: dict[str, dict[str, Any]] = {}
        self.logger = get_logger("tool_registry")

    def register(
        self,
        name: str,
        function: Callable,
        description: str,
        parameters: dict[str, Any] | None = None
    ) -> None:
        """
        Register a new tool.
        
        Args:
            name: Tool name
            function: Callable function implementing the tool
            description: Description of what the tool does
            parameters: JSON schema describing the tool's parameters
        """
        if name in self.tools:
            self.logger.warning(f"Tool '{name}' is already registered, overwriting")

        self.tools[name] = function
        self.tool_specs[name] = {
            "name": name,
            "description": description,
            "parameters": parameters or {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

        self.logger.debug(f"Registered tool: {name}")

    def unregister(self, name: str) -> None:
        """
        Unregister a tool.
        
        Args:
            name: Tool name to unregister
        """
        if name in self.tools:
            del self.tools[name]
            del self.tool_specs[name]
            self.logger.debug(f"Unregistered tool: {name}")
        else:
            self.logger.warning(f"Tool '{name}' not found in registry")

    def get_tool(self, name: str) -> Callable | None:
        """
        Get a tool function by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool function or None if not found
        """
        return self.tools.get(name)

    def get_tool_spec(self, name: str) -> dict[str, Any] | None:
        """
        Get a tool specification by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool specification dictionary or None if not found
        """
        return self.tool_specs.get(name)

    def get_all_tools(self) -> dict[str, Callable]:
        """
        Get all registered tools.
        
        Returns:
            Dictionary of tool names to functions
        """
        return self.tools.copy()

    def get_all_specs(self) -> list[dict[str, Any]]:
        """
        Get specifications for all registered tools.
        
        Returns:
            List of tool specification dictionaries
        """
        return list(self.tool_specs.values())

    def get_specs_for_llm(self) -> list[dict[str, Any]]:
        """
        Get tool specifications formatted for LLM consumption.
        
        Returns:
            List of tool specifications in LLM-compatible format
        """
        # Format according to Gemini function calling spec
        return [
            {
                "name": spec["name"],
                "description": spec["description"],
                "parameters": spec["parameters"]
            }
            for spec in self.tool_specs.values()
        ]

    def has_tool(self, name: str) -> bool:
        """
        Check if a tool is registered.
        
        Args:
            name: Tool name
            
        Returns:
            True if tool is registered, False otherwise
        """
        return name in self.tools

    def list_tools(self) -> list[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def clear(self) -> None:
        """Clear all registered tools."""
        self.tools.clear()
        self.tool_specs.clear()
        self.logger.info("Cleared all registered tools")

    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self.tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered (supports 'in' operator)."""
        return name in self.tools


# Global tool registry instance
_global_registry: ToolRegistry | None = None


def get_global_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.
    
    Returns:
        Global ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def tool(
    name: str | None = None,
    description: str | None = None,
    parameters: dict[str, Any] | None = None
) -> Callable:
    """
    Decorator for registering functions as tools.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
        parameters: Parameter schema
        
    Returns:
        Decorator function
    
    Example:
        ```python
        @tool(description="Reads a file from disk")
        def read_file(path: str) -> str:
            with open(path) as f:
                return f.read()
        ```
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"

        # Register in global registry
        registry = get_global_registry()
        registry.register(
            name=tool_name,
            function=func,
            description=tool_description,
            parameters=parameters
        )

        return func

    return decorator

