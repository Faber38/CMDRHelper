# CMDRHelper v3.9.15

- Kompaktere PP2-Konfliktkarten für nicht besetzte Systeme: Porträts, Balken und Abstände ungefähr 25 % kleiner; Schrift für bessere Lesbarkeit von 12 auf 10 Pixel reduziert.
- Ab drei beteiligten Mächten und ausreichender Fensterbreite stehen die zwei führenden Mächte links, alle weiteren rechts. Bei schmalen Fenstern oder höchstens zwei Mächten bleibt die Darstellung einspaltig.
- Die bestehende Systemkarte nutzt die Breite unter Aktionshinweisen und Bordartikeln, ohne diese zu verdecken. Beide Konfliktspalten beginnen bündig und benötigen weniger Höhe; alle Teilnehmer bleiben sichtbar.

Die Anpassung betrifft ausschließlich die vorhandene Konfliktdarstellung für nicht besetzte Systeme. Führende Karten behalten größere Porträts und Abstände als die rechte Spalte. Die Sortierung nach Konfliktfortschritt, bei Gleichstand nach Machtnamen, bleibt unverändert. Auch mehr als fünf Teilnehmer werden vollständig angezeigt; die Karten haben keine feste Gesamthöhe. Die kompaktere Darstellung entlastet den Platz oberhalb der PP2-Tageschronik. Lange Hinweise oder viele Teilnehmer können weiterhin zusätzliche Höhe benötigen.

Unverändert bleiben die CP-Näherungsberechnung, die Balkenskala bis 180000 CP, die Markierungen bei 36000 und 120000 CP, Machtfarben, Tooltips, die eigene Macht ohne Präsenz, Journalzeitstempel sowie Commander- und Systemwechsel. Diese bereits mit v3.9.14 veröffentlichten Funktionen sind keine Neuerungen dieses Releases. Andere Systemansichten, Rangdarstellung und Tageschronik werden nicht verkleinert. Das Datenbankschema bleibt bei Version 23.

README- und Updatehinweise sind in allen zwölf Sprachen vorhanden. Gezielte Prüfungen verwenden Qt offscreen, beide Themes und unterschiedliche Fensterbreiten. Eine native visuelle Prüfung unter Windows und KDE X11/KWin steht aus; eine vollständige Regression ist nicht Bestandteil dieser Veröffentlichung.
