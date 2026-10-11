# Working on Native Verification Skills

Keep these three skills portable and small. Do not add mandatory hooks, background
capture, model overrides, or deployment authority.

Run `python -B -m unittest -v test_installer` after installer changes. For payload
changes, refresh manifest SHA-256 hashes and check preview, apply, verify, and an
unchanged second apply in an isolated home. Preserve LF bytes so Git checkout does
not invalidate hashes.

Skill changes need bounded behavioral evaluation. Distinguish file installation,
native discovery, and actual behavior on each host. Keep fixture evidence separate
from production evidence and disclose skipped cases.

Never commit credentials, private instructions, session logs, customer data, or
downloaded media. Check redistribution rights before adding third-party files.
This repository intentionally has no Actions workflows or deployment integration.
