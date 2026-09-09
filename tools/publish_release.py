#!/usr/bin/env python3
"""Publish a committed CMDRHelper snapshot. Invoked only by github.sh.

All GitHub mutations happen after a validated local build. Existing tags/assets
are never overwritten. A retry rebuilds the same commit deterministically.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile

REPO = "Faber38/CMDRHelper"
REMOTE = f"https://github.com/{REPO}.git"


class ReleaseError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ReleaseError(message)


def literal(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ReleaseError(f"{name} fehlt in {path.name}.")


def version_at(root):
    version = literal(root / "cmdrhelper/version.py", "__version__")
    require(isinstance(version, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version),
            "Ungültige stabile Release-Version in cmdrhelper/version.py.")
    return version


def release_notes(root, version):
    keys = literal(root / "cmdrhelper/release_summaries.py", "RELEASE_SUMMARIES").get(version, ())[:6]
    translations = {}
    for language in "de en fr it no sv fi pl nl es tr el".split():
        table = literal(root / f"cmdrhelper/i18n/{language}.py", "TRANSLATIONS")
        translations[language] = [table[key] for key in keys]
    heading = f"## Neu in Version {version}\n\n"
    if not keys:
        return heading + "Weitere Verbesserungen und Fehlerkorrekturen.\n"
    return (heading + "\n".join(f"- {item}" for item in translations["de"])
            + "\n\n<!-- cmdrhelper-update-summary\n"
            + json.dumps(translations, ensure_ascii=False) + "\n-->\n")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_zip(archive, directory):
    require(archive.is_file() and not archive.is_symlink() and archive.stat().st_size > 0,
            "Das frisch gebaute Release-ZIP fehlt oder ist leer.")
    require(directory.is_dir() and not directory.is_symlink(), "Releaseordner fehlt.")
    files = {f.relative_to(directory).as_posix(): f for f in directory.rglob("*") if f.is_file()}
    require(files, "Releaseordner ist leer.")
    with zipfile.ZipFile(archive) as handle:
        require(handle.testzip() is None, "ZIP-Integritätsprüfung fehlgeschlagen.")
        names = [info.filename for info in handle.infolist()]
        require(len(names) == len(set(names)), "Doppelte ZIP-Einträge.")
        expected = {directory.name + "/" + name for name in files}
        require({info.filename for info in handle.infolist() if not info.is_dir()} == expected,
                "ZIP-Inhalt stimmt nicht mit dem Releaseordner überein.")
        for name, path in files.items():
            require(not path.is_symlink() and handle.read(directory.name + "/" + name) == path.read_bytes(),
                    "ZIP und Releaseordner enthalten unterschiedliche Dateien.")


def canonical_zip(archive, timestamp):
    """Normalize incidental build times for byte-identical retry comparisons."""
    stamp = time.gmtime(max(timestamp, 315532800))[:6]
    replacement = archive.with_suffix(".normalized.zip")
    with zipfile.ZipFile(archive) as source, zipfile.ZipFile(replacement, "w") as target:
        for original in sorted(source.infolist(), key=lambda item: item.filename):
            info = zipfile.ZipInfo(original.filename, stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            mode = 0o40755 if original.is_dir() else (0o100755 if (original.external_attr >> 16) & 0o111 else 0o100644)
            info.external_attr = (mode << 16) | (0x10 if original.is_dir() else 0)
            target.writestr(info, source.read(original), compresslevel=9)
    replacement.replace(archive)


class Publisher:
    def __init__(self, root):
        self.root = Path(root)
        self.phase = "Vorprüfungen"
        self.completed = []

    def run(self, args, *, cwd=None, allowed=(0,)):
        # Never echo raw credential/helper/API errors or command arguments.
        environment = dict(os.environ, GH_HOST="github.com")
        result = subprocess.run(args, cwd=cwd or self.root, env=environment, capture_output=True, text=True)
        require(result.returncode in allowed,
                f"{args[0]}: Schritt fehlgeschlagen (Exit-Code {result.returncode}). "
                "Verbindung, Berechtigungen und Repository-Zustand prüfen; danach erneut starten.")
        return result

    def git(self, *args, **kwargs):
        return self.run(["git", *args], **kwargs).stdout.strip()

    def api(self, endpoint):
        result = self.run(["gh", "api", "--hostname", "github.com", "--method", "GET", f"repos/{REPO}/{endpoint}"], allowed=(0, 1))
        try:
            data = json.loads(result.stdout)
        except ValueError:
            raise ReleaseError("GitHub-Antwort nicht lesbar; Verbindung und Anmeldung prüfen.") from None
        if result.returncode:
            raise ReleaseError("GitHub-Abfrage fehlgeschlagen; Verbindung und Berechtigungen prüfen.")
        return data

    def state(self, commit):
        local = self.run(["git", "show-ref", "--verify", "--quiet", f"refs/tags/{self.tag}"], allowed=(0, 1)).returncode == 0
        if local:
            require(self.git("rev-parse", f"refs/tags/{self.tag}^{{commit}}") == commit,
                    f"Lokaler Tag {self.tag} zeigt auf einen anderen Commit. Keine Tags überschrieben.")
        refs = self.git("ls-remote", "--tags", "origin", f"refs/tags/{self.tag}", f"refs/tags/{self.tag}^{{}}")
        values = dict(line.split()[::-1] for line in refs.splitlines())
        remote = values.get(f"refs/tags/{self.tag}^{{}}", values.get(f"refs/tags/{self.tag}"))
        require(remote is None or remote == commit,
                f"GitHub-Tag {self.tag} zeigt auf einen anderen Commit. Keine Tags überschrieben.")
        # The tag endpoint only promises published releases. Listing with push
        # access also finds drafts left by a failed asset upload.
        matches = []
        page = 1
        while True:
            releases = self.api(f"releases?per_page=100&page={page}")
            require(isinstance(releases, list), "GitHub-Releaseliste nicht lesbar.")
            matches.extend(item for item in releases if item.get("tag_name") == self.tag)
            if len(releases) < 100:
                break
            page += 1
        require(len(matches) <= 1, "Mehrere Releases für denselben Tag gefunden.")
        release = matches[0] if matches else None
        if release is not None:
            require(remote == commit and release.get("tag_name") == self.tag,
                    "Vorhandenes Release gehört nicht zum erwarteten Tag/Commit.")
            require(not release.get("prerelease") and release.get("name") == self.title,
                    "Vorhandenes Release hat einen widersprüchlichen Titel oder ist ein Prerelease.")
        return local, bool(remote), release

    def clean(self):
        require(not self.git("status", "--porcelain", "--untracked-files=all"),
                "Arbeitsverzeichnis ist nicht sauber. Änderungen prüfen und erneut starten.")

    def unchanged(self):
        require(self.git("rev-parse", "HEAD") == self.commit, "HEAD wurde während des Ablaufs verändert.")
        self.clean()

    def preflight(self):
        require(sys.version_info >= (3, 10), "Python 3.10 oder neuer erforderlich.")
        for tool in ("git", "gh", "bash", "cp", "find", "rm", "mkdir", "mktemp", "mv", "zip", "unzip"):
            require(shutil.which(tool), f"Benötigtes Werkzeug fehlt: {tool}")
        require(self.git("rev-parse", "--show-toplevel") == str(self.root.resolve()), "Kein Projekt-Repository.")
        require(self.git("branch", "--show-current") == "main", "Veröffentlichung nur auf Branch main erlaubt.")
        for option in ((), ("--push",)):
            urls = self.git("remote", "get-url", *option, "--all", "origin").splitlines()
            require(len(urls) == 1 and urls[0] in (REMOTE, REMOTE.removesuffix(".git")),
                    f"origin muss per HTTPS auf {REPO} zeigen (Fetch und Push).")
        self.run(["gh", "auth", "status", "--hostname", "github.com"])
        repo = json.loads(self.run(["gh", "repo", "view", REPO, "--json", "nameWithOwner,viewerPermission,isArchived"]).stdout)
        require(repo.get("nameWithOwner") == REPO and not repo.get("isArchived")
                and repo.get("viewerPermission") in ("ADMIN", "MAINTAIN", "WRITE"),
                "Zielrepository oder Schreibberechtigung stimmt nicht.")
        self.version = version_at(self.root)
        self.tag = "v" + self.version
        self.title = "CMDRHelper " + self.tag
        self.name = f"CMDRHelper_{self.tag}"
        self.commit = self.git("rev-parse", "HEAD")
        # Never include even already-staged historical release changes in a commit.
        require(not self.git("diff", "HEAD", "--name-only", "--", "release"),
                "Versionierte Releaseartefakte wurden geändert/vorgemerkt. Zuerst separat klären.")
        local, remote, release = self.state(self.commit)
        dirty = self.git("status", "--porcelain", "--untracked-files=all")
        require(not dirty or not (local or remote or release),
                "Diese Version ist bereits getaggt/veröffentlicht, aber der Quellstand ist verändert.")
        for path in (self.root / "release", self.root / f"release/{self.name}", self.root / f"release/{self.name}.zip"):
            require(not path.is_symlink(), "Release-Ziel darf kein symbolischer Link sein.")
        require(not self.git("ls-files", "--", f"release/{self.name}", f"release/{self.name}.zip"),
                "Das Zielrelease ist bereits versioniert; es wird nicht überschrieben.")
        return bool(dirty)

    def snapshot(self, destination):
        archive = destination.parent / "source.tar"
        # Omit historical release trees, but include all committed source inputs.
        roots = self.git("ls-tree", "--name-only", self.commit).splitlines()
        roots = [name for name in roots if name != "release"]
        self.git("archive", "--format=tar", f"--output={archive}", self.commit, "--", *roots)
        with tarfile.open(archive) as source:
            for member in source:
                path = PurePosixPath(member.name)
                require(not path.is_absolute() and ".." not in path.parts and (member.isfile() or member.isdir()),
                        "Commit enthält einen nicht unterstützten Dateityp oder Pfad.")
                target = destination.joinpath(*path.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with source.extractfile(member) as handle, target.open("wb") as output:
                        shutil.copyfileobj(handle, output)
                    target.chmod(member.mode & 0o777)

    def build(self, temp):
        snapshot = temp / "source"
        snapshot.mkdir()
        self.snapshot(snapshot)
        require(version_at(snapshot) == self.version, "Version wurde während des Ablaufs verändert.")
        self.run(["bash", "create_release.sh"], cwd=snapshot)
        directory = snapshot / "release" / self.name
        archive = directory.parent / (self.name + ".zip")
        validate_zip(archive, directory)
        timestamp = int(self.git("show", "-s", "--format=%ct", self.commit))
        canonical_zip(archive, timestamp)
        validate_zip(archive, directory)
        notes = temp / "release-notes.md"
        notes.write_text(release_notes(snapshot, self.version), encoding="utf-8")
        self.unchanged()
        target = self.root / "release"
        target.mkdir(exist_ok=True)
        # Only untracked, version-specific generated outputs may be replaced.
        if (target / self.name).exists():
            shutil.rmtree(target / self.name)
        shutil.copytree(directory, target / self.name)
        shutil.copyfile(archive, target / archive.name)
        self.unchanged()
        self.archive = target / archive.name
        validate_zip(self.archive, target / self.name)
        self.digest = sha256(self.archive)
        require(self.digest == sha256(archive), "Lokales ZIP stimmt nicht mit dem validierten Build überein.")
        self.size = self.archive.stat().st_size
        return notes

    def verify_asset(self, release, temp):
        assets = [a for a in release.get("assets", []) if a.get("name") == self.archive.name]
        require(len(assets) <= 1, "Mehrere gleichnamige Release-Assets gefunden.")
        if not assets:
            return False
        asset = assets[0]
        require(asset.get("state") == "uploaded" and asset.get("size") == self.size,
                "Vorhandenes ZIP-Asset ist unvollständig oder hat eine andere Größe. Kein Überschreiben.")
        if asset.get("digest"):
            require(asset["digest"] == "sha256:" + self.digest,
                    "Vorhandenes ZIP-Asset hat anderen Inhalt. Kein Überschreiben.")
        else:
            download = temp / "remote-asset"
            download.mkdir(exist_ok=True)
            self.run(["gh", "release", "download", self.tag, "--repo", REPO,
                      "--pattern", self.archive.name, "--dir", str(download), "--clobber"])
            require(sha256(download / self.archive.name) == self.digest,
                    "Heruntergeladenes Release-Asset stimmt nicht mit dem Build überein.")
        return True

    def execute(self):
        dirty = self.preflight()
        print(f"Repository: {REPO}\nBranch: main\nVersion: {self.version}\nCommit: {self.commit}")
        if dirty:
            print("Zu prüfende lokale Änderungen:\n" + self.git("status", "--short"))
        answer = input(f"{self.title} für {REPO} bauen und vollständig veröffentlichen? [j/N]: ")
        if answer.lower() not in ("j", "ja"):
            print("Abgebrochen; keine Veröffentlichung gestartet.")
            return
        self.phase = "Finaler Commit"
        if dirty:
            message = input("Commit-Nachricht: ").strip()
            require(message, "Keine Commit-Nachricht eingegeben.")
            require(not self.git("diff", "HEAD", "--name-only", "--", "release"),
                    "Versionierte Releaseartefakte wurden inzwischen geändert. Abbruch vor Commit.")
            self.git("add", "-A", "--", ".", ":(exclude)release")
            self.git("commit", "-m", message)
        self.commit = self.git("rev-parse", "HEAD")
        self.clean()
        self.state(self.commit)
        self.completed.append("Finaler Commit lokal geprüft")
        self.phase = "Lokaler Releasebau und Validierung"
        with tempfile.TemporaryDirectory(prefix="cmdrhelper-publish-") as temporary:
            temp = Path(temporary)
            notes = self.build(temp)
            self.completed.append("Release lokal gebaut und validiert")
            local, remote, release = self.state(self.commit)
            if release:
                self.verify_asset(release, temp)
            self.unchanged()
            self.phase = "Commit-Push"
            self.git("-c", "push.followTags=false", "push", "origin", f"{self.commit}:refs/heads/main")
            self.completed.append("Commit auf GitHub")
            self.phase = "Tag-Erstellung und Tag-Push"
            local, remote, release = self.state(self.commit)
            if not local:
                if remote:
                    self.git("fetch", "--no-tags", "origin", f"refs/tags/{self.tag}:refs/tags/{self.tag}")
                else:
                    self.git("tag", "-a", self.tag, self.commit, "-m", self.title)
            if not remote:
                self.git("push", "origin", f"refs/tags/{self.tag}:refs/tags/{self.tag}")
            self.completed.append("Tag lokal und auf GitHub")
            self.phase = "GitHub-Release und ZIP-Upload"
            _, remote, release = self.state(self.commit)
            require(remote, "Remote-Tag fehlt nach Tag-Push.")
            self.unchanged()
            require(sha256(self.archive) == self.digest, "Lokales ZIP wurde nach dem Build verändert.")
            if release is None:
                self.run(["gh", "release", "create", self.tag, str(self.archive), "--repo", REPO,
                          "--verify-tag", "--title", self.title, "--notes-file", str(notes)])
            elif not self.verify_asset(release, temp):
                self.run(["gh", "release", "upload", self.tag, str(self.archive), "--repo", REPO])
            self.phase = "Remote-Abschlussprüfung"
            _, _, release = self.state(self.commit)
            require(release is not None and self.verify_asset(release, temp),
                    "Release oder erwartetes ZIP-Asset fehlt nach Veröffentlichung.")
            if release.get("draft"):
                self.run(["gh", "release", "edit", self.tag, "--repo", REPO,
                          "--notes-file", str(notes), "--draft=false"])
                _, _, release = self.state(self.commit)
                require(release is not None and not release.get("draft") and self.verify_asset(release, temp),
                        "Release ist noch nicht öffentlich verfügbar.")
            self.completed.append("GitHub-Release und ZIP geprüft")
        print(f"Release {self.tag} erfolgreich veröffentlicht.\nCommit: {self.commit}\nTag: {self.tag}\n"
              f"Release: https://github.com/{REPO}/releases/tag/{self.tag}\nZIP: {self.archive}")


def main():
    publisher = Publisher(Path(__file__).resolve().parents[1])
    try:
        publisher.execute()
    except (ReleaseError, OSError, ValueError, KeyError, SyntaxError, zipfile.BadZipFile, EOFError, KeyboardInterrupt) as exc:
        # Operational errors from git/gh never expose raw stderr, tokens or URLs.
        detail = str(exc) if isinstance(exc, ReleaseError) else "Lokaler Vorgang oder Eingabe fehlgeschlagen."
        print(f"[FEHLER] Abbruch bei: {publisher.phase}. {detail}", file=sys.stderr)
        print("Bereits erfolgreich: " + ("; ".join(publisher.completed) or "keine Veröffentlichungsschritte"), file=sys.stderr)
        print("Vorhandene Tags und Assets wurden nicht überschrieben. Zustand prüfen und erneut starten.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
