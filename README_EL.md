# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) | [🇬🇧 English](README.md) | [🇫🇷 Français](README_FR.md) | [🇮🇹 Italiano](README_IT.md) | [🇳🇴 Norsk](README_NO.md) | [🇸🇪 Svenska](README_SV.md) | [🇫🇮 Suomi](README_FI.md) | [🇵🇱 Polski](README_PL.md) | [🇳🇱 Nederlands](README_NL.md) | [🇪🇸 Español](README_ES.md) | [🇹🇷 Türkçe](README_TR.md) | [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper](/docs/cmdrh.png)

**Προσωπικός βοηθός για το Elite Dangerous — εξερεύνηση, ανάλυση συστημάτων και δεδομένα Commander**

Το έργο βρίσκεται σε ενεργή ανάπτυξη.

## Λειτουργίες

### Journal του Elite Dangerous

Το CMDRHelper διαβάζει τα τοπικά αρχεία Journal του Elite Dangerous και επεξεργάζεται αστρικά συστήματα, άστρα, πλανήτες, δορυφόρους, Belt Clusters, σαρώσεις, χαρτογραφήσεις και βιολογικά/γεωλογικά σήματα.

### Αποστολές

Το CMDRHelper αναλύει συμβάντα αποστολών από τα Journal και εμφανίζει καθαρά τις ενεργές αποστολές. Μπορούν επίσης να εντοπιστούν προσφορές μέσω μηνυμάτων NPC (`ReceiveText`).

### Προβολή συστήματος και Explorer

Τα γνωστά ουράνια σώματα εμφανίζονται γραφικά με τύπο, απόσταση, κατάσταση σάρωσης/χαρτογράφησης, σήματα BIO/GEO και τιμές.

### Λεπτομέρειες ουράνιου σώματος

Η επιλογή ενός σώματος ανοίγει λεπτομερή προβολή με διαθέσιμα φυσικά δεδομένα, υλικά, σήματα BIO/GEO και τιμές εξερεύνησης.

## Έκδοση 0.9.9

### Πολυγλωσσικό περιβάλλον και έλεγχος μεταφράσεων

- Το CMDRHelper υποστηρίζει πλέον **12 γλώσσες διεπαφής**: γερμανικά, αγγλικά, γαλλικά, ιταλικά, νορβηγικά (Bokmål), σουηδικά, φινλανδικά, πολωνικά, ολλανδικά, ισπανικά, τουρκικά και ελληνικά.
- η γλώσσα επιλέγεται και αποθηκεύεται στις Ρυθμίσεις.
- fallback: **επιλεγμένη γλώσσα → αγγλικά → γερμανικά → κλειδί μετάφρασης**.
- το `tools/check_i18n.py` ελέγχει κλειδιά `tr("...")`, ελλείποντα/επιπλέον κλειδιά, διπλότυπα και placeholders.
- στο Linux ο έλεγχος εκτελείται αυτόματα μέσω `start.sh` χωρίς να εμποδίζει την εκκίνηση.


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

