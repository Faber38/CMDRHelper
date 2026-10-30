# CMDRHelper v3.9.22

- Schnellere Ansichten durch Zwischenspeicherung von Journalquellen, Favoritenbildern und Planetengrafiken.
- Reine Sprünge lösen keine unnötigen Inventarrekonstruktionen mehr aus; historische Materialwarnungen werden zusammengefasst.
- Neue Systempositionen und EDSM-Statusprüfungen warten nicht mehr auf langsame Uploads.
- Robustere Cursorsteuerung beim Schließen und Neuerstellen von Fenstern.
- 20 und 30 Ly stehen zusätzlich in vier Handelsansichten zur Auswahl; der Standard bleibt 100 Ly.
- „Markt ansehen“ kann nach bestätigter Schiffsfracht filtern. Bei unbekanntem oder veraltetem Bestand pausiert der Filter sichtbar.

## Umfang

Der Journalquellen-Cache vermeidet wiederholte Statistikabfragen. Favoritenbilder
werden im RAM wiederverwendet; Planetengrafiken nutzen einen verbesserten Qt-Bildcache.
Die tatsächliche Reaktionszeit hängt von Datenbestand und Umgebung ab.

Die Inventarinvalidierung unterscheidet Material-, Mining- und Odyssey-Daten.
Erforderliche Aktualisierungen bei Inventarereignissen, historischen Ergänzungen,
Quellen- und Commanderwechseln bleiben erhalten. Die Materialvalidierung wird
weiterhin vollständig ausgeführt; nur identische historische Diagnosewiederholungen
werden begrenzt zusammengefasst. Bestandsberechnung und Datenbankschema bleiben
unverändert.

Die lokale Position wird nach erfolgreicher Journalverarbeitung veröffentlicht,
bevor externe Übertragungen abgeschlossen sind. EDSM-Statusprüfungen können früher
beginnen; EDSM- und Inara-Uploads behalten ihre Verarbeitung und Fehlerbehandlung.
Die Cursorsteuerung prüft die Gültigkeit von Qt-Widgets vor weiteren Zugriffen.
Eine Behebung sämtlicher zuvor unter Windows gemeldeter Fehler ist damit nicht belegt.

Der neue Marktfilter verwendet ausschließlich bestätigte aktuelle Schiffsfracht.
SRV- und Carrier-Fracht werden nicht berücksichtigt. Ein bestätigter leerer
Frachtraum liefert keine Treffer; bei unbekanntem, veraltetem oder widersprüchlichem
Bestand pausiert nur dieser Filter mit sichtbarem Hinweis. Die Auswahl bleibt
erhalten. Gemeinsam mit „Nur Bergbaurohstoffe“ wird die Schnittmenge angezeigt.
Bestehende Entfernungswerte und gespeicherte Einstellungen bleiben erhalten.

## Testinfrastruktur

Material-Testfenster werden nach Workerabschluss kontrolliert im GUI-Thread
freigegeben, einschließlich ausstehender DeferredDelete-Ereignisse. Der betroffene
Quellenwechsel-Test wartet auf die tatsächlich verarbeitete neue Journalsitzung,
mit einem Timeout von 20 Sekunden. Bestehende fachliche Assertions bleiben erhalten.

## Abschlussprüfungen und bekannte Einschränkungen

Die gezielten Offscreen-Prüfungen umfassten 535 Tests: 533 bestanden, zwei bereits
vorhandene Opt-in-Tests für externe Referenzdatenbanken wurden mangels dieser
Daten nicht ausgeführt. Geprüft wurden Cursor und Bildcaches, Quellen und
Inventarinvalidierung, Materialdiagnose, Schiffsfrachtfilter, Handelsansichten,
EDSM-/Inara-Verarbeitung, Updatefenster, Paketierung und Publisher. Bestehende
Tests oder Assertions wurden für diese Veröffentlichung nicht verändert.

Die zuvor sporadisch fehlgeschlagene Transferzählungs-Assertion bestand in der
aktuellen Upload-/Statusgruppe mit 117 Tests. Ein einzelner erfolgreicher Lauf
beweist nicht, dass ein zeitabhängiger Testfehler grundsätzlich ausgeschlossen ist.
Die Quellenwechsel-Korrektur bestand zuvor 20 isolierte und zehn Gruppenläufe.
Die abschließenden gezielten Qt-Stressläufe bestanden zuvor unter Offscreen und
X11 jeweils 28 Tests einschließlich eines bestehenden Opt-in-Skips, ohne nativen
Absturz. Die erneute Releaseprüfung unter echtem X11 bestand zehn Cursor- und
Lebensdauertests; die bekannte Hover-Assertion scheiterte erneut. Sie erwartet
unmittelbar die Hoverfarbe, erhielt hier jedoch die normale Zeilenfarbe. Dasselbe
Verhalten wurde bereits mit unveränderten Ausgangstests beobachtet. Es wird
nicht durch eine abgeschwächte Assertion verdeckt.

Die Updatehinweise wurden in allen zwölf Sprachen und beiden Themes unter
Offscreen und echtem X11 geprüft (je 24 Kombinationen). Die Sprachprüfung bestand
mit 2.342 Referenzschlüsseln, gültigen Platzhaltern und ohne doppelte Schlüssel.
Python-Syntax für 601 Dateien, Imports der 26 zuvor geänderten Produktmodule und
`git diff --check` waren erfolgreich. Ältere Release-Metadaten bleiben erhalten.

Umgebung: Linux, Python 3.12.3, PySide6/Qt 6.11.2. Netzwerkantworten der
Uploadtests sind kontrolliert; keine unnötigen echten EDSM-/Inara-Anfragen.
Keine native Windows- oder Live-Spiel-Prüfung und kein vollständiger projektweiter
Testsuitenlauf. Eine Behebung sämtlicher Windows-Cursorfehler wird nicht behauptet.
Die zwei lokalen Benchmark-JSON-Dateien wurden vor dem Release entfernt; die
bestehenden Prüfungen gegen unerwartete Paketdateien bleiben unverändert aktiv.
