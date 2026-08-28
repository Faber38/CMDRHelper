# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) | [🇬🇧 English](README.md) | [🇫🇷 Français](README_FR.md) | [🇮🇹 Italiano](README_IT.md) | [🇳🇴 Norsk](README_NO.md) | [🇸🇪 Svenska](README_SV.md) | [🇫🇮 Suomi](README_FI.md) | [🇵🇱 Polski](README_PL.md) | [🇳🇱 Nederlands](README_NL.md) | [🇪🇸 Español](README_ES.md) | [🇹🇷 Türkçe](README_TR.md) | [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper](/docs/cmdrh.png)

**Persoonlijke begeleider voor Elite Dangerous — exploratie, systeemanalyse en Commander-gegevens**

Het project is actief in ontwikkeling.

## Functies

### Elite Dangerous Journals

CMDRHelper leest lokale Journal-bestanden van Elite Dangerous en verwerkt sterrenstelsels, sterren, planeten, manen, Belt Clusters, scans, mappings en biologische/geologische signalen.

### Missies

CMDRHelper analyseert missie-events uit de Journals en toont actieve missies overzichtelijk. Ook aanbiedingen via NPC-berichten (`ReceiveText`) kunnen worden herkend.

### Systeem- en Explorer-weergave

Bekende hemellichamen worden grafisch getoond met onder meer type, afstand, scan-/mappingstatus, BIO/GEO-signalen en waarden.

### Details van hemellichamen

Een klik opent een detailweergave met beschikbare fysieke gegevens, materialen, BIO/GEO-signalen en exploratiewaarden.

## Versie 0.9.9

### Meertalige interface en vertaalcontrole

- CMDRHelper ondersteunt nu **12 interfacetalen**: Duits, Engels, Frans, Italiaans, Noors (Bokmål), Zweeds, Fins, Pools, Nederlands, Spaans, Turks en Grieks.
- de taal kan in Instellingen worden gekozen en opgeslagen.
- fallback: **gekozen taal → Engels → Duits → vertaalsleutel**.
- `tools/check_i18n.py` controleert `tr("...")`-sleutels, ontbrekende/extra sleutels, duplicaten en placeholders.
- onder Linux draait de controle automatisch via `start.sh` zonder het starten te blokkeren.


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

