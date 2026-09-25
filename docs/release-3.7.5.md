# CMDRHelper 3.7.5

Interner Stand für Tests im echten Spielbetrieb, auf Basis von v3.7.0.
Diese Vorbereitung umfasst keine Veröffentlichung, keinen Push und keinen Tag.

## Explorer und EDSM

- Die Explorer-Kopfzeile zeigt den akzeptierten EDSM-Systemstatus des Status-HUDs. Die bestehende HUD-Einstellung steuert die Abfrage; der Status ist keine Aussage über eine Elite-Erstentdeckung.
- Die bestehende EDSM-Ergänzung fehlender Systemkörper bleibt erhalten. EDSM-Sternklassen werden Journal-kompatibel normalisiert, auch beim Einlesen älterer Cacheeinträge: insbesondere T-Braune-Zwerge (`T`) und T-Tauri-Sterne (`TTS`), außerdem L/Y-Zwerge, Herbig-Ae/Be-Sterne, Riesen, Überriesen, Neutronensterne, Schwarze Löcher, Wolf-Rayet-, Kohlenstoffsterne und Weiße Zwerge.
- Die Wertliste zeigt eine aus Journaldaten abgeleitete eigene ERSTBETRETUNG zusätzlich zum Kartierungsstatus.
- First-Footfall berücksichtigt gespeicherte Scanbeobachtungen über Journal- und Spielsitzungsgrenzen; bestätigte Erstbetretungen und ihr ursprünglicher Zeitpunkt bleiben erhalten. Die True-Merge-Korrektur bewahrt einen bereits bestätigten First-Footfall beim Zusammenführen mit aktuellen Körperdaten.
- „An Fensterbreite anpassen“ verteilt die Spaltenbreiten der Wertliste automatisch und speichert die Einstellung.
- Die Wertliste berechnet das Zeilenlayout nach dem Befüllen und Sortieren; wiederholte Größenberechnungen während jedes einzelnen Zelleneintrags entfallen. Der Layoutaufwand wächst damit linear statt quadratisch.

## Übersicht, Hilfe und Tests

- Unter „Übersicht → Letzte Systeme“ kopiert ein Symbol neben dem Systemnamen diesen in die Zwischenablage.
- Die zugehörige Hilfe und Übersetzungen sind in allen zwölf Sprachen ergänzt.
- Regressionstests decken EDSM-Status und Sternklassen, Erstbetretung über Sitzungsgrenzen, True-Merge, Wertlistenlayout und Breitenanpassung sowie das Kopiersymbol ab.

## Daten und Umfang

- Datenbankschema unverändert: **20**. Keine zusätzliche Migration.
- i18n: **1.742 unterschiedliche Schlüssel**; keine neuen Übersetzungsschlüssel für die interne Versionsanhebung.
- Die verworfene Codex-Chronik samt ihren zusätzlichen Import-, Persistenz- und Explorer-Marker-Änderungen ist nicht Bestandteil dieses Stands. Bereits in v3.7.0 vorhandene Codex-Funktionen bleiben unverändert.
- Produktive Datenbanken, Journale und QSettings werden bei dieser Vorbereitung nicht verändert.
