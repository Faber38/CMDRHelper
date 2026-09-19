# Releaseprüfung CMDRHelper 3.6.1

Unveröffentlichte lokale Vorbereitung; kein Commit, Push, Tag oder GitHub-Release.

## Git-Inventur

### A — Anwendung

- `cmdrhelper/bounty_manager.py`
- `cmdrhelper/database.py`
- `cmdrhelper/help_content/de.py`
- `cmdrhelper/help_content/el.py`
- `cmdrhelper/help_content/en.py`
- `cmdrhelper/help_content/es.py`
- `cmdrhelper/help_content/fi.py`
- `cmdrhelper/help_content/fr.py`
- `cmdrhelper/help_content/it.py`
- `cmdrhelper/help_content/nl.py`
- `cmdrhelper/help_content/no.py`
- `cmdrhelper/help_content/pl.py`
- `cmdrhelper/help_content/sv.py`
- `cmdrhelper/help_content/tr.py`
- `cmdrhelper/i18n/de.py`
- `cmdrhelper/i18n/el.py`
- `cmdrhelper/i18n/en.py`
- `cmdrhelper/i18n/es.py`
- `cmdrhelper/i18n/fi.py`
- `cmdrhelper/i18n/fr.py`
- `cmdrhelper/i18n/it.py`
- `cmdrhelper/i18n/nl.py`
- `cmdrhelper/i18n/no.py`
- `cmdrhelper/i18n/pl.py`
- `cmdrhelper/i18n/sv.py`
- `cmdrhelper/i18n/tr.py`
- `cmdrhelper/journal_catchup.py`
- `cmdrhelper/journal_reader.py`
- `cmdrhelper/journal_watcher.py`
- `cmdrhelper/mission_manager.py`
- `cmdrhelper/release_summaries.py`
- `cmdrhelper/state.py`
- `cmdrhelper/ui/commander_view.py`
- `cmdrhelper/ui/main_window.py`
- `cmdrhelper/version.py`
- `cmdrhelper/commodities.py`
- `cmdrhelper/mission_persistence.py`
- `cmdrhelper/ui/bounty_view.py`

### B — Tests und Dokumentation

- `README.md`
- `README_DE.md`
- `README_EL.md`
- `README_ES.md`
- `README_FI.md`
- `README_FR.md`
- `README_IT.md`
- `README_NL.md`
- `README_NO.md`
- `README_PL.md`
- `README_SV.md`
- `README_TR.md`
- `tests/test_biology_persistence.py`
- `tests/test_body_snapshot_preservation.py`
- `tests/test_commander_journal_delta.py`
- `tests/test_commander_persistent_state.py`
- `tests/test_context_help.py`
- `tests/test_mapping_metadata.py`
- `tests/test_mission_id_persistence.py`
- `tests/test_performance_round2.py`
- `tests/test_screenshot_multi_commander.py`
- `tests/test_startup_pipeline.py`
- `RELEASE_CHECK_3.6.1.md`
- `docs/current-missions.md`
- `docs/live-bounties.md`
- `docs/release-3.6.1.md`
- `tests/test_bounties.py`
- `tests/test_current_missions.py`
- `tests/test_encounter_missions.py`
- `tools/check_mission_cleanup.py`

- C: ignorierte `data/`-Datenbanken samt Sicherungen und Sidecars, Favoriten und `logs/`; externe QSettings und Bounty-JSON. Nicht veröffentlichen.
- D: ignorierte `backup/`, `venv/`, Python-Caches, `texture_test.py` und lokale `release/`-Builds. Temporäre Prüfskripte und Protokolle liegen außerhalb des Repositorys. Nicht als Quelländerungen veröffentlichen. Das geprüfte 3.6.1-ZIP ist ausschließlich das spätere Releaseasset.
- E: keine verdächtigen nicht ignorierten Änderungen gefunden.

Nur A/B sind für einen späteren Quellcommit vorgesehen. Das Kopier-Prüfwerkzeug
`tools/check_mission_cleanup.py` zählt zu B; es wird nicht ausgeführt oder ins ZIP
aufgenommen. Historisch bereits versionierte Releaseartefakte bleiben unverändert.

