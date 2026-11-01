# Entfernung der technischen Hauptfenster-Fußzeile

Stand: 31.10.2026. Implementierung im unveröffentlichten Arbeitsbaum; Release-Metadaten bleiben auf dem bisherigen Stand. Keine Veröffentlichung.

## Ergebnis und Umfang

Die beiden Aufrufe, die bisher bei Hotkey- oder Startproblemen eine `QStatusBar` erzeugten, sind entfernt. Es wird keine leere oder versteckte Ersatzleiste angelegt. Die Verbindung vom Hotkey-Änderungssignal zum Leeren der Statusleiste und die unbenutzten Statusleisten-Regeln beider Themes sind entfernt. Hauptfensterlayout und Geometriespeicherung wurden nicht geändert.

Separate Start-, Migrations- und Fehlerdialoge bleiben bestehen. Historische Teilfehler und vorübergehende Quellenfehler hinterlassen keine dauerhafte Hauptfensteranzeige. Ein handlungsbedürftiger Startfehler bleibt im vorhandenen Fortschritts-/Fehlerdialog sichtbar, mit beendeter Animation und Schließen-Schaltfläche. Fehlt dieser Dialog, verwendet der bestehende Warnungsdialog denselben verständlichen Hinweis. Technische Fehlerstrings werden dabei nicht mehr interpoliert.

## Geänderte Dateien und Funktionen

| Datei | Änderung |
| --- | --- |
| `cmdrhelper/ui/main_window.py` | `__init__`: Hotkey laden ohne Statusleiste; `_initialization_finished`: anhand des tatsächlichen Quellenfehlers entscheiden, ob der vorhandene Dialog sichtbar bleibt. Backup-Abschluss unverändert aufrufen. |
| `cmdrhelper/ui/startup_progress.py` | Zeilenumbruch für den längeren verständlichen Fehlerhinweis. |
| `cmdrhelper/ui/styles.py` | Unbenutzte `QStatusBar`-Regeln in beiden Themes entfernen. |
| `cmdrhelper/source_manager.py` | `_record_failure`: datenschutzgerechte Fehlerdiagnose mit Wiederholungsunterdrückung pro Quellenlaufzeit; Worker erfasst Fehler; `_finish_startup_source` aggregiert handlungsbedürftige Fehler aller initialen Quellen. |
| `cmdrhelper/startup_runtime.py` | `diagnostic` unterstützt sichere Quellenreferenz und optionalen Exception-Traceback; `issue` unterdrückt wiederholte inhaltsgleiche Komponenten-Zusammenfassungen ohne zusätzliche Exception. |
| `cmdrhelper/logging_config.py` | Bestehende Positivlisten um die benötigten Komponenten und Fehlergründe erweitern. |
| `cmdrhelper/global_hotkey.py` | `set_hotkey`: Registrierungsfehler über vorhandene Diagnoseprotokollierung erfassen; identische Wiederholungen bis zur Erholung unterdrücken. |
| Alle zwölf `cmdrhelper/i18n/*.py`-Sprachkataloge | Ausschließlich neuen Schlüssel `startup.action_required` anhängen. Bestehende Marktübersetzungen bleiben erhalten. |
| `tests/test_source_startup.py`, `tests/test_startup_resilience.py` | Geänderte Anzeigeverträge prüfen; Statusleiste nicht durch den Test selbst erzeugen. |
| `tests/test_footer_removal.py` | Neun neue Regressionstests mit synthetischen Quellen, echten Reparaturfehlern und tatsächlichem Diagnoseexport. |

## Fehlerklassifikation und Bestandsschutz

`critical` allein steuert die Anzeige ausdrücklich nicht: Der bestehende technische Startstatus kann auch nach einem erfolgreichen Hintergrund-Retry noch `critical` sein. Diesen Status, die ursprüngliche Fehlermeldung und die konservative Backup-Sperre ändert diese Arbeit nicht.

