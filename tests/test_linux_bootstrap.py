from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmdrhelper import update


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "posix", "Linux/Unix-Shelltest")
class LinuxScriptTests(unittest.TestCase):
    def _installation(self, parent: Path) -> Path:
        install = parent / "CMDR Helper Ü Test"
        (install / "cmdrhelper").mkdir(parents=True)
        shutil.copy2(ROOT / "install.sh", install / "install.sh")
        shutil.copy2(ROOT / "start.sh", install / "start.sh")
        shutil.copy2(
            ROOT / "cmdrhelper" / "python_support.py",
            install / "cmdrhelper" / "python_support.py",
        )
        (install / "cmdrhelper" / "version.py").write_text('__version__ = "9.9"\n')
        (install / "requirements.txt").write_text("")
        (install / "main.py").write_text("# test\n")
        (install / "data").mkdir()
        (install / "data" / "journal.keep").write_text("personal")
        return install

    def _fake_python(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            """#!/usr/bin/env bash
if [[ "$1" == "-m" && "$2" == "venv" ]]; then
  mkdir -p "$3/bin"; cp "$0" "$3/bin/python"; chmod +x "$3/bin/python"; exit 0
fi
if [[ "$1" == "-m" && "$2" == "pip" ]]; then exit 0; fi
if [[ "$1" == "-c" ]]; then echo "$0"; echo "Python 3.12 fake"; exit 0; fi
if [[ "$1" == *python_support.py ]]; then exit 0; fi
if [[ "$1" == *main.py ]]; then exit "${FAKE_APP_EXIT:-0}"; fi
exit 0
""",
            encoding="utf-8",
        )
        path.chmod(0o755)

    def test_symlinked_start_resolves_real_root_and_preserves_exitcode(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            install = self._installation(base)
            self._fake_python(install / "venv" / "bin" / "python")
            link_dir = base / "launcher"
            link_dir.mkdir()
            link = link_dir / "cmdrhelper-start"
            link.symlink_to(install / "start.sh")
            result = subprocess.run(
                [str(link)], cwd=base, text=True, capture_output=True,
                env={**os.environ, "FAKE_APP_EXIT": "37"},
            )
            self.assertEqual(result.returncode, 37)
            self.assertIn(str(install), result.stdout + result.stderr)

    def test_symlinked_install_resolves_real_root(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            install = self._installation(base)
            fake_bin = base / "fake-bin"
            self._fake_python(fake_bin / "python3.13")
            launcher = base / "launcher"
            launcher.mkdir()
            link = launcher / "install-cmdrhelper"
            link.symlink_to(install / "install.sh")
            result = subprocess.run(
                [str(link)], cwd=base, text=True, capture_output=True,
                env={**os.environ, "PATH": f"{fake_bin}:/usr/bin:/bin"},
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue((install / "venv" / "bin" / "python").exists())
            self.assertFalse((launcher / "venv").exists())

    def test_missing_python_has_explicit_error(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            install = self._installation(base)
            tool_bin = base / "tools"
            tool_bin.mkdir()
            for name in ("dirname", "basename", "readlink"):
                (tool_bin / name).symlink_to(Path("/usr/bin") / name)
            result = subprocess.run(
                ["/bin/bash", str(install / "install.sh")],
                text=True, capture_output=True,
                env={**os.environ, "PATH": str(tool_bin)},
            )
            self.assertEqual(result.returncode, 10)
            self.assertIn("Keine unterstützte Python-Version", result.stderr)

    def test_repair_marker_blocks_and_names_install_sh(self):
        with tempfile.TemporaryDirectory() as directory:
            install = self._installation(Path(directory))
            self._fake_python(install / "venv" / "bin" / "python")
            marker = install / "backup" / "update_repair_required.json"
            marker.parent.mkdir()
            marker.write_text("{}")
            result = subprocess.run(
                [str(install / "start.sh")], text=True, capture_output=True
            )
            self.assertEqual(result.returncode, 20)
            self.assertIn("install.sh", result.stderr)

    def test_venv_symlink_is_never_used_or_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            install = self._installation(base)
            external = base / "foreign venv"
            self._fake_python(external / "bin" / "python")
            sentinel = external / "keep"
            sentinel.write_text("foreign")
            (install / "venv").symlink_to(external, target_is_directory=True)
            start = subprocess.run([str(install / "start.sh")], capture_output=True)
            self.assertEqual(start.returncode, 4)
            fake_bin = base / "fake-bin"
            self._fake_python(fake_bin / "python3.13")
            install_result = subprocess.run(
                [str(install / "install.sh")], capture_output=True,
                env={**os.environ, "PATH": f"{fake_bin}:/usr/bin:/bin"},
            )
            self.assertEqual(install_result.returncode, 12)
            self.assertTrue(sentinel.exists())
            self.assertTrue((install / "venv").is_symlink())

    def test_defective_real_venv_is_rebuilt_idempotently(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            install = self._installation(base)
            (install / "venv").mkdir()
            (install / "venv" / "broken").write_text("broken")
            fake_bin = base / "fake-bin"
            self._fake_python(fake_bin / "python3.13")
            environment = {**os.environ, "PATH": f"{fake_bin}:/usr/bin:/bin"}
            first = subprocess.run([str(install / "install.sh")], env=environment)
            second = subprocess.run([str(install / "install.sh")], env=environment)
            self.assertEqual((first.returncode, second.returncode), (0, 0))
            self.assertFalse((install / "venv" / "broken").exists())
            self.assertEqual((install / "data" / "journal.keep").read_text(), "personal")


@unittest.skipUnless(os.name == "posix", "Linux/Unix-Pfadtest")
class LinuxUpdaterInterpreterTests(unittest.TestCase):
    def test_two_venvs_with_same_system_python_remain_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            install = base / "app"
            expected = install / "venv" / "bin" / "python"
            foreign = base / "other" / "venv" / "bin" / "python"
            expected.parent.mkdir(parents=True)
            foreign.parent.mkdir(parents=True)
            expected.symlink_to(Path(os.sys.executable))
            foreign.symlink_to(Path(os.sys.executable))
            with self.assertRaisesRegex(RuntimeError, "lokalen venv"):
                update._require_local_venv_interpreter(install, foreign)

    def test_internal_python_symlink_is_allowed_with_local_lexical_path(self):
        with tempfile.TemporaryDirectory() as directory:
            install = Path(directory) / "app"
            expected = install / "venv" / "bin" / "python"
            expected.parent.mkdir(parents=True)
            expected.symlink_to(Path(os.sys.executable))
            self.assertEqual(
                update._require_local_venv_interpreter(install, expected), expected
            )

    def test_rollback_cleanup_unlinks_new_symlink_without_following_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install = root / "app"
            (install / "cmdrhelper").mkdir(parents=True)
            previous = update._managed_file_manifest(install)
            external = root / "external"
            external.mkdir()
            sentinel = external / "journal.log"
            sentinel.write_text("keep")
            link = install / "cmdrhelper" / "new-link"
            link.symlink_to(external, target_is_directory=True)
            update._remove_new_managed_files(install, previous)
            self.assertFalse(link.exists())
            self.assertFalse(link.is_symlink())
            self.assertEqual(sentinel.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
