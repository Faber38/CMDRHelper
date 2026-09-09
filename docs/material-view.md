# Materialansicht

Die Seite `MaterialView` ist im Hauptfenster als zusätzlicher Hauptbereich angehängt.
Die bisherigen Seitenindizes 0–8 einschließlich CMDR Ansicht (7) und Einstellungen
(8) bleiben unverändert; Materialien erhält Index 9. Schiffe bleiben in der CMDR Ansicht.

## Darstellung

Drei Engineering-Reiter zeigen Raw (28), Manufactured (71) und Encoded (47).
Der vierte Reiter enthält [Odyssey](odyssey-view.md). Die Liste enthält
alle 146 Definitionen einschließlich Guardian/Thargoid. Zeilen sind nach Grad 1–5
und anschließend „Grad unbekannt“ gruppiert; innerhalb jeder Gruppe werden die
lokalisierten Namen mit `QCollator` alphabetisch sortiert. Name, Grad,
Bestand/Maximum und ein dezenter horizontaler Prozentbalken bleiben kompakt.
Die Liste wächst mit dem Fenster und bietet Scrollleisten. Alle vier Spalten
können am Header in Breite und Reihenfolge angepasst werden. Dark und Light verwenden die
bestehenden globalen Stylesheets und dazu passende Balken-/Hervorhebungsfarben.

Suche berücksichtigt lokalisierten und englischen Namen; Filter verwenden direkt
`CatalogStock.fill_state` aus Phase 2. Beide sind kombinierbar. Unbekannter Bestand
oder unbekanntes Maximum erzeugt keinen Balken/Prozentwert und erscheint nur unter
„Alle“. Fehlende Bestände werden ausschließlich durch `merge_inventory()` zu 0,
wenn ein zuverlässiger vollständiger Commanderbestand vorliegt. Ein oberhalb des
Maximums liegender Journalwert wird numerisch unverändert angezeigt; allein die
gezeichnete Balkenlänge ist auf die verfügbare Breite begrenzt.

`materials/category` und `materials/filter` speichern nur die UI-Auswahl in
QSettings. Es werden keine Materialbestände oder Journalsignaturen dort abgelegt.

## Gemeinsame Spaltenkonfiguration

`materials/columns` speichert Breiten nach logischer Spalte und die visuelle
Reihenfolge gemeinsam für alle drei Reiter. Der opt-in-Mechanismus
`persist_header_layout()` in `ui/table_widths.py` verwendet die bestehende
Breitenvalidierung. Die bisherige reine Breitenpersistenz anderer Tabellen bleibt
unverändert. Alle Spalten sind interaktiv und verschiebbar, einschließlich der
Materialnamenspalte. Fenstergrößenänderungen strecken keine Spalte automatisch;
bei Platzmangel wird horizontal gescrollt.

Version und stabile Spaltenkennungen sichern die Wiederherstellung ab. Beschädigte
Konfigurationen, ungültige Reihenfolgen, Breiten außerhalb 40–2000 Pixel oder eine
geänderte Spaltenstruktur verwerfen die gesamte gespeicherte Konfiguration.
Standard: Materialname / Grad / Bestand / Füllstand mit 320 / 80 / 160 / 160 Pixel.
Unsichtbare Spalten und Qt-interne Resize-/Sortierzustände werden nicht gespeichert.

## Visuelle Zeilenführung

Materialzeilen verwenden fünf sehr dezente, wiederkehrende Hintergrundtöne mit
eigenen Dark-/Light-Paletten. Jeder sichtbare Grad-Block beginnt neu bei Farbe A:
Das erleichtert das erneute Orientieren nach einer Überschrift. Nur Materialzeilen
zählen im Rhythmus; Grad-Überschriften einschließlich „Grad unbekannt“ bleiben frei.

`MaterialRowDelegate` zeichnet die Zellhintergründe mit der festen Priorität
**Auswahl > Live-Sammelhinweis > Hover > Fünfer-Rhythmus**. Eine einzelne ganze
Materialzeile kann per Maus ausgewählt werden; die Auswahl bleibt bei einer
Neuzeichnung erhalten, solange das Material in der Liste bleibt. Grad-Überschriften
sind nicht auswählbar. Hover gilt über alle Spalten; auch über dem Balken erreichen
Mausereignisse die Tabellenzeile. Balkenwerte, Füllfarben und Prozentberechnung
bleiben unverändert. Die Zustände werden nicht in QSettings gespeichert.

