# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Dein Co-Pilot für Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_de.png)

**Persönlicher Begleiter für Elite Dangerous – Exploration, Navigation und Commander-Daten auf einen Blick**

CMDRHelper ist ein eigenständiges Desktop-Programm, das die lokalen Journale von Elite Dangerous auswertet und planetare Positionsdaten aus `Status.json` verwendet. Es hilft dir, interessante Körper zu erkennen, gespeicherte Orte wiederzufinden und deine Reisen und Funde nachzuvollziehen. Persönliche Daten bleiben nach einem Neustart erhalten und werden nach Commander getrennt.

## Neu in v3.1 gegenüber v3.0.3

- Der BIO-Fortschritt erscheint kompakt: 1/3 gelb, 2/3 blau und 3/3 grün; der abgeschlossene Zustand „Fertig“ ist ebenfalls grün. Unter „auto einblenden“ besitzt GEO einen eigenen gespeicherten Schalter: BIO allein, GEO allein oder beide gemeinsam sind möglich. Manuell angepasste Spaltenbreiten der gemeinsamen Explorer-Tabelle BIO / GEO / ABBAU bleiben nach erneutem Öffnen und Programmneustart erhalten. Gespeicherte Popup-Spaltenbreiten werden robuster wiederhergestellt; ungültige Werte fallen auf sichere Standardbreiten zurück.

- Entdeckung und Kartographierung werden getrennt und auf den eigenen Scanzeitpunkt bezogen: „Bei deinem Scan bereits entdeckt“ beziehungsweise „Bei deinem Scan bereits kartographiert“. Fehlende Angaben bleiben Unbekannt. First-Discovery- und First-Mapping-Kandidaten gelten nur zum Scanzeitpunkt; historische Nein-Werte beweisen keinen heute noch unentdeckten oder unkartographierten Körper. Eigene Kartographierung bestätigt keinen offiziellen Erstanspruch. EDSM-Bekanntheit bleibt davon getrennt.

- „EDSM-Status-HUD“ unter „auto einblenden“ ist standardmäßig AUS. Nach einem Systemeintritt erscheint für ungefähr 2,5 Sekunden eine Kurzmeldung über Elite. „EDSM: BEKANNT“ bedeutet einen gültigen EDSM-Treffer für das System. „EDSM: NICHT BEKANNT“ bedeutet eine gültige EDSM-Antwort ohne Systemtreffer. „EDSM: KEINE ANTWORT“ bedeutet einen Netzwerk-, HTTP-, Timeoutfehler oder eine ungültige Antwort, niemals einen bestätigten fehlenden Treffer. EDSM-Bekanntheit ist nicht dasselbe wie offizielle Elite-Erstentdeckung; es werden keine Erstentdecker- oder Erstmeldernamen versprochen. Die Kurzmeldung funktioniert unabhängig von Navigations- und Frachtraum-HUD.

- Die Besuchshistorie berücksichtigt Location, FSDJump und CarrierJump auch im laufenden Journalabgleich. Mehrere Standortereignisse im selben ununterbrochenen Aufenthalt ergeben einen Besuch: A → A → A zählt einmal. Eine echte Rückkehr bleibt erhalten: A → B → C → A zählt vier Besuche.

- Nach Abschluss einer eigenen DSS-Kartographierung werden Mapping-Zeitpunkt, verwendete Sonden und Effizienzziel zuverlässig gespeichert. Spätere Scan-Ereignisse lassen vorhandene Angaben nicht mehr verloren gehen.

- Das Frachtraumfenster passt seine Höhe automatisch an den Inhalt an. Bei vielen Einträgen bleibt die Höhe begrenzt und die Tabelle lässt sich scrollen; Benutzerbreite und Fensterposition bleiben erhalten. Der vorhandene Schalter „Frachtraum-HUD“ befindet sich jetzt unter „auto einblenden“, nicht zusätzlich im Frachtraumfenster.

