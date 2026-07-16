from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?}")


@dataclass(frozen=True)
class BffConfig:
    base_url: str
    timeout_seconds: float = 10


@dataclass(frozen=True)
class KeycloakConfig:
    token_url: str
    client_id: str
    username: str
    password: str
    refresh_skew_seconds: int = 30
    timeout_seconds: float = 10


@dataclass(frozen=True)
class ReportPortalConfig:
    enabled: bool
    endpoint: str
    project: str
    api_key: str
    launch: str


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    max_body_chars: int
    redact_headers: frozenset[str]


@dataclass(frozen=True)
class FrameworkConfig:
    environment: str
    bff: BffConfig
    keycloak: KeycloakConfig
    reportportal: ReportPortalConfig
    logging: LoggingConfig


def _expand_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        name, default = match.group(1), match.group(2)
        if name in os.environ:
            return os.environ[name]
        if default is not None:
            return default
        raise ValueError(f"Required environment variable is not set: {name}")

    return ENV_PATTERN.sub(replace, value)


def load_config(path: str | Path | None = None) -> FrameworkConfig:
    config_path = Path(path or os.getenv("TEST_CONFIG", "config/config.yaml"))
    if not config_path.is_file():
        raise FileNotFoundError(f"Test configuration file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    data = _expand_env(raw)
    try:
        services = data["services"]
        logging_data = data["logging"]
        return FrameworkConfig(
            environment=str(data["environment"]),
            bff=BffConfig(**services["bff"]),
            keycloak=KeycloakConfig(**services["keycloak"]),
            reportportal=ReportPortalConfig(**services["reportportal"]),
            logging=LoggingConfig(
                level=str(logging_data["level"]),
                max_body_chars=int(logging_data["max_body_chars"]),
                redact_headers=frozenset(str(item).lower() for item in logging_data["redact_headers"]),
            ),
        )
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Invalid test configuration in {config_path}: {exc}") from exc

