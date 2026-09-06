#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
fail() { printf '[FEHLER] %s\n' "$*" >&2; exit 1; }

APP_NAME="CMDRHelper"
VERSION_FILE="cmdrhelper/version.py"
[[ -f "$VERSION_FILE" && ! -L "$VERSION_FILE" ]] || fail "Versionsdatei fehlt oder ist verlinkt: $VERSION_FILE"
VERSION="$(sed -nE 's/^__version__[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' "$VERSION_FILE")"
[[ "$VERSION" =~ ^[0-9]+(\.[0-9]+)*([.-][A-Za-z0-9]+)*$ ]] || fail "Ungültige Release-Version in $VERSION_FILE: $VERSION"

RELEASE="${APP_NAME}_v${VERSION}"
RELEASE_ROOT="release"
RELEASE_DIR="$RELEASE_ROOT/$RELEASE"
ARCHIVE="$RELEASE_ROOT/$RELEASE.zip"
required=(
    main.py requirements.txt LICENSE
    README.md README_DE.md README_FR.md README_IT.md README_NO.md README_SV.md
    README_FI.md README_PL.md README_NL.md README_ES.md README_TR.md README_EL.md
    install.sh start.sh install.bat install-windows.ps1 start.bat
)
# Check every prerequisite before creating, moving or removing release files.
for item in "${required[@]}"; do
    [[ -f "$item" && -r "$item" && ! -L "$item" ]] || fail "Pflichtdatei fehlt, ist unlesbar oder verlinkt: $item"
done
[[ -d cmdrhelper && ! -L cmdrhelper ]] || fail 'Programmverzeichnis fehlt oder ist verlinkt: cmdrhelper'
[[ ! -L docs ]] || fail 'Dokumentationsverzeichnis ist verlinkt: docs'
for tool in cp find rm mkdir mktemp mv zip unzip; do
    command -v "$tool" >/dev/null 2>&1 || fail "Benötigtes Werkzeug fehlt: $tool"
done
[[ ! -L "$RELEASE_ROOT" && ( ! -e "$RELEASE_ROOT" || -d "$RELEASE_ROOT" ) ]] || fail "Ungültiger Release-Ordner: $RELEASE_ROOT"
[[ ! -L "$RELEASE_DIR" && ( ! -e "$RELEASE_DIR" || -d "$RELEASE_DIR" ) ]] || fail "Ungültiges Release-Ziel: $RELEASE_DIR"
[[ ! -L "$ARCHIVE" && ( ! -e "$ARCHIVE" || -f "$ARCHIVE" ) ]] || fail "Ungültiges ZIP-Ziel: $ARCHIVE"

# These are authoring/backup files, not application assets.
excluded=(
    cmdrhelper/ui/backup_main_window.py
    cmdrhelper/ui/_main_window.py
    cmdrhelper/assets/readme/text/de.py
    cmdrhelper/assets/readme/cmdrhelper_readme_master.png
    docs/planet-navigation-i18n-audit.md
)

