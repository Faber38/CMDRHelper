# Entdeckung und Kartographierung — Zustandsprüfung vom 08.09.2026

## Verbindliche Semantik

`exploration_status.py` interpretiert die bestehenden Körperfelder; es gibt keine
neue DB-Struktur für diese Semantik. Die separate Migration auf Schema 16
und die historischen Start-Reparaturen sind in
[startup-repairs.md](startup-repairs.md) beschrieben.

| Feld/Ergebnis | Bedeutung |
| --- | --- |
| `was_discovered` / DB `was_discovered_at_scan` | Historische Journalbeobachtung: bei deinem Scan bereits entdeckt; True, False oder unbekannt. |
| `was_mapped` / DB `was_mapped_at_scan` | Unabhängige historische Journalbeobachtung: bei deinem Scan bereits kartographiert; True, False oder unbekannt. |
| `self_mapped` | Eigene Kartographierung aufgezeichnet, auch aus einem früheren Aufenthalt. Kein Beleg für einen offiziellen Erstanspruch. |
| `edsm_known` | EDSM kennt diesen Körper. Kein Beweis für offizielle Elite-Erstentdeckung oder Mapping. |
| `first_discovery_candidate` | Explizites eigenes `WasDiscovered=false`: Kandidat **zum Scanzeitpunkt**. |
| `first_mapping_candidate` | Explizites eigenes `WasMapped=false` für kartographierbaren Körper: Kandidat **zum Scanzeitpunkt**, unabhängig von Discovery und eigener Kartographierung. |

„Kandidat“ behauptet weder heutige Verfügbarkeit noch unverkaufte Daten. Nach
Verkauf oder Wiederbesuch wird aus einem historischen Kandidaten kein neuer
offener Erstanspruch. Ein kumulatives `self_mapped` beweist bei mehreren Besuchen
auch nicht automatisch die Reihenfolge gegenüber dem gespeicherten Scan.
Deshalb ersetzt „Kandidat beim Scan · selbst kartographiert; Erstanspruch
unbestätigt“ die bisherige definitive Beanspruchungsanzeige.

Fehlende oder ungültige Journalflags bleiben unbekannt. Explizit externe
Körperdatensätze liefern keine persönlichen Scanflags. Das bestehende
`edsm_known=False` kann auch „nicht abgefragt“ bedeuten; daraus wird keine
bestätigte negative EDSM-Auskunft erfunden. Das separate EDSM-Status-HUD
und dessen drei Ergebnisse bleiben unverändert.

## Geprüfte Datenwege

- `journal_reader.py`: `Scan` liest beide Flags unabhängig mit `get`;
  `SAAScanComplete` setzt separat eigene Kartographierung.
- `database.py`: commanderbezogene `commander_bodies`, nullable historische
  Flags, kumulatives `self_mapped` via MAX; Archiv und Snapshot behalten ihre
  vorhandenen Schreibwege. Keine DB-Änderung für diesen Agenda-Punkt.
- `state.py`: aktuelle eigene Scans und eigene gespeicherte Scans. Ein neuer
  Scan darf die gespeicherte eigene Kartographierung nicht zurücksetzen.
- `online_services.py`: EDSM-Normalisierung setzt keine eigenen Journalflags.
  Der Merge bereinigt auch bereits vorhandene ältere normalisierte Cachewerte;
  eigene Zustände und daraus berechnete Werte werden nicht aus EDSM ergänzt.
- `valuation.py`: Flags für Erstbonus-Schätzungen nur aus eigener Journalquelle.
  Formeln bleiben unverändert; die UI benennt die Zahlen als Schätzungen nach
  Scanstand, nicht als aktuell offenen Verkaufserlös.
- Karte, Wertliste und Körperdetail verwenden dieselben Statuszeilen und
  historische Einordnung. Marker/Legende und Wertvolle-Körper-Liste verwenden
  dieselbe zeitliche Semantik. Goldrahmen bleibt eine Wertschwelle, keine
  Bestätigung von First Discovery oder unverkauften Daten.
- `_main_window.py` und `backup_main_window.py` sind nicht importierte alte
  Kopien; die aktive UI läuft über `ui/main_window.py`.

