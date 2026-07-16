import os

import pytest


pytestmark = [
    pytest.mark.dashboard_demo,
    pytest.mark.iam,
    pytest.mark.rest,
    pytest.mark.skipif(
        os.getenv("RP_DASHBOARD_DEMO") != "1",
        reason="ReportPortal dashboard demo is opt-in",
    ),
]


def test_authenticated_profile_contract(iam_api_client, framework_config):
    response = iam_api_client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["data"]["username"] == framework_config.keycloak.username


def test_dashboard_contract_is_available(iam_api_client):
    response = iam_api_client.get("/api/dashboard")

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_market_dependency_health(iam_api_client):
    response = iam_api_client.get("/api/dashboard")

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert os.getenv("RP_DEMO_FORCE_FAILURE") != "1", (
        "Intentional dashboard seed failure: simulated market dependency outage"
    )
