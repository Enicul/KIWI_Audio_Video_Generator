"""Base agent class for all KIWI-Video agents."""

import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any

from kiwi_video.core.exceptions import AgentError
from kiwi_video.core.state_manager import StateManager
from kiwi_video.providers.llm.base import BaseLLMClient
from kiwi_video.utils.logger import get_logger


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the KIWI-Video framework.
    
    All agents must inherit from this class and implement the required abstract methods.
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: BaseLLMClient,
        state_manager: StateManager,
        workspace_dir: Path,
    ) -> None:
        """
        Initialize the base agent.
        
        Args:
            agent_name: Name of the agent
            llm_client: LLM client for AI operations
            state_manager: State manager for persistence
            workspace_dir: Working directory for the agent
        """
        self.agent_name = agent_name
        self.llm_client = llm_client
        self.state_manager = state_manager
        self.workspace_dir = workspace_dir
        self.logger = get_logger(f"agent.{agent_name}")

        self.conversation_history: list[dict[str, Any]] = []
        self.tool_call_counter = 0

        # Register agent-specific tools
        self.tools = self.register_tools()

        self.logger.info(f"Initialized {agent_name} with {len(self.tools)} tools")

    @abstractmethod
    def register_tools(self) -> dict[str, Callable]:
        """
        Register agent-specific tools.
        
        Returns:
            Dictionary mapping tool names to their implementation functions
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Returns:
            The system prompt string
        """
        pass

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent's main workflow.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Dictionary containing the agent's output
            
        Raises:
            AgentError: If execution fails
        """
        try:
            self.logger.info(f"Starting {self.agent_name} execution")

            # Initialize conversation with system prompt
            system_prompt = self.get_system_prompt()
            self.conversation_history.append({
                "role": "system",
                "content": system_prompt
            })

            # Execute agent loop (support both sync and async workflows)
            import inspect
            if inspect.iscoroutinefunction(self._execute_workflow):
                result = await self._execute_workflow(input_data)
            else:
                result = self._execute_workflow(input_data)

            self.logger.info(f"{self.agent_name} execution completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"{self.agent_name} execution failed: {e}", exc_info=True)
            raise AgentError(self.agent_name, str(e))

    @abstractmethod
    def _execute_workflow(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent-specific workflow logic.
        
        This method should be implemented by each agent to define its specific behavior.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            Dictionary containing the workflow output
        """
        pass

    def agent_loop(
        self,
        objective: str,
        goal_check: Callable[[], bool],
        max_turns: int = 50
    ) -> bool:
        """
        Execute the agent loop until the goal is achieved or max turns reached.
        
        Args:
            objective: The objective/task description
            goal_check: Function to check if the goal is achieved
            max_turns: Maximum number of turns
            
        Returns:
            True if goal achieved, False otherwise
        """
        self.logger.info(f"Starting agent loop: {objective}")

        # Add objective to conversation
        self.conversation_history.append({
            "role": "user",
            "content": objective
        })

        for turn in range(max_turns):
            # Check if goal is achieved
            if goal_check():
                self.logger.info(f"Goal achieved after {turn + 1} turns")
                return True

            self.logger.debug(f"Turn {turn + 1}/{max_turns}: Agent thinking...")

            try:
                # Get LLM decision with tool calling
                response = self.llm_client.generate_with_tools(
                    messages=self.conversation_history,
                    tools=self._format_tools_for_llm()
                )

                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.get("content", ""),
                    "tool_calls": response.get("tool_calls", [])
                })

                # Check if LLM returned text response (done)
                if response.get("content") and not response.get("tool_calls"):
                    self.logger.info(f"Agent completed with response: {response['content']}")
                    return goal_check()

                # Execute tool calls if any
                if response.get("tool_calls"):
                    self.logger.info(f"Executing {len(response['tool_calls'])} tool calls")
                    tool_results = self._execute_tool_calls(response["tool_calls"])

                    # Add tool results to history
                    self.conversation_history.append({
                        "role": "tool",
                        "content": json.dumps(tool_results)
                    })

            except Exception as e:
                self.logger.error(f"Error in agent loop turn {turn + 1}: {e}")
                return False

        self.logger.warning(f"Max turns ({max_turns}) reached without achieving goal")
        return False

    def _execute_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Execute a list of tool calls.
        
        Args:
            tool_calls: List of tool call specifications
            
        Returns:
            List of tool execution results
        """
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("arguments", {})

            self.logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")

            if tool_name not in self.tools:
                error_msg = f"Unknown tool: {tool_name}"
                self.logger.error(error_msg)
                results.append({"error": error_msg})
                continue

            try:
                # Execute the tool
                tool_function = self.tools[tool_name]
                result = tool_function(**tool_args)

                results.append({
                    "tool": tool_name,
                    "result": result
                })

                self.logger.debug(f"Tool {tool_name} executed successfully")

            except Exception as e:
                error_msg = f"Tool {tool_name} failed: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                results.append({
                    "tool": tool_name,
                    "error": error_msg
                })

        return results

    def _format_tools_for_llm(self) -> list[dict[str, Any]]:
        """
        Format registered tools for LLM consumption.
        
        Returns:
            List of tool specifications in LLM-compatible format
        """
        # This will be implemented based on specific LLM requirements
        # For now, return empty list
        return []

    def _generate_tool_call_id(self) -> str:
        """
        Generate a unique tool call ID.
        
        Returns:
            Tool call ID string
        """
        self.tool_call_counter += 1
        return f"{self.agent_name}_call_{self.tool_call_counter:03d}"

    def save_conversation(self, file_path: Path | None = None) -> None:
        """
        Save conversation history to a file.
        
        Args:
            file_path: Path to save the conversation (defaults to workspace)
        """
        if file_path is None:
            file_path = self.workspace_dir / f"{self.agent_name}_conversation.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"Conversation saved to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save conversation: {e}")

    def load_conversation(self, file_path: Path) -> None:
        """
        Load conversation history from a file.
        
        Args:
            file_path: Path to load the conversation from
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                self.conversation_history = json.load(f)

            self.logger.info(f"Conversation loaded from {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to load conversation: {e}")
            self.conversation_history = []

