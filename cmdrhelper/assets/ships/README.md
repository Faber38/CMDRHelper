# Lokale Schiffsbilder

Optional eigene Bilder hier ablegen. Kein Download und keine Speicherung in SQLite.
Dateiname: kanonischer technischer Schiffstyp in Kleinbuchstaben, beispielsweise
`cobramkv.webp`, `mandalay.webp`, `panthermkii.webp`, `smallcombat01_nx.webp`.
Unterstützt werden (in dieser Reihenfolge) WebP, PNG, JPG und JPEG.
Bekannte Anzeigenamen werden zentral in `cmdrhelper/ui/ship_assets.py` zugeordnet.
Unbekannte technische Typen benötigen keinen neuen Mapping-Eintrag.

Querformat mit etwas Rand eignet sich für die proportional eingepassten Vorschauen
(aktiv: 144 × 100, Liste: 72 × 52 logische Pixel). Fehlende, unlesbare oder defekte
Typbilder verwenden stattdessen `standart.png`. Nur wenn auch dieses Standardbild
fehlt oder defekt ist, erscheint die neutrale Fläche. Keine Unterverzeichnisse oder externen Links.
Änderungen an Dateien werden beim nächsten Aktualisieren der Ansicht berücksichtigt;
der begrenzte Thumbnail-Cache prüft Änderungszeit und Dateigröße.

`standart.png` ist das mitgelieferte Standardmotiv und wird unverändert als
Programmasset ausgeliefert. Der bestehende Releaseprozess kopiert den gesamten
Ordner `cmdrhelper` einschließlich dieses Assets.

## Persönliche Bilder je Schiff

In den aufgeklappten Schiffsdetails kann über den nativen Dateidialog ein eigenes
PNG-, JPG-, JPEG- oder WebP-Bild gewählt oder die Zuordnung entfernt werden.
Groß-/Kleinschreibung der Endung ist beliebig; Qt muss den Inhalt lesen können.
Persönliches Bild → mitgeliefertes Typbild → `standart.png` → neutrale Platzhalterfläche.
Alle tatsächlich dargestellten Bilder lassen sich per Doppelklick vergrößern.

Die persönliche Kopie wird atomar als PNG unter dem von Qt ermittelten
`QStandardPaths.AppDataLocation / ship_images` gespeichert. Qt entscheidet über
den tatsächlichen Benutzerdatenpfad auf Linux und Windows (AppDataLocation kann
unter Windows den Roaming-Bereich verwenden). Kein Schreibzugriff auf die
Installation und keine Administratorrechte erforderlich. Die Originaldatei bleibt
unverändert. QSettings speichert nur den gehashten FID-Schlüssel, die ShipID und
einen relativen internen Dateinamen; keine absoluten Quellpfade und keine Bilddaten.

Dieser Benutzerordner liegt außerhalb des Programm-/Releaseverzeichnisses und
wird vom bestehenden Updater und Releasepaket nicht erfasst. Persönliche Bilder
bleiben bei Programmupdates erhalten. Keine persönlichen Bilder hier ablegen.
