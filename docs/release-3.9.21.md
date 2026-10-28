# CMDRHelper v3.9.21

- Commanderbezogene Screenshot-Verwaltung für Steam und Heroic mit sicherer Zuordnung und verbesserten Dateinamen.
- Klarere Missionsstatus-Farben und automatische Markierung erreichter Missionsziele mit kurzem Blinkeffekt.
- Stabilere Trennung von SRV-, Schiffs- und Carrier-Fracht sowie verbesserte Verarbeitung von Cargo- und MiningRefined-Ereignissen.
- Bis zu zehn Cargo-Snapshots je Fahrzeug- und Quellenkontext; Erfassung auch bei geschlossener Mining-Ansicht.
- Zuletzt bekannte Schiffsbestände bleiben als möglicherweise veraltet sichtbar und werden nicht in Summen eingerechnet.
- Goldgelber Carrier-Bearbeitungsstift und einheitliche Hand-Cursor für anklickbare Elemente.

Screenshot-Quellen werden nach Commander-FID zugeordnet und aus den tatsächlichen Journalquellen für Steam und Heroic abgeleitet. Bei widersprüchlicher Zuordnung werden Originalbilder weder konvertiert noch über „Letzter Screenshot“ in den Favoriten angeboten. Bereits eindeutig zugeordnete Konvertierungen bleiben verfügbar; alte und neue Dateinamen werden unterstützt. Ohne eindeutige laufende Spielinstanz pausiert die Konvertierung. Eine manuell eingetragene, widerspruchsfreie Quelle bleibt eine ausdrückliche Zuordnung durch den Benutzer.

Die Missionsziel-Markierung benötigt verifizierte Ankunftsdaten am passenden Stations- oder Oberflächenziel. Sie verändert keinen gespeicherten Missionsstatus. Drei kurze Blinkimpulse gehen in eine dauerhafte Markierung über; beim Verlassen oder Verlust der verifizierten Zuordnung wird sie entfernt.

Cargo-Snapshots sind an Quelle, FID, Schiffs- und Fahrzeugkontext sowie das konkrete Journalereignis gebunden. Je Kontext bleiben höchstens zehn Versionen erhalten, insgesamt höchstens 32 Snapshot-Kontexte je Commander. Bereits vor der Beobachtung überschriebene Sidecars können nicht nachträglich gesichert werden. Veraltete Schiffsbestände sind ausdrücklich markiert und werden nicht in aktuelle Summen eingerechnet; bei einem unbekannten Teilbestand bleibt die Gesamtsumme unbekannt.

Datenbankschema bleibt 23. Die Releaseprüfung verlangt vor Commit, Push oder Tag gültige Neuerungen in allen zwölf Sprachen. Die Veröffentlichung erfolgt ausschließlich über `github.sh` nach ausdrücklicher Freigabe.

## Prüfungen und Einschränkungen

Die finale Vorbereitung wurde mit Python 3.12.3 und PySide6 6.11.2 geprüft. Der gemeinsame Lauf für Favoriten, Screenshots, Quellenverwaltung, Sichtbarkeit, Missionen, Mining, Carrier-Stift, Cursor und Systemübersicht bestand 429 Tests ohne Fehler oder übersprungene Tests. Ein nativer Qt-Absturz trat dabei nicht auf.

Die separate Release-Prüfung führte 55 Tests aus: 51 bestanden, vier historische Testmethoden scheiterten mit insgesamt 15 fehlgeschlagenen Assertions einschließlich Sprach-Untertests. Davon stammen 14 aus den drei 3.9.19-Testmethoden; der 3.9.20-Test verlangt weiterhin ausdrücklich Version 3.9.20. Publisher-, Paketierungs-, allgemeine Updatefenster- und i18n-Checker-Tests bestanden. Die bestehenden Testdateien wurden nicht geändert.

Die tatsächlichen 3.9.21-Metadaten wurden zusätzlich direkt mit `release_notes()` geprüft: sechs Texte in jeder der zwölf Sprachen, Übereinstimmung mit Sprachkatalogen und README-Abschnitten sowie erfolgreiche Anzeige im Updatefenster in allen 24 Sprach-/Theme-Kombinationen. Ältere Release-Einträge, Übersetzungen und README-Inhalte blieben unverändert. Die Sprachprüfung bestand mit 2.332 Referenzschlüsseln einschließlich ausgewiesener englischer Material-Fallbacks; Platzhalter und doppelte Schlüssel wurden geprüft. Python-Syntax für 588 Dateien und Imports der 33 neuen/geänderten Produktmodule waren erfolgreich. `git diff --check` war ebenfalls erfolgreich.

Automatisierte UI-Prüfungen erfolgen mit Qt offscreen. Eine native Windows-, Desktop- oder Live-Spiel-Prüfung ist nicht erfolgt. Der zuvor gemeldete native Qt-Absturz wurde in den bisherigen gemeinsamen Theme-Läufen nicht reproduziert; seine Ursache ist damit nicht abschließend geklärt.

Der frühere vollständige Testlauf wurde wegen extremer Verlangsamung gemeinsamer Qt-Theme-Tests nach etwa 15 Minuten abgebrochen. Er lieferte keinen erfolgreichen Gesamtnachweis. Unvollständige Settings-Testobjekte beim Fensterschließen und der Bounty-Missionsauswahltest scheiterten bereits auf v3.9.20. Historische Release-Tests vergleichen teilweise die aktuelle Version und aktuelle Kurztexte mit älteren Versionen. Diese Testprobleme werden durch die Metadatenvorbereitung nicht behoben oder durch geänderte Testbedingungen umgangen.

In dieser finalen Vorbereitung wurde die vollständige Testsuite nicht erneut ausgeführt. Die erfolgreichen gezielten Prüfungen ersetzen keinen vollständigen Gesamtnachweis. Es erfolgten kein Commit, Tag, Push oder Release; `github.sh` und der Veröffentlichungsablauf von `publish_release.py` wurden nicht gestartet. Vor der Veröffentlichung sind die verbleibenden Einschränkungen zu bewerten und die ausdrückliche Freigabe einzuholen.