- Für bestehende Installationen genügt im Normalfall: Update installieren → CMDRHelper starten. Notwendige historische Korrekturen für BIO-Daten, Besuchshistorie und DSS-Metadaten laufen automatisch; vor schreibenden Datenreparaturen wird eine DB-Sicherung erstellt. Die Reparaturen sind versioniert und idempotent: Erfolgreiche Revisionen werden nicht bei jedem Start erneut vollständig ausgeführt. Rekonstruktion ist nur mit vorhandenen, lesbaren und eindeutig einem Commander zuordenbaren Elite-Journalen möglich. Fehlende Quellen werden nicht ersetzt oder als Erfolg gewertet; offene Reparaturen werden beim nächsten Start erneut versucht. Datenbanklöschung, manuelle Skripte und Neuimport sind im Normalfall nicht nötig.

## Explorer

Der Explorer zeigt das aktuelle System in drei Ansichten:

- **Systemkarte:** grafische Darstellung bekannter Sterne, Planeten und Monde. Ein Klick auf einen Körper öffnet seine Details. „Alles anzeigen“ öffnet die Systemübersicht.
- **Wertliste:** Die Wertliste zeigt Schätzungen nach dem gespeicherten Scanstand, keine sicher noch auszahlbaren Erlöse. Erstboni bleiben unbestätigt. Tooltips in Karte und Liste sowie das Körperdetail verwenden dieselben zeitlich eingeordneten Zustände.
- **BIO / GEO / ABBAU:** biologische und geologische Signale, planetare Abbaustandorte und belegte persönliche Funde.

Die Auswertungen unterscheiden zwischen gemeldeten Signalen und tatsächlichen eigenen Funden. **BIO ×N** ist die gemeldete Signalzahl, keine Bestätigung vollständig analysierter Arten. **ABBAU ×N** zählt planetare Abbaustandorte und verrät nicht deren einzelne Rohstoffinhalte. Persönlich gewonnene Commodities, beim Abbau gesammelte Nebenmaterialien und die allgemeine Materialzusammensetzung eines Körpers bleiben getrennt.

Der Explorer zeigt außerdem BIO-Schätzwerte, den Fortschritt eigener Analysen und noch nicht verkaufte Kartographie- und BIO-Daten. Werte beruhen auf den verfügbaren Journal- und Körperinformationen; fehlende Daten werden nicht als eigene Entdeckungen ausgegeben. Ergänzende EDSM-Daten sind als externe Informationen von eigenen Funden zu unterscheiden.

Die Körperdetails enthalten die verfügbaren physikalischen Angaben, Atmosphäre, Ringe, Materialien und Entdeckungsinformationen. Körperdarstellungen verwenden passende Texturen und für bestimmte astronomische Sonderobjekte Animationen. Der Cargo-Bereich zeigt die bekannte Ladung und Kapazität des aktuell verwendeten Schiffs beziehungsweise SRV; beim Rhino bleiben Ladung und persönliche Abbau-Funde unterschiedliche Angaben.

Oben im Explorer stehen **★ Favoriten | Planeten-Navigation | Alles anzeigen**. Favoriten und Planeten-Navigation öffnen eigene Fenster; die drei Explorer-Ansichten bleiben daneben verfügbar.

## Planeten-Navigation

Der Planeten-Navigator hilft ausschließlich dabei, eine bestimmte **Latitude/Longitude auf einem Planeten oder Mond** anzufliegen. Für Reisen zwischen Sternensystemen gibt es den separaten Routenplaner.

### Ziel eingeben und losfliegen

Wähle den Zielbody oder verwende den möglichst automatisch erkannten aktuellen Body. Gib Latitude und Longitude sowie optional einen Zielnamen ein. Technische Angaben wie BodyID oder SystemAddress musst du nicht eingeben. Auch **0,0** ist eine gültige Koordinate.

Sobald Elite gültige planetare Positionsdaten für den passenden Body liefert, wird der Kompass automatisch aktiv. Fehlen passende Daten, zeigt der Navigator einen Wartezustand. Auf demselben Body kannst du jederzeit ein neues Koordinatenziel setzen; es ersetzt das bisherige Ziel.

