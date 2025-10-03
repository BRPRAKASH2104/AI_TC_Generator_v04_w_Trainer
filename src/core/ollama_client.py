"""
Ollama API clients for the AI Test Case Generator.

This module provides both synchronous and asynchronous clients for interacting
with Ollama API endpoints, with proper error handling and performance optimizations
for Python 3.13.7+.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aiohttp
import requests

from core.exceptions import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaResponseError,
    OllamaTimeoutError,
)

if TYPE_CHECKING:
    from config import OllamaConfig

# Type aliases for better readability (PEP 695 style)
type JSONResponse = dict[str, Any]


class OllamaClient:
    """Handles all interactions with Ollama API with enhanced logging"""

    __slots__ = ("config", "proxies", "_session")

    def __init__(self, config: OllamaConfig = None):
        from config import OllamaConfig
        self.config = config or OllamaConfig()
        self.proxies = {"http": None, "https": None}
        # Reuse session for better performance (Python 3.13.7+ optimization)
        self._session = requests.Session()
        self._session.proxies.update(self.proxies)

    def generate_response(self, model_name: str, prompt: str, is_json: bool = False) -> str:
        """
        Generate response from Ollama model with proper error handling.

        Args:
            model_name: Name of the Ollama model to use
            prompt: Input prompt for generation
            is_json: Whether to request JSON-formatted output

        Returns:
            Generated response text

        Raises:
            OllamaConnectionError: When connection to Ollama fails
            OllamaTimeoutError: When request times out
            OllamaModelNotFoundError: When requested model is not available
            OllamaResponseError: When response is invalid
        """
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.config.keep_alive,  # Ollama v0.11.10+ optimization
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": self.config.num_ctx,  # Context window size
                "num_predict": self.config.num_predict,  # Response length limit
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        if is_json:
            payload["format"] = "json"

        try:
            response = self._session.post(
                self.config.api_url,
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()

            try:
                data: JSONResponse = response.json()
            except ValueError as e:
                raise OllamaResponseError(
                    f"Invalid JSON response from Ollama: {e}",
                    status_code=response.status_code
                ) from e

            return str(data.get("response", ""))

        except requests.ConnectionError as e:
            raise OllamaConnectionError(
                f"Failed to connect to Ollama at {self.config.host}:{self.config.port}. "
                f"Ensure Ollama is running with 'ollama serve'",
                host=self.config.host,
                port=self.config.port
            ) from e

        except requests.Timeout as e:
            raise OllamaTimeoutError(
                f"Ollama request timed out after {self.config.timeout}s for model '{model_name}'. "
                f"Try increasing timeout or using a faster model.",
                timeout=self.config.timeout
            ) from e

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(
                    f"Model '{model_name}' not found. Install it with: ollama pull {model_name}",
                    model=model_name
                ) from e
            else:
                raise OllamaResponseError(
                    f"Ollama HTTP error {e.response.status_code}: {e.response.text}",
                    status_code=e.response.status_code
                ) from e

        except requests.RequestException as e:
            raise OllamaConnectionError(
                f"Ollama request failed: {e}",
                host=self.config.host,
                port=self.config.port
            ) from e


class AsyncOllamaClient:
    """Async client for high-performance Ollama API interactions"""

    __slots__ = ("config", "session", "semaphore")

    def __init__(self, config: OllamaConfig = None):
        from config import OllamaConfig
        self.config = config or OllamaConfig()
        self.session: aiohttp.ClientSession | None = None
        # Configurable GPU/CPU-aware concurrency limit
        concurrency_limit = self.config.gpu_concurrency_limit  # Use GPU setting by default
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=100,  # Connection pool limit
            limit_per_host=30,  # Per-host connection limit
            keepalive_timeout=30,
            enable_cleanup_closed=True,
        )

        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout,
            connect=10,
            sock_read=self.config.timeout,
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "AI-TestCase-Generator/3.0"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def generate_response(self, model_name: str, prompt: str, is_json: bool = False) -> str:
        """
        Generate response from Ollama model asynchronously with proper error handling.

        Args:
            model_name: Name of the Ollama model to use
            prompt: Input prompt for generation
            is_json: Whether to request JSON-formatted output

        Returns:
            Generated response text

        Raises:
            OllamaConnectionError: When connection to Ollama fails
            OllamaTimeoutError: When request times out
            OllamaModelNotFoundError: When requested model is not available
            OllamaResponseError: When response is invalid
        """
        if not self.session:
            raise RuntimeError("AsyncOllamaClient must be used as async context manager")

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.config.keep_alive,
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": self.config.num_ctx,
                "num_predict": self.config.num_predict,
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        if is_json:
            payload["format"] = "json"

        async with self.semaphore:  # Limit concurrent requests
            try:
                async with self.session.post(self.config.api_url, json=payload) as response:
                    response.raise_for_status()
                    try:
                        data = await response.json()
                    except aiohttp.ContentTypeError as e:
                        raise OllamaResponseError(
                            f"Invalid JSON response from Ollama: {e}",
                            status_code=response.status
                        ) from e

                    return str(data.get("response", ""))

            except asyncio.TimeoutError as e:
                raise OllamaTimeoutError(
                    f"Ollama async request timed out after {self.config.timeout}s for model '{model_name}'",
                    timeout=self.config.timeout
                ) from e

            except aiohttp.ClientConnectorError as e:
                raise OllamaConnectionError(
                    f"Failed to connect to Ollama at {self.config.host}:{self.config.port}. "
                    f"Ensure Ollama is running with 'ollama serve'",
                    host=self.config.host,
                    port=self.config.port
                ) from e

            except aiohttp.ClientResponseError as e:
                if e.status == 404:
                    raise OllamaModelNotFoundError(
                        f"Model '{model_name}' not found. Install it with: ollama pull {model_name}",
                        model=model_name
                    ) from e
                else:
                    raise OllamaResponseError(
                        f"Ollama HTTP error {e.status}: {e.message}",
                        status_code=e.status
                    ) from e

            except aiohttp.ClientError as e:
                raise OllamaConnectionError(
                    f"Ollama async client error: {e}",
                    host=self.config.host,
                    port=self.config.port
                ) from e

    async def generate_with_retry(self, model_name: str, prompt: str, is_json: bool = False, max_retries: int = 3) -> str:
        """Generate response with exponential backoff retry logic"""
        for attempt in range(max_retries + 1):
            try:
                result = await self.generate_response(model_name, prompt, is_json)
                if result:  # Success
                    return result
            except Exception:
                pass  # Continue to retry

            if attempt < max_retries:
                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2 ** attempt)

        return ""  # All retries failed