## Reale, ausschließlich lesend geprüfte Fälle

Commander-ID 1, `data/cmdrhelper.db`; Journalzeiten unten in UTC.

| Körper | Entdeckt beim Scan | Kartographiert beim Scan | Selbst kartographiert | Neue Interpretation |
| --- | --- | --- | --- | --- |
| Nuekuae LS-B d28 1 b | Ja | Nein | Ja | Kein Discovery-Kandidat laut Scan; historischer Mapping-Kandidat mit eigener Kartographierung, Erstanspruch unbestätigt. |
| Prua Hypai RB-D c29-73 AB 2 f | Nein | Nein | Ja | Historischer Discovery- und Mapping-Kandidat; eigene Kartographierung belegt, offizielle Erstansprüche unbestätigt. |
| Colonia 1 | Ja | Ja | Nein | Beim Scan beides bereits vorhanden; keine eigene Kartographierung aufgezeichnet. |
| HIP 77917 A, echter alter EDSM-Cache | Unbekannt | Unbekannt | Unbekannt | EDSM bekannt, keine eigenen Elite-Statusangaben daraus. Stern: Mapping nicht anwendbar. |

Journalbelege:

- Nuekuae: `Journal.2026-05-22T062213.01.log`, Scan 04:33:52Z mit
  `WasDiscovered=true`, `WasMapped=false`; eigener `SAAScanComplete` 04:38:44Z.
  Auch der nachfolgende Scan um 04:38:44Z meldet true/false.
- Prua Hypai: `Journal.2026-09-04T134325.01.log`, Scan 12:20:57Z mit false/false;
  eigener `SAAScanComplete` 12:29:47Z und nachfolgender Scan erneut false/false.
  Die DB nennt als letzten Körperkontakt 07.09.2026 05:16:17Z; dieser Kontakt
  macht aus den älteren Flags keine neue aktuelle Verfügbarkeitsauskunft.
- Die lokale Verkaufs-Lerntabelle ordnet Nuekuae einem Verkauf vom 22.05.2026
  14:24:19Z und Prua Hypai einem Verkauf vom 04.09.2026 13:15:27Z zu. Diese
  Zuordnung sammelt offene Körper für Wertschätzungen. Sie ist kein individueller
  Beleg für einen offiziell zuerkannten Discovery-/Mapping-Erstanspruch.
- Der echte Cache `e052c91ac207c44360787722.json` enthält für HIP 77917 A noch
  das frühere synthetische `was_discovered=true`. Nach dem neuen Merge ist
  der eigene Discovery-Status unbekannt, EDSM-Bekanntheit bleibt erhalten.

## Grenzen und Prüfung

Aktueller offizieller Erstentdecker, Erstkartograph und offene Erstboni bleiben
mit diesen Daten unbestimmt. Es werden keine Namen geraten und keine neuen
Verkaufs- oder Ownership-Daten behauptet. Die Benutzerhilfe und READMEs
beschreiben die Semantik inzwischen in allen zwölf Sprachen; ebenso sind
die sichtbaren App-Texte in allen zwölf Sprachen angepasst.

Regressionen decken alle neun Scanflag-Kombinationen inklusive fehlender Werte,
SAAScanComplete, DB-Roundtrip, eigene Kartographierung und Wiederbesuch,
Quellentrennung inklusive altem EDSM-Cache und identische Statuszeilen in
Karte/Liste/Detail ab. Beide Themes wurden offscreen gerendert.

Teststand der ursprünglichen Semantikprüfung (vor der späteren
Start-Reparaturintegration und Dokumentationspflege):

- 126 gezielte Explorer-/Bodydetail-/EDSM-/Hilfetests erfolgreich.
- Gesamtsuite: 599 Tests erfolgreich (Qt offscreen, 143,522 s).
- i18n: 964 Schlüssel vollständig in 12 Sprachen, Platzhalter konsistent,
  keine doppelten Schlüssel.
- `venv/bin/python -m compileall -q cmdrhelper tests tools main.py` erfolgreich.
- `git diff --check` ohne Befund.
- Keine Commits, kein Push; reale DB und reale Journale ausschließlich gelesen.