## Hintergrundabfrage und Commanderwechsel

`MaterialController` verbindet die Seite mit AppState-Signalen `changed`,
`viewedCommanderChanged`, `commanderIdentityChanged`, `journalIndexReady` und
`databaseImportFinished`. Der normale Journal-Refresh emittiert `changed`; damit
werden alle bereits fachlich unterstützten Materialereignisse erfasst.

Ein Controller hält einen einzigen `MaterialInventoryReader` und einen Threadpool
mit maximal einem gleichzeitig laufenden Job. Kurze Signalfolgen werden über einen
150-ms-Timer zusammengefasst. Während einer laufenden Abfrage wird höchstens eine
weitere Abfrage vorgemerkt. SQLite wird in einem eigenen Read-only-Worker-Handle
geöffnet; Sessions und FID stammen aus der bestehenden DB. Journalzugriff und
Rekonstruktion finden außerhalb des GUI-Threads statt. Worker verändern weder
AppState noch Widgets; Ergebnisse werden über Qt-Signale im GUI-Thread übernommen.

Das Ziel ist `viewed_commander_id`, ansonsten der aktive Commander. Bei einem
Identitätswechsel verschwinden vorherige Werte sofort. Eine Generationsnummer
verhindert die Anzeige verspäteter Worker-Ergebnisse des vorherigen Commanders.
Die Anzeige beginnt mit „Materialbestand wird geladen …“ und unbekannten Werten.
Suchtext und Filter dürfen über den Wechsel erhalten bleiben. Der nächste Job nutzt
denselben Reader-Dateicache, aber die fachliche Rekonstruktion bleibt commanderbezogen.

## Live-Hervorhebung

Nur eine neue positive `MaterialCollected`-Änderung wird vier Sekunden lang an der
betroffenen Zeile als etwa „Vanadium +1“ hervorgehoben. Physische Quellenidentität
und Zeit werden mit dem letzten angezeigten Zustand verglichen. Erstes Laden,
Commanderwechsel und Wiederherstellung eines zuvor unbekannten Bestands erzeugen
keine historische Sammelmeldung. Wiederholtes Einlesen derselben Quelle verlängert
den Hinweis nicht. Verbrauch und andere Änderungstypen erzeugen keinen Sammelhinweis.
Der bisherige `last_change`-Vertrag liefert die letzte Änderung; mehrere Ereignisse
zwischen zwei Abfragen werden mengenmäßig vollständig ausgewertet, aber nicht als
separate Benachrichtigungswarteschlange dargestellt.

## Lokalisierung, Hilfe und Regression

Die statischen Material-UI-Texte sind in allen zwölf Sprachen vorhanden. Materialnamen
verwenden unverändert `localized_name()` aus Phase 2 mit englischem Fallback.
Alle zwölf Hilfesprachen enthalten Materialien, Odyssey und die Materialhändlersuche.
Die goldene Schrift positiver Bestände gehört ausschließlich zur Odyssey-Ansicht;
Engineering verwendet weiterhin die normale Theme-Textfarbe.

`tests/test_material_view.py` prüft Darstellung, Filter, Sortierung, unbekannte
Werte, echte FABER38-Journale (optional, wenn lokal vorhanden), Live-Ereignisse,
Timer-Hervorhebung, verzögerte Worker-Ergebnisse, zwei Commander, Reader-Wiederverwendung,
QSettings und beide Themes. Die portable FABER38-Fixture bleibt ohne private
Journaldateien nutzbar. Navigation und kontextbezogene Hilfe sind zusätzlich durch
`tests/test_context_help.py` und `tests/test_help_translations.py` abgesichert.

Keine Engineering-Planung, kein Zugriff auf surface_mining_materials, keine Änderung
an Rhino-Fundhistorie, Explorer, Frachtraum oder Start-Reparaturen.
