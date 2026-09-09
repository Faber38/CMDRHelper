#!/usr/bin/env python3
"""Opt-in local update fixture runner. Never shipped inside the application.

Uses the normal GUI/download/helper/install/restart flow. Only the release
metadata source is replaced for this one test process; no product switch or
persistent setting is installed. Run exclusively in a disposable installation.
"""
from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path
import shutil
import sys
import zipfile


def archive_version(archive: Path) -> str:
    with zipfile.ZipFile(archive) as source:
        names = [n for n in source.namelist() if n.endswith('/cmdrhelper/version.py')
                 or n == 'cmdrhelper/version.py']
        if len(names) != 1:
            raise ValueError('ZIP muss genau eine cmdrhelper/version.py enthalten.')
        tree = ast.parse(source.read(names[0]).decode('utf-8'))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == '__version__' for t in node.targets
            ):
                version = ast.literal_eval(node.value)
                if isinstance(version, str):
                    return version
    raise ValueError('Versionsangabe fehlt.')


def prepare(source_zip: Path, output: Path, next_version: str) -> None:
    """Derive a next-version fixture from the normal local release ZIP."""
    if not next_version or not all(part.isdigit() for part in next_version.split('.')):
        raise ValueError('Testversion muss numerisch sein, z.B. 3.2.1.')
    source_version = archive_version(source_zip)
    def numbers(value):
        parts = [int(p) for p in value.split('.')]
        return parts + [0] * (10 - len(parts))
    if numbers(next_version) <= numbers(source_version):
        raise ValueError('Testversion muss neuer als die Paketversion sein.')
    output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source_zip, output / source_zip.name)
    target = output / f'CMDRHelper_v{next_version}.zip'
    with zipfile.ZipFile(source_zip) as source, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as dest:
        for entry in source.infolist():
            content = source.read(entry)
            if entry.filename.endswith('/cmdrhelper/version.py') or entry.filename == 'cmdrhelper/version.py':
                content = f'__version__ = "{next_version}"\n'.encode()
            dest.writestr(entry, content)
    shutil.copy2(Path(__file__), output / Path(__file__).name)
    guide = Path(__file__).resolve().parents[1] / 'docs/windows-update-test.md'
    if guide.is_file():
        shutil.copy2(guide, output / 'Windows-Updatetest.md')
    print(f'Lokale Testpakete: {output.resolve()} ({source_version} -> {next_version})')


def run(install: Path, archive: Path) -> None:
    install, archive = install.resolve(), archive.resolve()
    if not (install / '.cmdrhelper-update-test').is_file():
        raise ValueError('Nur Testinstallationen: zuerst .cmdrhelper-update-test im Testordner anlegen.')
    if not (install / 'main.py').is_file():
        raise ValueError('main.py fehlt im Testordner.')
    version = archive_version(archive)
    os.chdir(install)
    sys.path.insert(0, str(install))
    from cmdrhelper import update
    from cmdrhelper.version import __version__
    info = {
        'ok': True, 'version': version, 'tag': f'v{version}',
        'name': f'Lokaler Windows-Updatetest {version}', 'html_url': '',
        'release_notes': 'Lokales Testpaket; kein öffentliches Release.',
        'asset_name': archive.name, 'asset_url': archive.as_uri(),
        'asset_size': archive.stat().st_size,
        'newer': update.is_newer_version(version, __version__),
    }
    if not info['newer']:
        raise ValueError(f'Testziel {version} ist nicht neuer als {__version__}.')
    update.check_latest_release = lambda *args, **kwargs: dict(info)
    print(f'TEST: {install}: {__version__} -> {version}; Quelle: {archive}', flush=True)
    # The updater's restart uses the normal main.py; this override ends here.
    sys.argv = [str(install / 'main.py')]
    from cmdrhelper.app import run as run_app
    run_app()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    build = commands.add_parser('prepare')
    build.add_argument('--source-zip', type=Path, required=True)
    build.add_argument('--output', type=Path, required=True)
    build.add_argument('--next-version', default='3.2.1')
    launch = commands.add_parser('run')
    launch.add_argument('--install-dir', type=Path, required=True)
    launch.add_argument('--zip', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.source_zip, args.output, args.next_version)
    else:
        run(args.install_dir, args.zip)


if __name__ == '__main__':
    main()
