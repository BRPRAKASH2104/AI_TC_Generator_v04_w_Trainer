"""Unit tests for RAFT training-data collection consent controls.

The README documents that BOTH training.enable_raft and
training.collect_training_data must be enabled (via AI_TG_* env vars or
config/cli_config.yaml) before any requirement/test content is written to
training_data/. These tests pin that contract (review 2026-07-17 finding 6).
"""

from config import ConfigManager


class TestTrainingEnvVars:
    """AI_TG_ENABLE_RAFT / AI_TG_COLLECT_TRAINING_DATA must be honored."""

    def test_enable_raft_env_var_is_mapped(self, monkeypatch):
        monkeypatch.setenv("AI_TG_ENABLE_RAFT", "true")

        effective = ConfigManager().apply_cli_overrides()

        assert effective.training.enable_raft is True

    def test_collect_training_data_env_var_is_mapped(self, monkeypatch):
        monkeypatch.setenv("AI_TG_COLLECT_TRAINING_DATA", "true")

        effective = ConfigManager().apply_cli_overrides()

        assert effective.training.collect_training_data is True

    def test_env_vars_default_off(self, monkeypatch):
        monkeypatch.delenv("AI_TG_ENABLE_RAFT", raising=False)
        monkeypatch.delenv("AI_TG_COLLECT_TRAINING_DATA", raising=False)

        effective = ConfigManager().apply_cli_overrides()

        assert effective.training.enable_raft is False
        assert effective.training.collect_training_data is False


class TestTrainingYamlSection:
    """load_cli_config must import the documented `training:` section."""

    def test_training_section_is_loaded(self, tmp_path):
        config_file = tmp_path / "cli_config.yaml"
        config_file.write_text(
            "training:\n"
            "  enable_raft: true\n"
            "  collect_training_data: true\n"
            "  training_data_dir: custom_dir\n",
            encoding="utf-8",
        )

        config = ConfigManager()
        config.load_cli_config(config_file)

        assert config.training.enable_raft is True
        assert config.training.collect_training_data is True
        assert config.training.training_data_dir == "custom_dir"

    def test_unknown_training_keys_are_ignored(self, tmp_path):
        config_file = tmp_path / "cli_config.yaml"
        config_file.write_text(
            "training:\n  enable_raft: true\n  not_a_real_key: 1\n",
            encoding="utf-8",
        )

        config = ConfigManager()
        config.load_cli_config(config_file)

        assert config.training.enable_raft is True


class TestCollectorConsentGate:
    """BaseProcessor must require BOTH flags before creating a collector."""

    @staticmethod
    def _processor_with(enable_raft, collect_training_data, tmp_path):
        from processors.standard_processor import REQIFZFileProcessor

        config = ConfigManager()
        config.training.enable_raft = enable_raft
        config.training.collect_training_data = collect_training_data
        config.training.training_data_dir = str(tmp_path / "training_data")
        return REQIFZFileProcessor(config)

    def test_both_flags_enabled_creates_collector(self, tmp_path):
        processor = self._processor_with(True, True, tmp_path)
        assert processor.raft_collector is not None

    def test_enable_raft_alone_is_not_consent(self, tmp_path):
        processor = self._processor_with(True, False, tmp_path)
        assert processor.raft_collector is None

    def test_collect_alone_is_not_consent(self, tmp_path):
        processor = self._processor_with(False, True, tmp_path)
        assert processor.raft_collector is None

    def test_both_disabled_creates_no_collector(self, tmp_path):
        processor = self._processor_with(False, False, tmp_path)
        assert processor.raft_collector is None
