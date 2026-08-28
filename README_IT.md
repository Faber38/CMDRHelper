# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) | [🇬🇧 English](README.md) | [🇫🇷 Français](README_FR.md) | [🇮🇹 Italiano](README_IT.md) | [🇳🇴 Norsk](README_NO.md) | [🇸🇪 Svenska](README_SV.md) | [🇫🇮 Suomi](README_FI.md) | [🇵🇱 Polski](README_PL.md) | [🇳🇱 Nederlands](README_NL.md) | [🇪🇸 Español](README_ES.md) | [🇹🇷 Türkçe](README_TR.md) | [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper](/docs/cmdrh.png)

**Compagno personale per Elite Dangerous — esplorazione, analisi dei sistemi e dati del Commander**

Il progetto è in sviluppo attivo.

## Funzionalità

### Journal di Elite Dangerous

CMDRHelper legge i file Journal locali di Elite Dangerous ed elabora sistemi stellari, stelle, pianeti, lune, Belt Cluster, scansioni, mappature e segnali biologici e geologici. I dati personali del Commander restano distinguibili dalle informazioni esterne supplementari.

### Missioni

CMDRHelper analizza gli eventi delle missioni nei Journal di Elite Dangerous e presenta chiaramente le missioni attive. Stato ed eventi associati vengono monitorati. Anche le offerte ricevute tramite messaggi NPC (`ReceiveText`) possono essere rilevate e associate progressivamente.

### Vista sistema ed Explorer

I corpi conosciuti vengono rappresentati graficamente e possono essere selezionati direttamente. CMDRHelper mostra tra l’altro tipo, distanza, stato di scansione e mappatura, possibili prime scoperte/First Mapping, segnali BIO/GEO e valori di scansione/cartografia.

### Dettagli dei corpi

Selezionando un corpo si apre una vista dettagliata con, quando disponibili, tipo, massa, distanza, gravità, atmosfera, vulcanismo, possibilità di atterraggio, terraformazione, materiali, segnali BIO/GEO e valori di esplorazione.

## Versione 0.9.9

### Interfaccia multilingue e controllo traduzioni

- CMDRHelper supporta ora **12 lingue dell’interfaccia**: tedesco, inglese, francese, italiano, norvegese (Bokmål), svedese, finlandese, polacco, olandese, spagnolo, turco e greco.
- la lingua può essere selezionata e salvata nelle impostazioni.
- fallback: **lingua selezionata → inglese → tedesco → chiave di traduzione**.
- `tools/check_i18n.py` controlla chiavi `tr("...")`, chiavi mancanti/aggiuntive, duplicati e placeholder.
- su Linux il controllo viene eseguito automaticamente da `start.sh` senza bloccare l’avvio.

### Altre novità della versione 0.9.9

La versione 0.9.9 comprende tutte le migliorie della linea 0.9.8: mappa di sistema gerarchica, panoramica “Mostra tutto”, lista valori Explorer, valori non ancora venduti, finestre live per corpi preziosi e ritrovamenti BIO, progresso BIO dettagliato, miglioramenti alle missioni e `MissionRedirected`, galleria screenshot, upload EDSM, scelta del font, impostazioni scorrevoli, protezione single-instance e miglioramenti di stabilità.

## Piattaforme e installazione

CMDRHelper è sviluppato con Python e PySide6 per **Linux e Windows**. Dipendenze principali: `PySide6>=6.7,<7`, `numpy`, `Pillow>=10.0`.

Linux:
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Su Windows usare `install.bat` e quindi `start.bat`.

## Licenza

CMDRHelper è software libero distribuito sotto **GNU General Public License Version 3 (GPL-3.0)**.

Copyright © 2026 **Holger Mangold (Faber38)**.

CMDRHelper è un progetto community/hobby indipendente e non è un prodotto ufficiale di Frontier Developments. **Elite Dangerous** e i relativi nomi e contenuti appartengono ai rispettivi titolari.
