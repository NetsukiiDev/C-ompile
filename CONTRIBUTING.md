# Contributing

Issues and pull requests are welcome. Include your operating system, Bash version,
compiler version, invocation, expected behavior and actual exit status. Use a
minimal example without private code or credentials.

Keep the wrapper small and compatible with Bash 3.2+. Do not add package-manager
calls, automatic sudo, automatic program execution, or diagnostic filters.
Preserve the default flags, `-NoFlags`, quoted arguments and compiler exit status.

Run these checks before submitting:

```bash
for script in bin/c install.sh uninstall.sh; do bash -n "$script"; done
python3 -m unittest discover -s tests -v
```

Add regression tests for behavioral changes. Tests must use temporary directories
and must not modify a contributor's real installation or source projects. The CI
matrix runs on Ubuntu and macOS; do not claim support for a platform without tests.

Contributions are provided under the repository's MIT license.
