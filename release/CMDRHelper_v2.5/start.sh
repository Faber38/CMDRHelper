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
            || fail 2 "Der Pfad des Startscripts konnte nicht ermittelt werden."
    fi
    while [[ -L "$source" ]]; do
        (( hops += 1 ))
        (( hops <= 40 )) || fail 2 "Zu viele symbolische Links beim Auflösen von start.sh."
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
MAIN_PY="$INSTALL_ROOT/main.py"
PYTHON_SUPPORT="$INSTALL_ROOT/cmdrhelper/python_support.py"
REPAIR_MARKER="$INSTALL_ROOT/backup/update_repair_required.json"

printf 'CMDRHelper-Installation: %s\n' "$INSTALL_ROOT"

if [[ -e "$REPAIR_MARKER" ]]; then
    printf '%s\n' 'Update fehlgeschlagen. Die vorherige Version wurde wiederhergestellt.' >&2
    printf '%s\n' 'Das lokale venv muss repariert werden.' >&2
    printf 'Bitte jetzt %s/install.sh ausführen.\n' "$INSTALL_ROOT" >&2
    printf 'Update-Log: %s/backup/update.log\n' "$INSTALL_ROOT" >&2
    exit 20
fi

[[ ! -L "$VENV_DIR" ]] \
    || fail 4 "Das lokale venv ist ein Symlink und wird nicht verwendet. Bitte $INSTALL_ROOT/install.sh prüfen."
[[ -x "$VENV_PYTHON" ]] \
    || fail 4 "Das lokale venv fehlt oder ist nicht startbereit. Bitte $INSTALL_ROOT/install.sh ausführen."
[[ -f "$PYTHON_SUPPORT" ]] \
    || fail 4 "Die Python-Prüfung fehlt. Bitte $INSTALL_ROOT/install.sh ausführen."
"$VENV_PYTHON" "$PYTHON_SUPPORT" --check >/dev/null 2>&1 \
    || fail 4 "Die Python-Version des lokalen venv wird nicht unterstützt. Bitte $INSTALL_ROOT/install.sh ausführen."
"$VENV_PYTHON" -m pip --version >/dev/null 2>&1 \
    || fail 4 "pip fehlt im lokalen venv. Bitte $INSTALL_ROOT/install.sh ausführen."
[[ -f "$MAIN_PY" ]] \
    || fail 3 "main.py wurde nicht in dieser Installation gefunden: $MAIN_PY"

version="$("$VENV_PYTHON" -c 'from cmdrhelper.version import __version__; print(__version__)' 2>/dev/null || true)"
[[ -n "$version" ]] && printf 'CMDRHelper-Version: %s\n' "$version"

# Bestehende Entwicklerdiagnose beibehalten, aber ausschließlich mit dem
# validierten lokalen Interpreter ausführen.
I18N_CHECK="$INSTALL_ROOT/tools/check_i18n.py"
if [[ -f "$I18N_CHECK" ]]; then
    "$VENV_PYTHON" "$I18N_CHECK"
    i18n_status=$?
    if (( i18n_status != 0 )); then
        printf '\nACHTUNG: Die i18n-Prüfung hat Probleme gefunden.\n'
        printf 'CMDRHelper wird trotzdem gestartet.\n\n'
    fi
fi

"$VENV_PYTHON" "$MAIN_PY"
app_exit=$?
if (( app_exit == 0 )); then
    exit 0
fi

printf '\nCMDRHelper wurde mit Exitcode %d beendet.\n' "$app_exit" >&2
printf 'Installation: %s\n' "$INSTALL_ROOT" >&2
exit "$app_exit"
