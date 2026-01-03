"""LLM Client for agent interactions.

This module provides a unified interface for agents to interact with
language models (Claude claude-sonnet-4-20250514 by default). It handles:
- API authentication
- Request formatting
- Response parsing
- Error handling and retries
- Token usage tracking
- Rate limiting
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Awaitable
from enum import Enum

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL = "local"  # For testing/development


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    
    provider: LLMProvider = LLMProvider.ANTHROPIC
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout_seconds: float = 60.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    
    # API settings
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    
    # Resource management
    max_concurrent_requests: int = 10
    tokens_per_minute_limit: int = 100000


@dataclass
class LLMMessage:
    """A message in an LLM conversation."""
    
    role: str  # "system", "user", "assistant"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """Response from LLM."""
    
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class StreamChunk:
    """A chunk from streaming response."""
    
    content: str
    is_final: bool = False
    accumulated_content: str = ""


class LLMClient:
    """Unified client for LLM interactions.
    
    Provides a consistent interface for making LLM calls across different
    providers, with built-in error handling, retries, and token tracking.
    
    Example:
        client = LLMClient(config)
        response = await client.generate(
            system_prompt="You are a fiscal policy analyst.",
            user_prompt="Analyze this tax provision...",
        )
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the LLM client.
        
        Args:
            config: LLM configuration. Uses defaults if not provided.
        """
        self.config = config or LLMConfig()
        self._client = None
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        # Token tracking
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._request_count = 0
        
        # Initialize provider client
        self._init_client()
    
    def _init_client(self) -> None:
        """Initialize the provider-specific client."""
        if self.config.provider == LLMProvider.ANTHROPIC:
            if not ANTHROPIC_AVAILABLE:
                logger.warning(
                    "Anthropic package not installed. Install with: pip install anthropic"
                )
                return
            
            api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning(
                    "ANTHROPIC_API_KEY not set. LLM calls will use mock responses."
                )
                return
            
            self._client = anthropic.AsyncAnthropic(api_key=api_key)
            logger.info(f"Initialized Anthropic client with model {self.config.model}")
        
        elif self.config.provider == LLMProvider.LOCAL:
            logger.info("Using local/mock LLM provider for testing")
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream_callback: Optional[Callable[[StreamChunk], Awaitable[None]]] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            system_prompt: System-level instructions
            user_prompt: User input/query
            temperature: Override config temperature
            max_tokens: Override config max_tokens
            stream_callback: Optional callback for streaming responses
        
        Returns:
            LLMResponse with generated content and metadata
        """
        async with self._semaphore:
            return await self._generate_with_retry(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream_callback=stream_callback,
            )
    
    async def _generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        stream_callback: Optional[Callable[[StreamChunk], Awaitable[None]]] = None,
    ) -> LLMResponse:
        """Generate with retry logic."""
        last_error = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = datetime.now()
                
                if self.config.provider == LLMProvider.ANTHROPIC and self._client:
                    response = await self._call_anthropic(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream_callback=stream_callback,
                    )
                else:
                    # Mock response for testing
                    response = await self._mock_response(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                    )
                
                latency = (datetime.now() - start_time).total_seconds() * 1000
                response.latency_ms = latency
                
                # Update tracking
                self._total_input_tokens += response.input_tokens
                self._total_output_tokens += response.output_tokens
                self._request_count += 1
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM request failed (attempt {attempt + 1}/{self.config.retry_attempts}): {e}"
                )
                
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay_seconds * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        # All retries failed
        logger.error(f"LLM request failed after {self.config.retry_attempts} attempts")
        raise last_error or RuntimeError("LLM request failed")
    
    async def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        stream_callback: Optional[Callable[[StreamChunk], Awaitable[None]]] = None,
    ) -> LLMResponse:
        """Make a call to Anthropic's Claude API."""
        if stream_callback:
            return await self._call_anthropic_streaming(
                system_prompt, user_prompt, temperature, max_tokens, stream_callback
            )
        
        response = await self._client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        
        content = response.content[0].text if response.content else ""
        
        return LLMResponse(
            content=content,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason or "stop",
            raw_response=response.model_dump() if hasattr(response, 'model_dump') else None,
        )
    
    async def _call_anthropic_streaming(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        stream_callback: Callable[[StreamChunk], Awaitable[None]],
    ) -> LLMResponse:
        """Make a streaming call to Anthropic's Claude API."""
        accumulated = ""
        input_tokens = 0
        output_tokens = 0
        
        async with self._client.messages.stream(
            model=self.config.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                accumulated += text
                await stream_callback(StreamChunk(
                    content=text,
                    is_final=False,
                    accumulated_content=accumulated,
                ))
            
            # Get final message for token counts
            final_message = await stream.get_final_message()
            input_tokens = final_message.usage.input_tokens
            output_tokens = final_message.usage.output_tokens
        
        # Send final chunk
        await stream_callback(StreamChunk(
            content="",
            is_final=True,
            accumulated_content=accumulated,
        ))
        
        return LLMResponse(
            content=accumulated,
            model=self.config.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            finish_reason="stop",
        )
    
    async def _mock_response(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResponse:
        """Generate a mock response for testing."""
        # Simulate latency
        await asyncio.sleep(0.1)
        
        # Generate a structured mock response based on the prompt
        mock_content = self._generate_mock_content(system_prompt, user_prompt)
        
        return LLMResponse(
            content=mock_content,
            model="mock-model",
            input_tokens=len(system_prompt.split()) + len(user_prompt.split()),
            output_tokens=len(mock_content.split()),
            total_tokens=len(system_prompt.split()) + len(user_prompt.split()) + len(mock_content.split()),
            finish_reason="stop",
        )
    
    def _generate_mock_content(self, system_prompt: str, user_prompt: str) -> str:
        """Generate mock analysis content based on prompts."""
        # Check if this is an analysis request
        if "analyze" in system_prompt.lower() or "analysis" in user_prompt.lower():
            return json.dumps({
                "findings": [
                    {
                        "category": "revenue",
                        "description": "Mock finding: Estimated revenue impact of policy",
                        "confidence": 0.75,
                        "impact_magnitude": "medium",
                        "fiscal_impact": {
                            "amount_billions": 50.0,
                            "time_period": "10-year",
                            "confidence_low": 40.0,
                            "confidence_mid": 50.0,
                            "confidence_high": 60.0,
                        }
                    }
                ],
                "overall_confidence": 0.7,
                "executive_summary": "Mock analysis summary for testing purposes.",
                "key_takeaways": [
                    "This is a mock response",
                    "Actual LLM integration required for real analysis"
                ],
                "uncertainty_areas": [
                    "Mock uncertainty area"
                ]
            }, indent=2)
        
        # Check if this is a critique request
        if "critique" in system_prompt.lower() or "critique" in user_prompt.lower():
            return json.dumps({
                "critiques": [
                    {
                        "critique_type": "methodology",
                        "argument": "Mock critique for testing",
                        "severity": "moderate",
                        "suggested_revision": "Consider mock revision"
                    }
                ]
            }, indent=2)
        
        # Default mock response
        return json.dumps({
            "response": "Mock LLM response for testing",
            "note": "Configure ANTHROPIC_API_KEY for real responses"
        }, indent=2)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics."""
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "request_count": self._request_count,
            "avg_tokens_per_request": (
                (self._total_input_tokens + self._total_output_tokens) / self._request_count
                if self._request_count > 0 else 0
            ),
        }
    
    def reset_usage_stats(self) -> None:
        """Reset token usage tracking."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._request_count = 0


# Global client instance (can be configured at startup)
_global_client: Optional[LLMClient] = None


def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """Get the global LLM client instance.
    
    Args:
        config: Optional configuration. If provided and no client exists,
                creates a new client with this config.
    
    Returns:
        LLMClient instance
    """
    global _global_client
    
    if _global_client is None:
        _global_client = LLMClient(config)
    
    return _global_client


def configure_llm_client(config: LLMConfig) -> LLMClient:
    """Configure or reconfigure the global LLM client.
    
    Args:
        config: New configuration to use
    
    Returns:
        New LLMClient instance
    """
    global _global_client
    _global_client = LLMClient(config)
    return _global_client