### Darstellung beim Anflug

| Zielentfernung | Darstellung |
| --- | --- |
| **Mehr als 380 km** | Planetenkugel mit eigener Position als weißem Kreis und Ziel als kleinem Punkt. Auf der sichtbaren Planetenseite ist das Ziel orange, auf der verdeckten Rückseite rot. Die Spielerposition bleibt in der Darstellung fest; Planet und Ziel werden relativ dazu dargestellt. |
| **Bis einschließlich 380 km** | Automatischer Wechsel auf ein gekipptes Perspektivraster mit **50-km-Entfernungsraster** und der darin eingezeichneten Zielposition für den weiteren Anflug. |

Das Navigatorfenster ist frei skalierbar. Kugel beziehungsweise Perspektivraster passen sich proportional dem verfügbaren Platz an; die Detailwerte bleiben lesbar.

### Navigationswerte verstehen

- **Zielkoordinaten:** gespeicherte Latitude und Longitude des Ziels.
- **Aktuelle Koordinaten:** die zuletzt gültige eigene planetare Position.
- **Zielentfernung / Entfernung über Oberfläche:** die berechnete Entfernung zum Ziel über die Kugeloberfläche; die große Zielentfernung und der Detailwert zeigen denselben Abstand mit unterschiedlicher Rundung.
- **Peilung:** die absolute Richtung von der aktuellen Position zum Ziel.
- **Heading:** die aktuelle eigene Ausrichtung, die Elite meldet.
- **Relative Richtung:** die Abweichung zwischen Heading und Peilung, etwa „23° rechts“, „links“ oder „geradeaus“.
- **Zielkurs:** der absolute Kurs, auf den du im Elite-HUD drehen kannst. Er entspricht der Peilung und ist kein zusätzlicher relativer Drehwinkel.

Beispiel: **Heading 051° → Zielkurs 074° = 23° rechts**.

Die Navigation hängt von den Statusdaten des Spiels ab; Aktualisierungen können je nach Spielzustand verzögert eintreffen. Die Oberflächenentfernung ist keine Gelände- oder Straßenroute. Hindernisse und Geländehöhen entlang der Strecke werden nicht berücksichtigt.

## Navigations-HUD

Links unter **auto einblenden → Navigations-HUD** aktivierst du eine optionale zusätzliche Anzeige direkt über Elite. Bei gültiger Planetennavigation zeigt sie:

- relative Richtung,
- absoluten Zielkurs,
- Entfernung.

Das HUD ist transparent, klickdurchlässig und fokusneutral: Es nimmt weder deine Mausklicks noch den Eingabefokus vom Spiel weg. Ohne gültige Navigation wird es automatisch unsichtbar; der Sidebar-Haken kann dabei aktiviert bleiben. Der normale Navigator funktioniert unabhängig vom HUD.

Das HUD wurde unter **Linux/X11** sowie unter **Windows 11 mit Elite** im Spiel getestet. Unter Windows erfolgt die Zuordnung bei mehreren Monitoren über deren Geometrie und die Position des Elite-Fensters, nicht über übereinstimmende Monitornamen.

## Favoriten

**Explorer → ★ Favoriten** öffnet ein eigenes, wiederverwendbares Fenster. Favoriten gehören zum **aktiven Commander**. Beim Commanderwechsel wird die Ansicht aktualisiert; die Commander-Auswahl der Chronik erweitert die Favoritenliste nicht.

### Drei Arten speichern

Die obere Aktionszeile bietet:

| Aktion | Gespeicherter Favorit |
| --- | --- |
| **★ Aktuelles System speichern** | Das aktuelle System, ohne Oberflächenkoordinaten. |
| **★ Planet / Mond speichern** | Ein ausgewählter bekannter Planet oder Mond des aktuellen Systems, ohne Oberflächenkoordinaten. |
| **★ Aktuellen Standort speichern** | Ein Oberflächenort mit aktuellem System, Body, Latitude und Longitude. |

