# CI Workflow Review — Issue #32

## Scope

Reviewed `.github/workflows/ci.yml` to verify the existing CI workflow,
confirm whether Ruff lint and pytest run for pull requests, and document
observed gaps or potential reliability concerns.

No workflow, lint, or test configuration changes were made as part of this
review.

---

## Pull Request Triggers

The CI workflow runs for pull requests targeting:

- `main`
- `Stabilized-version`
- `issue-22-dataset-validation`

Pull requests targeting other branches do not trigger this workflow.

Therefore, CI coverage is limited to the configured target branches rather
than applying repository-wide to every possible pull request.

---

## Ruff Verification

The Python Tests job installs Ruff version `0.9.10` and runs:

```text
ruff check orchestrator workers monitoring database tests scripts routers retrieval
```

This step has no pull-request-specific exclusion or `continue-on-error`
setting.

It runs on the configured pull request triggers when preceding steps succeed.
A Ruff failure causes the Python Tests job to fail.

---

## Pytest Verification

The Python Tests job runs:

```text
pytest tests/ --ignore=tests/test_e2e_smoke.py --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=50 -v
```

The excluded E2E smoke test runs separately:

```text
pytest tests/test_e2e_smoke.py -v -m e2e
```

The E2E job depends on the Python Tests job succeeding.

---

## Gaps and Follow-up

The following observations were identified during the CI workflow review:

- Branch filters prevent CI from running on pull requests targeting branches
  other than the configured target branches.
- Checks run sequentially, so an earlier failure can prevent later checks from
  executing in the same workflow run.
- Ruff checks only the explicitly listed directories rather than the entire
  repository.
- The E2E workflow depends on Docker builds, service startup, and an API
  readiness loop, which are potential reliability risks.
- A workflow configuration review alone cannot establish the absence of flaky
  tests.
- Required branch-protection checks were not verified as part of this review.

These observations are documentation findings only. No CI workflow changes were
made as part of Issue #32.

---

## Conclusion

Ruff linting and pytest are configured in the existing CI workflow and run for
the supported pull request target branches when their required preceding steps
succeed.

However, CI coverage is limited to the configured branch targets, and the
identified gaps or potential reliability concerns should be reviewed separately
by the maintainers if follow-up changes are required.