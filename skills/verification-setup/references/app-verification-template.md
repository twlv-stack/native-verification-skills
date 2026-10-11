# App verification record

Adapt these fields to the existing project docs. Keep only information another agent needs to repeat the checked flow. No secrets or real customer data.

## Runbook

- Application, repository identity, workspace, checked revision and date.
- Target: local, preview or live; exact URL or launch target.
- Runtime prerequisites, setup/start command, working directory, expected readiness signal, and how to stop only this task's server.
- Available browser/computer/simulator tool on this host; supported fallback and limits.
- Named test account/fixture and required roles. Explain safe reset and cleanup; identify side effects requiring specific authorization.
- Commands for relevant tests, lint/types/build, and mandatory project gates. Describe what each proves.
- Representative journey: preconditions, ordered actions, expected visible result, expected underlying state, and one relevant failure/boundary case.
- Evidence location, observed result, checked revision/date, known gaps.

## Feature map

| Feature and user intent | Preconditions | Actual navigation | Observable success | Source and checks | Verification status |
|---|---|---|---|---|---|
| Use the app's own feature name | Account/role/fixture/flag | URL, clicks, visible labels, observed stable selectors | Visible result plus state that must persist or change | Source entry points and targeted check command | Observed + revision/date, inferred from code, or blocked + reason |

A map is a navigation aid, not a complete specification. Add the feature involved in the task and nearby dependencies. Do not mark a row observed until it has been exercised. Keep account identifiers and secrets outside the map.

## Evidence record

- Request/acceptance condition:
- Environment and revision:
- Action performed:
- Actual result:
- Screenshot/log/test result path:
- What this evidence does and does not establish:
- Fix and recheck, or remaining blocker:

## Maintenance triggers

Update the affected row and runbook command after a route, label, role, feature flag, startup method, test fixture, or tooling change. Recheck that path. A new cloud computer needs its own environment discovery and smoke check even if the source files were copied successfully.