Der Standort-Button bleibt immer sichtbar und ist nur mit gültigen aktuellen planetaren Positionsdaten und aktivem Commander verfügbar. **Beim Klick werden Commander, System, Body und Koordinaten eingefroren, bevor der Bearbeitungsdialog erscheint.** Bewegungen im Spiel verändern diese Position anschließend nicht. Derselbe Speicherweg ist auch im Planeten-Navigator erreichbar. Bekannte interne IDs werden automatisch übernommen; es werden keine Koordinaten erfunden.

Vergib einen Namen und genau eine Kategorie: **Bio, Geo, Abbau, Aussicht, Landestelle, Interessant oder Sonstiges**. Eine Notiz und ein Bild sind optional.

### Finden, ansehen und bearbeiten

Die alphabetisch nach Namen sortierte, scrollbare Liste zeigt Name, Typ, System, gegebenenfalls Body und Koordinaten, Kategorie und eine kleine Bildvorschau. **Freitextsuche, Typ- und Kategoriefilter** lassen sich kombinieren. Die Suche berücksichtigt Name, System, Body und Notiz.

**Öffnen / Anzeigen** zeigt gespeicherte Angaben, Notiz und eine größere Bildvorschau. **Im Explorer anzeigen** verwendet die vorhandene Systemübersicht oder Body-Detailansicht, sofern der Favorit zum aktuellen Explorer-System gehört und passende Daten vorhanden sind. Für andere Systeme bleiben die gespeicherten Favoritenangaben verfügbar.

**Bearbeiten** ändert Name, Kategorie, Notiz und Bild. System, Body und die gespeicherten Koordinaten werden dabei nicht durch Livewerte ersetzt. Für eine andere Position legst du einen neuen Oberflächenfavoriten an.

**Löschen** verlangt eine Bestätigung und entfernt ausschließlich den Favoritendatensatz und seine interne Bildkopie. Explorer-, Journal- und Bodydaten bleiben erhalten.

### Favoritenbilder und letzter Screenshot

Favoritenbilder sind **vollständig vom normalen Bereich Bilder getrennt**. CMDRHelper verwaltet eine eigene interne Kopie im Favoriten-Bildordner (`data/favorites/images/` bei der üblichen Datenablage). Das Original wird weder verschoben noch verändert.

- **Bild auswählen …** nimmt PNG, JPEG oder WebP entgegen und zeigt eine Vorschau. Die interne Kopie entsteht erst beim Speichern.
- **Letzten Screenshot verwenden** scannt bei jedem Klick den tatsächlichen Screenshot-Quellordner frisch. Zusätzlich berücksichtigt es passende konvertierte Elite-Screenshots im Ordner des aktiven Commanders innerhalb des konfigurierten Konvertierungsziels. So bleibt ein neuer Screenshot verfügbar, wenn die automatische Konvertierung sein BMP bereits gelöscht hat.
- Angeboten werden lesbare Dateien mit passenden Elite- beziehungsweise Konvertierungsnamen, keine beliebigen Bilder aus allgemeinen Bilderordnern. Für die Reihenfolge zählt eine eindeutige Aufnahmezeit im Dateinamen, ansonsten die Dateizeit. Bei konvertierten Bildern wird die im Namen gespeicherte Aufnahmezeit verwendet, nicht der Zeitpunkt der Konvertierung.
- Vor der Übernahme eines gefundenen Screenshots siehst du Dateiname, Aufnahmezeit und eine frisch geladene Vorschau. Bestätige mit **Dieses Bild verwenden**. Findet sich kein passender Screenshot, bleibt die manuelle Bildauswahl verfügbar. CMDRHelper löst selbst keinen Screenshot aus.

Ein Bild kann später ersetzt oder entfernt werden. Nicht mehr benötigte interne Kopien werden beim Speichern beziehungsweise Löschen des Favoriten entfernt. **Favoritenaktionen löschen niemals den ursprünglichen Screenshot oder ein ausgewähltes Originalbild.** Fehlt eine interne Bilddatei, bleibt der Favorit ohne Vorschau benutzbar.

