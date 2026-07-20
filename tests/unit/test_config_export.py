"""Unit tests for configuration export hygiene.

save_to_file() must never persist credentials in plaintext and must write
the export with owner-only permissions (review 2026-07-17 finding 9).
"""

import stat

import yaml

from config import ConfigManager


class TestSecretExclusion:
    @staticmethod
    def _config_with_secrets():
        config = ConfigManager()
        config.secrets.ollama_api_key = "secrets-section-key"
        return config

    def test_secret_values_not_written(self, tmp_path):
        config = self._config_with_secrets()
        export_path = tmp_path / "export.yaml"

        config.save_to_file(str(export_path))

        content = export_path.read_text(encoding="utf-8")
        assert "secrets-section-key" not in content

    def test_secrets_section_absent_and_config_still_valid(self, tmp_path):
        config = self._config_with_secrets()
        export_path = tmp_path / "export.yaml"

        config.save_to_file(str(export_path))

        data = yaml.safe_load(export_path.read_text(encoding="utf-8"))
        assert "secrets" not in data
        # Non-secret content must still be exported
        assert data["ollama"]["synthesizer_model"]

    def test_export_has_owner_only_permissions(self, tmp_path):
        config = self._config_with_secrets()
        export_path = tmp_path / "export.yaml"

        config.save_to_file(str(export_path))

        mode = stat.S_IMODE(export_path.stat().st_mode)
        assert mode == 0o600
