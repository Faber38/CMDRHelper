# CMDRHelper v3.9.27

- Handelsansichten unterscheiden blaue MissionID-Fracht und rosa mögliche Missionsfracht mit Mengen-Tooltips und kompakten Legenden; Mischfracht zeigt beide Symbole.
- Missionen zeigen benötigte, gelieferte und fehlende Warenmengen, Teamfähigkeit und den Hinweis „Am Missionsziel“. Strukturierte Angaben und WingUpdate-Lieferstände bleiben erhalten; vollständige Lieferungen erinnern an die Belohnung.
- Favoritennotizen bewahren Zeilenumbrüche und Leerzeilen und werden als Plain Text bearbeitet. Vollständige Favoritennamen erscheinen als Tooltip.
- Besonderer Dank an CMDR Nanjan mit goldfarbenem Commander-Namen; bestehende Danksagungen bleiben erhalten. Neue Texte sind in allen zwölf Sprachen verfügbar.

## Vollständiger Änderungsumfang seit v3.9.26

Ausgangspunkt: main, Commit 805a9a35758fc1279608f25aaf69eacff816434d (Tag v3.9.26).
Vor der Releasevorbereitung: 28 modifizierte und sieben neue Dateien, keine
zusätzlichen Commits. Alle vorhandenen Produktänderungen werden übernommen.

- Fracht: Cargo-Normalisierung bewahrt explizite MissionID-Mengen. Das neue
  `ui/mission_cargo.py` berechnet blaue und rosa Kennzeichnungen, gemeinsame
  verfügbare Mengen ohne Doppelzählung und übersetzte Tooltips. Ohne auswertbare
  offene Warenmission entfällt die zusätzliche Prüfung für rosa Markierungen.
- Handel: `trade_view.py` und `saved_markets_view.py` ergänzen Symbole und
  Legenden sowie Aktualisierungen bei Fracht-, Missions- und Kontextänderungen.
  Reine Kennzeichnungsänderungen erhalten laufende Verkaufssuchen und Auswahl.
  Handelsfilter bleiben bestehen.
- Missionen: `models.py`, `journal_reader.py`, `mission_manager.py`,
  `mission_persistence.py` und `database.py` übernehmen strukturierte Warenmengen,
  Warenart, Teamfähigkeit und kumulative Depotstände einschließlich WingUpdate.
  Persistenz erfolgt transaktional in vorhandenen app_meta-Einträgen; Schema 23
  bleibt unverändert. Spärliche Snapshots erhalten bekannte Fakten; terminale
  Ereignisse entfernen zugehörige Zusatzdaten.
- Missionsoberfläche: `main_window.py`, `ui/mission_arrival.py` und das neue
  `ui/mission_legend.py` zeigen Mengen, Teamkennzeichnung, Zielhinweis,
  Lieferabschluss und kompakte Farb-/Symbolerklärungen in beiden Themes.
- Favoriten: `favorites.py` erhält Notiz-Whitespace; `ui/favorites_view.py`
  lädt Notizen ausdrücklich als Plain Text und zeigt vollständige, HTML-escaped
  Namen als Tooltip. Namensverarbeitung und Favoritenzuordnung bleiben erhalten.
- Über-Dialog: `ui/about_dialog.py` ergänzt die besondere Danksagung mit
  goldenem Namen für CMDR Nanjan; die bisherigen Unterstützer bleiben genannt.
- Alle zwölf Sprachkataloge enthalten die neuen Produkttexte.
- `docs/current-missions.md` beschreibt Persistenz, Fortschritt und mögliche
  Missionsfracht einschließlich ihrer Grenzen. `tools/check_mission_cleanup.py`
  berücksichtigt Zusatzdaten ausschließlich der tatsächlich bereinigten
  terminalen Missionszeilen auf einer ausdrücklich erstellten Datenbankkopie.
- Tests: neue Dateien für MissionID-Fracht, mögliche Missionsfracht,
  Missionsfortschritt, Favoritennotizen und Namen-Tooltips; erweiterter About-Test.
- Releasepflege: zentrale Version 3.9.27, lokalisierte Kurztexte und Eintrag in
  `release_summaries.py`, Versionshistorie in allen zwölf READMEs und diese Datei.

