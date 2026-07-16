import pytest
import requests
import responses

from api_test_framework.auth import KeycloakTokenManager


TOKEN_URL = "http://keycloak.test/token"


@pytest.mark.unit
@responses.activate
def test_manager_uses_refresh_token_before_access_expiry():
    now = [100.0]
    responses.post(
        TOKEN_URL,
        json={"access_token": "first", "refresh_token": "refresh-1", "expires_in": 60, "refresh_expires_in": 300},
    )
    responses.post(
        TOKEN_URL,
        json={"access_token": "second", "refresh_token": "refresh-2", "expires_in": 60, "refresh_expires_in": 300},
    )
    manager = KeycloakTokenManager(
        TOKEN_URL, "client", "user", "password", refresh_skew_seconds=10, clock=lambda: now[0]
    )
    assert manager.get_access_token() == "first"
    now[0] = 151.0
    assert manager.get_access_token() == "second"
    assert responses.calls[1].request.body == "grant_type=refresh_token&client_id=client&refresh_token=refresh-1"


@pytest.mark.unit
@responses.activate
def test_manager_reauthenticates_when_refresh_is_rejected():
    responses.post(
        TOKEN_URL,
        json={"access_token": "first", "refresh_token": "bad", "expires_in": 1, "refresh_expires_in": 300},
    )
    responses.post(TOKEN_URL, status=400, json={"error": "invalid_grant"})
    responses.post(
        TOKEN_URL,
        json={"access_token": "reauthed", "refresh_token": "new", "expires_in": 60, "refresh_expires_in": 300},
    )
    manager = KeycloakTokenManager(TOKEN_URL, "client", "user", "password", refresh_skew_seconds=60)
    assert manager.get_access_token() == "first"
    assert manager.get_access_token() == "reauthed"
    assert isinstance(responses.calls[1].response, requests.Response)

