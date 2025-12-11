"""Gemini LLM client implementation."""

import json
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from google.oauth2 import service_account

from kiwi_video.core.exceptions import ProviderError
from kiwi_video.providers.llm.base import BaseLLMClient
from kiwi_video.utils.config import settings
from kiwi_video.utils.logger import get_logger


class GeminiClient(BaseLLMClient):
    """
    Google Gemini LLM client implementation.
    
    Supports text generation, streaming, and tool calling.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-2.5-pro"
    ) -> None:
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google AI API key (uses settings if not provided)
            model_name: Model name to use
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name
        self.logger = get_logger("gemini_client")

        # Initialize client based on authentication method
        if settings.google_application_credentials:
            # Use service account credentials for Vertex AI
            try:
                scopes = ["https://www.googleapis.com/auth/cloud-platform"]
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_application_credentials,
                    scopes=scopes
                )
                self.client = genai.Client(
                    credentials=credentials,
                    vertexai=True,
                    project=settings.gcp_project_id,
                    location="global"
                )
                self.logger.info("Initialized Gemini client with Vertex AI")
            except Exception as e:
                self.logger.warning(f"Failed to init Vertex AI client: {e}, falling back to API key")
                self.client = genai.Client(api_key=self.api_key)
        else:
            # Use API key
            self.client = genai.Client(api_key=self.api_key)
            self.logger.info("Initialized Gemini client with API key")

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
            
        Raises:
            ProviderError: If generation fails
        """
        try:
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or 8192,
                response_mime_type="text/plain"
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=config
            )

            return response.text

        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            raise ProviderError("gemini", f"Text generation failed: {e}")

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
            
        Raises:
            ProviderError: If generation fails
        """
        try:
            # Convert messages to Gemini format
            contents = self._convert_messages(messages)

            # Convert tools to Gemini format
            tool_declarations = self._convert_tools(tools)

            # Configure tool calling
            if tool_declarations:
                gemini_tools = types.Tool(function_declarations=tool_declarations)
                tool_config = types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(mode="ANY")
                )
                config = types.GenerateContentConfig(
                    tools=[gemini_tools],
                    tool_config=tool_config,
                    temperature=temperature
                )
            else:
                config = types.GenerateContentConfig(temperature=temperature)

            # Generate response
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

            # Parse response
            result = {
                "content": "",
                "tool_calls": []
            }

            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                content = candidate.content

                for part in content.parts:
                    if part.text:
                        result["content"] = part.text
                    elif part.function_call:
                        result["tool_calls"].append({
                            "name": part.function_call.name,
                            "arguments": dict(part.function_call.args)
                        })

            return result

        except Exception as e:
            self.logger.error(f"Tool-based generation failed: {e}")
            raise ProviderError("gemini", f"Tool calling failed: {e}")

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
            
        Raises:
            ProviderError: If generation fails
        """
        try:
            config = types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="text/plain"
            )

            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

            output_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config
            ):
                if hasattr(chunk, "text") and chunk.text:
                    output_text += chunk.text

            return output_text

        except Exception as e:
            self.logger.error(f"Streaming generation failed: {e}")
            raise ProviderError("gemini", f"Streaming failed: {e}")

    def stream(
        self,
        prompt: str,
        purpose: str = "generation",
        if_search: bool = False
    ) -> str:
        """
        Synchronous streaming generation (compatibility method).
        
        Args:
            prompt: Input prompt
            purpose: Purpose of generation
            if_search: Whether to enable web search
            
        Returns:
            Generated text
        """
        try:
            temperature = 0.2 if purpose == "tool_selection" else 0.6

            tools_for_config = [types.Tool(google_search=types.GoogleSearch())] if if_search else None
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

            config = types.GenerateContentConfig(
                tools=tools_for_config,
                response_mime_type="text/plain",
                temperature=temperature
            )

            output_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=config
            ):
                if hasattr(chunk, "text") and chunk.text:
                    output_text += chunk.text

            return output_text

        except Exception as e:
            self.logger.error(f"Stream generation failed: {e}")
            return f"Error: {e}"

    def _convert_messages(self, messages: list[dict[str, Any]]) -> list[types.Content]:
        """
        Convert messages to Gemini Content format.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of Gemini Content objects
        """
        contents = []

        for msg in messages:
            role = msg.get("role", "user")
            content_text = msg.get("content", "")

            # Map role to Gemini roles
            if role in ["system", "assistant"]:
                gemini_role = "model"
            else:
                gemini_role = "user"

            if content_text:
                contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=content_text)]
                    )
                )

        return contents

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[types.FunctionDeclaration]:
        """
        Convert tool definitions to Gemini FunctionDeclaration format.
        
        Args:
            tools: List of tool definitions
            
        Returns:
            List of Gemini FunctionDeclaration objects
        """
        declarations = []

        for tool in tools:
            if "name" in tool and "description" in tool:
                declarations.append(
                    types.FunctionDeclaration(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool.get("parameters", {})
                    )
                )

        return declarations

    def analyze_image(
        self,
        prompt: str,
        image_path: Path,
        response_schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Analyze an image with Gemini Vision.
        
        Args:
            prompt: Analysis prompt
            image_path: Path to image file
            response_schema: Optional JSON schema for structured response
            
        Returns:
            Analysis result
            
        Raises:
            ProviderError: If analysis fails
        """
        try:
            # Load image
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            # Create content with image
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/png",
                                data=image_bytes
                            )
                        )
                    ]
                )
            ]

            # Configure response
            config_params = {
                "temperature": 0.4,
                "max_output_tokens": 8192
            }

            if response_schema:
                config_params["response_mime_type"] = "application/json"
                config_params["response_schema"] = response_schema

            config = types.GenerateContentConfig(**config_params)

            # Generate response
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

            # Parse response
            if response_schema:
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    return {"raw_response": response.text}
            else:
                return {"analysis": response.text}

        except Exception as e:
            self.logger.error(f"Image analysis failed: {e}")
            raise ProviderError("gemini", f"Image analysis failed: {e}")