Nur tatsächliche `JournalPending`-Exceptions mit `journal_changed_during_read`, `partial_final_line`, `catchup_budget` oder `journal_identity_changed` werden als vorübergehende, durch die vorhandenen Watcher-/Quellentimer erneut versuchte Startprobleme behandelt. Ein gleichlautender Text in einer anderen Exception genügt nicht. Präfixkonflikte, ersetzte/gekürzte Journale, Zugriffs-, SQLite- und unbekannte Fehler bleiben handlungsbedürftig. Die Entscheidung berücksichtigt alle initialen Quellen; ein früher vorübergehender Fehler darf einen späteren kritischen Fehler nicht verdecken.

Die Startabschlussfunktion und ihre Einmaligkeit bleiben erhalten. Ebenso unverändert: Verarbeitung, Commit-/Publikationsgrenzen, automatische Retries, historische Reparaturen, Uploads, Commander-/FID-Zuordnung, Hotkey-Einstellungen und Backup-Bereinigungsvoraussetzungen. Es gibt keine neue Meldungsarchitektur und keine Änderung an Markt-, Fracht- oder Inventarberechnungen.

## Diagnose und Datenschutz

Neue Quellen-Diagnosen enthalten erlaubten Fehlergrund, Status, Exception-Typ, gegebenenfalls Betriebssystem-/SQLite-Fehlernummer und eine SHA-256-Quellenreferenz statt des persönlichen Pfads. Der vorhandene `PrivacyFormatter` entfernt Exception-Payloads und persönliche Pfade aus Tracebacks. Unbekannte freie Fehlertexte werden nicht ungeprüft als Grund übernommen. Die Quellenreferenz ist pseudonymisiert, nicht als kryptografische Anonymitätsgarantie zu verstehen.

Hotkey-Fehler erhalten `component=hotkey` und `reason=hotkey_registration_failed`. Die Tastenkombination und rohe Backend-Fehlermeldung werden nicht protokolliert. Identische neue Quellen-/Hotkey-Diagnosen werden innerhalb einer fortdauernden Fehlerepisode einmal ausgegeben; nach Erfolg kann ein erneuter Fehler wieder protokolliert werden. Bereits bestehende Watcher- und Reparaturdiagnosen bleiben unverändert. Die Unterdrückung ist kein globaler Logfilter und überlebt keinen Programmneustart.

Tatsächlich erzeugte und anschließend entpackt geprüfte Testarchive:

- `/tmp/cmdr-footer-implementation/x11/verified-diagnostics.zip`
- `/tmp/cmdr-footer-implementation/x11/retry-diagnostics.zip`
- Entsprechende Archive unter `/tmp/cmdr-footer-implementation/offscreen/`.

Das erste Archiv enthält `cmdrhelper.log`, `system_info.json`, `diagnose_summary.txt` und `odyssey_display_diagnostics.json`. Nachgewiesen sind Quellenfehlergrund, `PermissionError` mit `errno=13`, Hotkey-Registrierungsfehler sowie `repair_json_syntax` mit Quellenreferenz und Zeile 3 aus einem tatsächlich fehlgeschlagenen historischen Reparaturlauf. Das zweite Archiv enthält den Fehlergrund aus dem echten Quellenworker-Retry-Test. In sämtlichen Archivmitgliedern fehlen die gezielt eingebrachten privaten Namen, FIDs, Pfade, Journal-Payloads und die Hotkey-Kombination. Zehn identische Hotkey-Fehlversuche erzeugen genau einen neuen Diagnoseeintrag; nach Erholung ist eine erneute Meldung zulässig.

## Tests und Ergebnisse

| Lauf | Ergebnis |
| --- | --- |
| Bestehende Start-, Resilienz-, Hotkey-, Reparatur- und Diagnosetests, offscreen | 91 bestanden, 39,276 s |
| Neue Fußzeilentests, offscreen | 9 bestanden, 6,657 s |
| Ergänzende finale Offscreen-Suite inklusive Popup-, Diagnose-, Hotkey- und Backup-/Migrationstests | 99 bestanden, 68,365 s |
| Breite X11-Suite mit Quellenverarbeitung, Publikation, Transfers und den Marktregressionen | 223 von 224 bestanden, 162,463 s; Ausnahme unten erläutert |
| Abschließender X11-Lauf mit den neun Fußzeilentests und isoliertem Migrationstest | Alle neun Fußzeilentests bestanden; Migrationstest erneut gesperrt, insgesamt 7,925 s |
| Sprachprüfung | Zwölf Sprachen, 2349 Referenzschlüssel; keine fehlenden Schlüssel, Platzhalterabweichungen oder Duplikate |
| Syntaxprüfung und `git diff --check` | Bestanden |
| Produktsuche nach `statusBar(` und `QStatusBar` | Keine Fundstellen |

