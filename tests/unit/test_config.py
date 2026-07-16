from pathlib import Path

import pytest

from api_test_framework.config import load_config


@pytest.mark.unit
def test_load_config_expands_environment_and_defaults(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("IAM_USER", "configured.user")
    config_file = tmp_path / "test.yaml"
    config_file.write_text(
        """
environment: test
services:
  bff: {base_url: http://bff, timeout_seconds: 3}
  keycloak:
    token_url: http://keycloak/token
    client_id: tests
    username: ${IAM_USER}
    password: ${IAM_PASSWORD:-fallback}
  reportportal:
    enabled: false
    endpoint: http://rp
    project: demo
    api_key: ${RP_API_KEY:-}
    launch: demo
logging:
  level: INFO
  max_body_chars: 100
  redact_headers: [Authorization]
""".strip(),
        encoding="utf-8",
    )
    config = load_config(config_file)
    assert config.keycloak.username == "configured.user"
    assert config.keycloak.password == "fallback"
    assert config.logging.redact_headers == frozenset({"authorization"})


@pytest.mark.unit
def test_load_config_rejects_missing_required_environment(tmp_path: Path):
    config_file = tmp_path / "test.yaml"
    config_file.write_text("value: ${DEFINITELY_NOT_SET}", encoding="utf-8")
    with pytest.raises(ValueError, match="DEFINITELY_NOT_SET"):
        load_config(config_file)

