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
- Die aktive UI läuft über `ui/main_window.py`.

## Neutrale Referenzfälle

Die Beispiele beschreiben synthetische Zustände, keine persönliche Besuchshistorie.

| Körper | Entdeckt beim Scan | Kartographiert beim Scan | Selbst kartographiert | Interpretation |
| --- | --- | --- | --- | --- |
| Beispielplanet A | Ja | Nein | Ja | Historischer Mapping-Kandidat; Erstanspruch unbestätigt. |
| Beispielplanet B | Nein | Nein | Ja | Historischer Discovery-/Mapping-Kandidat; eigene Kartographierung belegt. |
| Beispielplanet C | Ja | Ja | Nein | Beides beim Scan vorhanden; keine eigene Kartographierung aufgezeichnet. |
| Beispielstern aus EDSM | Unbekannt | Unbekannt | Unbekannt | Keine persönlichen Elite-Statusangaben aus der externen Quelle. |

Ein Scan vor und nach `SAAScanComplete` darf dieselben historischen Flags liefern.
Ein späterer Kontakt macht daraus keine neue Verfügbarkeitsauskunft. Auch eine
Zuordnung zu einem späteren Verkauf belegt keinen offiziellen Erstanspruch.
Ein alter EDSM-Cache mit synthetischem `was_discovered=true` darf nach dem Merge
keinen eigenen Discovery-Status begründen; EDSM-Bekanntheit bleibt davon getrennt.

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
