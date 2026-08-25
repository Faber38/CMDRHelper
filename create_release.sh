#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="CMDRHelper"

# Version möglichst direkt aus main_window.py übernehmen.
VERSION="$(
    grep -Eo 'CMDRHelper[[:space:]]+[0-9]+(\.[0-9]+)+' \
        cmdrhelper/ui/main_window.py 2>/dev/null \
    | head -1 \
    | awk '{print $2}' \
    || true
)"

if [[ -z "${VERSION}" ]]; then
    VERSION="$(date +%Y%m%d)"
fi

RELEASE_NAME="${APP_NAME}-${VERSION}"
BUILD_DIR="build"
STAGE_DIR="${BUILD_DIR}/${RELEASE_NAME}"
ZIP_FILE="${BUILD_DIR}/${RELEASE_NAME}.zip"

echo "=========================================="
echo "  ${APP_NAME} Release erstellen"
echo "  Version: ${VERSION}"
echo "=========================================="
echo

# Pflichtdateien prüfen.
required=(
    "main.py"
    "requirements.txt"
    "cmdrhelper"
)

for item in "${required[@]}"; do
    if [[ ! -e "${item}" ]]; then
        echo "[FEHLER] ${item} fehlt."
        exit 1
    fi
done

# Für eine Windows-Version sollten diese Dateien im Release liegen.
for item in "install.bat" "start.bat"; do
    if [[ ! -f "${item}" ]]; then
        echo "[WARNUNG] ${item} fehlt und wird nicht mitgepackt."
    fi
done

rm -rf "${STAGE_DIR}"
rm -f "${ZIP_FILE}"
mkdir -p "${STAGE_DIR}"

echo "[1/4] Programmdateien kopieren ..."

cp "main.py" "${STAGE_DIR}/"
cp "requirements.txt" "${STAGE_DIR}/"

# Start-/Installationsdateien mitnehmen, sofern vorhanden.
for item in \
    "install.bat" \
    "start.bat" \
    "install.sh" \
    "start.sh" \
    "README.md" \
    "README_DE.md" \
    "LICENSE"
do
    if [[ -f "${item}" ]]; then
        cp "${item}" "${STAGE_DIR}/"
    fi
done

# Programmcode und Assets kopieren.
cp -a "cmdrhelper" "${STAGE_DIR}/cmdrhelper"

# Leeres Datenverzeichnis anlegen.
# Die persönliche SQLite-Datenbank wird NICHT ausgeliefert.
mkdir -p "${STAGE_DIR}/data"

echo "[2/4] Entwicklungs-/Benutzerdaten entfernen ..."

find "${STAGE_DIR}" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "${STAGE_DIR}" -type f \( \
    -name "*.pyc" -o \
    -name "*.pyo" -o \
    -name "*.log" -o \
    -name "*.bak" -o \
    -name "*~" \
\) -delete

# Persönliche/lokale Daten niemals in ein Release aufnehmen.
rm -f \
    "${STAGE_DIR}/data/cmdrhelper.db" \
    "${STAGE_DIR}/cmdrhelper.db"

# Falls solche Verzeichnisse versehentlich im Projekt liegen:
rm -rf \
    "${STAGE_DIR}/venv" \
    "${STAGE_DIR}/.venv" \
    "${STAGE_DIR}/.git" \
    "${STAGE_DIR}/.idea" \
    "${STAGE_DIR}/.vscode"

echo "[3/4] Release-Inhalt:"
find "${STAGE_DIR}" -maxdepth 2 -type f | sort
echo

echo "[4/4] ZIP erstellen ..."

if command -v zip >/dev/null 2>&1; then
    (
        cd "${BUILD_DIR}"
        zip -qr "${RELEASE_NAME}.zip" "${RELEASE_NAME}"
    )
else
    echo "[FEHLER] Das Programm 'zip' ist nicht installiert."
    echo "Unter Ubuntu/Pop!_OS: sudo apt install zip"
    exit 1
fi

echo
echo "=========================================="
echo "Release fertig:"
echo "${ZIP_FILE}"
echo "=========================================="
echo
echo "NICHT enthalten:"
echo "  - data/cmdrhelper.db"
echo "  - venv/.venv"
echo "  - Git-/Editor-Dateien"
echo "  - Logs, Cache und Backups"
