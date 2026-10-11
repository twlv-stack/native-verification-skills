# Contributing

Open an issue describing the observed failure or send a focused pull request.
Include the expected behavior, what changed, and the checks you ran.

Use Python 3.10 or newer. The installer has no third-party dependencies:

```sh
python -B -m unittest -v test_installer
```

Use a temporary home when exercising installation. Never test against another
person's real agent settings. Preserve existing instructions and backups, reject
unsafe paths, and keep repeated installs unchanged.

If you edit files listed in `manifest.json`, recalculate each changed file's SHA-256
hash from its LF-normalized bytes. Test the actual bundle in addition to the unit
test fixtures. Do not include secrets or customer data in evidence.

Contributions are provided under the project's MIT license. Do not add material
whose redistribution rights are unknown.