Keine nicht zugeordnete Änderung gefunden. Die beiden neuen Produktmodule werden
rekursiv paketiert; ihre Symbole werden gezeichnet und benötigen keine zusätzlichen
Bilddateien. Bereits veröffentlichte Releasehinweise bleiben byteidentisch.

## Prüfungsnachweise und Grenzen

Vorhandene lokale Protokolle vom 05.11.2026: 37 Handels-Kerntests und 33 Markttests
bestanden. Die Protokolle entstanden nach den betreffenden Produktänderungen;
ein kryptografischer Quellstand ist darin nicht hinterlegt. Sprach-/Layoutläufe
für zwölf Sprachen liegen ebenfalls vor. Ein unvollständiges weiteres
Handelsprotokoll wird nicht als bestandener Lauf gezählt. Die vom Auftraggeber
berichteten umfangreichen Entwicklungsprüfungen werden nicht vollständig wiederholt.

Neue gezielte Linux/offscreen-Prüfungen: 30 Tests zu Favoriten, Missionsfortschritt
und About-Dialog sowie 23 Tests zu expliziter und möglicher Missionsfracht bestanden.
Sprachprüfung: 2.424 Schlüssel in zwölf Sprachen, passende Platzhalter und keine
Duplikate. Syntax, Imports betroffener Produktmodule und Release-Sprachmetadaten
werden geprüft; git diff --check ist Bestandteil der Abschlussprüfung.

Unbekannte Lieferstände bleiben unbekannt. Rosa Fracht bedeutet keine Zusage,
dass Elite die Ware annimmt; der dokumentierte Silber-Praxistest ist kein
allgemeiner Nachweis für jede Abbaumission. Teamfähigkeit bedeutet nicht, dass
andere Commander teilnehmen. Alte Missionen erhalten keine erfundenen Details
und keine automatische historische Rekonstruktion. Linux/offscreen ersetzt
keinen nativen Windows-Praxistest. Frühere, in v3.9.26 dokumentierte Testgrenzen
werden nicht als behoben behauptet.

Der Publisher baut nach persönlicher Bestätigung ausschließlich über github.sh
nochmals aus dem finalen Commit. Die normalisierte finale ZIP-Prüfsumme wird
anschließend mit dem GitHub-Asset verglichen; eine Probebuild-Prüfsumme ist nicht
die finale Releaseprüfsumme.

## Abgeschlossene Paket- und Smoke-Prüfung

- Syntax von 641 Python-Dateien und Imports von 29 betroffenen Produktmodulen
  bestanden; Release-Sprachblock und unveränderte historische Notes geprüft.
- Paketierter MainWindow-Start mit echtem AppState unter Linux/offscreen:
  Initialisierung erfolgreich, Fenster sichtbar, reguläres Beenden erfolgreich.
  Einstellungen, Datenbank und XDG-Verzeichnisse lagen isoliert unter /tmp;
  Journalerkennung, Prozessabfrage, Stationsabruf und Updateabfrage waren ersetzt.
  Ein erster Versuch hatte XDG_DATA_HOME noch nicht isoliert und meldete einen
  vom Sandbox-Dateisystem abgewiesenen Marktpfad; der korrigierte Lauf bestand.
- Echter Updater aus dem v3.9.26-Paket installiert das vollständige v3.9.27-ZIP
  ausschließlich in einem temporären Verzeichnis: Entpacken, Backup, Kopieren
  und echte Versionsprüfung bestanden. Alle ausgelieferten Programmdateien
  stimmen bytegenau überein. Synthetische Datenbank und Einstellungen bleiben
  byteidentisch; integrity_check und Fremdschlüsselprüfung bestanden.
  Interpreterbindung, Prozesswarten, Abhängigkeitsinstallation und Neustart
  waren im Update-Smoke kontrolliert ersetzt. Die beiden Quell-ZIPs im
  produktiven release-Verzeichnis blieben nachweislich unverändert.
- Vollständiger Probebuild mit unverändertem create_release.sh; Integrität,
  bytegenauer Paketvergleich, neue Produktmodule und Ausschlussregeln geprüft.
  Persönliche Daten, Testskripte und lokale Prüfprotokolle sind nicht enthalten.