mkdir -p -- "$RELEASE_ROOT"
staging="$(mktemp -d "$RELEASE_ROOT/.cmdrhelper-stage.XXXXXX")"
payload="$staging/$RELEASE"
old_dir=0 old_zip=0 new_dir=0 new_zip=0 committed=0
cleanup() {
    local status=$? rollback_failed=0
    trap - EXIT
    if (( ! committed )); then
        if (( new_zip )); then rm -f -- "$ARCHIVE" || rollback_failed=1; fi
        if (( new_dir )); then rm -rf -- "$RELEASE_DIR" || rollback_failed=1; fi
        if (( old_dir )); then mv -- "$staging/previous-directory" "$RELEASE_DIR" || rollback_failed=1; fi
        if (( old_zip )); then mv -- "$staging/previous.zip" "$ARCHIVE" || rollback_failed=1; fi
    fi
    if (( rollback_failed )); then
        printf '[FEHLER] Wiederherstellung fehlgeschlagen; Sicherungen bleiben in %s\n' "$staging" >&2
        exit 1
    fi
    if ! rm -rf -- "$staging"; then
        printf '[FEHLER] Temporärer Release-Ordner konnte nicht entfernt werden: %s\n' "$staging" >&2
        status=1
    fi
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

printf 'Erstelle lokalen Probe-Release %s\n' "$RELEASE"
mkdir -p -- "$payload"
printf '[1/5] Pflichtdateien kopieren ...\n'
for item in "${required[@]}"; do cp -- "$item" "$payload/"; done
for item in CHANGELOG.md CONTRIBUTING.md; do
    if [[ -f "$item" ]]; then cp -a -- "$item" "$payload/"; fi
done

printf '[2/5] Programm, Sprachkataloge und Assets rekursiv kopieren ...\n'
cp -a -- cmdrhelper "$payload/cmdrhelper"
if [[ -d docs ]]; then cp -a -- docs "$payload/docs"; fi
# Never copy the developer's data directory, including its .gitkeep contents.
mkdir -p -- "$payload/data"
: > "$payload/data/.gitkeep"

printf '[3/5] Bekannte Entwicklungsdateien und Python-Caches entfernen ...\n'
for item in "${excluded[@]}"; do
    rm -f -- "$payload/$item" || fail "Ausschluss konnte nicht entfernt werden: $item"
done
# These disposable compiler outputs are expected in a working checkout.
# Other unexpected development/user data is rejected below, not silently erased.
find "$payload" -depth -type d -name __pycache__ -exec rm -rf -- {} + \
    || fail 'Python-Cacheverzeichnisse konnten nicht bereinigt werden.'
find "$payload" -type f \( -iname '*.pyc' -o -iname '*.pyo' \) -delete \
    || fail 'Python-Cachedateien konnten nicht bereinigt werden.'

printf '[4/5] Release-Inhalt prüfen ...\n'
for item in "${required[@]}"; do
    [[ -f "$payload/$item" && ! -L "$payload/$item" ]] || fail "Pflichtdatei fehlt im Release: $item"
done
for item in "${excluded[@]}"; do
    [[ ! -e "$payload/$item" && ! -L "$payload/$item" ]] || fail "Ausgeschlossene Datei im Release: $item"
done
# Save find's result explicitly: traversal errors must not disappear in a pipe
# or process substitution. Also reject symlinks and special files before zip.
find "$payload" \( \
    \( ! -type f ! -type d \) -o \
    -iname '*.db' -o -iname '*.db-*' -o -iname '*.sqlite' -o -iname '*.sqlite-*' -o \
    -iname '*.sqlite3' -o -iname '*.sqlite3-*' -o \
    -iname '*.log' -o -iname '*.log.*' -o -iname '*.pyc' -o -iname '*.pyo' -o \
    -iname '*.tmp' -o -iname '*.temp' -o -iname '*.bak' -o -iname '*.orig' -o -iname '*.rej' -o \
    -iname '*.swp' -o -iname '*.swo' -o -name '*~' -o \
    -iname '*.ini' -o -iname '*.cfg' -o -iname '*.conf' -o -iname '*.config' -o -iname '*.json' -o \
    -iname '*.yaml' -o -iname '*.yml' -o -iname '*.toml' -o -iname '.env' -o -iname '.env.*' -o \
    -iname '*.bmp' -o -iname 'Screenshot*.png' -o -iname 'Screenshot*.jpg' -o \
    -iname 'Screenshot*.jpeg' -o -iname 'Screenshot*.webp' -o \
    -iname 'HighResScreenshot*.png' -o -iname 'HighResScreenshot*.jpg' -o \
    -iname 'HighResScreenshot*.jpeg' -o -iname 'HighResScreenshot*.webp' -o \
    -iname '????-??-??_??-??-??_*' -o -iname .git -o -iname AGENTS.md -o \
    \( -type d \( -iname __pycache__ -o -iname logs -o -iname log -o \
        -iname .git -o -iname .github -o -iname .venv -o -iname venv -o \
        -iname tests -o -iname test -o -iname .codex -o -iname .agents -o \
        -iname .vscode -o -iname .idea -o -iname .pytest_cache -o -iname .mypy_cache -o \
        -iname .ruff_cache -o -iname .tox -o -iname .cache -o -iname build -o -iname dist -o \
        -iname release -o -iname backup -o -iname backups -o -iname tmp -o -iname temp -o \
        -iname favorites -o -iname config -o -iname .config -o -iname settings -o \
        -iname screenshots -o -iname data \) \) \
\) ! -path "$payload/data" -print0 > "$staging/unexpected"
unexpected=0
while IFS= read -r -d '' item; do
    printf '[FEHLER] Unerwarteter Release-Inhalt: %s\n' "${item#"$payload/"}" >&2
    if [[ -d "$item" && ! -L "$item" ]]; then
        find "$item" -mindepth 1 -print >&2
    fi
    unexpected=1
done < "$staging/unexpected"
(( unexpected == 0 )) || exit 1
# Only the freshly created empty marker may exist in data/.
find "$payload/data" -mindepth 1 ! -path "$payload/data/.gitkeep" -print0 > "$staging/data-unexpected"
while IFS= read -r -d '' item; do
    printf '[FEHLER] Unerwartete Benutzerdaten: %s\n' "${item#"$payload/"}" >&2
    unexpected=1
done < "$staging/data-unexpected"
[[ ! -s "$payload/data/.gitkeep" ]] || fail 'Unerwarteter Inhalt: data/.gitkeep'
(( unexpected == 0 )) || exit 1

printf '[5/5] ZIP erstellen und Integrität prüfen ...\n'
(cd "$staging" && zip -qr "$RELEASE.zip" "$RELEASE" && zip -T "$RELEASE.zip")
# Replace only this version, after all checks succeed. Keep rollback copies
# until both the directory and its ZIP have been installed successfully.
if [[ -e "$RELEASE_DIR" ]]; then mv -- "$RELEASE_DIR" "$staging/previous-directory"; old_dir=1; fi
if [[ -e "$ARCHIVE" ]]; then mv -- "$ARCHIVE" "$staging/previous.zip"; old_zip=1; fi
mv -- "$payload" "$RELEASE_DIR"; new_dir=1
mv -- "$staging/$RELEASE.zip" "$ARCHIVE"; new_zip=1
committed=1
printf 'Release erfolgreich erstellt und geprüft: %s\n' "$ARCHIVE"