## Version und Freeze

Zentrale Version 3.6.1. Oberfläche, Einstellungen, Diagnose, Updater,
HTTP-User-Agent und API-Metadaten importieren diese Quelle; lokale Releasewerkzeuge
lesen dieselbe Datei. Historische 3.6-Releasehinweise bleiben unverändert.
Keine Ingenieur-Funktion oder sonstige Erweiterung außerhalb des festgelegten
Entwicklungsstands. Zusätzliche Releasekorrektur: reale FID in der bestehenden
Screenshot-Hilfe und Testbeispielen durch eine fiktive Kennung ersetzt.

## Fachliche Prüfung

- Kopfgelder: Live-Bounty, mehrere Rewards/Fraktionen, atomare Speicherung mittels
  flush/fsync/os.replace, FID-Trennung, Neustart, Journalanker, Catch-up ausschließlich
  im aktuellen Journal und Schutz vor Doppelzählung geprüft. RedeemVoucher(bounty)
  und Died setzen zurück; SRVDestroyed nicht. Manueller Reset benötigt Bestätigung
  und setzt den sicheren neuen Journalanker. Keine historischen Journalimporte
  und kein zusätzlicher Timer/Poller; Anbindung an den bestehenden Watcher.
- Encounter: ReceiveText erzeugt sofort sichtbares, persistentes und FID-getrenntes
  Pending. MissionAccepted, Missions.Active und CargoDepot bestätigen eindeutig
  zu einer echten MissionID mit genau einer normalen Mission und entferntem Pending.
  Matching berücksichtigt Ware, Menge, Station, System, Reward und Zeit; Konflikte
  und Mehrdeutigkeiten werden abgewiesen. Pending-Reward zählt nicht zur bestätigten
  Summe. 24-h-TTL läuft an bestehenden Lade-/Verarbeitungsanlässen.
- Missionspersistenz: Accepted öffnet; Redirected und CargoDepot aktualisieren.
  Completed/Failed/Abandoned entfernen ausschließlich die betroffene aktuelle
  Missionszeile. Alte Ereignisse können neueren Bestand nicht zurücksetzen.
  Missions.Complete bleibt erhalten, inactive wird konservativ gespeichert.
  Odyssey, Materialien, Mining und INARA erhalten weiterhin die Ereignisse.
- Chronik basiert auf Besuchen, Scans und ihren eigenen Daten; keine Abhängigkeit
  vom alten commander_missions-Abschlussarchiv. Commander → Missionen fragt nur
  offene Zeilen ab. Kein produktiver Aufruf des separaten Bereinigungswerkzeugs.
- Schema bleibt 20; keine neue strukturelle Migration.

## Produktive Daten

Der Benutzer bestätigte zunächst einen parallel laufenden Helper und schloss ihn
anschließend. Daher war der anfängliche Dateihash der gesamten DB nicht stabil.
Der separate Vergleich der vollständigen historischen Missionszeilen blieb gleich:
131 Abschlusszeilen (121 completed, 8 failed, 2 abandoned) plus 7 inactive.
Nach dem Schließen wurde zusätzlich ein Dateihash als Abschlussreferenz erfasst.
Die Releasevorbereitung öffnet die produktive DB ausschließlich immutable/read-only;
Startproben verwenden entpackte Pakete mit isolierter leerer DB und Qt-Einstellungen.
Keine automatische Altbereinigung beim Update auf 3.6.1.

## Sprachen und Dokumentation

Referenz DE/EN: **1.585 Schlüssel**. Alle neuen Kopfgeld-/Encounter- und sechs
Release-Schlüssel sind in DE EN EL ES FI FR IT NL NO PL SV TR vorhanden, nicht leer
und mit übereinstimmenden Platzhaltern. Explizite Kataloggrößen:
DE/EN/IT 1.585; ES/FR 1.574; EL/FI/NL/NO/PL/SV/TR 1.463.
Die Differenzen sind ausschließlich bestehende Materialnamen mit englischem
Fallback (11 beziehungsweise 122), keine neuen Übersetzungslücken.

