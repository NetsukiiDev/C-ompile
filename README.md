# C(ompile)

[![CI](https://github.com/NetsukiiDev/C-ompile/actions/workflows/ci.yml/badge.svg)](https://github.com/NetsukiiDev/C-ompile/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Compile C with one letter.** C(ompile) installs `c`, a small Bash wrapper that clears the terminal and runs your C compiler with strict warnings enabled.

```bash
c main.c -o app
# Equivalent to:
clear
cc -Werror -Wextra -Wall main.c -o app
```

The project is named **C(ompile)**; its GitHub slug is `C-ompile`, and the installed command is always **`c`**.

## Features

- Uses `cc` when available, otherwise falls back to `gcc`.
- Adds `-Werror -Wextra -Wall` by default.
- Accepts `-NoFlags` anywhere to disable only those automatic flags.
- Preserves explicit compiler options, multiple source files and paths with spaces.
- Clears the terminal before each invocation.
- Prints the exact compiler command and English progress, success or failure messages.
- Passes through compiler diagnostics and exit status without filtering.
- Installs for one user without sudo or shell configuration changes.

## Requirements and compatibility

| Component | Requirement |
| --- | --- |
| Runtime | Bash 3.2+ and `clear` (usually provided by ncurses) |
| Compiler | `cc` or `gcc` in `PATH`, accepting `-Werror`, `-Wextra`, `-Wall` |
| Toolchains | GCC or Clang; `cc` may point to either |
| Installation | Standard Unix tools: `mkdir`, `dirname`, `cmp`, `mktemp`, `cp`, `install`, `mv`, `rm` |
| Calling shell | Bash, Zsh, Fish or another shell that can run executables |
| Desktop | No desktop dependencies or settings changes |

### Operating systems

| Operating system | Support and verification |
| --- | --- |
| Linux — Arch, Ubuntu, Debian, Fedora and similar distributions | Supported when the requirements above are available. Locally verified on Arch Linux; automated tests passed on Ubuntu. Other distributions have not been individually tested. |
| macOS | Supported when the requirements above are available. Automated tests passed on the GitHub-hosted macOS runner. Intel and Apple Silicon are expected to work, but CI does not separately verify both architectures. |
| Windows with WSL | Expected to work inside a Linux distribution with the required dependencies; not directly tested on WSL. Install and run from the Linux shell. |
| Native Windows — PowerShell or Command Prompt | Not supported. Use WSL instead. Git Bash and other compatibility layers are not tested or supported. |
| FreeBSD, OpenBSD and other BSD systems | Potentially compatible with Bash and the required Unix tools installed; not tested or officially supported. |

The calling shell can be Bash, Zsh or Fish; the script itself always runs with Bash. No particular desktop environment or window manager is required. Installing the wrapper does not require sudo; its dependencies must be installed separately and available in `PATH`.

Locally verified with `cc` pointing to GCC. CI uses mock compilers to test the wrapper and installer; it does not certify every compiler, OS version or hardware architecture. See the [CI results](https://github.com/NetsukiiDev/C-ompile/actions/workflows/ci.yml) for the latest status. A GCC- or Clang-compatible compiler must be available on your chosen platform. The command does not enforce a language standard, install a toolchain, or guarantee compliance with 42 evaluations.

## Install without sudo

```bash
git clone https://github.com/NetsukiiDev/C-ompile.git
cd C-ompile
./install.sh
```

The default destination is **`$HOME/.local/bin/c`**. No dependencies are installed, no startup files are edited, and no administrator permissions are requested. A missing compiler produces an installation warning and runtime exit status `127` until one is available.

You can choose any writable directory:

```bash
./install.sh --bin-dir "$HOME/tools/bin"
```

If no compiler is installed, provide a suitable toolchain in your `PATH` or ask your system administrator. The wrapper itself needs no sudo, but it cannot provide the compiler for you.

### PATH and command conflicts

Check `type -a c` first: an existing shell alias or function may take precedence over the executable. The installer never edits those definitions and never overwrites an existing file without explicit permission.

If `$HOME/.local/bin` is not already on `PATH`, add this once to `~/.bashrc` for Bash or `~/.zshrc` for Zsh:

```bash
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
esac
```

For Fish, run once:

```fish
fish_add_path "$HOME/.local/bin"
```

Open a new terminal and verify `command -v c`. Substitute your custom directory if you used `--bin-dir`. No PATH changes are necessary if the directory is already present.

## Usage

```bash
c main.c                              # Strict warnings, usual compiler output
c main.c -o app                       # Select the output name
c main.c utils.c -o app                # Multiple source files
c "source with spaces.c" -o "my app"   # Paths with spaces
c -c helpers.c                        # Compile an object file
c -fsyntax-only main.c                # Check without producing a binary
c -NoFlags main.c                     # No automatic warning flags
c main.c -NoFlags -o app               # Option can appear anywhere
c -NoFlags -Wall main.c               # Keep a flag you explicitly supplied
```

C(ompile) now shows what it is doing. For example:

```text
c: Starting compilation...
c: Command: cc -Werror -Wextra -Wall main.c -o app
c: Compilation succeeded.
```

If compilation fails, the compiler prints its usual errors and C(ompile) ends with a message such as `c: Compilation failed (exit code 1).` Status messages go to standard error so compiler output on standard output (including preprocessor output) stays unchanged. The command returns the compiler's original exit code.

`-NoFlags` is case-sensitive and is consumed by the wrapper, never passed to the compiler. Repeating it is harmless. It removes only the wrapper's defaults: your own options are preserved, and the compiler may still report its own warnings and errors. Other arguments are passed as `"$@"` with their boundaries preserved.

With no arguments, the compiler reports its normal “no input files” error; `c` does **not** automatically select `*.c`. Shell globs such as `c *.c` are expanded by the calling shell. The output name, object files and other generated files follow normal compiler behavior; there is no automatic program execution.

`clear` runs even for `c --help`. A valid terminal/`TERM` is needed for screen clearing. If it fails, compilation still runs and returns the compiler's status. Scrollback clearing depends on terminal support. Only the three warning flags are supplied automatically: add `-std=...`, sanitizers or other options yourself.

## Update and uninstall

```bash
git pull --ff-only
./install.sh --force
```

An identical installation is a no-op. A different file requires `--force`, which first saves it beside the command as `c.backup.XXXXXX`. Symlinks and non-regular destinations are never replaced. Backups are not automatically deleted.

```bash
./uninstall.sh
# For a custom destination:
./uninstall.sh --bin-dir "$HOME/tools/bin"
```

Uninstall removes only a file identical to `bin/c` in this checkout. It refuses modified files, symlinks and different installed versions. Use the matching checkout for an older version. Compilers, backups, directories and PATH settings are not removed.

## Development

```bash
for script in bin/c install.sh uninstall.sh; do bash -n "$script"; done
python3 -m unittest discover -s tests -v
```

Python 3.8+ is needed for tests. Tests use temporary directories and mock compilers, never your current installation or C projects. They check flags, compiler selection, argument quoting, clear ordering, exit codes, installation, backups and safe removal.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE).
