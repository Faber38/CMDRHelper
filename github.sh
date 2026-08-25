#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="CMDRHelper"

echo
echo "CMDRHelper – GitHub Upload"
echo "=========================="
echo

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "[FEHLER] Dieses Verzeichnis ist kein Git-Repository."
    exit 1
fi

if [[ ! -f "create_release.sh" ]]; then
    echo "[FEHLER] create_release.sh wurde nicht gefunden."
    exit 1
fi

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
    echo "[FEHLER] VERSION konnte nicht aus ${VERSION_FILE} gelesen werden."
    exit 1
fi

TAG="v${VERSION}"

echo "Projekt : ${APP_NAME}"
echo "Version : ${VERSION}"
echo
echo "Aktueller Git-Status:"
git status --short
echo

has_changes=0

if ! git diff --quiet; then
    has_changes=1
fi

if ! git diff --cached --quiet; then
    has_changes=1
fi

if [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
    has_changes=1
fi

if [[ "${has_changes}" -eq 1 ]]; then
    read -r -p "Commit-Nachricht: " commit_message

    if [[ -z "${commit_message}" ]]; then
        echo "Abgebrochen: Keine Commit-Nachricht eingegeben."
        exit 1
    fi

    echo
    echo "Dateien werden hinzugefügt ..."
    git add .

    echo "Commit wird erstellt ..."
    git commit -m "${commit_message}"
else
    echo "Keine lokalen Änderungen vorhanden."
fi

echo
echo "Änderungen werden zu GitHub übertragen ..."
git push

echo
echo "GitHub-Push erfolgreich."
git log -1 --oneline
echo

read -r -p "Release ${TAG} vorbereiten und taggen? [j/N]: " create_tag

case "${create_tag}" in
    j|J|ja|JA|Ja)
        if git rev-parse "${TAG}" >/dev/null 2>&1; then
            echo
            echo "[FEHLER] Der Tag ${TAG} existiert bereits."
            exit 1
        fi

        echo
        echo "Erstelle Release-ZIP ..."
        ./create_release.sh

        echo
        echo "Erstelle Git-Tag ${TAG} ..."
        git tag -a "${TAG}" -m "${APP_NAME} ${TAG}"

        echo "Übertrage Tag zu GitHub ..."
        git push origin "${TAG}"

        echo
        echo "Tag ${TAG} wurde erfolgreich erstellt und hochgeladen."

        ARCHIVE="release/${APP_NAME}_v${VERSION}.zip"

        if command -v gh >/dev/null 2>&1; then
            echo
            read -r -p "GitHub Release mit ZIP jetzt erstellen? [j/N]: " create_release_answer

            case "${create_release_answer}" in
                j|J|ja|JA|Ja)
                    echo
                    echo "Erstelle GitHub Release ${TAG} ..."
                    gh release create "${TAG}" \
                        "${ARCHIVE}" \
                        --title "${APP_NAME} ${TAG}" \
                        --generate-notes

                    echo
                    echo "GitHub Release ${TAG} wurde erstellt."
                    ;;
                *)
                    echo
                    echo "GitHub Release wurde nicht automatisch erstellt."
                    echo "ZIP liegt bereit unter:"
                    echo "${ARCHIVE}"
                    ;;
            esac
        else
            echo
            echo "GitHub CLI 'gh' ist nicht installiert."
            echo "Der Tag ist auf GitHub; das ZIP liegt bereit unter:"
            echo "${ARCHIVE}"
            echo
            echo "Du kannst es auf GitHub unter Releases manuell hochladen."
        fi
        ;;
    *)
        echo
        echo "Kein neuer Versions-Tag erstellt."
        ;;
esac

echo
echo "Fertig."
