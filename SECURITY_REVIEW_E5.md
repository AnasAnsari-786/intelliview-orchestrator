# E5 — CORS & Input Validation Security Review

## 1. CORS Policy Review

The FastAPI application uses `CORSMiddleware` in `orchestrator/main.py`.

Current configuration:

* `allow_origins` is configured from the `CORS_ALLOW_ORIGINS` environment setting.
* The default value of `CORS_ALLOW_ORIGINS` is `"*"`.
* When the value is `"*"`, the application converts it to `allow_origins=["*"]`.
* `allow_credentials=True`.
* `allow_methods=["*"]`.
* `allow_headers=["*"]`.

### Security finding

The CORS policy is overly permissive in the default configuration.

The main concern is the combination of:

* wildcard origin (`*`)
* credentials enabled
* all HTTP methods allowed
* all request headers allowed

This broad policy increases the potential cross-origin attack surface, particularly if authenticated browser-based requests or sensitive API responses are exposed.

**Risk: High / potentially high depending on deployment and authentication usage.**

### Recommendation

The current policy should be reviewed and restricted to explicitly trusted frontend origins and only the HTTP methods and headers required by the application.

**Note:** This task only documents the issue. Fixes are deferred to E6.

---

## 2. Input Validation Review

### Routes / files reviewed

The following FastAPI route modules were reviewed:

* `orchestrator/main.py`
* `routers/admin.py`
* `routers/analytics.py`
* `routers/candidates.py`
* `routers/export.py`
* `routers/integrity.py`
* `routers/practice_sessions.py`
* `routers/questions.py`
* `routers/schedule.py`
* `routers/session_control.py`
* `routers/sessions.py`
* `routers/settings.py`
* `routers/templates.py`
* `routers/workers.py`

### Positive validation controls observed

Several endpoints already use Pydantic/FastAPI validation.

Examples include:

* Candidate names and emails have explicit minimum and maximum lengths.
* Candidate statistics use non-negative numeric constraints.
* Schedule list limits use `ge=1` and `le=500`.
* Template names have length restrictions.
* Interview candidate IDs have length and character restrictions.
* Some fields use enumerated/explicit validation inside route handlers.
* A global request-body size limit of approximately 1 MB is configured.

These controls reduce some common malformed-input risks.

### Validation gaps found

Despite the existing validation, validation is inconsistent across endpoints.

#### 2.1 Candidate endpoints

`routers/candidates.py` contains several fields with limited or missing validation.

Examples:

* `email` is limited by length but does not enforce an email format.
* `resume_text` does not have an explicit maximum length.
* `skills` does not have an explicit maximum list size or per-item length.
* Bulk candidate requests require at least one candidate but do not define a maximum number of candidates.
* Verification `email` and `token` fields do not have explicit length/format constraints.
* Candidate search/filter parameters are mostly unrestricted strings.
* Candidate list `limit` does not have an explicit upper bound.
* CSV import primarily checks the filename extension and that the uploaded content is non-empty; stricter file size, row-count, field-size, and structure validation is not enforced at the route level.

**Risk: Medium**

These gaps could allow unnecessarily large or malformed input and may contribute to resource-exhaustion risks.

#### 2.2 Schedule endpoints

`routers/schedule.py` performs useful validation, including allowed schedule statuses and bounded list limits.

However:

* `candidate_id` and `interviewer_id` do not have explicit length/format constraints.
* `notes` does not have an explicit maximum length.
* Some query/path identifiers are accepted as unrestricted strings.

**Risk: Low–Medium**

#### 2.3 Template endpoints

`routers/templates.py` validates the template name length, but several other fields have limited validation.

Examples:

* `interview_type` has no explicit length restriction.
* `description` has no explicit maximum length.
* `duration_minutes` does not have an explicit positive/range constraint.
* `question_count` does not have an explicit positive/range constraint.
* Distribution dictionaries do not have explicit size or value-range validation.
* The template listing `limit` does not have an explicit upper bound.

**Risk: Medium**

#### 2.4 Worker endpoints

Worker request models accept:

* `worker_id`
* `capacity`
* `active_tasks`
* `cpu_pct`
* `memory_pct`
* `queue_depth`

Several numeric fields do not have explicit range constraints.

For example, CPU and memory percentages are not explicitly restricted to `0–100`, and task/capacity values are not explicitly restricted to non-negative values at the Pydantic model level.