### Oberflächenfavorit als Ziel

**▶ Zum Ziel** übergibt gespeicherten Body, Latitude, Longitude und Favoritennamen an den vorhandenen Planeten-Navigator und ersetzt dessen bisheriges Ziel. Favoriten haben keine eigene Navigationslogik. Mit passenden gültigen planetaren Daten beginnt die Navigation; andernfalls wartet der Navigator wie gewohnt.

Favoriten anderer Commander können nicht als eigene Ziele übernommen werden. Beim Commanderwechsel wird ein noch als Favoritenziel geführtes Ziel des bisherigen Commanders beendet. System- und Bodyfavoriten dienen der Anzeige vorhandener Informationen, nicht einer eigenen Routenplanung.

## Chronik

Die Chronik ist deine gespeicherte Reise- und Fundhistorie. Ihre **3D-Reisekarte** zeigt besuchte Systeme und Commander-Routen. System- und Körperdetails helfen beim Wiederfinden bekannter BIO-, GEO-, Material-, Codex- und Mining-Informationen.

### Gemeinsame Filter

**Anwenden** oder **Enter im Freitextfeld** führt alle gesetzten Filter gemeinsam aus:

- Freitext,
- optional **Von** und **Bis**,
- **Planetare Abbaustandorte** und **Mindestanzahl**,
- **Eigene Abbau-Funde** und **Rohstoff**.

Ein Begriff aus **Suchhilfe / Legende** wird ins Suchfeld übernommen und zusammen mit den bereits gesetzten Zeitraum- und Miningfiltern ausgeführt.

### Zeitraum in UTC

Von und Bis werden jeweils über ihren Haken aktiviert. Nur eine Grenze ist ebenfalls möglich; ohne aktivierten Haken besteht auf dieser Seite keine Zeitbeschränkung. **Von** beginnt einschließlich am Anfang des ausgewählten UTC-Kalendertages. **Bis** umfasst den vollständigen ausgewählten UTC-Tag. UTC ist die gemeinsame Zeitbasis, nicht deine lokale Kalenderzeit.

Maßgeblich sind **tatsächliche Systembesuche**: Mindestens ein gespeicherter Besuch muss im Zeitraum liegen. Ein bloßes erstes oder letztes Bekanntwerden des Systems ersetzt keinen Besuch. Besuchszahl, erster und letzter Besuch in der Kartenansicht beziehen sich bei aktivem Zeitraum auf die gefilterten Besuche.

Der Zeitraum filtert Besuche, nicht einzelne Entdeckungs-, BIO-, GEO- oder Mining-Ereignisse. Bekannte Fundinformationen und persönliche Mining-Mengen bleiben gespeicherte **Gesamtwerte**. **„Kupfer 56 t“ bedeutet bei aktivem Zeitraum nicht automatisch „56 t in diesem Zeitraum“.** Liegt Von nach Bis, erscheint eine Fehlermeldung; es wird keine Datenbankabfrage gestartet.

### Commander und Aktualisierung

Die **Commander-Auswahl der Karte** bestimmt die dargestellten Commander-Routen. Persönliche Freitext- und Mining-Suchen beziehen sich dagegen auf den betrachteten beziehungsweise aktiven Commander. Die Karten-Haken erweitern persönliche Suchen nicht automatisch auf mehrere Commander.

**Chronik aktualisieren** lädt die Daten neu und führt die aktiven Filter erneut aus. **Aktuelle Position** wendet zuerst den aktuellen Filterzustand an und zentriert nur dann auf das aktuelle System, wenn es in der resultierenden Karte enthalten ist. Andernfalls erscheint ein Hinweis; die Filter bleiben bestehen.

