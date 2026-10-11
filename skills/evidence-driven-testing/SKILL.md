---
name: evidence-driven-testing
description: Verify changed app behavior by exercising the real flow and inspecting
  its result. Use during implementation and before claiming an app fix or UI change
  works; collect focused evidence and record only when motion or timing matters.
metadata:
  version: '1.4'
  compatibility: Requires access to the app under test and the host's supported
    browser or computer tools. Recording is optional and uses an existing authorized
    recorder. This distribution does not bundle a screen recorder.
---


# Evidence-driven testing

Prove the requested behavior with evidence appropriate to the change. Use this within the current build or debugging workflow. Read the project's existing verification runbook and the affected feature-map entries; reuse a working setup instead of starting over. If no reliable way to run or navigate the app exists, use `verification-setup` when available or establish the smallest working setup directly.

1. Identify testable outcomes, the exact local/preview/live target and revision, and relevant project checks. Ground diagnoses in the actual code and observed behavior. For a defect, reproduce the reported failure before changing it when feasible, and re-run the same path after the fix. If the baseline cannot be reproduced, say so; do not invent a before/after claim. Exercise the affected flow with the host's supported browser/computer tools. Respect the host's tool restrictions; do not install an alternative driver to bypass them.
2. Capture the smallest useful evidence: results and screenshots usually suffice. Record a video when requested or when timing and interaction are important. Bound recording to the target app/region; avoid other windows, notifications, credentials, and unrelated customer data.
3. When a video is needed, discover an existing recorder supported and authorized by the host. Check capture capability before the test, record only the relevant flow, stop capture, and play back the saved artifact. Keep a short record of test steps, assertions, results, and approximate timestamps. Do not silently install capture software or bypass tool restrictions. If recording is unavailable, use screenshots and observed behavior checks where they satisfy the task; if video itself was requested, report that part as blocked. This skill does not bundle or assume a recorder executable.
4. Inspect the actual screen and relevant underlying state, including persistence after reload when it matters. Run the project's required checks and the smallest meaningful regression/boundary checks. Fix relevant failures and return to the affected check. A passing build proves buildability; a screenshot proves appearance; neither alone proves the complete user flow. Record blocked or untested conditions explicitly rather than marking them passed.
5. Store artifacts locally and inspect them. Update affected feature-map/runbook entries if navigation, startup, or prerequisites changed, with observed status and revision/date. For recurring failures, consider a narrow test, type, lint, or architectural check that rejects the bad case and accepts the good case; do not broaden the task into a rewrite. Never present a synthetic fixture, test video, or copied screenshot as real app evidence. Do not record continuously or make every small change generate a video.
6. Summarize the outcome, environment/revision, what was exercised, evidence paths, and limitations. Attach or publish evidence only with task authorization for the destination after inspecting the actual artifact. A live verification must stay within the authorized data/payment/message scope.

No screen capture starts merely by loading this skill.

Discover capture capabilities on the current host. A local PC, Grok Bot cloud computer, and Claude running inside that computer can have different tools and permissions. A copied skill does not establish access or successful verification. Use screenshots and direct behavior checks when they meet the requested acceptance conditions.
