#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d "venv" ]; then echo "Bitte zuerst ./install.sh ausführen."; exit 1; fi
source venv/bin/activate
python main.py
