# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) | [🇬🇧 English](README.md) | [🇫🇷 Français](README_FR.md) | [🇮🇹 Italiano](README_IT.md) | [🇳🇴 Norsk](README_NO.md) | [🇸🇪 Svenska](README_SV.md) | [🇫🇮 Suomi](README_FI.md) | [🇵🇱 Polski](README_PL.md) | [🇳🇱 Nederlands](README_NL.md) | [🇪🇸 Español](README_ES.md) | [🇹🇷 Türkçe](README_TR.md) | [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper](/docs/cmdrh.png)

**Personlig följeslagare för Elite Dangerous — utforskning, systemanalys och Commander-data**

Projektet är under aktiv utveckling.

## Funktioner

### Elite Dangerous-journaler

CMDRHelper läser lokala Journal-filer från Elite Dangerous och behandlar stjärnsystem, stjärnor, planeter, månar, Belt Cluster, skanningar, kartläggningar samt biologiska och geologiska signaler.

### Uppdrag

CMDRHelper analyserar uppdragshändelser från Journal-filerna och visar aktiva uppdrag tydligt. Även erbjudanden via NPC-meddelanden (`ReceiveText`) kan registreras.

### System- och Explorer-vy

Kända himlakroppar visas grafiskt med bland annat typ, avstånd, skannings-/kartläggningsstatus, BIO/GEO-signaler och värden.

### Kroppsdetaljer

Ett klick öppnar en detaljvy med tillgängliga fysiska data, material, BIO/GEO-signaler och utforskningsvärden.

## Version 0.9.9

### Flerspråkigt gränssnitt och översättningskontroll

- CMDRHelper stöder nu **12 gränssnittsspråk**: tyska, engelska, franska, italienska, norska (Bokmål), svenska, finska, polska, nederländska, spanska, turkiska och grekiska.
- språk väljs och sparas i inställningarna.
- fallback: **valt språk → engelska → tyska → översättningsnyckel**.
- `tools/check_i18n.py` kontrollerar `tr("...")`-nycklar, saknade/extra nycklar, dubbletter och platshållare.
- Linux kör kontrollen automatiskt via `start.sh` utan att blockera starten.


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

