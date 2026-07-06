"""
Ollama API clients for the AI Test Case Generator.

This module provides both synchronous and asynchronous clients for interacting
with Ollama API endpoints, with proper error handling and performance optimizations
for Python 3.14+.
"""

import asyncio
import base64
import logging
from pathlib import Path  # noqa: TC003 - Used at runtime for file operations
from typing import TYPE_CHECKING, Any, Self

import aiohttp
import requests

from src.config import OllamaConfig

from .exceptions import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaResponseError,
    OllamaTimeoutError,
)

if TYPE_CHECKING:
    from types import TracebackType

    from src.config import OllamaConfig

# Module logger for Ollama client
_logger = logging.getLogger(__name__)

# Type aliases for better readability (PEP 695 style)
type JSONResponse = dict[str, Any]


def _build_generate_payload(
    config: OllamaConfig,
    model_name: str,
    prompt: str,
    is_json: bool,
    images_base64: list[str] | None,
    context_window: int,
) -> dict[str, Any]:
    """Build the /api/generate request payload (shared by sync and async clients)."""
    payload: dict[str, Any] = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "keep_alive": config.keep_alive,
        "options": {
            "temperature": config.temperature,
            "num_ctx": context_window,
            "num_predict": config.num_predict,
            "top_k": 40,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "tfs_z": config.tfs_z,
            "typical_p": config.typical_p,
            "repeat_last_n": config.repeat_last_n,
        },
    }

    if images_base64:
        payload["images"] = images_base64

    if is_json:
        payload["format"] = "json"

    # Logprobs for confidence scoring (Ollama 0.13.3+)
    if getattr(config, "enable_logprobs", False):
        payload["logprobs"] = True
        payload["top_logprobs"] = getattr(config, "top_logprobs", 1)

    return payload


def _load_images_base64(image_paths: list[Path] | None) -> list[str]:
    """Read and base64-encode image files, skipping unreadable ones with a warning."""
    images_base64: list[str] = []
    failed_count = 0
    for img_path in image_paths or []:
        try:
            with open(img_path, "rb") as img_file:
                img_data = img_file.read()
                images_base64.append(base64.b64encode(img_data).decode("utf-8"))
        except FileNotFoundError:
            failed_count += 1
            _logger.warning(f"Image file not found: {img_path}")
        except PermissionError:
            failed_count += 1
            _logger.warning(f"Permission denied reading image: {img_path}")
        except Exception as e:
            failed_count += 1
            _logger.warning(f"Failed to load image {img_path}: {e}")

    if failed_count > 0:
        _logger.warning(
            f"Failed to load {failed_count}/{len(image_paths or [])} image(s). "
            "Vision model will proceed with available images."
        )

    return images_base64


