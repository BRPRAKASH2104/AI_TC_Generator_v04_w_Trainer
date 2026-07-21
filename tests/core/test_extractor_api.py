"""Constructor-API contract tests for REQIFArtifactExtractor.

Guards review 2026-07-20 Recommended finding 5: after `use_streaming` /
`max_workers` were removed from the extractor constructors, `config` is made
keyword-only so a stale positional call cannot silently bind an unrelated value
(e.g. a leftover boolean) to `config`.
"""

import pytest

from src.config import ConfigManager
from src.core.extractors import (
    HighPerformanceREQIFArtifactExtractor,
    REQIFArtifactExtractor,
)


class TestExtractorConstructorApi:
    def test_config_accepted_as_keyword(self) -> None:
        cfg = ConfigManager()
        assert REQIFArtifactExtractor(config=cfg).config is cfg

    def test_config_rejected_as_positional(self) -> None:
        """A second positional argument must not bind to `config`."""
        cfg = ConfigManager()
        with pytest.raises(TypeError):
            REQIFArtifactExtractor(None, cfg)  # type: ignore[misc]

    def test_hp_extractor_inherits_keyword_only_config(self) -> None:
        cfg = ConfigManager()
        assert HighPerformanceREQIFArtifactExtractor(config=cfg).config is cfg
        with pytest.raises(TypeError):
            HighPerformanceREQIFArtifactExtractor(None, cfg)  # type: ignore[misc]

    @pytest.mark.parametrize("removed_kwarg", ["use_streaming", "max_workers"])
    def test_removed_kwargs_are_rejected(self, removed_kwarg: str) -> None:
        with pytest.raises(TypeError):
            REQIFArtifactExtractor(**{removed_kwarg: True})  # type: ignore[arg-type]
