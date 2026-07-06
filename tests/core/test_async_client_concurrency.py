"""
Regression tests for AsyncOllamaClient concurrency wiring.

The CLI --max-concurrent flag flows into ollama.concurrent_requests and the HP
processor's max_concurrent_requirements, but the client's semaphore was built
only from gpu_concurrency_limit (default 2) — so the flag had no effect.
These tests pin the fixed behavior: an explicit limit overrides the GPU
default, and omitting it preserves the previous default.
"""

from config import OllamaConfig
from core.ollama_client import AsyncOllamaClient


def test_default_semaphore_uses_gpu_concurrency_limit():
    """Without an explicit limit, the semaphore follows gpu_concurrency_limit (unchanged behavior)."""
    config = OllamaConfig(gpu_concurrency_limit=3)

    client = AsyncOllamaClient(config)

    assert client.semaphore._value == 3


def test_explicit_concurrency_limit_overrides_gpu_default():
    """An explicit concurrency_limit (wired from --max-concurrent) must win over the GPU default."""
    config = OllamaConfig(gpu_concurrency_limit=2)

    client = AsyncOllamaClient(config, concurrency_limit=7)

    assert client.semaphore._value == 7


def test_non_positive_concurrency_limit_falls_back_to_gpu_default():
    """Zero/negative limits are invalid and must fall back to the configured default."""
    config = OllamaConfig(gpu_concurrency_limit=2)

    client = AsyncOllamaClient(config, concurrency_limit=0)

    assert client.semaphore._value == 2
