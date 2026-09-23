# Audit Logging

## Status

`orchestrator/audit_logger.py` provides a structured `AuditLogger` for compliance-relevant events. As of issue J4, it is wired into:

- API mutations (POST/PUT/PATCH/DELETE) - logged automatically by `RequestContextMiddleware` in `orchestrator/main.py` for every mutating request.
- Authentication failures - logged by the `require_token` dependency whenever an invalid/missing API token is presented.

Other event types (`log_ai_decision`, `log_config_change`, `log_data_access`) exist and are ready to use, but are not yet called from application code - callers should invoke them at the relevant call sites as those features are built out.

## Fields captured per event

Every AuditEvent captures:

- event_id: Unique UUID for this event
- event_type: What happened (e.g. POST /sessions, AUTH_FAILURE)
- category: API_MUTATION, SECURITY, AI_DECISION, CONFIG_CHANGE, DATA_ACCESS, SYSTEM_EVENT
- actor: Who performed the action (currently: authenticated/anonymous for API calls, since raw tokens are never logged)
- target: What was acted on (e.g. the request path)
- details: Event-specific extra context (dict)
- timestamp: UTC ISO-8601 timestamp
- request_id: Correlates this event with the request's X-Request-ID
- ip_address: Client IP address (now captured for all event types)
- severity: INFO / WARNING / ERROR

## Known gaps (not fixed in this change - flagged for follow-up)

- Actor identity is not a real authenticated user ID. The system currently uses a single shared API token (no per-user identity), so actor can only distinguish "a valid token was presented" from "no valid token" - it cannot identify which caller made the request. Proper per-user audit trails would require a per-user auth scheme.
- "Tamper-evident" claim in the module docstring is aspirational. There is no hash-chaining, signing, or checksum on stored log entries - a log file can currently be edited without detection. Implementing real tamper-evidence is out of scope for this change and should be tracked separately.
- Log retention policy is out of scope for J4 (see issue J5).

## Configuration

Set AUDIT_LOG_FILE to a file path to additionally persist audit events as JSON lines to disk (in addition to stdout via the standard logger). If unset, events go to stdout only. See .env.example.
