param(
    [string]$Config = "config/config.yaml",
    [switch]$Integration,
    [switch]$ReportPortal
)

$expression = if ($Integration) { "integration" } else { "unit" }
if ($ReportPortal) {
    $env:RP_API_KEY = Read-Host "ReportPortal API key"
    $tempConfig = "config/config.local.yaml"
    @"
environment: local
services:
  bff: {base_url: http://localhost:8000, timeout_seconds: 10}
  keycloak:
    token_url: http://localhost:8180/realms/trading-demo/protocol/openid-connect/token
    client_id: trading-demo-tests
    username: `${IAM_TEST_USERNAME:-qa.user}
    password: `${IAM_TEST_PASSWORD:-qa123456}
    refresh_skew_seconds: 60
    timeout_seconds: 10
  reportportal:
    enabled: true
    endpoint: http://localhost:8080
    project: superadmin_personal
    api_key: `${RP_API_KEY}
    launch: Trading QA IAM API Tests
logging: {level: INFO, max_body_chars: 100000, redact_headers: [authorization, cookie, set-cookie]}
"@ | Set-Content -Encoding UTF8 $tempConfig
    $Config = $tempConfig
}

python -m pytest -m $expression --config $Config