**Zurücksetzen** leert Freitext, deaktiviert Von/Bis und setzt deren sichtbare Datumsfelder zurück. Die Mining-Haken werden entfernt, Mindestanzahl wird 0 und Rohstoff wird Alle. Die Commander-Auswahl bleibt erhalten; anschließend wird die normale Chronik geladen.

Bei **keinen Treffern** werden Karte und Routen geleert, die Trefferliste geleert und ausgeblendet, die Detailanzeige zurückgesetzt und ein offenes Chronik-Systemdetailfenster geschlossen. Alte Ergebnisse bleiben nicht stehen.

### Karte bedienen

- Linke Maustaste ziehen: drehen.
- Rechte Maustaste ziehen: verschieben.
- Mittlere Maustaste ziehen: ein Zoom-Fenster aufziehen.
- Mausrad: zoomen.
- **Ausrichten:** Orientierung auf die galaktische Draufsicht zurücksetzen; Verschiebung und Zoom bleiben erhalten.

## Bilder und automatische Screenshot-Konvertierung

Im Bereich **Bilder** stellst du den Elite-Screenshot-Quellordner und das Konvertierungsziel ein. Die automatische Konvertierung verarbeitet neu hinzukommende BMP-Screenshots zu **PNG oder JPEG**. Eine einstellbare Aufhellung ist verfügbar. Bereits beim Start vorhandene BMPs werden nicht allein durch das Einschalten der Überwachung automatisch nachträglich konvertiert; dafür gibt es die manuelle Konvertierung.

Konvertierte Dateien erhalten Aufnahmezeit, Commander- und Systembezug im Namen und werden commanderbezogen abgelegt. Die automatische Zuordnung richtet sich nach dem aktiven Journal-Commander. Eine andere Auswahl für die Galerie ändert diesen aktiven Commander nicht.

Die Option zum **Löschen des ursprünglichen BMP nach erfolgreicher Konvertierung** gehört ausschließlich zu dieser Konvertierung und ist eine eigene Einstellung. Sie ist unabhängig von der Favoriten-Bildverwaltung.

Die Galerie zeigt die passenden konvertierten Bilder mit Vorschau. Beim erneuten Anzeigen wird sie frisch eingelesen; auch die Aktualisierung berücksichtigt den aktuellen Dateibestand. Auswahl und große Vorschau werden gemeinsam aktualisiert. Verschwindet das ausgewählte Bild, wird ein noch vorhandenes Bild gewählt oder die Vorschau geleert. Der Bereich Bilder bietet außerdem seine eigene Bildauswahl und Löschfunktion mit Bestätigung.

## Weitere Ansichten

- **Übersicht:** aktiver Commander, Schiff, Standort, Journalerkennung, offene Missionen und Online-Status.
- **Missionen:** dauerhaft gespeicherte offene Missionen mit bekannten Zielen, Fortschritt und Abschlusszustand. Fehlende Angaben werden nicht ergänzt oder erfunden.
- **CMDR:** Vermögen, Ränge, Statistik, Söldnermünzen, Schiffe/Flotte und bekannter Fleet-Carrier-Standort. Söldnermünzen werden als von Frontier gemeldete Gesamtstände dargestellt, nicht als selbst berechnete Bilanz.
- **Routenplaner:** getrennte Planung für Schiff und Fleet Carrier mit Spansh. Berechnete Carrier-Routen lassen sich als CSV für CTSVision exportieren. Die Berechnung benötigt eine Verbindung zum externen Dienst.

## Commander, lokale Daten und Online-Dienste

CMDRHelper erkennt den aktiven Commander anhand der Frontier-ID aus der aktuellen Journalsitzung. Persönliche Exploration, Missionen, Vermögen, Favoriten und Online-Zugänge werden getrennt gespeichert. Das bloße Betrachten eines anderen Commanders ändert weder den Live-Commander noch dessen Upload-Zuordnung.

