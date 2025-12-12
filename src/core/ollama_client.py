"""
Ollama API clients for the AI Test Case Generator.

This module provides both synchronous and asynchronous clients for interacting
with Ollama API endpoints, with proper error handling and performance optimizations
for Python 3.13.7+.
"""

import asyncio
import base64
import logging
from pathlib import Path  # noqa: TC003 - Used at runtime for file operations
from typing import TYPE_CHECKING, Any

import aiohttp
import requests

from .exceptions import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaResponseError,
    OllamaTimeoutError,
)

if TYPE_CHECKING:
    from src.config import OllamaConfig

# Module logger for Ollama client
_logger = logging.getLogger(__name__)

# Type aliases for better readability (PEP 695 style)
type JSONResponse = dict[str, Any]


class OllamaClient:
    """Handles all interactions with Ollama API with enhanced logging"""

    __slots__ = ("config", "proxies", "_session", "_version_validated", "_available_features")

    def __init__(self, config: OllamaConfig = None):
        from src.config import OllamaConfig

        self.config = config or OllamaConfig()
        self.proxies = {"http": None, "https": None}
        # Reuse session for better performance (Python 3.13.7+ optimization)
        self._session = requests.Session()
        self._session.proxies.update(self.proxies)

        # Version and feature validation
        self._version_validated = False
        self._available_features: dict[str, bool] = {}

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
                "tfs_z": self.config.tfs_z,
                "typical_p": self.config.typical_p,
                "repeat_last_n": self.config.repeat_last_n,
            },
        }

        # Add logprobs if enabled (new in Ollama 0.13.3)
        if getattr(self.config, "enable_logprobs", False):
            payload["logprobs"] = True
            payload["top_logprobs"] = getattr(self.config, "top_logprobs", 1)

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
        return self.generate_completion(
            model_name, prompt, is_json, return_full_response=False
        )

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

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.config.keep_alive,
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": context_window,
                "num_predict": self.config.num_predict,
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "tfs_z": self.config.tfs_z,
                "typical_p": self.config.typical_p,
                "repeat_last_n": self.config.repeat_last_n,
            },
        }

        # Add images if provided (for vision models)
        if image_paths:
            images_base64 = []
            failed_count = 0
            for img_path in image_paths:
                try:
                    with open(img_path, "rb") as img_file:
                        img_data = img_file.read()
                        img_b64 = base64.b64encode(img_data).decode("utf-8")
                        images_base64.append(img_b64)
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
                    f"Failed to load {failed_count}/{len(image_paths)} image(s). "
                    "Vision model will proceed with available images."
                )

            if images_base64:
                payload["images"] = images_base64

        if is_json:
            payload["format"] = "json"

        # Add logprobs if enabled
        if getattr(self.config, "enable_logprobs", False):
            payload["logprobs"] = True
            payload["top_logprobs"] = getattr(self.config, "top_logprobs", 1)

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

    def _check_version_compatibility(self) -> None:
        """
        Check Ollama version compatibility and available features (sync version).

        This method validates that the connected Ollama instance meets
        minimum version requirements and detects available API features.
        """
        if self._version_validated:
            return  # Already validated

        try:
            response = self._session.get(
                self.config.version_url,
                timeout=10,  # Shorter timeout for version check
            )
            response.raise_for_status()

            try:
                data = response.json()
                version_str = data.get("version", "")
                if not version_str:
                    raise OllamaResponseError("No version information received from Ollama")

                # Parse version (e.g., "0.12.5")
                version_parts = version_str.split(".")
                if len(version_parts) < 3:
                    raise OllamaResponseError(f"Invalid version format: {version_str}")

                major, minor, patch = map(int, version_parts[:3])

                # Check minimum version (0.12.5)
                min_major, min_minor, min_patch = 0, 12, 5
                if (major, minor, patch) < (min_major, min_minor, min_patch):
                    raise OllamaResponseError(
                        f"Ollama version {version_str} is incompatible. "
                        f"Minimum required: {min_major}.{min_minor}.{min_patch}",
                        status_code=200,
                        response_body=f"Current: {version_str}, Required: >=0.12.5",
                    )

                # Detect available features based on version
                self._available_features = {
                    "version_endpoint": True,
                    "gpu_offload": (major, minor, patch) >= (0, 12, 5),
                    "enhanced_context": (major, minor, patch) >= (0, 12, 5),
                    "detailed_errors": (major, minor, patch) >= (0, 12, 5),
                }

                self._version_validated = True

            except ValueError as e:
                raise OllamaResponseError(
                    f"Invalid version response format from Ollama: {e}",
                    status_code=response.status_code,
                ) from e

        except requests.ConnectionError as e:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.config.version_url}. "
                f"Ensure Ollama is running with 'ollama serve'",
                host=self.config.host,
                port=self.config.port,
            ) from e
        except requests.Timeout as e:
            raise OllamaConnectionError(
                "Timeout connecting to Ollama for version check. "
                "Check if Ollama is running and accessible",
                host=self.config.host,
                port=self.config.port,
            ) from e
        except requests.HTTPError as e:
            raise OllamaResponseError(
                f"Ollama version check failed: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                response_body=e.response.text,
            ) from e

    def is_feature_available(self, feature: str) -> bool:
        """
        Check if a specific Ollama feature is available.

        Args:
            feature: Feature name to check (e.g., 'gpu_offload', 'enhanced_context')

        Returns:
            True if feature is available, False otherwise
        """
        if not self._version_validated:
            try:
                self._check_version_compatibility()
            except Exception:
                return False  # Conservative fallback

        return self._available_features.get(feature, False)

    def get_model_info(self, model_name: str) -> dict[str, Any] | None:
        """
        Get detailed information about a model using /api/show endpoint (async client).

        Args:
            model_name: Name of the model to get information about

        Returns:
            Dictionary containing model information, or None if not available
        """
        # For async client, we use session for show endpoint (similar to version check)
        try:
            # Use synchronous requests for model info since it's simple metadata
            temp_session = requests.Session()
            response = temp_session.post(
                self.config.show_url,
                json={"name": model_name},
                timeout=self.config.timeout,
            )
            response.raise_for_status()

            try:
                data = response.json()
                return data
            except ValueError as e:
                raise OllamaResponseError(
                    f"Invalid JSON response from Ollama /api/show: {e}",
                    status_code=response.status_code,
                ) from e

        except requests.ConnectionError as e:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.config.host}:{self.config.port}. "
                f"Ensure Ollama is running with 'ollama serve'",
                host=self.config.host,
                port=self.config.port,
            ) from e

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(
                    f"Model '{model_name}' not found. Use 'ollama pull {model_name}' to download it.",
                    model=model_name,
                ) from e
            else:
                try:
                    error_details = e.response.json()
                    error_msg = error_details.get("error", e.response.text)
                except Exception:
                    error_msg = e.response.text

                raise OllamaResponseError(
                    f"Ollama HTTP error {e.response.status_code} getting model info: {error_msg}",
                    status_code=e.response.status_code,
                    response_body=error_msg,
                ) from e

        except requests.RequestException as e:
            raise OllamaConnectionError(
                f"Ollama request failed: {e}", host=self.config.host, port=self.config.port
            ) from e

    def validate_model_compatibility(self, model_name: str) -> bool:
        """
        Validate if a model is compatible with current requirements (async client).

        Args:
            model_name: Name of the model to validate

        Returns:
            True if model is compatible, False otherwise
        """
        try:
            model_info = self.get_model_info(model_name)
            return model_info is not None
        except Exception:
            return False


