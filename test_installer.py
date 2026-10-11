"""Behavioral tests confined to a temporary tree inside this workspace."""

from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import installer


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="installer-test-", dir=Path(__file__).resolve().parent))
        self.addCleanup(self.clean_temp)
        self.bundle = self.temp / "bundle"
        self.home = self.temp / "home"
        self.home.mkdir()
        self.files = {
            "defaults.md": b"Use verification-setup for verification setup.\n",
            "skills/verification-setup/SKILL.md": b"---\nname: verification-setup\ndescription: Verify changes\n---\nRead [checks](references/checks.md).\n",
            "skills/verification-setup/references/checks.md": b"Check the actual result.\n",
        }
        self.write_bundle()

    def clean_temp(self):
        # No shell-based deletion. Assert the exact resolved test root is here.
        root = Path(__file__).resolve().parent
        resolved = self.temp.resolve()
        self.assertEqual(resolved.parent, root)
        self.assertTrue(resolved.name.startswith("installer-test-"))
        if resolved.exists():
            shutil.rmtree(resolved)

    def write_bundle(self):
        self.bundle.mkdir(exist_ok=True)
        entries = []
        for name, data in self.files.items():
            path = self.bundle / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            entries.append({"path": name, "sha256": installer.digest(data)})
        (self.bundle / "manifest.json").write_text(json.dumps({"version": 1, "files": entries}), encoding="utf-8")

    def run_cli(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = installer.main(["--home", str(self.home), *args], bundle=self.bundle)
        return result, output.getvalue()

    def snapshot(self):
        return {str(path.relative_to(self.home)): (path.read_bytes(), path.stat().st_mtime_ns)
                for path in self.home.rglob("*") if path.is_file()}

    def test_preview_does_not_create_target_or_change_any_files(self):
        self.home.rmdir()
        result, output = self.run_cli()
        self.assertEqual(result, 0, output)
        self.assertFalse(self.home.exists())
        self.assertIn("Preview only", output)

    def test_first_install_preserves_instructions_and_ignores_unlisted_file(self):
        original = b"# Existing instructions\r\nKeep this exact text.\r\n"
        instructions = self.home / ".claude/CLAUDE.md"
        instructions.parent.mkdir()
        instructions.write_bytes(original)
        (self.bundle / "skills/verification-setup/unlisted.txt").write_text("do not install", encoding="utf-8")
        result, output = self.run_cli("--apply", "--verify")
        self.assertEqual(result, 0, output)
        self.assertTrue(instructions.read_bytes().startswith(original))
        self.assertIn(b"\r\n" + installer.START.encode(), instructions.read_bytes())
        self.assertTrue((self.home / ".agents/skills/verification-setup/SKILL.md").is_file())
        self.assertFalse((self.home / ".claude/skills/verification-setup/unlisted.txt").exists())
        backups = list((self.home / ".skill-install-backups").rglob("CLAUDE.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)
        self.assertIn("Host discovery is NOT verified", output)

    def test_second_install_has_no_duplicates_rewrites_or_backups(self):
        self.assertEqual(self.run_cli("--apply")[0], 0)
        before = self.snapshot()
        result, output = self.run_cli("--apply")
        self.assertEqual(result, 0, output)
        self.assertEqual(self.snapshot(), before)
        for name in (".claude/CLAUDE.md", ".codex/AGENTS.md"):
            self.assertEqual((self.home / name).read_text().count(installer.START), 1)
        self.assertIn("Applied 0 file change(s)", output)

    def test_changed_content_is_backed_up_and_user_text_preserved(self):
        self.assertEqual(self.run_cli("--apply", "--targets", "claude")[0], 0)
        path = self.home / ".claude/skills/verification-setup/references/checks.md"
        old = path.read_bytes()
        instructions = self.home / ".claude/CLAUDE.md"
        instructions.write_bytes(b"User prefix\n\n" + instructions.read_bytes() + b"\nUser suffix\n")
        previous_instructions = instructions.read_bytes()
        self.files["defaults.md"] = b"Updated bounded defaults.\n"
        self.files["skills/verification-setup/references/checks.md"] = b"Updated checks.\n"
        self.write_bundle()
        result, output = self.run_cli("--apply", "--targets", "claude")
        self.assertEqual(result, 0, output)
        self.assertTrue(instructions.read_bytes().startswith(b"User prefix\n\n"))
        self.assertTrue(instructions.read_bytes().endswith(b"\nUser suffix\n"))
        backups = list((self.home / ".skill-install-backups").rglob("checks.md"))
        self.assertEqual([backup.read_bytes() for backup in backups], [old])
        instruction_backups = list((self.home / ".skill-install-backups").rglob("CLAUDE.md"))
        self.assertEqual([backup.read_bytes() for backup in instruction_backups], [previous_instructions])

    def test_verify_detects_content_and_instruction_drift_without_writes(self):
        self.assertEqual(self.run_cli("--apply")[0], 0)
        (self.home / ".agents/skills/verification-setup/SKILL.md").write_text("Read [missing](missing.md).", encoding="utf-8")
        (self.home / ".claude/CLAUDE.md").write_text("User-only instructions", encoding="utf-8")
        before = self.snapshot()
        result, output = self.run_cli("--verify")
        self.assertEqual(result, 1, output)
        self.assertIn("content/hash differs", output)
        self.assertIn("missing reference", output)
        self.assertIn("instruction block missing", output)
        self.assertEqual(self.snapshot(), before)

    def test_missing_bundled_reference_is_refused_before_any_write(self):
        self.files["skills/verification-setup/SKILL.md"] += b"[missing](references/missing.md)\n"
        self.write_bundle()
        result, output = self.run_cli("--apply")
        self.assertEqual(result, 2, output)
        self.assertIn("Unbundled or missing reference", output)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_skill_reference_to_uninstalled_defaults_is_refused(self):
        self.files["skills/verification-setup/SKILL.md"] += b"[defaults](../../defaults.md)\n"
        self.write_bundle()
        result, output = self.run_cli("--apply")
        self.assertEqual(result, 2, output)
        self.assertIn("../../defaults.md", output)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_verify_does_not_treat_defaults_as_an_installed_file(self):
        self.assertEqual(self.run_cli("--apply")[0], 0)
        name = "skills/verification-setup/SKILL.md"
        self.files[name] += b"[defaults](../../defaults.md)\n"
        (self.home / ".claude/skills/verification-setup/SKILL.md").write_bytes(self.files[name])
        # Call the verifier directly to exercise its own layout check even
        # when the source-validation entry point has not been used.
        problems = installer.verify_install(self.home, ("claude",), self.files)
        self.assertTrue(any("missing reference" in problem and "../../defaults.md" in problem for problem in problems))

    def test_defaults_links_are_resolved_from_each_host_instruction_file(self):
        self.files["defaults.md"] = b"Read [skill](skills/verification-setup/SKILL.md).\n"
        self.write_bundle()
        # This relative path exists from Claude's instruction directory, but
        # Codex's skill root is .agents/skills rather than .codex/skills.
        result, output = self.run_cli("--apply", "--targets", "claude,codex")
        self.assertEqual(result, 2, output)
        self.assertIn(".codex/AGENTS.md", output)
        self.assertEqual(list(self.home.iterdir()), [])
        result, output = self.run_cli("--apply", "--targets", "claude")
        self.assertEqual(result, 0, output)
        self.assertEqual(self.run_cli("--verify", "--targets", "claude")[0], 0)

    def test_defaults_can_link_to_codex_skill_root_and_verify_missing_target(self):
        self.files["defaults.md"] = b"Read [skill](../.agents/skills/verification-setup/SKILL.md).\n"
        self.write_bundle()
        result, output = self.run_cli("--apply", "--targets", "codex")
        self.assertEqual(result, 0, output)
        (self.home / ".agents/skills/verification-setup/SKILL.md").unlink()
        result, output = self.run_cli("--verify", "--targets", "codex")
        self.assertEqual(result, 1, output)
        self.assertIn("missing reference in .codex/AGENTS.md", output)

    def test_actual_bundle_installs_and_verifies_in_temporary_home(self):
        output = io.StringIO()
        actual_bundle = Path(__file__).resolve().parent
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = installer.main(["--home", str(self.home), "--apply", "--verify"], bundle=actual_bundle)
        self.assertEqual(result, 0, output.getvalue())
        self.assertIn("Host discovery is NOT verified", output.getvalue())
        files = installer.load_bundle(actual_bundle)
        self.assertEqual(installer.verify_install(self.home, ("claude", "codex"), files), [])

    def test_duplicate_or_partial_instruction_markers_refuse_every_write(self):
        instructions = self.home / ".claude/CLAUDE.md"
        instructions.parent.mkdir()
        instructions.write_text(installer.START + "\nIncomplete\n", encoding="utf-8")
        before = self.snapshot()
        result, output = self.run_cli("--apply")
        self.assertEqual(result, 2, output)
        self.assertIn("markers", output)
        self.assertEqual(self.snapshot(), before)

    def test_marker_on_user_text_line_is_not_treated_as_a_managed_block(self):
        instructions = self.home / ".claude/CLAUDE.md"
        instructions.parent.mkdir()
        instructions.write_text(installer.START + " User text\n" + installer.END + "\n", encoding="utf-8")
        before = self.snapshot()
        result, output = self.run_cli("--apply")
        self.assertEqual(result, 2, output)
        self.assertIn("separate lines", output)
        self.assertEqual(self.snapshot(), before)

    def test_unsafe_manifest_path_and_hash_mismatch_are_refused(self):
        manifest_path = self.bundle / "manifest.json"
        original = json.loads(manifest_path.read_text())
        for name in ("../escaped.md", "skills/../../escaped.md", "C:/escaped.md", "skills/test/NUL.md"):
            bad = {"version": 1, "files": [{"path": name, "sha256": "0" * 64}]}
            manifest_path.write_text(json.dumps(bad), encoding="utf-8")
            self.assertEqual(self.run_cli("--apply")[0], 2)
        original["files"][0]["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(original), encoding="utf-8")
        result, output = self.run_cli("--apply")
        self.assertEqual(result, 2, output)
        self.assertIn("hash mismatch", output)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_unsafe_symlink_outside_home_is_refused(self):
        outside = self.temp / "outside"
        outside.mkdir()
        sentinel = outside / "sentinel.txt"
        sentinel.write_bytes(b"untouched")
        link = self.home / ".claude"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Host does not permit symlink creation: {exc}")
        try:
            for args in ((), ("--apply",), ("--verify",)):
                result, output = self.run_cli(*args)
                self.assertEqual(result, 2, output)
                self.assertIn("symlink or junction", output)
            self.assertEqual(list(outside.iterdir()), [sentinel])
            self.assertEqual(sentinel.read_bytes(), b"untouched")
            self.assertFalse((self.home / ".agents").exists())
        finally:
            link.unlink()

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_windows_junction_outside_home_is_refused(self):
        # Create the fixture through the Windows API without starting a shell.
        import ctypes
        import struct
        from ctypes import wintypes
        outside = self.temp / "outside-junction"
        outside.mkdir()
        link = self.home / ".claude"
        link.mkdir()
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.DeviceIoControl.argtypes = (wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
                                             wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
                                             ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p)
        kernel32.DeviceIoControl.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        substitute = ("\\??\\" + str(outside)).encode("utf-16-le")
        display = str(outside).encode("utf-16-le")
        paths = substitute + b"\x00\x00" + display + b"\x00\x00"
        data = struct.pack("<LHHHHHH", 0xA0000003, len(paths) + 8, 0, 0, len(substitute), len(substitute) + 2, len(display)) + paths
        handle = kernel32.CreateFileW(str(link), 0x40000000, 0, None, 3, 0x02200000, None)
        if handle == wintypes.HANDLE(-1).value:
            link.rmdir()
            self.fail(f"Unable to open junction fixture: {ctypes.get_last_error()}")
        try:
            returned = wintypes.DWORD()
            buffer = ctypes.create_string_buffer(data)
            ok = kernel32.DeviceIoControl(handle, 0x000900A4, buffer, len(data), None, 0, ctypes.byref(returned), None)
            if not ok:
                self.fail(f"Unable to create junction fixture: {ctypes.get_last_error()}")
        finally:
            kernel32.CloseHandle(handle)
        try:
            for args in ((), ("--apply",), ("--verify",)):
                result, output = self.run_cli(*args)
                self.assertEqual(result, 2, output)
                self.assertIn("symlink or junction", output)
            self.assertEqual(list(outside.iterdir()), [])
        finally:
            # Removing only this known junction itself, never its target.
            link.rmdir()


if __name__ == "__main__":
    unittest.main(verbosity=2)