Die X11-Ausnahme ist `test_full_dialog_worker_success_and_reopen_gate`: Der vorhandene Migrationsschutz erkennt tatsächlich laufende Elite-Prozesse und bricht vor der Migration mit `MigrationError('active')` ab. Eine separate Prüfung außerhalb der Sandbox fand zwei Prozesse mit erkanntem Namen `elitedangerous64.exe`. Der Fehler reproduziert sich isoliert und kommt bereits aus der unveränderten Prozessprüfung, nicht aus dem geänderten Startabschluss. Dieser Schutz wurde weder abgeschaltet noch der Test umgeschrieben. Unter offscreen innerhalb der Sandbox besteht der Test. Ein vollständiger grüner X11-Gesamtlauf ist daher nicht belegt.

Die neuen Tests prüfen Normalstart, automatischen Retry bis zur wieder bereiten Quelle, genau ein Abschlusssignal, gestoppte Animation, sichtbaren kritischen Dialog, historische Teilfehler, Backup-Sperre, Fehlertypklassifikation, Diagnoseexport, Datenschutz und Wiederholungsunterdrückung. Der Hauptfenstertest prüft beide Themes, vier Menübereiche, fehlende Statusleiste und konstante Geometrie bei 1400 × 1000. Unbeteiligte Hauptfensterdienste sind dabei durch die vorhandene GUI-Testfixture ersetzt. Es ist kein ungemockter End-to-End-Lauf mit Benutzerjournalen und kein Windows-Test.

Reproduktion der gezielten Tests (alle Daten sind temporäre synthetische Fixtures):

```sh
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. \
  venv/bin/python -m unittest test_footer_removal
QT_QPA_PLATFORM=xcb PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. \
  venv/bin/python -m unittest test_footer_removal
```

Für dauerhaft abgelegte ZIP-Testartefakte zusätzlich `CMDRHELPER_FOOTER_TEST_ARTIFACTS=/tmp/cmdr-footer-retest` setzen. X11 benötigt Zugriff auf die laufende Displaysitzung.

## Git-Status und Grenzen

Vorher: 15 geänderte versionierte und vier neue Dateien, insgesamt die 19 vorhandenen Marktänderungen. Nachher einschließlich dieses Berichts: 24 geänderte versionierte und sechs neue Dateien. Hinzugekommen sind neun Änderungen an weiteren bestehenden Dateien sowie neuer Test und dieser Bericht. Die zwölf bereits geänderten Sprachkataloge enthalten zusätzlich ausschließlich den neuen Fehlerhinweis.

Der SHA-256-Vergleich bestätigt alle 19 ursprünglichen Dateiinhalte: sieben Dateien sind bytegleich, bei zwölf Sprachkatalogen ergibt das Entfernen des exakt dokumentierten neuen Suffixes wieder den ursprünglichen Hash. Nachweise liegen unter `/tmp/cmdr-footer-implementation/` in `status-before.txt`, `status-after.txt`, `market-before.json`, `translation-additions.json` und `market-preservation.json`; dort liegen auch die Testprotokolle.

Keine Versionsänderung, keine Datenbankmigration, kein Commit, Tag, Push oder Release; `github.sh` wurde nicht ausgeführt. Für später auftretende Hintergrundfehler bleibt die vorhandene Diagnose-/Quellenstatusbehandlung zuständig; es wurde bewusst keine neue allgemeine Alarmierung implementiert. Die vorhandenen Retry-Regeln erhalten auch keine neue zeitliche Eskalationsschwelle. Weitere Änderungen benötigen eine neue Freigabe.