Die lokale SQLite-Datenbank bewahrt bekannte Systeme, Körper und persönliche Historie über Neustarts hinweg. Neue vollständige Journaleinträge werden während des Spiels verarbeitet; gespeicherte Lesepositionen vermeiden unnötiges erneutes Einlesen. Wenn Standort oder Commander nicht stimmen, prüfe zuerst die Journalerkennung und den Journalordner in den Einstellungen.

**EDSM** kann ergänzende Systemdaten liefern. Unterstützte Journaldaten können an **EDSM und Inara** übertragen werden, wenn der jeweilige Dienst für den aktiven Commander mit eigenen Zugangsdaten eingerichtet und aktiviert ist. Ein Commander verwendet nicht automatisch den API-Key eines anderen. Die lokale Speicherung funktioniert unabhängig von einer erreichbaren Online-Verbindung.

## Sprachen und kontextbezogene Hilfe

Die Oberfläche unterstützt **12 Sprachen**: **DE, EN, FR, IT, NO, SV, FI, PL, NL, ES, TR, EL** – Deutsch, Englisch, Französisch, Italienisch, Norwegisch, Schwedisch, Finnisch, Polnisch, Niederländisch, Spanisch, Türkisch und Griechisch.

Aktuell sind **937 UI-i18n-Keys je Sprache** vorhanden. Über **? Hilfe** stehen **10 ausführliche kontextbezogene Hilfethemen in allen 12 Sprachen** bereit. Favoriten sind Teil der Explorer-Hilfe; die Planeten-Navigation hat ihr eigenes Thema, direkt aus dem Navigator erreichbar. Die Hilfe verwendet die aktuelle Oberflächensprache und behält Deutsch als Rückfall bei fehlendem Katalog oder Eintrag bei.

## Voraussetzungen

| Plattform | Python |
| --- | --- |
| **Windows** | **Python 3.10 oder neuer, x64 erforderlich.** Keine künstliche Obergrenze für vorhandene Versionen. Entscheidend sind anschließend die tatsächlichen Paket- und Importprüfungen. |
| **Linux** | **Python 3.10 oder neuer**, 64 Bit empfohlen. Das zur Python-Version passende venv-Modul muss verfügbar sein. |

Die benötigten Pakete stehen in `requirements.txt`:

