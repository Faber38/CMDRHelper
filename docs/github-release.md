# Veröffentlichung mit github.sh

`./github.sh` startet `tools/publish_release.py` (Python >= 3.10, nur
Standardbibliothek). Das Skript fragt einmal nach Zustimmung zur vollständigen
Veröffentlichung und bei lokalen Änderungen nach einer Commit-Nachricht.
Eine zusätzliche Bedienung von github.com ist im erfolgreichen Ablauf unnötig.
Das Skript führt keine Testsuite aus; die finalen Projekttests gehören zur
Releasevorbereitung. Ein separater finaler Build ist nicht erforderlich.

## Reihenfolge

1. Werkzeuge, `gh auth status`, Repository `Faber38/CMDRHelper` mit Schreibrecht,
   Branch `main`, HTTPS-Remote `origin`, Version sowie lokale und entfernte Tags
   und Releases einschließlich Entwürfen prüfen.
2. Zustimmung einholen. Falls nötig Quelländerungen gezielt stagen und committen.
3. Sauberes Arbeitsverzeichnis und finalen Commit prüfen.
4. Den Commit mit `git archive` in ein temporäres Verzeichnis exportieren, ohne
   historische Releaseordner. Dort den unveränderten `create_release.sh` aus
   diesem Commit ausführen. Ignorierte/unversionierte Dateien werden nie gebaut.
5. ZIP auf Integrität und exakte Übereinstimmung mit dem Releaseordner prüfen.
   ZIP-Metadaten für Wiederholungen normalisieren (Commit-Zeit, stabile Sortierung
   und Dateimodi), nochmals validieren und nur die generierten Ziele dieser
   Version nach `release/` übernehmen. SHA-256 und Größe merken.
6. Erneut sauberen Quellstand, HEAD und Remote-Zustand prüfen. Erst jetzt den
   finalen Commit ohne automatisches Tag-Mitpushen nach `origin/main` pushen.
7. Fehlenden annotierten Tag erstellen und pushen; einen nur entfernt vorhandenen
   passenden Tag lokal übernehmen. Bestehende Tags niemals überschreiben.
8. Fehlendes GitHub-Release mittels explizitem Repository, `--verify-tag`, Titel,
   Notes-Datei und frisch gebautem ZIP erstellen. Bei vorhandenem Release nur
   das fehlende Asset hochladen. Kein `--clobber` für Uploads.
9. Release, Remote-Tag/Commit, Assetname, Uploadstatus, Größe und SHA-256 prüfen.
   Liefert GitHub keinen Digest, das Asset zum Vergleich temporär herunterladen.
   Einen passenden Entwurf erst nach Assetprüfung veröffentlichen und erneut
   prüfen. Erst dann Erfolg mit Commit, Tag, Release-URL und ZIP-Pfad melden.

Die Release-Liste wird paginiert gelesen, damit auch Entwürfe nach einem
fehlgeschlagenen Upload gefunden werden. Die GitHub-API dokumentiert die
Sichtbarkeit von Entwürfen für Konten mit Push-Recht:
[GitHub: List releases](https://docs.github.com/en/rest/releases/releases#list-releases).

## Version und Notes

`cmdrhelper/version.py` ist die einzige Versionsquelle. `cmdrhelper/__init__.py`
importiert diese Angabe. Die Umstellung dieses Ablaufs erhöht die Version nicht.

Die ersten sechs v3.2-Punkte kommen aus den vorhandenen Versionsschlüsseln in
`cmdrhelper/release_summaries.py` und den zwölf Sprachkatalogen des gebauten
Commits. Der sichtbare Text ist Deutsch; der zusätzliche unsichtbare
`cmdrhelper-update-summary`-Block enthält alle zwölf Sprachen für den Updater.
Keine duplizierte Textpflege und keine automatisch generierten technischen Notes.
Weitere Versionen werden in derselben Struktur ergänzt. Ohne Eintrag erscheint
„Weitere Verbesserungen und Fehlerkorrekturen.“.

## Wiederaufnahme und Grenzen

Ein erneuter Start baut denselben Commit frisch und validiert ihn erneut.
Bereits vorhandene Tags müssen auf genau diesen Commit zeigen; vorhandene Assets
müssen auch inhaltlich passen. Fehlende Schritte werden fortgesetzt. Ein gleicher
Commit mit unterschiedlichen ZIP-Bytes (beispielsweise nach einem Wechsel der
Kompressionsbibliothek) wird vorsichtshalber nicht über ein vorhandenes Asset
hochgeladen. Widersprüche verlangen eine gezielte Prüfung, keine automatische
Löschung oder Überschreibung.

Bei Fehlern werden Phase und abgeschlossene Schritte gemeldet. Bereits erfolgte
Remote-Schritte werden nicht zurückgerollt. Bei Verbindungsabbruch kann GitHub den
letzten Auftrag dennoch angenommen haben; der nächste Lauf ermittelt den Zustand
neu. Ein unvollständiges oder abweichendes vorhandenes Asset wird nicht ersetzt.

Generierte `release/CMDRHelper_v*/`-Ordner und ZIPs werden ignoriert und beim
Staging ausgeschlossen. Historisch versionierte Artefakte bleiben versioniert.
Änderungen an ihnen, auch bereits vorgemerkte, führen vor einem automatischen
Commit zum Abbruch und müssen in der Releasevorbereitung separat geklärt werden.
Ein bereits versioniertes Zielrelease wird nicht überschrieben.

Während der Veröffentlichung keine parallelen Änderungen oder zweiten
Veröffentlichungsprozesse starten. Der Ablauf prüft den Quellstand mehrfach und
baut ausschließlich aus dem festgehaltenen Commit; Remote-Operationen sind keine
übergreifende Transaktion.

## Vorbereitung des Quellstands

Die zentrale Laufzeitversion steht in `cmdrhelper/version.py`; `cmdrhelper/__init__.py`
importiert sie. Vor dem finalen Commit README- und Hilfetexte in allen zwölf Sprachen
sowie die versionsbezogenen Kurztexte abgleichen und die Projekttests ausführen.
`/logs/`, `*.log` und numerisch rotierte Logs sind ignoriert. Persönliche
Testreferenzen sind anonymisiert; optionale lokale Regressionen ermitteln die FID
rein lesend anhand des Test-Commandernamens und betten keine reale Kennung ein.
