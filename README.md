# Native Verification Skills

Three portable agent skills for checking that software actually works.

| Skill | What it does |
| --- | --- |
| [verification-setup](skills/verification-setup/SKILL.md) | Builds a tested app runbook and feature map so another agent can repeat the same flow. |
| [evidence-driven-testing](skills/evidence-driven-testing/SKILL.md) | Reproduces failures, operates the real app, checks the resulting state, and reports evidence and gaps. |
| [skill-evals](skills/skill-evals/SKILL.md) | Evaluates a skill on representative tasks, edge cases, and a held-out case with bounded retries. |

A passing build or a “Saved” toast alone is not proof that a user flow works.
These skills ask agents to inspect the actual result and distinguish local,
preview, and live evidence.

Inspired by [Lauren Tan's pstack](https://github.com/cursor/plugins/tree/main/pstack).
These are portable adaptations of verification practices, not the full pstack
framework. See [origins and distribution scope](NOTICE.md).

## Install or recover on a new computer

Clone or download this repository. Keep the files together. Python 3.10+ is required;
the installer uses only the standard library.

```sh
git clone https://github.com/twlv-stack/native-verification-skills.git
cd native-verification-skills
python3 installer.py --home "$HOME"
python3 installer.py --home "$HOME" --targets claude,codex --apply
python3 installer.py --home "$HOME" --targets claude,codex --verify
```

On Windows, use `python` and `--home "$env:USERPROFILE"` in PowerShell.
The first installer command previews without writing. Choose only the agents you
use: `--targets claude`, `--targets codex`, or both.

The installer checks file hashes, preserves existing instructions outside its
marked block, backs up changed files, and refuses symlink or junction traversal.
An unchanged second install makes no changes. It does not delete obsolete files
or start background jobs. Read [installation and rollback details](INSTALL.md).

Start a fresh agent session and confirm all three skills appear. Then exercise a
harmless fixture with a passing case and an intentional failure. Installer success
alone does not prove native discovery or behavior.

## Cloud computers and Grok Bot

Run installation inside the actual computer that runs Claude or Codex. A local PC
installation does not reach a separate cloud computer.

Grok Bot's native skill registry needs its own supported registration and discovery
check. The Python installer does not do that. Use the
[cloud setup checklist](GROK-BOT-BOOTSTRAP.md); cloud behavior is not yet verified.

## Verification and boundaries

See [validation notes](VALIDATION.md) for observed checks and their limits.
Run the installer suite with:

```sh
python -B -m unittest -v test_installer
```

No credentials, downloaded video, private personal instructions, or runtime
evidence are bundled. No screen recorder is bundled. Use the host's supported
tools. Installing skills does not grant permission to deploy, spend money, alter
live data, send messages, or broaden access.

There are no GitHub Actions workflows or deployment jobs in this repository.

## License

[MIT](LICENSE). Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).
