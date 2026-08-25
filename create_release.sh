#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="CMDRHelper"

# ============================================================
# RELEASE-VERSION
# Zentrale Versionsnummer: cmdrhelper/version.py
# Für ein neues Release nur dort __version__ ändern.
# ============================================================
VERSION_FILE="cmdrhelper/version.py"

if [[ ! -f "${VERSION_FILE}" ]]; then
    echo "[FEHLER] ${VERSION_FILE} wurde nicht gefunden."
    exit 1
fi

VERSION="$(
    sed -nE 's/^__version__[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' \
        "${VERSION_FILE}" \
    | head -1
)"

if [[ -z "${VERSION}" ]]; then
    echo "[FEHLER] Versionsnummer konnte nicht aus ${VERSION_FILE} gelesen werden."
    exit 1
fi

RELEASE="${APP_NAME}_v${VERSION}"
RELEASE_ROOT="release"
RELEASE_DIR="${RELEASE_ROOT}/${RELEASE}"
ARCHIVE="${RELEASE_ROOT}/${RELEASE}.zip"

echo "========================================="
echo "       Erstelle CMDRHelper Release"
echo "========================================="
echo
echo "Version : ${VERSION}"
echo "Release : ${RELEASE}"
echo

# ------------------------------------------------------------
# Pflichtdateien prüfen
# ------------------------------------------------------------
required=(
    "main.py"
    "requirements.txt"
    "cmdrhelper"
    "README.md"
    "README_DE.md"
)

for item in "${required[@]}"; do
    if [[ ! -e "${item}" ]]; then
        echo "[FEHLER] ${item} fehlt."
        exit 1
    fi
done

# ------------------------------------------------------------
# Altes Release entfernen
# ------------------------------------------------------------
rm -rf "${RELEASE_ROOT}"
mkdir -p "${RELEASE_DIR}"

echo "[1/5] Programmdateien kopieren ..."

cp "main.py" "${RELEASE_DIR}/"
cp "requirements.txt" "${RELEASE_DIR}/"
cp "README.md" "${RELEASE_DIR}/"
cp "README_DE.md" "${RELEASE_DIR}/"

# Start-/Installationsdateien
for item in \
    "install.bat" \
    "start.bat" \
    "install.sh" \
    "start.sh"
do
    if [[ -f "${item}" ]]; then
        cp "${item}" "${RELEASE_DIR}/"
    fi
done

# Optionale Dateien
for item in \
    "LICENSE" \
    "CHANGELOG.md" \
    "CONTRIBUTING.md"
do
    if [[ -f "${item}" ]]; then
        cp "${item}" "${RELEASE_DIR}/"
    fi
done

echo "[2/5] CMDRHelper-Code und Assets kopieren ..."

cp -a "cmdrhelper" "${RELEASE_DIR}/cmdrhelper"

if [[ -d "docs" ]]; then
    cp -a "docs" "${RELEASE_DIR}/docs"
fi

# Leeres Datenverzeichnis mitnehmen.
mkdir -p "${RELEASE_DIR}/data"
if [[ -f "data/.gitkeep" ]]; then
    cp "data/.gitkeep" "${RELEASE_DIR}/data/.gitkeep"
fi

echo "[3/5] Persönliche Daten und Entwicklungsreste entfernen ..."

# Persönliche Datenbank niemals veröffentlichen.
rm -f \
    "${RELEASE_DIR}/data/cmdrhelper.db" \
    "${RELEASE_DIR}/data/cmdrhelper.db-wal" \
    "${RELEASE_DIR}/data/cmdrhelper.db-shm" \
    "${RELEASE_DIR}/cmdrhelper.db"

# Python-/Editor-/Entwicklungsreste entfernen.
find "${RELEASE_DIR}" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "${RELEASE_DIR}" -type f \( \
    -name "*.pyc" -o \
    -name "*.pyo" -o \
    -name "*.log" -o \
    -name "*.bak" -o \
    -name "*.tmp" -o \
    -name "*~" \
\) -delete 2>/dev/null || true

find "${RELEASE_DIR}" -type d \( \
    -name ".git" -o \
    -name ".github" -o \
    -name ".vscode" -o \
    -name ".idea" -o \
    -name "venv" -o \
    -name ".venv" -o \
    -name "build" -o \
    -name "release" \
\) -prune -exec rm -rf {} + 2>/dev/null || true

# Sicherheitsprüfung: Es darf keine SQLite-DB im Release liegen.
if find "${RELEASE_DIR}" -type f \( \
    -name "*.db" -o \
    -name "*.db-wal" -o \
    -name "*.db-shm" \
\) | grep -q .; then
    echo
    echo "[FEHLER] Im Release wurde eine Datenbankdatei gefunden:"
    find "${RELEASE_DIR}" -type f \( \
        -name "*.db" -o \
        -name "*.db-wal" -o \
        -name "*.db-shm" \
    \)
    exit 1
fi

echo "[4/5] Release-Inhalt geprüft."
echo

echo "[5/5] ZIP erstellen ..."

if ! command -v zip >/dev/null 2>&1; then
    echo "[FEHLER] 'zip' ist nicht installiert."
    echo "Unter Pop!_OS/Ubuntu: sudo apt install zip"
    exit 1
fi

(
    cd "${RELEASE_ROOT}"
    zip -qr "${RELEASE}.zip" "${RELEASE}"
)

echo
echo "========================================="
echo "Release erfolgreich erstellt!"
echo
echo "Version : ${VERSION}"
echo "Archiv  : ${ARCHIVE}"
echo "========================================="
echo
echo "Nicht enthalten:"
echo "  - data/cmdrhelper.db"
echo "  - venv/.venv"
echo "  - .git/.github"
echo "  - Build-/Cache-/Editor-Dateien"
