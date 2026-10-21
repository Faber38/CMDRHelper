# CMDRHelper v3.9.16

- PP2-Bereiche für aktuelles System, Aktivitäten und Bordartikel einzeln aufklappbar: beim ersten Start geschlossen, danach mit dauerhaft gespeichertem Zustand. Deine Macht und Tageschronik bleiben sichtbar.
- Bei unklarer Aktionsart erscheint ein kurzer allgemeiner Hinweis zum Abfangen anderer KDTN, ohne bestätigte lokale Verfügbarkeit zu behaupten. Eindeutige Aktivitäten, Ethos-Kennzeichnungen und Schutzprüfungen bleiben erhalten.
- Fremde kontrollierende Mächte erhalten im aktuellen System ein vorhandenes Porträt mit 42 × 56 Pixeln neben ihrem Namen. Bei eigener Macht erscheint kein zusätzliches Porträt.
- Die Vier-Stufen-Kontrollgrafik für kontrollierte Systeme ist ungefähr 25 % flacher, einschließlich Beschriftungen und Legende. Markerpositionen, Rot-/Blaufärbung und CP-Berechnungen bleiben unverändert.

Gezieltes Verbesserungsupdate der PP2-Oberfläche. Die drei aufklappbaren Bereiche behalten ihre Datenaktualisierung auch im geschlossenen Zustand; die Einstellungen werden über QSettings wiederhergestellt. Spaltenanordnung, persönliche Machtinformationen und Tageschronik bleiben erhalten.

Der allgemeine Aktivitätshinweis lautet: „Andere KDTN abfangen, die hier Aktionen ausführen, um den Fortschritt einer anderen Macht zu verlangsamen.“ Er ist ausdrücklich keine bestätigte lokale Aktivität und ersetzt keine eindeutig erkannte Kategorie. Ohne eigene Macht oder bei veraltetem System-Snapshot bleiben die Schutzmeldungen erhalten. Es gibt keine Systemnamen-Sonderregel und keine allgemeinen Ersatzlisten für acquisition oder conflict.

Die fremden Machtporträts verwenden die bestehende zentrale Zuordnung einschließlich des Alias A. Lavigny-Duval und des bisherigen Fallbacks. Sie erscheinen nur bei bekannter eigener und fremder kontrollierender Macht in einem zum aktuellen System gehörenden Snapshot. Die Grafikänderung betrifft Exploited, Fortified und Stronghold. Die horizontale Balkenbreite bleibt flexibel; die tatsächliche Widgethöhe sinkt, beispielsweise von 117 auf 88 Pixel bei 480 Pixel Breite. Je nach Schrift und Textumbruch kann die Höhenersparnis abweichen.

Die mit v3.9.15 veröffentlichten kompakten Unoccupied-Konfliktkarten und deren Spaltenaufteilung bleiben unverändert und sind keine Neuerungen dieses Releases. Ebenso unverändert bleiben Journalverarbeitung, Commander-Erkennung, Merit-, Rang-, Konflikt- und CP-Berechnungen. Das Datenbankschema bleibt bei Version 23. Es werden keine neuen Bilder oder Hintergrundprozesse eingeführt.

README- und Updatehinweise sind in allen zwölf Sprachen vorhanden. Gezielte Prüfungen verwenden Qt offscreen, Dark-/Light-Mode und unterschiedliche Fensterbreiten. Eine native visuelle Prüfung unter Windows und KDE X11/KWin steht aus; eine vollständige Regression ist nicht Bestandteil dieser Veröffentlichung. Der bekannte horizontale Überlauf der bestehenden Gesamtansicht bei 360 Pixel Fensterbreite auf Finnisch und Niederländisch wird durch die Porträtzeile nicht vergrößert und bleibt unverändert.
