---
name: verification-setup
description: Set up or repair an app's repeatable verification workflow and feature map so agents can run the app and check user behavior. Use when verification is missing, unreliable, or being moved to a new computer; reuse a working setup for ordinary changes.
---

# Verification setup

Make the current app verifiable by an agent on the current computer. Work within the active task and repository conventions; this is a supporting capability, not a replacement build workflow.

## Build the smallest working setup

1. Identify the actual repository, revision, existing instructions, app entry points, documented checks, and local or preview target. Reuse an existing runbook and feature map. Discover this host's browser, terminal, simulator, and capture tools; a tool available on another computer is not evidence it exists here.
2. Choose one representative flow relevant to the task. Establish its expected visible and underlying result and safe test data. Prefer a local test account or isolated fixture. Record required access as a named prerequisite, never a password, cookie, token, or customer record.
3. Start the app through its documented command. Add the smallest repeatable command or helper only when needed. Use the host's supported browser/computer tools and observe the real app; source code can suggest navigation but cannot prove a control is reachable.
4. Run the flow, inspect the resulting screen and state, and exercise a relevant failure or boundary case. If it fails, return to the failing setup or app step and recheck after a concrete fix. Stop repeating unchanged attempts when access or infrastructure is the obstacle; complete independent checks and report the precise gap.
5. Save a concise runbook and feature map, using [references/app-verification-template.md](references/app-verification-template.md) for the fields. Prefer the project's existing paths; otherwise use `docs/verification/RUNBOOK.md` and `docs/verification/FEATURE-MAP.md`. Document the tested scope, not an imaginary inventory of the entire app. Link the runbook from project instructions where useful.
6. Have a fresh agent follow the runbook for the representative flow when independent delegation is available and authorized. Require the actual result and artifacts. A written plan or successful document validation does not establish that the runbook works.

Keep an explicit distinction between `observed`, `inferred from code`, and `blocked`. Record a verification date and revision. Future work should maintain affected entries when navigation, environment, or behavior changes; do not remap the whole app for every edit.

## Feature map quality

Use the user's feature names and actual click paths, accessible labels, roles, stable test IDs, URLs, and prerequisites. Include the relevant source entry points and automated checks as supporting information. Record selectors only after observing them; do not invent selectors or rely on fragile screen coordinates as universal instructions. For a missing/hidden feature, record what was attempted and why it is unreachable.

## Durable improvement

When a repeated failure demonstrates a missing invariant, prefer the narrowest effective check at the relevant architectural boundary, type, lint rule, test, or CI gate. Prove the check rejects the bad case and allows a valid case. Keep broader rewrites separate from the current task. Examples from a video, such as banning all effects or comments, are not blanket rules for other apps.

## Completion

Report the target and revision, the flow actually exercised, the result, evidence paths, and the remaining limitations. Hand ordinary follow-up verification to `evidence-driven-testing` when it is available; the runbook remains usable without that skill.

This skill does not authorize production changes, paid runs, messaging, permission changes, merges, or releases. Reuse the user's task-specific authorization for any consequential test action.