class OllamaClient:
    """Handles all interactions with Ollama API with enhanced logging"""

    __slots__ = ("config", "proxies", "_session")

    def __init__(self, config: OllamaConfig | None = None):
        from src.config import OllamaConfig

        self.config = config or OllamaConfig()
        # None values are requests' documented way to disable proxying for a
        # scheme; typeshed's Session.proxies stub only declares dict[str, str].
        self.proxies: dict[str, str | None] = {"http": None, "https": None}
        # Reuse session for better performance (Python 3.14+ optimization)
        self._session = requests.Session()
        self._session.proxies.update(self.proxies)  # type: ignore[arg-type]

    def close(self) -> None:
        """Close the underlying HTTP session and its connection pool."""
        self._session.close()

    def __enter__(self) -> OllamaClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def generate_completion(
        self,
        model_name: str,
        prompt: str,
        is_json: bool = False,
        return_full_response: bool = True,
    ) -> dict | str:
        """
        Generate completion from Ollama model with full response control.

        Args:
            model_name: Name of the Ollama model to use
            prompt: Input prompt for generation
            is_json: Whether to request JSON-formatted output
            return_full_response: If True, returns full JSON dict. If False, returns just text.

        Returns:
            Full response dictionary (if return_full_response=True) or response text string.
        """
        # Text-only generation is the vision path without images; a single
        # request/error-handling implementation lives there
        return self.generate_response_with_vision(
            model_name,
            prompt,
            image_paths=None,
            is_json=is_json,
            return_full_response=return_full_response,
        )

    def generate_response(self, model_name: str, prompt: str, is_json: bool = False) -> str:
        """
        Generate response from Ollama model (backward compatibility wrapper).

        Args:
            model_name: Name of the Ollama model to use
            prompt: Input prompt for generation
            is_json: Whether to request JSON-formatted output

        Returns:
            Generated response text
        """
        # Call the new method but request only text (implicit backward compatibility)
        result = self.generate_completion(model_name, prompt, is_json, return_full_response=False)
        assert isinstance(result, str), "return_full_response=False must yield a str"
        return result

    def generate_response_with_vision(
        self,
        model_name: str,
        prompt: str,
        image_paths: list[Path] | None = None,
        is_json: bool = False,
        return_full_response: bool = False,
    ) -> dict | str:
        """
        Generate response from Ollama vision model with optional image inputs.

        This method supports multimodal models like llama3.2-vision that can process
        both text and images. Images are encoded as base64 and sent with the prompt.

        Args:
            model_name: Name of the Ollama vision model to use (e.g., "llama3.2-vision:11b")
            prompt: Input prompt for generation
            image_paths: Optional list of image file paths to include
            is_json: Whether to request JSON-formatted output
            return_full_response: If True, returns full JSON dict. If False, returns just text.

        Returns:
            Full response dictionary (if return_full_response=True) or response text string.

        Raises:
            OllamaConnectionError: When connection to Ollama fails
            OllamaTimeoutError: When request times out
            OllamaModelNotFoundError: When requested model is not available
            OllamaResponseError: When response is invalid
        """
        # Use vision_context_window for vision models (larger context for image patches)
        context_window = self.config.vision_context_window if image_paths else self.config.num_ctx
        images_base64 = _load_images_base64(image_paths) if image_paths else None
        payload = _build_generate_payload(
            self.config, model_name, prompt, is_json, images_base64, context_window
        )

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
                    f"Invalid JSON response from Ollama: {e}", status_code=response.status_code
                ) from e

            if return_full_response:
                return data
            return str(data.get("response", ""))

        except requests.ConnectionError as e:
            raise OllamaConnectionError(
                f"Failed to connect to Ollama at {self.config.host}:{self.config.port}. "
                f"Ensure Ollama is running with 'ollama serve'",
                host=self.config.host,
                port=self.config.port,
            ) from e

        except requests.Timeout as e:
            raise OllamaTimeoutError(
                f"Ollama request timed out after {self.config.timeout}s for model '{model_name}'. "
                f"Try increasing timeout or using a faster model.",
                timeout=self.config.timeout,
            ) from e

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(
                    f"Model '{model_name}' not found. Install it with: ollama pull {model_name}",
                    model=model_name,
                ) from e
            else:
                try:
                    error_details = e.response.json()
                    error_msg = error_details.get("error", e.response.text)
                except Exception:
                    error_msg = e.response.text

                raise OllamaResponseError(
                    f"Ollama HTTP error {e.response.status_code}: {error_msg}",
                    status_code=e.response.status_code,
                    response_body=error_msg,
                ) from e

        except requests.RequestException as e:
            raise OllamaConnectionError(
                f"Ollama request failed: {e}", host=self.config.host, port=self.config.port
            ) from e


