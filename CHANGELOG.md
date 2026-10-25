# Changelog

## 1.0.0 — 2026-10-25

- Initial public release of C(ompile), installing the `c` command.
- Clear the terminal and compile with `-Werror -Wextra -Wall` by default.
- Add `-NoFlags` and prefer `cc`, with `gcc` as a fallback.
- Preserve compiler arguments, diagnostics and exit status.
- Add user-local installation, collision protection, backup and safe uninstall.
- Add English documentation and isolated tests with Linux/macOS CI.
