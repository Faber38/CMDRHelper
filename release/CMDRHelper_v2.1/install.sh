#!/usr/bin/env bash
set -u

fail() {
    local code="$1"
    shift
    printf '[FEHLER] %s\n' "$*" >&2
    exit "$code"
}

resolve_script() {
    local source="${BASH_SOURCE[0]}" directory target hops=0
    if [[ "$source" != */* ]]; then
        source="$(command -v -- "$source")" \
            || fail 2 "Der Pfad des Installationsscripts konnte nicht ermittelt werden."
    fi
    while [[ -L "$source" ]]; do
        (( hops += 1 ))
        (( hops <= 40 )) || fail 2 "Zu viele symbolische Links beim Auflösen von install.sh."
        directory="$(cd -P -- "$(dirname -- "$source")" && pwd)" \
            || fail 2 "Der Ordner des Script-Links konnte nicht geöffnet werden."
        target="$(readlink -- "$source")" \
            || fail 2 "Der Script-Link konnte nicht aufgelöst werden: $source"
        [[ "$target" = /* ]] && source="$target" || source="$directory/$target"
    done
    directory="$(cd -P -- "$(dirname -- "$source")" && pwd)" \
        || fail 2 "Das reale Installationsverzeichnis konnte nicht ermittelt werden."
    printf '%s/%s\n' "$directory" "$(basename -- "$source")"
}

SCRIPT_PATH="$(resolve_script)"
INSTALL_ROOT="$(dirname -- "$SCRIPT_PATH")"
cd -- "$INSTALL_ROOT" \
    || fail 2 "Der CMDRHelper-Installationsordner konnte nicht geöffnet werden: $INSTALL_ROOT"

VENV_DIR="$INSTALL_ROOT/venv"
VENV_PYTHON="$VENV_DIR/bin/python"
PYTHON_SUPPORT="$INSTALL_ROOT/cmdrhelper/python_support.py"
REQUIREMENTS="$INSTALL_ROOT/requirements.txt"
REPAIR_MARKER="$INSTALL_ROOT/backup/update_repair_required.json"

printf '%s\n' '=========================================='
printf '%s\n' '       CMDRHelper - Installation'
printf '%s\n' '=========================================='
printf 'Installationsordner: %s\n\n' "$INSTALL_ROOT"

[[ -f "$PYTHON_SUPPORT" ]] \
    || fail 3 "Python-Kompatibilitätsprüfung fehlt: $PYTHON_SUPPORT"

PYTHON_CMD=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
    command -v -- "$candidate" >/dev/null 2>&1 || continue
    if "$candidate" "$PYTHON_SUPPORT" --check >/dev/null 2>&1; then
        PYTHON_CMD="$(command -v -- "$candidate")"
        break
    fi
done

[[ -n "$PYTHON_CMD" ]] || fail 10 \
    'Keine unterstützte Python-Version gefunden. Benötigt wird Python 3.10 bis 3.13.'

printf '[1/5] Verwendeter Python-Interpreter:\n'
"$PYTHON_CMD" -c 'import sys; print(sys.executable); print(sys.version)' \
    || fail 11 "Der ausgewählte Python-Interpreter konnte nicht gestartet werden."

printf '\n[2/5] Lokale virtuelle Umgebung wird geprüft...\n'
if [[ -L "$VENV_DIR" ]]; then
    fail 12 "venv ist ein Symlink. Aus Sicherheitsgründen wird weder das Ziel verwendet noch gelöscht: $VENV_DIR"
fi

rebuild=0
[[ -e "$REPAIR_MARKER" ]] && rebuild=1
[[ -x "$VENV_PYTHON" ]] || rebuild=1
if (( rebuild == 0 )); then
    "$VENV_PYTHON" "$PYTHON_SUPPORT" --check >/dev/null 2>&1 || rebuild=1
fi
if (( rebuild == 0 )); then
    "$VENV_PYTHON" -m pip --version >/dev/null 2>&1 || rebuild=1
fi

if (( rebuild == 1 )); then
    printf '%s\n' 'Das ausschließlich lokale venv ist fehlend, defekt oder inkompatibel.'
    printf '%s\n' 'Es wird neu erstellt. data und persönliche Dateien bleiben unangetastet.'
    if [[ -e "$VENV_DIR" ]]; then
        [[ ! -L "$VENV_DIR" ]] || fail 12 "Ein verlinktes venv wird nicht gelöscht."
        [[ "$(dirname -- "$VENV_DIR")" == "$INSTALL_ROOT" && "$(basename -- "$VENV_DIR")" == venv ]] \
            || fail 12 "Unsicheres venv-Ziel; Reparatur abgebrochen: $VENV_DIR"
        rm -rf -- "$VENV_DIR" \
            || fail 13 "Das lokale venv konnte nicht entfernt werden: $VENV_DIR"
        [[ ! -e "$VENV_DIR" ]] \
            || fail 13 "Das lokale venv ist nach der Reparatur noch vorhanden."
    fi
    if ! "$PYTHON_CMD" -m venv "$VENV_DIR"; then
        printf '%s\n' '[HINWEIS] Möglicherweise fehlt das Distributionspaket für venv.' >&2
        printf '%s\n' 'Unter Ubuntu/Pop!_OS heißt es meist python3-venv bzw. python3.x-venv.' >&2
        printf '%s\n' 'CMDRHelper installiert keine Systempakete automatisch.' >&2
        exit 14
    fi
else
    printf '%s\n' 'Das lokale venv ist gesund und wird weiterverwendet.'
fi

printf '\n[3/5] Lokaler venv-Interpreter:\n'
"$VENV_PYTHON" -c 'import sys; print(sys.executable); print(sys.version)' \
    || fail 15 "Der lokale venv-Interpreter ist nicht startbar."
"$VENV_PYTHON" "$PYTHON_SUPPORT" --check \
    || fail 15 "Das lokale venv verwendet keine unterstützte Python-Version."

printf '\n[4/5] pip wird aktualisiert...\n'
"$VENV_PYTHON" -m pip install --upgrade pip \
    || fail 16 "pip konnte im lokalen venv nicht aktualisiert werden."

[[ -f "$REQUIREMENTS" ]] \
    || fail 17 "requirements.txt wurde nicht gefunden: $REQUIREMENTS"
printf '\n[5/5] Abhängigkeiten werden im lokalen venv installiert...\n'
"$VENV_PYTHON" -m pip install -r "$REQUIREMENTS" \
    || fail 18 "Nicht alle Abhängigkeiten konnten installiert werden."

rm -f -- "$REPAIR_MARKER" \
    || fail 19 "Der Update-Reparaturmarker konnte nicht entfernt werden."

printf '\n%s\n' '=========================================='
printf '%s\n' 'CMDRHelper wurde erfolgreich eingerichtet.'
printf 'Start: %s/start.sh\n' "$INSTALL_ROOT"
printf '%s\n' '=========================================='
exit 0
