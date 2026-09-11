# Kurzbeschreibung im Update-Dialog

`MainWindow._update_check_finished()` öffnet `UpdateConfirmationBox`, eine
QMessageBox mit unveränderten Ja/Nein-Aktionen. Version und Release Notes kommen
weiterhin aus `check_latest_release()`; die installierte Version aus `version.py`.

`cmdrhelper/release_summaries.py` ordnet Versionen Übersetzungsschlüssel zu.
Für 3.2 sind sechs Hauptpunkte in allen zwölf `cmdrhelper/i18n/*.py` hinterlegt.
Für 3.3 sind fünf Hauptpunkte in allen zwölf Sprachen hinterlegt: Systemanalyse,
Spielmodus, Kopieren letzter Systeme, verständlichere Erfahrungsdaten und der
Archivimport-Fix. `tools/publish_release.py` verwendet dieselben Schlüssel für
die GitHub-Release-Beschreibung und deren mehrsprachige Update-Metadaten.
Weitere lokal bekannte Versionen können als weiterer Dictionary-Eintrag ergänzt
werden, mit den zugehörigen Übersetzungen.

Für zukünftige, der installierten Anwendung noch unbekannte Versionen kann die
bestehende GitHub-Release-Beschreibung eine explizite Kurzbeschreibung enthalten:

```html
<!-- cmdrhelper-update-summary
{"de": ["Erste Verbesserung", "Zweite Verbesserung"],
 "en": ["First improvement", "Second improvement"]}
-->
```

Alle unterstützten Sprachcodes: de, en, fr, it, no, sv, fi, pl, nl, es, tr, el.
Die Liste der aktiven Sprache hat Vorrang vor lokal hinterlegten Punkten.
Höchstens sechs Punkte werden als Text angezeigt, kein vollständiger Changelog.
Fehlende oder ungültige Metadaten verwenden die lokale Versionsliste; fehlt auch
diese, erscheint die bisherige Updatefrage ohne Änderungsblock.

Der Änderungsbereich ist maximal 200 Pixel hoch und scrollbar. Farben werden aus
dem bestehenden Theme übernommen, die Buttons liegen außerhalb des Bereichs.
Die Erweiterung wird erst von Installationen angezeigt, die diesen Dialogcode
bereits enthalten; ein unveränderter älterer Client erhält keine neue UI allein
durch die Release Notes.
