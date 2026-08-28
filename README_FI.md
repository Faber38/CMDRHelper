# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) | [🇬🇧 English](README.md) | [🇫🇷 Français](README_FR.md) | [🇮🇹 Italiano](README_IT.md) | [🇳🇴 Norsk](README_NO.md) | [🇸🇪 Svenska](README_SV.md) | [🇫🇮 Suomi](README_FI.md) | [🇵🇱 Polski](README_PL.md) | [🇳🇱 Nederlands](README_NL.md) | [🇪🇸 Español](README_ES.md) | [🇹🇷 Türkçe](README_TR.md) | [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper](/docs/cmdrh.png)

**Henkilökohtainen Elite Dangerous -kumppani — tutkimusmatkailu, järjestelmäanalyysi ja Commander-tiedot**

Projektia kehitetään aktiivisesti.

## Ominaisuudet

### Elite Dangerous Journal -tiedostot

CMDRHelper lukee Elite Dangerousin paikallisia Journal-tiedostoja ja käsittelee tähtijärjestelmiä, tähtiä, planeettoja, kuita, Belt Clustereita, skannauksia, kartoituksia sekä biologisia ja geologisia signaaleja.

### Tehtävät

CMDRHelper analysoi Journal-tiedostojen tehtävätapahtumia ja näyttää aktiiviset tehtävät selkeästi. Myös NPC-viesteinä (`ReceiveText`) saapuvia tarjouksia voidaan tunnistaa.

### Järjestelmä- ja Explorer-näkymä

Tunnetut taivaankappaleet näytetään graafisesti yhdessä tyypin, etäisyyden, skannaus-/kartoitustilan, BIO/GEO-signaalien ja arvojen kanssa.

### Kappaleen tiedot

Kappaleen valinta avaa yksityiskohtaisen näkymän saatavilla olevista fyysisistä tiedoista, materiaaleista, BIO/GEO-signaaleista ja tutkimusarvoista.

## Versio 0.9.9

### Monikielinen käyttöliittymä ja käännösten tarkistus

- CMDRHelper tukee nyt **12 käyttöliittymäkieltä**: saksa, englanti, ranska, italia, norja (Bokmål), ruotsi, suomi, puola, hollanti, espanja, turkki ja kreikka.
- kieli valitaan ja tallennetaan asetuksissa.
- fallback: **valittu kieli → englanti → saksa → käännösavain**.
- `tools/check_i18n.py` tarkistaa `tr("...")`-avaimet, puuttuvat/ylimääräiset avaimet, kaksoiskappaleet ja paikkamerkit.
- Linuxissa tarkistus suoritetaan automaattisesti `start.sh`:n kautta estämättä käynnistystä.


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

