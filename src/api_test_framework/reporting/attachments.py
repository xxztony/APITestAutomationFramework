from __future__ import annotations

import json
import logging
from typing import Any


def redact_headers(headers: dict[str, Any], sensitive_headers: frozenset[str]) -> dict[str, Any]:
    return {
        key: "<redacted>" if key.lower() in sensitive_headers else value
        for key, value in headers.items()
    }


def log_json_attachment(logger: logging.Logger, message: str, name: str, payload: Any) -> None:
    rendered = json.dumps(payload, ensure_ascii=True, indent=2, default=str)
    try:
        logger.info(
            message,
            attachment={"name": name, "data": rendered.encode("utf-8"), "mime": "application/json"},
        )
    except TypeError:
        logger.info("%s\n%s", message, rendered)

