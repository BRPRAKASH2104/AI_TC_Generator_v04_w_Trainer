"""Unit tests for main.py result-aggregation helpers.

Covers directory-level aggregation and exit-code resolution so that partial
generation failures produce a non-zero exit (review 2026-07-17 finding 1).
"""

from main import _aggregate_directory_results, _resolve_exit_code


class TestAggregateDirectoryResults:
    """Directory processing must succeed only when every file succeeds."""

    def test_all_files_succeeded(self):
        results = [
            {"success": True, "partial": False, "total_test_cases": 3},
            {"success": True, "partial": False, "total_test_cases": 2},
        ]

        aggregated = _aggregate_directory_results(results)

        assert aggregated["success"] is True
        assert aggregated["partial"] is False
        assert aggregated["failed_files"] == []
        assert aggregated["total_test_cases"] == 5

    def test_one_file_failed_means_partial_not_success(self):
        results = [
            {"success": True, "partial": False, "total_test_cases": 3},
            {"success": False, "error": "boom", "input_file": "b.reqifz"},
        ]

        aggregated = _aggregate_directory_results(results)

        assert aggregated["success"] is False
        assert aggregated["partial"] is True
        assert aggregated["failed_files"] == ["b.reqifz"]

    def test_partial_file_propagates_partial(self):
        results = [
            {"success": True, "partial": True, "total_test_cases": 1},
            {"success": True, "partial": False, "total_test_cases": 2},
        ]

        aggregated = _aggregate_directory_results(results)

        assert aggregated["success"] is True
        assert aggregated["partial"] is True

    def test_all_files_failed(self):
        results = [
            {"success": False, "error": "x", "input_file": "a.reqifz"},
            {"success": False, "error": "y", "input_file": "b.reqifz"},
        ]

        aggregated = _aggregate_directory_results(results)

        assert aggregated["success"] is False
        assert aggregated["partial"] is False
        assert aggregated["failed_files"] == ["a.reqifz", "b.reqifz"]

    def test_empty_results_is_failure(self):
        aggregated = _aggregate_directory_results([])

        assert aggregated["success"] is False
        assert aggregated["partial"] is False


class TestResolveExitCode:
    """Exit code contract: 0 complete, 2 partial, 1 failure."""

    def test_complete_success_is_zero(self):
        assert _resolve_exit_code({"success": True, "partial": False}) == 0

    def test_partial_success_is_two(self):
        assert _resolve_exit_code({"success": True, "partial": True}) == 2

    def test_partial_directory_failure_is_two(self):
        assert _resolve_exit_code({"success": False, "partial": True}) == 2

    def test_total_failure_is_one(self):
        assert _resolve_exit_code({"success": False, "partial": False}) == 1

    def test_missing_partial_key_defaults_to_strict(self):
        assert _resolve_exit_code({"success": True}) == 0
        assert _resolve_exit_code({"success": False}) == 1


class TestPresetPrecedence:
    """Preset values must control execution: mode, boolean flags, and
    concurrency must survive CLI defaults and model-specific defaults
    (review 2026-07-17 finding 5).
    """

    @staticmethod
    def _effective_for_preset(preset_name):
        import pytest

        from config import ConfigManager
        from main import _apply_preset

        base = ConfigManager()
        base.load_cli_config()
        if preset_name not in base.cli.presets:
            pytest.skip(f"Preset {preset_name} not defined in cli_config.yaml")

        merged, preset_keys = _apply_preset(base, preset_name)
        return merged.apply_cli_overrides(
            model=None,
            template=None,
            max_concurrent=None,
            num_ctx=None,
            verbose=None,
            debug=None,
            performance=None,
            config=None,
            preset_overrides=preset_keys,
        )

    def test_production_preset_mode_and_flags_survive(self):
        effective = self._effective_for_preset("production")

        assert effective.cli.mode == "hp"
        assert effective.cli.performance is True
        assert effective.ollama.synthesizer_model == "deepseek-coder-v2:16b"

    def test_production_preset_concurrency_not_clobbered_by_model_defaults(self):
        """Preset max_concurrent=8 must beat deepseek recommended_concurrent=3."""
        effective = self._effective_for_preset("production")

        assert effective.ollama.concurrent_requests == 8

    def test_development_preset_verbose_survives_absent_cli_flag(self):
        effective = self._effective_for_preset("development")

        assert effective.cli.verbose is True
        assert effective.cli.debug is True


class TestResolveProcessingMode:
    """Dispatch must honor effective config mode, with --hp as an override."""

    @staticmethod
    def _config(mode):
        from config import ConfigManager

        config = ConfigManager()
        config.cli.mode = mode
        return config

    def test_hp_flag_forces_hp(self):
        from main import _resolve_processing_mode

        assert _resolve_processing_mode(True, self._config("standard")) == "hp"

    def test_config_mode_hp_without_flag(self):
        from main import _resolve_processing_mode

        assert _resolve_processing_mode(False, self._config("hp")) == "hp"

    def test_default_is_standard(self):
        from main import _resolve_processing_mode

        assert _resolve_processing_mode(False, self._config("standard")) == "standard"


class TestTriStateBooleanFlags:
    """Absent CLI boolean flags must be None so they cannot overwrite
    preset-enabled verbose/debug/performance with Click's False default."""

    def test_flags_default_to_none(self):
        from main import main as cli_main

        defaults = {param.name: param.default for param in cli_main.params}

        assert defaults["verbose"] is None
        assert defaults["debug"] is None
        assert defaults["performance"] is None
