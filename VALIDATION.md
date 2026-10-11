# Validation

Checked on 2026-10-11 on Windows. These results describe this package and local
fixtures; they do not establish that another computer or a production app works.

## Public package

- Three skill entrypoints passed the skill format validator.
- Installer suite: 16 cases, 15 passed, one skipped because Windows denied symbolic
  link creation. The separate Windows junction traversal test passed.
- The actual bundle preview wrote nothing. Applying to a separate test home
  created 16 files for Claude and Codex. Read-only verification checked hashes,
  local Markdown links, and instruction blocks. An unchanged second apply changed
  zero files.
- Existing-instruction preservation, changed-file backups, path rejection,
  manifest tampering, missing references, and drift detection have regression cases.
- The public payload omits the optional third-party recorder and source guide.
  No recorder or cloud-computer behavior is certified by these tests.

## Earlier local behavior checks

An independent read-only reasoning evaluation of the public evidence skill passed
three cases: reject build/toast evidence when reload loses data; report a required
video as blocked when no authorized recorder is available; and limit a repaired
fixture result to that fixture while production remains untested. This was a
reasoning evaluation, not a fresh browser or recorder test.

Before public packaging, an independent agent used a synthetic task-list UI and
caught an item disappearing after reload despite a successful-looking save. After
the fixture was repaired, it repeated the flow, confirmed persistence, and checked
that an empty submission did not add an item.

Local Claude Opus 5.5 and Sonnet 5.5 discovery/reasoning checks loaded the three
skills and rejected a passing build and save toast as sufficient persistence proof.
These checks used the earlier local evidence skill variant with an optional
recorder; they are not new browser tests of the public version.

The public evidence skill preserves the core flow, state, persistence, and scope
requirements while changing recording to use host-supported tools. Agent discovery
and real behavior must still be checked after installation on each target host.

## Not verified

- Grok Bot native registration or Claude discovery inside its cloud computer.
- Linux or macOS installation in this publication run.
- Screen recording with any particular capture tool.
- Any customer-facing production flow.

No model usage logs, private settings, or customer data are distributed as evidence.
