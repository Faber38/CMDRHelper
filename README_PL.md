# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) | [🇬🇧 English](README.md) | [🇫🇷 Français](README_FR.md) | [🇮🇹 Italiano](README_IT.md) | [🇳🇴 Norsk](README_NO.md) | [🇸🇪 Svenska](README_SV.md) | [🇫🇮 Suomi](README_FI.md) | [🇵🇱 Polski](README_PL.md) | [🇳🇱 Nederlands](README_NL.md) | [🇪🇸 Español](README_ES.md) | [🇹🇷 Türkçe](README_TR.md) | [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper](/docs/cmdrh.png)

**Osobisty pomocnik do Elite Dangerous — eksploracja, analiza systemów i dane Commandera**

Projekt jest aktywnie rozwijany.

## Funkcje

### Dzienniki Elite Dangerous

CMDRHelper odczytuje lokalne pliki Journal gry Elite Dangerous i przetwarza systemy gwiezdne, gwiazdy, planety, księżyce, Belt Cluster, skany, mapowanie oraz sygnały biologiczne i geologiczne.

### Misje

CMDRHelper analizuje zdarzenia misji z plików Journal i przejrzyście pokazuje aktywne misje. Oferty z wiadomości NPC (`ReceiveText`) również mogą być wykrywane.

### Widok systemu i Explorer

Znane ciała są prezentowane graficznie wraz z typem, odległością, stanem skanowania/mapowania, sygnałami BIO/GEO i wartościami.

### Szczegóły ciała

Kliknięcie ciała otwiera widok szczegółowy z dostępnymi danymi fizycznymi, materiałami, sygnałami BIO/GEO i wartościami eksploracji.

## Wersja 0.9.9

### Wielojęzyczny interfejs i kontrola tłumaczeń

- CMDRHelper obsługuje teraz **12 języków interfejsu**: niemiecki, angielski, francuski, włoski, norweski (Bokmål), szwedzki, fiński, polski, niderlandzki, hiszpański, turecki i grecki.
- język można wybrać i zapisać w ustawieniach.
- fallback: **wybrany język → angielski → niemiecki → klucz tłumaczenia**.
- `tools/check_i18n.py` sprawdza klucze `tr("...")`, brakujące/dodatkowe klucze, duplikaty i placeholdery.
- w Linux kontrola uruchamia się automatycznie przez `start.sh` bez blokowania startu.


### Weitere / Additional 0.9.9 improvements

Version 0.9.9 also contains the Explorer, system-map, BIO valuation, mission, screenshot, EDSM, usability and stability improvements documented in the German and English main README files. Those two files remain the most detailed release documentation.

## Technical requirements

`PySide6>=6.7,<7`, `numpy`, `Pillow>=10.0`

Linux:
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Windows: `install.bat`, then `start.bat`.

## License

CMDRHelper is free software released under **GNU General Public License Version 3 (GPL-3.0)**.

Copyright © 2026 **Holger Mangold (Faber38)**.

CMDRHelper is an independent community/hobby project and is not an official Frontier Developments product. **Elite Dangerous** and related names and content belong to their respective rights holders.