```text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

Die Installation lädt diese Abhängigkeiten. Für Journalauswertung und Planetennavigation müssen die lokalen Elite-Dateien erreichbar sein. Unter Linux kann Elite über Steam/Proton laufen; den tatsächlichen Journal- und Screenshotpfad stellst du in CMDRHelper ein. Die oben beschriebene Linux-HUD-Unterstützung bezieht sich auf X11.

## Installation unter Linux

Entpacke das vollständige Projekt beziehungsweise Release und führe im Projektordner aus:

```bash
./install.sh
./start.sh
```

Die Skripte verwenden ausschließlich das lokale `venv` dieser Installation. Sie lösen symbolische Script-Links auf, prüfen Python und pip und können eine beschädigte lokale Umgebung reparieren, ohne persönliche Daten oder Elite-Journale anzutasten. Fehlende Systempakete werden nicht automatisch installiert; fehlt das venv-Modul, meldet der Installer dies. Der bestehende Linux-Installationsweg bleibt unverändert.

## Installation unter Windows

1. Entpacke das vollständige ZIP in einen eigenen Ordner.
2. Starte **install.bat**. Es ruft das mitgelieferte **install-windows.ps1** auf.
3. Nach erfolgreicher Installation startest du CMDRHelper mit **start.bat**.

Vorhandenes **Python ab 3.10 x64** wird ohne künstliche Versionsobergrenze akzeptiert. Eine zukünftige Python-Version wird nicht allein wegen ihrer Versionsnummer abgewiesen. Ein geeignetes vorhandenes Python beziehungsweise ein verwendbares lokales venv verhindert eine unnötige automatische Python-Installation.

Wenn kein geeignetes Python vorhanden ist, bietet der Installer nach Zustimmung eine automatische Installation über **winget** an. Dafür ist bewusst die feste Versionsreihe **Python 3.14 x64** ausgewählt; diese Auswahl ist von der offenen Regel für bereits vorhandene Python-Versionen getrennt. Ist die automatische Installation nicht möglich, meldet der Installer den Fehler.

Der Installer erstellt beziehungsweise prüft oder repariert nur das **lokale venv dieser CMDRHelper-Kopie**, installiert die Requirements und führt **pip check** sowie Importprüfungen für **PySide6, PySide6.QtWidgets, numpy und PIL** aus. Erst diese tatsächlichen Prüfungen entscheiden über die Nutzbarkeit der Umgebung. Schlagen sie fehl, bricht die Installation mit einer verständlichen Fehlermeldung ab. Fremde virtuelle Umgebungen werden nicht repariert oder ersetzt.

## Diagnose und Release-Pakete

Bei Problemen helfen die Journal- und Online-Statusanzeigen sowie die Logdateien im Ordner `logs`. Persönliche Daten liegen in der lokalen Datenablage; zu einer Sicherung der Favoriten gehören neben der Datenbank auch deren interne Bildkopien.

Für das Erstellen eines eigenen Release-Pakets steht `./create_release.sh` bereit. Die Programmversion wird zentral in `cmdrhelper/version.py` verwaltet und vom Release-Skript gelesen. Das Paket enthält Programmcode und Assets, keine persönliche Datenbank, kein venv und keine Git- oder Cache-Dateien.

## Bild- und Videomaterial / Media Credits

CMDRHelper verwendet für einzelne astronomische Sonderobjekte
Visualisierungen der **NASA Scientific Visualization Studio (NASA
SVS)**. Die jeweiligen Medien bleiben Eigentum ihrer Rechteinhaber und
werden entsprechend den auf den NASA-SVS-Seiten angegebenen Credits
genannt.

### Neutronenstern

-   CMDRHelper-Datei: `star_neutron.webm`
-   Quelle: NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatoren: Walt Feimer (KBR Wyle Services, LLC) und Lisa Poje
    (USRA)
-   Quelle: https://svs.gsfc.nasa.gov/20267/

### Schwarzes Loch

-   CMDRHelper-Datei: `black_hole.mp4` bzw. die im Projekt verwendete
    Video-Endung
-   Quelle: NASA Scientific Visualization Studio, **Black Hole Accretion
    Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Quelle: https://svs.gsfc.nasa.gov/13326/

### Supermassives Schwarzes Loch

-   CMDRHelper-Datei: `black_hole_supermassive.mp4` bzw. die im Projekt
    verwendete Video-Endung
-   Quelle: NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Quelle: https://svs.gsfc.nasa.gov/14576/

### Weißer Zwerg

-   CMDRHelper-Datei: `star_white_dwarf.webm`
-   verwendetes NASA-Medium: **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Quelle: NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatorin: Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Quelle: https://svs.gsfc.nasa.gov/20344/

Die Nennung dieser Quellen und Credits bedeutet nicht, dass CMDRHelper
von NASA unterstützt, zertifiziert oder herausgegeben wird. Für die
Weiterverwendung der NASA-Medien gelten die jeweiligen Hinweise und
Reproduktionsrichtlinien der Originalquellen.

## Lizenz

CMDRHelper ist freie Software und wird unter der **GNU General Public
License Version 3 (GPL-3.0)** veröffentlicht.

Der Quellcode darf unter den Bedingungen der GPL-3.0 verwendet,
verändert und weitergegeben werden. Bei der Weitergabe abgeleiteter
Versionen gelten ebenfalls die Bedingungen der GPL-3.0.

Copyright © 2026 **Holger Mangold (Faber38)**.

Die vollständigen Lizenzbedingungen befinden sich in der Datei
`LICENSE`.

## Hinweis zu Elite Dangerous

CMDRHelper ist ein unabhängiges Community-/Hobbyprojekt und kein
offizielles Produkt von Frontier Developments.

**Elite Dangerous** und zugehörige Namen und Inhalte sind Eigentum ihrer
jeweiligen Rechteinhaber.