class AsyncOllamaClient:
    """Async client for high-performance Ollama API interactions"""

    __slots__ = ("config", "session", "semaphore")

    def __init__(self, config: OllamaConfig | None = None, concurrency_limit: int | None = None):
        from src.config import OllamaConfig

        self.config = config or OllamaConfig()
        self.session: aiohttp.ClientSession | None = None
        # Effective request concurrency: an explicit limit (wired from the
        # CLI --max-concurrent via the HP processor) overrides the GPU-aware
        # default; the semaphore is the single throttle for all requests.
        if concurrency_limit is None or concurrency_limit < 1:
            concurrency_limit = self.config.gpu_concurrency_limit
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def __aenter__(self) -> Self:
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

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def generate_completion(
        self,
        model_name: str,
        prompt: str,
        is_json: bool = False,
        return_full_response: bool = True,
    ) -> dict | str:
        """
        Generate completion from Ollama model asynchronously with full response control.

        Args:
            model_name: Name of the Ollama model to use
            prompt: Input prompt for generation
            is_json: Whether to request JSON-formatted output
            return_full_response: If True, returns full JSON dict. If False, returns just text.

        Returns:
            Full response dictionary (if return_full_response=True) or response text string.
        """
        # Text-only generation is the vision path without images; a single
        # request/error-handling implementation lives there
        return await self.generate_response_with_vision(
            model_name,
            prompt,
            image_paths=None,
            is_json=is_json,
            return_full_response=return_full_response,
        )

    async def generate_response(self, model_name: str, prompt: str, is_json: bool = False) -> str:
        """
        Generate response from Ollama model asynchronously (backward compatibility wrapper).

        Args:
            model_name: Name of the Ollama model to use
            prompt: Input prompt for generation
            is_json: Whether to request JSON-formatted output

        Returns:
            Generated response text
        """
        # Call the new method but request only text
        result = await self.generate_completion(
            model_name, prompt, is_json, return_full_response=False
        )
        assert isinstance(result, str), "return_full_response=False must yield a str"
        return result

    async def generate_response_with_vision(
        self,
        model_name: str,
        prompt: str,
        image_paths: list[Path] | None = None,
        is_json: bool = False,
        return_full_response: bool = False,
    ) -> dict | str:
        """
        Generate response from Ollama vision model with optional image inputs (async version).

        This async method supports multimodal models like llama3.2-vision that can process
        both text and images. Images are encoded as base64 and sent with the prompt.

        Args:
            model_name: Name of the Ollama vision model to use (e.g., "llama3.2-vision:11b")
            prompt: Input prompt for generation
            image_paths: Optional list of image file paths to include
            is_json: Whether to request JSON-formatted output
            return_full_response: If True, returns full JSON dict. If False, returns just text.

        Returns:
            Full response dictionary (if return_full_response=True) or response text string.

        Raises:
            OllamaConnectionError: When connection to Ollama fails
            OllamaTimeoutError: When request times out
            OllamaModelNotFoundError: When requested model is not available
            OllamaResponseError: When response is invalid
        """
        if not self.session:
            raise RuntimeError("AsyncOllamaClient must be used as async context manager")

        # Use vision_context_window for vision models (larger context for image patches)
        context_window = self.config.vision_context_window if image_paths else self.config.num_ctx
        images_base64 = _load_images_base64(image_paths) if image_paths else None
        payload = _build_generate_payload(
            self.config, model_name, prompt, is_json, images_base64, context_window
        )

        async with self.semaphore:  # Limit concurrent requests
            try:
                async with self.session.post(self.config.api_url, json=payload) as response:
                    response.raise_for_status()
                    try:
                        data: JSONResponse = await response.json()
                    except aiohttp.ContentTypeError as e:
                        raise OllamaResponseError(
                            f"Invalid JSON response from Ollama: {e}", status_code=response.status
                        ) from e

                    if return_full_response:
                        return data
                    return str(data.get("response", ""))

            except TimeoutError as e:
                raise OllamaTimeoutError(
                    f"Ollama async request timed out after {self.config.timeout}s for model '{model_name}'",
                    timeout=self.config.timeout,
                ) from e

            except aiohttp.ClientConnectorError as e:
                raise OllamaConnectionError(
                    f"Failed to connect to Ollama at {self.config.host}:{self.config.port}. "
                    f"Ensure Ollama is running with 'ollama serve'",
                    host=self.config.host,
                    port=self.config.port,
                ) from e

            except aiohttp.ClientResponseError as e:
                if e.status == 404:
                    raise OllamaModelNotFoundError(
                        f"Model '{model_name}' not found. Install it with: ollama pull {model_name}",
                        model=model_name,
                    ) from e
                else:
                    raise OllamaResponseError(
                        f"Ollama HTTP error {e.status}: {e.message}",
                        status_code=e.status,
                        response_body=str(e.message),
                    ) from e

            except aiohttp.ClientError as e:
                raise OllamaConnectionError(
                    f"Ollama async client error: {e}", host=self.config.host, port=self.config.port
                ) from e
