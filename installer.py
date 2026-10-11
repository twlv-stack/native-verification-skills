#!/usr/bin/env python3
"""Preview, install, and verify a manifest-listed agent skill bundle (stdlib only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit


START = "<!-- shared-verification-skills:start -->"
END = "<!-- shared-verification-skills:end -->"
TARGETS = {
    "claude": (".claude/skills", ".claude/CLAUDE.md"),
    "codex": (".agents/skills", ".codex/AGENTS.md"),
}
RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.I)


class InstallError(Exception):
    """An invalid bundle or unsafe destination; no workaround is attempted."""


@dataclass(frozen=True)
class Change:
    path: Path
    before: bytes | None
    after: bytes


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def absolute(path: Path) -> Path:
    # Deliberately do not resolve links before checking the original path.
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def safe_path(path: Path, boundary: Path) -> None:
    path, boundary = absolute(path), absolute(boundary)
    try:
        within = os.path.commonpath([str(path), str(boundary)])
    except ValueError as exc:
        raise InstallError(f"Path leaves the selected directory: {path}") from exc
    if os.path.normcase(within) != os.path.normcase(str(boundary)):
        raise InstallError(f"Path leaves the selected directory: {path}")
    # lstat sees broken links too. Reparse points include Windows junctions,
    # including on Python versions without Path.is_junction(). Refuse all links.
    for item in reversed((path, *path.parents)):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise InstallError(f"Cannot inspect {item}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise InstallError(f"Refusing symlink or junction traversal: {item}")
        if item != path and not stat.S_ISDIR(info.st_mode):
            raise InstallError(f"Parent is not a directory: {item}")


def relative_name(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise InstallError(f"Invalid manifest path: {value!r}")
    parts = value.split("/")
    if any(part in ("", ".", "..") or part.rstrip(" .") != part
           or RESERVED.match(part) or re.search(r'[<>:"|?*\x00-\x1f]', part)
           for part in parts):
        raise InstallError(f"Unsafe or nonportable manifest path: {value!r}")
    return value


def read_regular(path: Path, boundary: Path) -> bytes | None:
    safe_path(path, boundary)
    if not path.exists():
        return None
    if not path.is_file():
        raise InstallError(f"Expected a regular file: {path}")
    return path.read_bytes()


def markdown_links(text: str):
    """Read ordinary inline and reference links, excluding fenced examples."""
    text = re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$", "", text)
    for match in re.finditer(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[\"'][^\n]*?[\"'])?\s*\)", text):
        yield match.group(1).strip("<>")
    for match in re.finditer(r"(?m)^\s{0,3}\[[^\]\n]+\]:\s*(<[^>]+>|\S+)", text):
        yield match.group(1).strip("<>")


def validate_references(files: dict[str, bytes]) -> None:
    for name, data in files.items():
        if not name.lower().endswith(".md"):
            continue
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise InstallError(f"Markdown must be UTF-8: {name}") from exc
        for link in markdown_links(text):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                if parsed.scheme.lower() == "file" or re.match(r"^[A-Za-z]:", link):
                    raise InstallError(f"Nonportable local reference in {name}: {link}")
                continue
            local = unquote(parsed.path)
            if not local:
                continue
            if local.startswith("/") or "\\" in local:
                raise InstallError(f"Nonportable local reference in {name}: {link}")
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), local))
            if target not in files and not any(key.startswith(target.rstrip("/") + "/") for key in files):
                raise InstallError(f"Unbundled or missing reference in {name}: {link}")


def load_bundle(bundle: Path) -> dict[str, bytes]:
    bundle = absolute(bundle)
    raw = read_regular(bundle / "manifest.json", bundle)
    if raw is None:
        raise InstallError("Bundle is missing manifest.json")
    try:
        manifest = json.loads(raw.decode("utf-8-sig"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise InstallError("manifest.json is not valid UTF-8 JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("version") != 1 or not isinstance(manifest.get("files"), list):
        raise InstallError("Expected manifest version 1 with a files array")
    files: dict[str, bytes] = {}
    folded = set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict):
            raise InstallError("Each manifest file must have path and sha256 fields")
        name = relative_name(entry.get("path"))
        parts = PurePosixPath(name).parts
        if name != "defaults.md" and not (
            len(parts) >= 3 and parts[0] == "skills"
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", parts[1])
        ):
            raise InstallError(f"Only defaults.md and skills/<name>/ resources are installable: {name}")
        if name.casefold() in folded:
            raise InstallError(f"Duplicate or case-colliding manifest path: {name}")
        folded.add(name.casefold())
        expected = entry.get("sha256", "")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise InstallError(f"Invalid SHA-256 for {name}")
        data = read_regular(bundle / name, bundle)
        if data is None or digest(data) != expected:
            raise InstallError(f"Bundle file missing or hash mismatch: {name}")
        files[name] = data
    if "defaults.md" not in files:
        raise InstallError("Manifest must list defaults.md")
    skills = {PurePosixPath(name).parts[1] for name in files if name.startswith("skills/")}
    if not skills:
        raise InstallError("Manifest must include at least one skill")
    for skill in skills:
        if f"skills/{skill}/SKILL.md" not in files:
            raise InstallError(f"Skill is missing manifest-listed SKILL.md: {skill}")
    for name in files:
        if any(str(parent) in files for parent in PurePosixPath(name).parents):
            raise InstallError(f"Manifest file conflicts with a parent file: {name}")
    # defaults.md becomes an instruction block, never a standalone installed
    # file. Skill resources may only link to other installed skill resources.
    validate_references({name: data for name, data in files.items() if name != "defaults.md"})
    return files


def instruction_block(defaults: bytes, newline: str) -> str:
    try:
        text = defaults.decode("utf-8-sig").replace("\r\n", "\n").strip()
    except UnicodeDecodeError as exc:
        raise InstallError("defaults.md must be UTF-8") from exc
    if not text or START in text or END in text:
        raise InstallError("defaults.md must be nonempty and must not contain installer markers")
    return newline.join((START, text.replace("\n", newline), END))


def merge_instructions(before: bytes | None, defaults: bytes) -> bytes:
    try:
        original = (before or b"").decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InstallError("Existing instructions must be UTF-8; refusing to overwrite") from exc
    newline = "\r\n" if "\r\n" in original else "\n"
    block = instruction_block(defaults, newline)
    starts, ends = original.count(START), original.count(END)
    if starts == ends == 0:
        gap = "" if not original or original.endswith(newline * 2) else newline if original.endswith(newline) else newline * 2
        return (original + gap + block + newline).encode("utf-8")
    if starts != 1 or ends != 1:
        raise InstallError("Instruction markers are incomplete or duplicated; refusing an ambiguous merge")
    start, end = original.index(START), original.index(END)
    end += len(END)
    start_end = start + len(START)
    end_start = end - len(END)
    if (end_start <= start or (start and original[start - 1] != "\n")
            or original[start_end:start_end + 1] not in ("\r", "\n")
            or original[end_start - 1:end_start] != "\n"
            or (end < len(original) and original[end] not in "\r\n")):
        raise InstallError("Instruction markers must be ordered and on separate lines")
    return (original[:start] + block + original[end:]).encode("utf-8")


def parse_targets(value: str) -> tuple[str, ...]:
    result = tuple(part.strip() for part in value.split(","))
    if not result or len(set(result)) != len(result) or any(part not in TARGETS for part in result):
        raise InstallError("--targets must be claude, codex, or claude,codex")
    return result


def plan_install(home: Path, targets: tuple[str, ...], files: dict[str, bytes]) -> list[Change]:
    home = absolute(home)
    safe_path(home, home)
    if home.exists() and not home.is_dir():
        raise InstallError(f"--home must be a directory: {home}")
    changes = []
    for target in targets:
        skill_root, instructions = TARGETS[target]
        # Embedding defaults changes its relative-link base. Validate the
        # complete expected layout separately for each selected host.
        reference_files = {
            f"{skill_root}/{name.removeprefix('skills/')}": data
            for name, data in files.items() if name != "defaults.md"
        }
        reference_files[instructions] = files["defaults.md"]
        validate_references(reference_files)
        for name, data in files.items():
            if name == "defaults.md":
                continue
            path = home / skill_root / name.removeprefix("skills/")
            old = read_regular(path, home)
            if old != data:
                changes.append(Change(path, old, data))
        path = home / instructions
        old = read_regular(path, home)
        new = merge_instructions(old, files["defaults.md"])
        if old != new:
            changes.append(Change(path, old, new))
    return changes


def write_new(path: Path, data: bytes, home: Path) -> None:
    safe_path(path, home)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_path(path, home)
    with path.open("xb") as stream:
        stream.write(data)


def apply_changes(home: Path, changes: list[Change]) -> Path | None:
    home = absolute(home)
    backup = None
    # Validate every affected destination before creating even a backup.
    for change in changes:
        if read_regular(change.path, home) != change.before:
            raise InstallError(f"File changed since preview; retry: {change.path}")
    if any(change.before is not None for change in changes):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup = home / ".skill-install-backups" / (stamp + "-" + uuid.uuid4().hex[:8])
        safe_path(backup, home)
        for change in changes:
            if change.before is not None:
                write_new(backup / change.path.relative_to(home), change.before, home)
    for change in changes:
        safe_path(change.path, home)
        if read_regular(change.path, home) != change.before:
            raise InstallError(f"File changed during installation; backup retained: {change.path}")
        change.path.parent.mkdir(parents=True, exist_ok=True)
        safe_path(change.path, home)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(prefix=".skill-install-", dir=change.path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(change.after)
            # Preserve existing file permissions when replacing an existing file.
            if change.before is not None:
                os.chmod(temporary, stat.S_IMODE(change.path.stat().st_mode))
            safe_path(change.path, home)
            if read_regular(change.path, home) != change.before:
                raise InstallError(f"File changed during installation; backup retained: {change.path}")
            os.replace(temporary, change.path)
            temporary = None
        finally:
            if temporary is not None:
                safe_path(temporary, home)
                temporary.unlink(missing_ok=True)
    return backup


def verify_install(home: Path, targets: tuple[str, ...], files: dict[str, bytes]) -> list[str]:
    home = absolute(home)
    problems = []
    for target in targets:
        skill_root, instructions = TARGETS[target]
        installed = {}
        for name, expected in files.items():
            if name == "defaults.md":
                continue
            path = home / skill_root / name.removeprefix("skills/")
            actual = read_regular(path, home)
            if actual is None:
                problems.append(f"{target}: missing {name}")
            elif digest(actual) != digest(expected):
                problems.append(f"{target}: content/hash differs for {name}")
            if actual is not None:
                installed[f"{skill_root}/{name.removeprefix('skills/')}"] = actual
        path = home / instructions
        actual = read_regular(path, home)
        try:
            if actual is None or merge_instructions(actual, files["defaults.md"]) != actual:
                problems.append(f"{target}: instruction block missing or differs")
            else:
                # The block's exact content was verified above. Resolve only
                # its links at the real instruction file path; unrelated user
                # instructions are outside the installer's responsibility.
                installed[instructions] = files["defaults.md"]
        except InstallError as exc:
            problems.append(f"{target}: {exc}")
        try:
            validate_references(installed)
        except InstallError as exc:
            problems.append(f"{target}: {exc}")
    return problems


def main(argv: list[str] | None = None, *, bundle: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True, type=Path, help="Explicit target user home directory")
    parser.add_argument("--targets", default="claude,codex", help="claude,codex (default), claude, or codex")
    parser.add_argument("--apply", action="store_true", help="Apply changes; otherwise preview only")
    parser.add_argument("--verify", action="store_true", help="Verify installed files; combine with --apply to install then verify")
    args = parser.parse_args(argv)
    try:
        home = absolute(args.home)
        targets = parse_targets(args.targets)
        files = load_bundle(bundle or Path(__file__).parent)
        if args.apply or not args.verify:
            changes = plan_install(home, targets, files)
            print(f"{'Install' if args.apply else 'Preview'}: {len(changes)} file(s) would change in {home}")
            for change in changes:
                print(f"  {'Update' if change.before is not None else 'Create'} {change.path.relative_to(home)}")
            if args.apply:
                backup = apply_changes(home, changes)
                print(f"Applied {len(changes)} file change(s).")
                if backup:
                    print(f"Backups: {backup}")
            else:
                print("Preview only. No directories or files were created or changed.")
        if args.verify or args.apply:
            problems = verify_install(home, targets, files)
            if problems:
                for problem in problems:
                    print(f"FAIL: {problem}")
                return 1
            print("PASS: filesystem files, SHA-256 hashes, local Markdown references, and instruction block verified.")
            print("Host discovery is NOT verified. Reload the target agent and confirm each skill is actually listed and usable.")
        return 0
    except (InstallError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
