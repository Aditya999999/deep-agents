"""
ForgeX — AzureClaudeChat

LangChain BaseChatModel implementation for Azure-hosted Anthropic Claude.
Uses direct HTTP requests to Azure AI / Anthropic endpoints matching the proven curl pattern.
"""

import json
import time
from typing import Any, Dict, List, Optional, Union

import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict, Field

from app.core.logging import get_logger

logger = get_logger("llm.azure_claude")

# Request timeout configuration per spec reference
REQUEST_TIMEOUT = httpx.Timeout(connect=15.0, read=600.0, write=60.0, pool=60.0)
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2.0


class AzureClaudeChat(BaseChatModel):
    """
    LangChain chat model wrapper for Azure-hosted Anthropic Claude.
    
    Communicates directly with Azure AI Services / Anthropic endpoints.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str = Field(default="")
    base_url: str = Field(default="")
    model: str = Field(default="claude-sonnet-4-5-forgex-rnd")
    temperature: float = Field(default=0.0)
    max_tokens: int = Field(default=8192)
    tools: Optional[List[Any]] = Field(default=None)

    @property
    def _llm_type(self) -> str:
        return "azure-claude"

    def _get_endpoint_url(self) -> str:
        """Resolve the Azure Claude endpoint URL."""
        base = self.base_url.rstrip("/")
        if not base or base == "REPLACE_ME":
            return ""
        if base.endswith("/messages") or base.endswith("/chat/completions"):
            return base
        if "/models" in base:
            return f"{base}/chat/completions"
        return f"{base}/v1/messages"

    def _get_headers(self) -> Dict[str, str]:
        """Construct request headers with API key authentication."""
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if self.api_key and self.api_key != "REPLACE_ME":
            headers["api-key"] = self.api_key
            headers["x-api-key"] = self.api_key
        return headers

    def _convert_messages(self, messages: List[BaseMessage]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Separate system message from conversation messages and format for Anthropic."""
        system_prompt: Optional[str] = None
        formatted_messages: List[Dict[str, Any]] = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_prompt = str(msg.content)
            elif isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": str(msg.content)})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": str(msg.content)})
            elif isinstance(msg, ToolMessage):
                formatted_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id or "tool_call",
                            "content": str(msg.content),
                        }
                    ]
                })
            else:
                formatted_messages.append({"role": "user", "content": str(msg.content)})

        return system_prompt, formatted_messages

    def _format_payload(self, messages: List[BaseMessage], **kwargs: Any) -> Dict[str, Any]:
        """Build the JSON payload for the Anthropic Messages API."""
        system_prompt, formatted_msgs = self._convert_messages(messages)

        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "messages": formatted_msgs,
        }

        if system_prompt:
            payload["system"] = system_prompt

        return payload

    def is_configured(self) -> bool:
        """Check if valid Azure Claude credentials are provided."""
        return bool(
            self.api_key
            and self.api_key != "REPLACE_ME"
            and self.base_url
            and self.base_url != "REPLACE_ME"
        )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Synchronous chat completion."""
        if not self.is_configured():
            logger.info("Azure Claude credentials not configured; generating local response.")
            last_msg = messages[-1].content if messages else "Hello"
            reply = f"ForgeX received: {last_msg}"
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=reply))])

        url = self._get_endpoint_url()
        headers = self._get_headers()
        payload = self._format_payload(messages, **kwargs)

        for attempt in range(MAX_RETRIES):
            try:
                with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    content_blocks = data.get("content", [])
                    text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                    full_text = "".join(text_parts) if text_parts else data.get("message", {}).get("content", "")
                    return ChatResult(generations=[ChatGeneration(message=AIMessage(content=full_text))])
            except Exception as e:
                logger.warning(f"Azure Claude attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
                else:
                    logger.error(f"All {MAX_RETRIES} attempts to Azure Claude failed: {e}")
                    raise

        raise RuntimeError("Azure Claude generation failed unexpectedly.")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Asynchronous chat completion."""
        if not self.is_configured():
            logger.info("Azure Claude credentials not configured; generating local async response.")
            last_msg = messages[-1].content if messages else "Hello"
            reply = f"ForgeX received: {last_msg}"
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=reply))])

        url = self._get_endpoint_url()
        headers = self._get_headers()
        payload = self._format_payload(messages, **kwargs)

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    content_blocks = data.get("content", [])
                    text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                    full_text = "".join(text_parts) if text_parts else data.get("message", {}).get("content", "")
                    return ChatResult(generations=[ChatGeneration(message=AIMessage(content=full_text))])
            except Exception as e:
                logger.warning(f"Azure Claude async attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    import asyncio
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
                else:
                    logger.error(f"All {MAX_RETRIES} async attempts to Azure Claude failed: {e}")
                    raise

        raise RuntimeError("Azure Claude async generation failed unexpectedly.")
