# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) | [🇬🇧 English](README.md) | [🇫🇷 Français](README_FR.md) | [🇮🇹 Italiano](README_IT.md) | [🇳🇴 Norsk](README_NO.md) | [🇸🇪 Svenska](README_SV.md) | [🇫🇮 Suomi](README_FI.md) | [🇵🇱 Polski](README_PL.md) | [🇳🇱 Nederlands](README_NL.md) | [🇪🇸 Español](README_ES.md) | [🇹🇷 Türkçe](README_TR.md) | [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper](/docs/cmdrh.png)

**Personlig følgesvenn for Elite Dangerous — utforskning, systemanalyse og Commander-data**

Prosjektet er under aktiv utvikling.

## Funksjoner

### Elite Dangerous-journaler

CMDRHelper leser lokale Journal-filer fra Elite Dangerous og behandler stjernesystemer, stjerner, planeter, måner, Belt Cluster, skanninger, kartlegging samt biologiske og geologiske signaler.

### Oppdrag

CMDRHelper analyserer oppdragshendelser fra Journal-filene og viser aktive oppdrag oversiktlig. Også tilbud via NPC-meldinger (`ReceiveText`) kan registreres.

### System- og Explorer-visning

Kjente himmellegemer vises grafisk med blant annet type, avstand, skanne-/kartleggingsstatus, BIO/GEO-signaler og verdier.

### Detaljer om himmellegemer

Et klikk åpner detaljvisning med tilgjengelige fysiske data, materialer, BIO/GEO-signaler og utforskningsverdier.

## Versjon 0.9.9

### Flerspråklig grensesnitt og oversettelseskontroll

- CMDRHelper støtter nå **12 grensesnittspråk**: tysk, engelsk, fransk, italiensk, norsk (Bokmål), svensk, finsk, polsk, nederlandsk, spansk, tyrkisk og gresk.
- språk velges og lagres i innstillingene.
- fallback: **valgt språk → engelsk → tysk → oversettelsesnøkkel**.
- `tools/check_i18n.py` kontrollerer `tr("...")`-nøkler, manglende/ekstra nøkler, duplikater og plassholdere.
- Linux kjører kontrollen automatisk via `start.sh` uten å blokkere oppstarten.


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