class AsyncOllamaClient:
    """Async client for high-performance Ollama API interactions"""

    __slots__ = ("config", "session", "semaphore", "_version_validated", "_available_features")

    def __init__(self, config: OllamaConfig = None):
        from src.config import OllamaConfig

        self.config = config or OllamaConfig()
        self.session: aiohttp.ClientSession | None = None
        # Configurable GPU/CPU-aware concurrency limit
        concurrency_limit = self.config.gpu_concurrency_limit  # Use GPU setting by default
        self.semaphore = asyncio.Semaphore(concurrency_limit)

        # Version and feature validation for async client
        self._version_validated = False
        self._available_features: dict[str, bool] = {}

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
                "tfs_z": self.config.tfs_z,
                "typical_p": self.config.typical_p,
                "repeat_last_n": self.config.repeat_last_n,
            },
        }

        # Add logprobs if enabled
        if getattr(self.config, "enable_logprobs", False):
            payload["logprobs"] = True
            payload["top_logprobs"] = getattr(self.config, "top_logprobs", 1)

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
                    # Ollama 0.12.5 enhanced error details
                    raise OllamaResponseError(
                        f"Ollama HTTP error {e.status}: {e.message}",
                        status_code=e.status,
                        response_body=str(e.message),
                    ) from e

            except aiohttp.ClientError as e:
                raise OllamaConnectionError(
                    f"Ollama async client error: {e}", host=self.config.host, port=self.config.port
                ) from e

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
        return await self.generate_completion(
            model_name, prompt, is_json, return_full_response=False
        )

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

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.config.keep_alive,
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": context_window,
                "num_predict": self.config.num_predict,
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "tfs_z": self.config.tfs_z,
                "typical_p": self.config.typical_p,
                "repeat_last_n": self.config.repeat_last_n,
            },
        }

        # Add images if provided (for vision models)
        if image_paths:
            images_base64 = []
            failed_count = 0
            for img_path in image_paths:
                try:
                    with open(img_path, "rb") as img_file:
                        img_data = img_file.read()
                        img_b64 = base64.b64encode(img_data).decode("utf-8")
                        images_base64.append(img_b64)
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
                    f"Failed to load {failed_count}/{len(image_paths)} image(s). "
                    "Vision model will proceed with available images."
                )

            if images_base64:
                payload["images"] = images_base64

        if is_json:
            payload["format"] = "json"

        # Add logprobs if enabled
        if getattr(self.config, "enable_logprobs", False):
            payload["logprobs"] = True
            payload["top_logprobs"] = getattr(self.config, "top_logprobs", 1)

        async with self.semaphore:  # Limit concurrent requests
            try:
                async with self.session.post(self.config.api_url, json=payload) as response:
                    response.raise_for_status()
                    try:
                        data = await response.json()
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

    async def generate_with_retry(
        self, model_name: str, prompt: str, is_json: bool = False, max_retries: int = 3
    ) -> str:
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
                await asyncio.sleep(2**attempt)

        return ""  # All retries failed

    def _check_version_compatibility(self) -> None:
        """
        Check Ollama version compatibility and available features (shared implementation).

        This method validates that the connected Ollama instance meets
        minimum version requirements and detects available API features.
        Used by both sync and async clients through temporary session.
        """
        if self._version_validated:
            return  # Already validated

        try:
            # Use synchronous requests for version checking (works for both sync/async clients)
            temp_session = requests.Session()
            response = temp_session.get(
                self.config.version_url,
                timeout=10,  # Shorter timeout for version check
            )
            response.raise_for_status()

            try:
                data = response.json()
                version_str = data.get("version", "")
                if not version_str:
                    raise OllamaResponseError("No version information received from Ollama")

                # Parse version (e.g., "0.12.5")
                version_parts = version_str.split(".")
                if len(version_parts) < 3:
                    raise OllamaResponseError(f"Invalid version format: {version_str}")

                major, minor, patch = map(int, version_parts[:3])

                # Check minimum version (0.12.5)
                min_major, min_minor, min_patch = 0, 12, 5
                if (major, minor, patch) < (min_major, min_minor, min_patch):
                    raise OllamaResponseError(
                        f"Ollama version {version_str} is incompatible. "
                        f"Minimum required: {min_major}.{min_minor}.{min_patch}",
                        status_code=response.status_code,
                        response_body=f"Current: {version_str}, Required: >=0.12.5",
                    )

                # Detect available features based on version
                self._available_features = {
                    "version_endpoint": True,
                    "gpu_offload": (major, minor, patch) >= (0, 12, 5),
                    "enhanced_context": (major, minor, patch) >= (0, 12, 5),
                    "detailed_errors": (major, minor, patch) >= (0, 12, 5),
                }

                self._version_validated = True

            except ValueError as e:
                raise OllamaResponseError(
                    f"Invalid version response format from Ollama: {e}",
                    status_code=response.status_code,
                ) from e

        except requests.ConnectionError as e:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.config.version_url}. "
                f"Ensure Ollama is running with 'ollama serve'",
                host=self.config.host,
                port=self.config.port,
            ) from e
        except requests.Timeout as e:
            raise OllamaConnectionError(
                "Timeout connecting to Ollama for version check. "
                "Check if Ollama is running and accessible",
                host=self.config.host,
                port=self.config.port,
            ) from e
        except requests.HTTPError as e:
            raise OllamaResponseError(
                f"Ollama version check failed: HTTP {e.response.status_code}",
                status_code=e.response.status_code,
                response_body=e.response.text,
            ) from e

    def is_feature_available(self, feature: str) -> bool:
        """
        Check if a specific Ollama feature is available.

        Args:
            feature: Feature name to check (e.g., 'gpu_offload', 'enhanced_context')

        Returns:
            True if feature is available, False otherwise
        """
        if not self._version_validated:
            try:
                self._check_version_compatibility()
            except Exception:
                return False  # Conservative fallback

        return self._available_features.get(feature, False)
