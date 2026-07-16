import pytest


@pytest.mark.integration
@pytest.mark.iam
@pytest.mark.rest
def test_bff_rejects_anonymous_request(iam_api_client):
    response = iam_api_client.get("/api/dashboard", authenticate=False)
    assert response.status_code == 401
    assert response.json()["errorCode"] == "AUTH_REQUIRED"


@pytest.mark.integration
@pytest.mark.iam
@pytest.mark.rest
def test_keycloak_token_is_accepted_by_bff(iam_api_client, framework_config):
    response = iam_api_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["data"]["username"] == framework_config.keycloak.username
    assert "qa_user" in response.json()["data"]["roles"]


@pytest.mark.integration
@pytest.mark.iam
@pytest.mark.rest
def test_access_token_is_refreshed_before_expiry(iam_api_client, token_manager):
    first_token = token_manager.get_access_token()
    response = iam_api_client.get("/api/dashboard")
    refreshed_token = token_manager.get_access_token()
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert token_manager.refresh_count >= 1
    assert refreshed_token != first_token

