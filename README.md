# Trading API Test Framework

A standalone pytest framework for demonstrating IAM-aware API testing against the Trading QA API Demo. It uses `requests`, obtains and refreshes Keycloak tokens automatically, and publishes sanitized request/response JSON as ReportPortal attachments.

## Structure

```text
config/                  YAML environment configuration
src/api_test_framework/  reusable config, auth, client, and reporting layers
tests/unit/              isolated framework tests
tests/integration/       real Keycloak and BFF tests
tests/demo/              opt-in ReportPortal dashboard seed scenarios
scripts/                 local runner helpers
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[test]"
```

Run fast framework tests:

```powershell
pytest -m unit
```

With the demo stack running at `localhost`, run the real IAM flow:

```powershell
pytest -m integration --config config/config.yaml
```

## YAML configuration

Select a configuration with `--config` or `TEST_CONFIG`. `${NAME}` requires an environment variable; `${NAME:-default}` supplies a local demo default. Keep secrets in environment variables or an ignored `config/config.local.yaml`.

## ReportPortal

Set an API key, enable `services.reportportal.enabled` in an ignored local YAML file, then run pytest normally:

```powershell
$env:RP_API_KEY = "your-api-key"
pytest -m integration --config config/reportportal.yaml
```

Each API call emits `request.json` and `response.json` attachments. Authorization and cookie headers are redacted before logging.

To seed a dashboard with a clearly labeled failure followed by recovery, run the
opt-in demo twice. The first command intentionally exits with a failed test:

```powershell
$env:RP_DASHBOARD_DEMO = "1"
$env:RP_DEMO_FORCE_FAILURE = "1"
pytest -m dashboard_demo --config config/reportportal.yaml

$env:RP_DEMO_FORCE_FAILURE = "0"
pytest -m dashboard_demo --config config/reportportal.yaml
```

These scenarios call the real Keycloak-protected BFF and publish the same sanitized
request and response attachments as the integration suite. They remain skipped in
normal runs unless `RP_DASHBOARD_DEMO=1` is set.

## IAM behavior

`KeycloakTokenManager` caches tokens, refreshes proactively inside the configured skew window, retries a rejected refresh with the password grant, and is protected by a re-entrant lock. `IamApiClient` retries one HTTP 401 after forcing a refresh.

For production CI, use a confidential service-account client and inject its secret from the CI secret store. The password grant remains here only because it makes refresh-token behavior easy to demonstrate to testers.
