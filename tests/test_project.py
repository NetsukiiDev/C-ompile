"""Isolated CLI and installer tests; no real compiler is needed."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = 'c'
CLEAR = b'\x1b[H\x1b[2J\x1b[3J'
FLAGS = [b'-Werror', b'-Wextra', b'-Wall']


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='compile-test-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.mock_bin = self.home / 'mock bin'
        self.mock_bin.mkdir()
        (self.mock_bin / 'bash').symlink_to(shutil.which('bash'))
        self.trace = self.home / 'trace'
        self.argv = self.home / 'argv'
        self.env = dict(os.environ)
        self.env.update(HOME=str(self.home), PATH=str(self.mock_bin),
                        TRACE=str(self.trace), ARGV=str(self.argv), TERM='xterm')
        self.write_mock('clear', 'printf "clear\\n" >> "$TRACE"\n'
                        'printf "\\033[H\\033[2J\\033[3J"\nexit "${CLEAR_STATUS:-0}"\n')
        self.compiler_body = ('printf "run\\n" >> "$TRACE"\n'
                              'printf "%s\\000" "$@" > "$ARGV"\n'
                              'printf "original stdout\\n"\nprintf "original stderr\\n" >&2\n'
                              'exit "${RUN_STATUS:-0}"\n')
        self.write_mock('cc', self.compiler_body)

    def write_mock(self, name, body):
        path = self.mock_bin / name
        path.write_text('#!/bin/sh\n' + body)
        path.chmod(0o755)

    def cli(self, *args, **env):
        return subprocess.run([str(ROOT / 'bin' / PROGRAM), *args], cwd=self.home,
                              env=dict(self.env, **env), capture_output=True, timeout=15)

    def arguments(self):
        return self.argv.read_bytes().split(b'\0')[:-1]

    def installer(self, *args, uninstall=False):
        env = dict(os.environ, HOME=str(self.home))
        name = 'uninstall.sh' if uninstall else 'install.sh'
        return subprocess.run(['bash', str(ROOT / name), *args], cwd=self.home,
                              env=env, capture_output=True, timeout=15)

    def test_default_flags_and_order(self):
        result = self.cli('main.c')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.arguments(), FLAGS + [b'main.c'])
        self.assertEqual(self.trace.read_text(), 'clear\nrun\n')
        self.assertEqual(result.stdout, CLEAR + b'original stdout\n')
        self.assertEqual(result.stderr, b'original stderr\n')

    def test_argument_boundaries(self):
        args = ['one.c', 'file with spaces.c', '-o', 'my app']
        self.assertEqual(self.cli(*args).returncode, 0)
        self.assertEqual(self.arguments(), FLAGS + [os.fsencode(a) for a in args])

    def test_no_flags_in_any_position(self):
        for args in [('-NoFlags', 'one.c', '-Wall'), ('one.c', '-NoFlags', '-Wall'),
                     ('one.c', '-Wall', '-NoFlags', '-NoFlags')]:
            with self.subTest(args=args):
                self.assertEqual(self.cli(*args).returncode, 0)
                self.assertEqual(self.arguments(), [b'one.c', b'-Wall'])

    def test_no_flags_is_case_sensitive(self):
        self.assertEqual(self.cli('-noflags').returncode, 0)
        self.assertEqual(self.arguments(), FLAGS + [b'-noflags'])

    def test_no_input_is_forwarded(self):
        self.assertEqual(self.cli().returncode, 0)
        self.assertEqual(self.arguments(), FLAGS)

    def test_status_and_clear_failure(self):
        for status in [0, 1, 42, 127]:
            self.assertEqual(self.cli(RUN_STATUS=str(status), CLEAR_STATUS='9').returncode,
                             status)

    def test_prefer_cc_over_gcc(self):
        self.write_mock('gcc', 'printf "wrong compiler\\n" >&2\nexit 99\n')
        self.assertEqual(self.cli('main.c').returncode, 0)

    def test_fallback_to_gcc(self):
        (self.mock_bin / 'cc').unlink()
        self.write_mock('gcc', self.compiler_body)
        self.assertEqual(self.cli('main.c').returncode, 0)
        self.assertEqual(self.arguments(), FLAGS + [b'main.c'])

    def test_missing_compiler(self):
        (self.mock_bin / 'cc').unlink()
        result = self.cli()
        self.assertEqual(result.returncode, 127)
        self.assertEqual(result.stdout, CLEAR)
        self.assertIn(b'neither cc nor gcc was found in PATH', result.stderr)

    def test_install_default_and_idempotence(self):
        target = self.home / '.local/bin' / PROGRAM
        self.assertEqual(self.installer().returncode, 0)
        self.assertEqual(target.read_bytes(), (ROOT / 'bin' / PROGRAM).read_bytes())
        self.assertTrue(os.access(target, os.X_OK))
        before = target.stat().st_mtime_ns
        result = self.installer()
        self.assertEqual(result.returncode, 0)
        self.assertIn(b'Already installed', result.stdout)
        self.assertEqual(before, target.stat().st_mtime_ns)
        self.assertFalse(list(target.parent.glob(PROGRAM + '.backup.*')))

    def test_custom_directory_with_spaces(self):
        target_dir = self.home / 'custom tools/bin'
        self.assertEqual(self.installer('--bin-dir', str(target_dir)).returncode, 0)
        self.assertTrue((target_dir / PROGRAM).is_file())
        self.assertFalse((self.home / '.local/bin' / PROGRAM).exists())
        self.assertEqual(self.installer('--bin-dir', str(target_dir), uninstall=True).returncode, 0)
        self.assertFalse((target_dir / PROGRAM).exists())

    def test_collision_and_force_backup(self):
        target = self.home / '.local/bin' / PROGRAM
        target.parent.mkdir(parents=True)
        target.write_text('existing command\n')
        self.assertNotEqual(self.installer().returncode, 0)
        self.assertEqual(target.read_text(), 'existing command\n')
        self.assertEqual(self.installer('--force').returncode, 0)
        backups = list(target.parent.glob(PROGRAM + '.backup.*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'existing command\n')

    def test_symlink_is_never_replaced_or_removed(self):
        target = self.home / '.local/bin' / PROGRAM
        target.parent.mkdir(parents=True)
        target.symlink_to(ROOT / 'bin' / PROGRAM)
        self.assertNotEqual(self.installer('--force').returncode, 0)
        self.assertNotEqual(self.installer(uninstall=True).returncode, 0)
        self.assertTrue(target.is_symlink())

    def test_directory_is_never_replaced(self):
        target = self.home / '.local/bin' / PROGRAM
        target.mkdir(parents=True)
        self.assertNotEqual(self.installer('--force').returncode, 0)
        self.assertTrue(target.is_dir())

    def test_safe_uninstall(self):
        self.assertEqual(self.installer(uninstall=True).returncode, 0)
        self.assertEqual(self.installer().returncode, 0)
        self.assertEqual(self.installer(uninstall=True).returncode, 0)
        target = self.home / '.local/bin' / PROGRAM
        self.assertFalse(target.exists())
        self.assertEqual(self.installer().returncode, 0)
        target.write_text('modified command\n')
        self.assertNotEqual(self.installer(uninstall=True).returncode, 0)
        self.assertEqual(target.read_text(), 'modified command\n')

    def test_installer_help_and_bad_options(self):
        for uninstall in [False, True]:
            self.assertEqual(self.installer('--help', uninstall=uninstall).returncode, 0)
            for args in [('--bin-dir',), ('--bin-dir', ''), ('--unknown',)]:
                self.assertEqual(self.installer(*args, uninstall=uninstall).returncode, 64)


if __name__ == '__main__':
    unittest.main()