README: in jeder Sprache nur einen 3.6.1-Abschnitt ergänzt. Entfernt man diesen
Abschnitt rechnerisch, entspricht die Datei bytegenau dem bisherigen Git-Inhalt.
Damit bleiben KI-Hinweis und historische 3.6-Abschnitte unverändert.
`docs/release-3.6.1.md` hält den freigegebenen Umfang fest. Lokale Analyseergebnisse
zu einer früher geprüften produktiven Kopie wurden aus der neuen Missionsdokumentation
entfernt; dieser Prüfbericht wird nicht ins Anwendungspaket aufgenommen.

## Publisher und Paket

Unveränderter offizieller Mechanismus: `release_summaries.py` und zwölf vorhandene
Sprachkataloge. Lokaler Notes-Dry-Run über `tools.publish_release.release_notes`
erzeugt sechs deutsche Punkte und den Metadatenblock für alle zwölf Sprachen.
Der Publisher hat keinen CLI-Dry-Run-Schalter. Seine echten Notes-/ZIP-Funktionen
werden lokal geprüft; die reguläre Suite simuliert seine Veröffentlichungsschritte
mit abgefangenen Remote-Operationen in isolierten temporären Testrepositorys.
Keine Veröffentlichung im Projekt. `github.sh`, `tools/publish_release.py`,
`create_release.sh` und Releaseworkflow bleiben unverändert.

Build: `bash create_release.sh`; ZIP-Integrität und offizielle Publisher-Prüfung
`validate_zip` erfolgreich. Alle Paketdateien bytegenau gegen den Quellstand geprüft.
BountyManager/BountyView sowie Commodity-, Encounter-/Journal- und Missionsmodule
sind enthalten, ebenso alle zwölf Sprachkataloge und READMEs.
`data/` enthält ausschließlich die leere `.gitkeep`.
Keine Bounty-JSON, Spansh-Caches, QSettings, reale DB, Journale, persönlichen Bilder,
Tests, Tools oder Analyseartefakte im ZIP. Alle enthaltenen Pythonmodule syntaktisch
gültig. Entpackter Start über den unveränderten main.py-Einstieg erfolgreich;
Fenstertitel, Einstellungen, Diagnose und Kopfgeldansicht geprüft. Qt offscreen,
leere isolierte DB, isolierte QSettings, keine echten Journale, Updatecheck deaktiviert.
Kein nativer Windows-GUI-Lauf.

## Endergebnis

Vollständige reguläre Suite: `QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest discover -s tests -v`.

**1807 bestanden, 0 fehlgeschlagen, 0 Fehler, 0 übersprungen; 539.247 Sekunden.**
Keine Tests ausgeschlossen. Der erste Vorlauf wurde wegen der gefundenen
FID-Anonymisierung beendet; danach lief die gesamte Suite auf dem finalen Stand
vollständig erneut.

`git diff --check` ohne Befund; alle elf unversionierten Dateien zusätzlich mit
`git diff --no-index --check` geprüft. Keine neuen Debugprints, persönlichen
Pfadkonstanten, Testfixtures im Produktcode oder temporären Analyseartefakte.
Vorhandene Beispielkennungen in der Hilfe sind nun fiktiv.

Paket: `release/CMDRHelper_v3.6.1.zip`, **183,696,604 Bytes**
(**175.19 MiB**), 360 Dateien.
SHA-256: `ef8a252ab8aabec4ddb6d9dd5920b6b39747a7137f94646060216a5afca38b71`.

Abschließender Dateihash der geschlossenen produktiven DB unverändert;
alle 138 historischen/inaktiven Missionszeilen feldgleich. Keine Bereinigung.

Keine verbleibenden nachgewiesenen Releaseblocker. Prüflimit: kein nativer
Windows-GUI-Test; bestehende Materialnamen-Fallbacks bleiben erhalten.
Feature Freeze gilt. Kein Commit, Push, Tag oder GitHub-Release im Projekt.

CMDRHelper 3.6.1 ist releasebereit.
