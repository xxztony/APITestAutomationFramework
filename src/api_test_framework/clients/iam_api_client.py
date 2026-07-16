from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import requests

from api_test_framework.auth import KeycloakTokenManager
from api_test_framework.reporting import log_json_attachment, redact_headers


class IamApiClient:
    """Requests client with bearer auth, one-time 401 retry, and RP attachments."""

    def __init__(
        self,
        base_url: str,
        token_manager: KeycloakTokenManager,
        *,
        timeout_seconds: float = 10,
        max_body_chars: int = 100_000,
        sensitive_headers: frozenset[str] = frozenset({"authorization", "cookie", "set-cookie"}),
        session: requests.Session | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.token_manager = token_manager
        self.timeout_seconds = timeout_seconds
        self.max_body_chars = max_body_chars
        self.sensitive_headers = sensitive_headers
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)

    def request(self, method: str, path: str, *, authenticate: bool = True, **kwargs: Any) -> requests.Response:
        url = urljoin(self.base_url, path.lstrip("/"))
        headers = dict(kwargs.pop("headers", {}))
        if authenticate:
            headers["Authorization"] = f"Bearer {self.token_manager.get_access_token()}"

        request_kwargs = dict(kwargs)
        log_json_attachment(
            self.logger,
            f"HTTP request: {method.upper()} {url}",
            "request.json",
            {
                "method": method.upper(),
                "url": url,
                "headers": redact_headers(headers, self.sensitive_headers),
                "query": request_kwargs.get("params"),
                "json": request_kwargs.get("json"),
                "body": request_kwargs.get("data"),
            },
        )
        response = self._send(method, url, headers, request_kwargs)
        if authenticate and response.status_code == 401:
            self.logger.warning("API returned 401; refreshing the IAM token and retrying once")
            headers["Authorization"] = f"Bearer {self.token_manager.refresh_access_token()}"
            response = self._send(method, url, headers, request_kwargs)

        try:
            body: Any = response.json()
        except ValueError:
            body = response.text[: self.max_body_chars]
        log_json_attachment(
            self.logger,
            f"HTTP response: {response.status_code} {method.upper()} {url}",
            "response.json",
            {
                "status": response.status_code,
                "elapsedMs": round(response.elapsed.total_seconds() * 1000, 2),
                "headers": redact_headers(dict(response.headers), self.sensitive_headers),
                "body": body,
            },
        )
        return response

    def _send(self, method: str, url: str, headers: dict[str, str], kwargs: dict[str, Any]) -> requests.Response:
        return self.session.request(
            method,
            url,
            headers=headers,
            timeout=kwargs.pop("timeout", self.timeout_seconds),
            **kwargs,
        )

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, **kwargs)

