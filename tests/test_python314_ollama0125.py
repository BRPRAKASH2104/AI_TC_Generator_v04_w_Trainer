"""Test Python 3.14 and Ollama 0.12.5 specific features"""
import asyncio
import sys

import pytest
import requests


def test_python_version():
    """Verify Python 3.14+"""
    assert sys.version_info >= (3, 14), f"Python 3.14+ required, found {sys.version_info}"


def test_ollama_version():
    """Verify Ollama 0.12.5+"""
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        version = response.json()["version"]

        # Parse version string (e.g., "0.12.5")
        major, minor, patch = map(int, version.split('.'))
        assert (major, minor, patch) >= (0, 12, 5), f"Ollama 0.12.5+ required, found {version}"
    except requests.RequestException as e:
        pytest.skip(f"Ollama not available: {e}")


def test_type_aliases():
    """Test Python 3.14 type parameter syntax"""
    from core.generators import ProcessingResult, TestCaseData, TestCaseList

    # Type aliases should be accessible
    assert TestCaseData is not None
    assert TestCaseList is not None
    assert ProcessingResult is not None


def test_ollama_larger_context():
    """Test Ollama 0.12.5 larger context window support"""
    from config import OllamaConfig

    config = OllamaConfig(num_ctx=16384)  # 0.12.5 supports 16K+
    assert config.num_ctx == 16384


def test_ollama_increased_response_length():
    """Test Ollama 0.12.5 increased response length"""
    from config import OllamaConfig

    config = OllamaConfig(num_predict=4096)  # 0.12.5 increased max
    assert config.num_predict == 4096


def test_ollama_gpu_offload():
    """Test Ollama 0.12.5 GPU offload config"""
    from config import OllamaConfig

    config = OllamaConfig(enable_gpu_offload=True, max_vram_usage=0.95)
    assert config.enable_gpu_offload is True
    assert config.max_vram_usage == 0.95


def test_ollama_version_url():
    """Test Ollama 0.12.5 version_url property"""
    from config import OllamaConfig

    config = OllamaConfig()
    assert config.version_url == "http://127.0.0.1:11434/api/version"


def test_ollama_improved_gpu_concurrency():
    """Test Ollama 0.12.5 improved GPU concurrency default"""
    from config import OllamaConfig

    config = OllamaConfig()
    assert config.gpu_concurrency_limit == 2  # Improved from 1


def test_exception_response_body_field():
    """Test OllamaResponseError has response_body field"""
    from core.exceptions import OllamaResponseError

    error = OllamaResponseError(
        "Test error",
        status_code=500,
        response_body='{"error": "Test detail"}'
    )
    assert error.status_code == 500
    assert error.response_body == '{"error": "Test detail"}'


@pytest.mark.asyncio
async def test_taskgroup_available():
    """Test Python 3.14 TaskGroup availability"""
    from asyncio import TaskGroup

    async def dummy_task(i: int) -> int:
        await asyncio.sleep(0.001)
        return i * 2

    async with TaskGroup() as tg:
        tasks = [tg.create_task(dummy_task(i)) for i in range(5)]

    results = [task.result() for task in tasks]
    assert results == [0, 2, 4, 6, 8]


def test_no_future_import_annotations():
    """Verify 'from __future__ import annotations' has been removed"""
    from pathlib import Path

    # Check key modules don't have future imports
    modules_to_check = [
        "src/core/ollama_client.py",
        "src/core/generators.py",
        "src/core/parsers.py",
        "src/config.py",
    ]

    for module_path in modules_to_check:
        full_path = Path(module_path)
        if full_path.exists():
            content = full_path.read_text()
            assert "from __future__ import annotations" not in content, \
                f"{module_path} still contains 'from __future__ import annotations'"


def test_package_version():
    """Verify package version is 2.1.0"""
    import src
    assert src.__version__ == "2.1.0"


def test_config_defaults_for_ollama_0125():
    """Test that default config values match Ollama 0.12.5 capabilities"""
    from config import OllamaConfig

    config = OllamaConfig()

    # Ollama 0.12.5 defaults
    assert config.num_ctx == 16384, "Default context window should be 16K for 0.12.5"
    assert config.num_predict == 4096, "Default response length should be 4K for 0.12.5"
    assert config.enable_gpu_offload is True, "GPU offload should be enabled by default"
    assert config.max_vram_usage == 0.95, "Default VRAM usage should be 95%"


def test_python314_union_type_syntax():
    """Test that Python 3.14 union type syntax works"""
    from core.exceptions import OllamaResponseError

    # Python 3.14 supports | syntax without future imports
    error: OllamaResponseError | None = None
    assert error is None

    error = OllamaResponseError("test", status_code=404, response_body="not found")
    assert error is not None
