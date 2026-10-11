# Portable verification skills

This installer puts the bundled skills in Claude's and Codex's user skill folders and adds a bounded instruction block. It requires Python 3.10 or newer, uses only the standard library, and installs no packages. It makes no network requests or service changes.

Keep this entire folder together, including `manifest.json`, `defaults.md`, and `skills/`. The manifest lists the exact files and SHA-256 hashes approved for installation. Unlisted files are ignored. The installer itself does not create or modify the manifest.

## Preview and install

Supply the intended account's home directory explicitly. The preview is the default and does not write anything.

Windows examples, from this folder:

```powershell
python installer.py --home 'C:\Users\YOUR_ACCOUNT'
python installer.py --home 'C:\Users\YOUR_ACCOUNT' --targets claude,codex --apply
python installer.py --home 'C:\Users\YOUR_ACCOUNT' --targets claude,codex --verify
```

On a Linux or macOS cloud computer, run these inside that computer using the account that runs the agent:

```sh
python3 installer.py --home "$HOME"
python3 installer.py --home "$HOME" --targets claude --apply
python3 installer.py --home "$HOME" --targets claude --verify
```

Choose `--targets claude`, `--targets codex`, or `--targets claude,codex`. An apply also runs filesystem verification; `--apply --verify` is supported. `--verify` alone is read-only. Exit codes are `0` for success, `1` for verification drift, and `2` for an invalid bundle, unsafe path, or installation error.

| Target | Skill files | Instructions merged |
| --- | --- | --- |
| Claude | `<home>/.claude/skills/<skill>/` | `<home>/.claude/CLAUDE.md` |
| Codex | `<home>/.agents/skills/<skill>/` | `<home>/.codex/AGENTS.md` |

Existing instructions outside the `shared-verification-skills` markers are preserved. Changed existing files are backed up to `<home>/.skill-install-backups/<timestamp>/`, with their relative paths intact. Rerunning an unchanged bundle does not rewrite files, create backups, or duplicate instruction blocks. The installer never removes unrelated or obsolete files. On failure after some writes, inspect the output and backups before rerunning; an installation is atomic per file, not across the entire bundle.

For safety, every symlink, Windows junction, or other reparse point encountered in a bundle or destination path is refused, including links that point inside the selected home. It also refuses ambiguous instruction markers and invalid hashes before writing. Use a real target directory, and let the local owner decide how an existing linked setup should be maintained. Do not replace links just to force installation.

Backups can contain your existing instructions. Keep them private. To undo an update, restore only the affected files from the named backup after reviewing any newer changes. Newly created files have no prior backup; remove them only after confirming that nothing has since been added to them. There is deliberately no automatic recursive uninstall.

## Confirm actual agent discovery

A passing installer check confirms the files, hashes, bundled Markdown references, and instruction block. It does **not** prove that an agent has loaded the skills or used them.

After installation, start a new session or use the host's supported reload mechanism. Confirm that the skill names appear in its native skills list. Ask the agent to use `verification-setup` on a harmless temporary fixture and run the documented skill evaluation. Check both an expected success and an intentional failure. Save the observed result. Report file installation, native discovery, and successful behavior as separate outcomes.

## Grok Bot cloud computer and native skills

Claude running inside Grok Bot's cloud computer can use the Claude files above when that computer exposes a supported terminal and normal Claude configuration. Run the installer **inside the cloud computer**, with its actual Claude account home. Installing on a separate PC does not install anything in the cloud computer.

Grok Bot's **native private skill registry is separate from Claude file skills**. There is no assumed Grok Bot filesystem installation path. Using Grok Bot's supported UI or skill tool, save each skill as a **private** native skill with its bundled references and scripts. The documented workflow uses **Save a skill**, then **Settings > Plugins > Yours**. Enable the saved skills and reload or start a session as the product requires. Check that Grok Bot itself discovers each native skill and can execute a harmless verification example with a deliberate failure case. If its native registry cannot retain or execute a required resource, record that limitation instead of claiming successful installation. The Python installer cannot perform or verify these native registry steps.

Product reference: [Grok Bot work documentation](https://cursor.com/docs/grok-bot/work).

## Bundle maintenance and tests

Manifest schema:

```json
{
  "version": 1,
  "files": [
    {"path": "defaults.md", "sha256": "64 lowercase hexadecimal characters"},
    {"path": "skills/example/SKILL.md", "sha256": "64 lowercase hexadecimal characters"}
  ]
}
```

Each skill must have a listed `SKILL.md`. Include every required local resource in the manifest and use ordinary relative Markdown links for references that should be checked. External URLs and fragment anchors are not fetched. Fenced code examples are ignored by the Markdown reference check. The checker does not execute scripts or validate arbitrary path strings embedded in code.

Run behavioral tests with `python -B -m unittest -v test_installer` from this folder. Tests create and remove only their own temporary tree inside this folder. A filesystem that disallows symbolic-link creation may skip that fixture; the Windows junction fixture is tested on Windows. No test targets your real agent home.
