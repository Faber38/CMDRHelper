#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Bitte zuerst ./install.sh ausführen."
    exit 1
fi

source venv/bin/activate

# Entwicklerprüfung: Übersetzungen kontrollieren.
# Fehler werden deutlich angezeigt, blockieren den Programmstart aber nicht.
if [ -f "tools/check_i18n.py" ]; then
    python tools/check_i18n.py
    I18N_STATUS=$?

    if [ "$I18N_STATUS" -ne 0 ]; then
        echo
        echo "ACHTUNG: Die i18n-Prüfung hat Probleme gefunden."
        echo "CMDRHelper wird trotzdem gestartet."
        echo
    fi
fi

python main.py
