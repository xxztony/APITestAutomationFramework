from __future__ import annotations

import logging
from pathlib import Path

import pytest

from api_test_framework import FrameworkConfig, load_config
from api_test_framework.auth import KeycloakTokenManager
from api_test_framework.clients import IamApiClient


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--config", default="config/config.yaml", help="YAML test configuration path")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    cfg = load_config(Path(config.getoption("--config")))
    config._framework_config = cfg  # type: ignore[attr-defined]
    rp = cfg.reportportal
    if rp.enabled:
        if not rp.api_key:
            raise pytest.UsageError("ReportPortal is enabled but RP_API_KEY is empty")
        config.option.rp_enabled = True
        config.option.rp_endpoint = rp.endpoint
        config.option.rp_project = rp.project
        config.option.rp_api_key = rp.api_key
        config.option.rp_launch = rp.launch


@pytest.fixture(scope="session")
def framework_config(pytestconfig: pytest.Config) -> FrameworkConfig:
    return pytestconfig._framework_config  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def api_logger(framework_config: FrameworkConfig) -> logging.Logger:
    logger = logging.getLogger("trading_api_tests")
    logger.setLevel(framework_config.logging.level)
    return logger


@pytest.fixture
def token_manager(framework_config: FrameworkConfig, api_logger: logging.Logger) -> KeycloakTokenManager:
    cfg = framework_config.keycloak
    return KeycloakTokenManager(
        cfg.token_url,
        cfg.client_id,
        cfg.username,
        cfg.password,
        refresh_skew_seconds=cfg.refresh_skew_seconds,
        timeout_seconds=cfg.timeout_seconds,
        logger=api_logger,
    )


@pytest.fixture
def iam_api_client(
    framework_config: FrameworkConfig,
    token_manager: KeycloakTokenManager,
    api_logger: logging.Logger,
) -> IamApiClient:
    return IamApiClient(
        framework_config.bff.base_url,
        token_manager,
        timeout_seconds=framework_config.bff.timeout_seconds,
        max_body_chars=framework_config.logging.max_body_chars,
        sensitive_headers=framework_config.logging.redact_headers,
        logger=api_logger,
    )