`worker_id` also does not have an explicit length/format restriction.

**Risk: Medium**

#### 2.5 Analytics/PDF endpoint

The analytics PDF request accepts candidate lists and dictionaries for statistics/fault information.

The route-level model does not define strong limits for:

* candidate list size
* dictionary size
* individual string lengths
* nested input size

Because the endpoint performs PDF generation, unusually large input could increase CPU or memory consumption.

**Risk: Low–Medium**

### Overall input-validation assessment

The application uses Pydantic models in many places, which provides a good baseline. However, validation is not consistently strict across all endpoints.

The main recurring gaps are:

1. Missing maximum lengths.
2. Missing numeric ranges.
3. Missing maximum list/dictionary sizes.
4. Missing format validation for some identifiers and emails.
5. Limited validation of uploaded CSV content.
6. Unbounded query parameters on some endpoints.

These should be reviewed and hardened during E6.

---

## 3. Injection Risk Assessment

### 3.1 SQL Injection

No direct SQL injection vulnerability was identified in the reviewed FastAPI route handlers.

Database access in the reviewed routes generally uses SQLAlchemy ORM/query expressions rather than constructing SQL statements through string concatenation.

For example, schedule and export routes use patterns equivalent to:

```python
select(Model).where(Model.field == user_input)
```

rather than building SQL strings such as:

```python
"SELECT ... WHERE id = '" + user_input + "'"
```

No obvious route-level raw SQL concatenation was identified during this review.

**Assessment: Low risk in the reviewed route handlers.**

However, route handlers delegate some operations to managers/services. Those downstream components should also be reviewed separately before concluding that the entire application is free of SQL injection.

---

### 3.2 Command Injection

No direct command-injection sink was identified in the reviewed FastAPI route handlers.

No route-level use of patterns such as:

* `os.system()`
* `subprocess` with shell execution
* `shell=True`
* `eval()`
* `exec()`

with directly supplied request parameters was identified during the review.

**Assessment: Low risk in the reviewed route handlers.**

As with SQL injection, downstream service/manager code should be reviewed separately because route handlers may pass user-controlled values to other components.

---

### 3.3 Other Injection Risks

No confirmed template, shell, or SQL injection vulnerability was identified directly in the reviewed FastAPI route handlers.

However, several endpoints accept free-form strings, dictionaries, lists, uploaded CSV content, and other user-controlled data with limited size or format restrictions.

These inputs should be treated as untrusted throughout the application, especially when passed to:

* database/service layers
* file-processing functions
* PDF generation
* logging
* external services

**Assessment: Low–Medium**, primarily due to inconsistent input constraints rather than a confirmed injection exploit.

---

## 4. Summary of Findings

| Area                     | Finding                                                                           | Risk                    |
| ------------------------ | --------------------------------------------------------------------------------- | ----------------------- |
| CORS                     | Default wildcard origin with credentials enabled and wildcard methods/headers     | High / potentially high |
| Candidate validation     | Missing limits/format checks on several fields and bulk inputs                    | Medium                  |
| Schedule validation      | Several IDs/text fields lack explicit constraints                                 | Low–Medium              |
| Template validation      | Missing ranges and size limits on several fields                                  | Medium                  |
| Worker validation        | Numeric ranges and worker ID constraints are incomplete                           | Medium                  |
| Analytics/PDF validation | Collection and nested input sizes are not strongly bounded                        | Low–Medium              |
| SQL injection            | No direct route-level SQL injection identified; ORM usage observed                | Low                     |
| Command injection        | No direct route-level command execution sink identified                           | Low                     |
| Other injection          | No confirmed direct injection exploit; untrusted inputs need stronger constraints | Low–Medium              |

---

## 5. Conclusion

The E5 security review identified an overly permissive default CORS configuration and several inconsistent input-validation controls across FastAPI routes.

The most significant finding is the default CORS configuration using a wildcard origin together with credentials, wildcard methods, and wildcard headers.

Input validation exists throughout the application but should be made more consistent, particularly for string lengths, numeric ranges, collection sizes, identifiers, and uploaded CSV content.

No direct SQL injection or command injection vulnerability was identified in the reviewed FastAPI route handlers. Database queries observed during the review primarily use SQLAlchemy expressions rather than raw SQL string concatenation.

**No fixes are implemented as part of E5. All remediation work is deferred to E6.**
