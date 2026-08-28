# CMDRHelper

🇩🇪 Deutsch \| [🇬🇧 English](README.md)

![CMDRHelper – Dein Co-Pilot für Elite Dangerous](/docs/cmdrh.png)

**Persönlicher Begleiter für Elite Dangerous -- Exploration,
Systemanalyse und Commander-Daten auf einen Blick**

CMDRHelper ist ein eigenständiges Desktop-Programm für **Elite
Dangerous**, das Informationen aus den lokalen Journal-Dateien des
Spiels auswertet und übersichtlich darstellt. Ziel ist ein persönlicher
Helper, der beim Erkunden eines Systems schnell zeigt, was bereits
bekannt ist, welche Himmelskörper interessant sind und welche eigenen
Entdeckungen und Kartographierungen vorliegen.

Das Projekt befindet sich noch in aktiver Entwicklung.


## Funktionsübersicht

### Elite-Dangerous-Journale

CMDRHelper liest die lokalen Journal-Dateien und verarbeitet unter
anderem Sternsysteme, Sterne, Planeten, Monde, Belt Cluster, Scans,
Kartographierungen sowie biologische und geologische Signale. Eigene
Commander-Daten bleiben von ergänzenden externen Informationen
unterscheidbar.

### Missionen

CMDRHelper wertet Missionsereignisse aus den Elite-Dangerous-Journalen
aus und stellt aktive Missionen übersichtlich dar. Missionsstatus und
zugehörige Journalereignisse werden nachverfolgt.

Auch Missionsangebote, die während des Spiels über NPC-Nachrichten
(`ReceiveText`) eintreffen, können erkannt und für die weitere
Missionszuordnung berücksichtigt werden. Da Elite Dangerous nicht bei
jedem Missionstyp alle Informationen im selben Journalereignis
bereitstellt, wird die Zuordnung schrittweise aus den vorhandenen
Journaldaten aufgebaut.

### System- und Explorer-Ansicht

Die bekannten Körper eines Systems werden grafisch dargestellt und
können direkt ausgewählt werden. CMDRHelper kann unter anderem anzeigen:

-   Name und Art des Körpers
-   Entfernung im System
-   selbst gescannt oder nur extern bekannt
-   bereits entdeckt und kartographiert
-   mögliche Erstentdeckung und mögliches First Mapping
-   vom Commander kartographiert
-   effiziente Kartographierung
-   biologische und geologische Signale
-   Scan- und Kartographiewerte

BIO-Signale werden deutlich am betroffenen Körper hervorgehoben. Die
Zuordnung erfolgt systembezogen, damit BodyIDs verschiedener
Sternsysteme nicht verwechselt werden.

### Körper-Detailansicht

Beim Anklicken eines Körpers öffnet sich eine ausführliche Ansicht. Je
nach vorhandenen Daten erscheinen Körperart, Masse, Entfernung,
Schwerkraft, Atmosphäre, Vulkanismus, Landbarkeit, Terraforming-Status,
Materialien, BIO-/GEO-Signale, Scanwert, Kartographiewert und
Entdeckungsstatus.

Fehlende Informationen werden als unbekannt dargestellt und nicht als
sichere Daten ausgegeben.

## Grafische Körperdarstellung

CMDRHelper besitzt eigene Grafiken für zahlreiche Körpertypen, darunter
High Metal Content Worlds, Metal Rich Bodies, Rocky Bodies, Icy Bodies,
Rocky Ice Worlds, Earth-like Worlds, Water Worlds, Ammonia Worlds,
mehrere Gasriesenklassen, Gasriesen mit Wasser- oder Ammoniak-Leben,
heliumreiche Gasriesen, verschiedene Sternklassen und Belt Cluster.

Normale PNG-Bilder dienen den Übersichten. Für viele Körper gibt es
zusätzlich eine **2:1-equirectangulare `_texture.png`** für die
animierte Detailansicht.

### Rotierende 3D-Planeten

Passende 2:1-Texturen werden auf eine rotierende Kugel projiziert. Der
CPU-Renderer arbeitet mit **PySide6 und NumPy** ohne zusätzliche
OpenGL-/PyOpenGL-Abhängigkeit. Er beinhaltet Kugelprojektion, langsame
Rotation, Beleuchtung, Randabdunklung und atmosphärischen Rand.

### Animierte Lebensformen

Für Life-Gasriesen existieren unterschiedliche Animationen:

**Water Life:** cyan-/türkisfarbene schwebende Organismen mit Halo und
bewegten Schweifen.

**Ammonia Life:** eigene violett-/amberfarbene, halbtransparente
Organismen mit pulsierendem Kern, kurzen Fäden und langsamerer Bewegung.

### Animierte Belt Cluster

Belt Cluster werden nicht als Kugel dargestellt. Die Detailansicht
erzeugt ein prozedurales Asteroidenfeld mit einzelnen Asteroiden,
unterschiedlichen Größen und Tiefen, eigener Rotation, individueller
Drift, Parallax-Effekt, Kratern sowie dezenten Staub- und
Partikeleffekten.

## EDSM als ergänzende Datenquelle

CMDRHelper kann eigene Journal-Daten und EDSM-Informationen
unterscheiden. Die Quelle wird entsprechend als eigenes Journal, EDSM
oder eigenes Journal + EDSM gekennzeichnet. Eigene Journal-Daten sind
besonders wichtig, weil sie zeigen, was der jeweilige Commander
tatsächlich selbst gescannt oder kartographiert hat.

CMDRHelper kann neue Journal-Daten automatisch an EDSM übertragen. Dabei
wird die aktuelle dynamische EDSM-Discard-Liste berücksichtigt, sodass
nur von EDSM gewünschte Ereignisse gesendet werden. Der
Übertragungsfortschritt wird sicher pro Journaldatei gespeichert. Bei
der ersten Aktivierung werden bereits vorhandene alte Journale nicht
erneut vollständig übertragen.

Der EDSM-Status wird direkt oben in der Übersicht angezeigt. Eine grüne
Anzeige signalisiert eine funktionierende Übertragung; Fehler werden rot
dargestellt und zusätzlich im CMDRHelper-Log protokolliert.

## Lokale Datenbank

CMDRHelper verwendet SQLite. Dabei gilt:

-   `cmdrhelper/database.py` ist Programmcode und gehört zum Release.
-   `data/cmdrhelper.db` enthält persönliche Commander-Daten und wird
    **nicht** verteilt.
-   Bei einer frischen Installation wird die lokale Datenbank für den
    jeweiligen Benutzer neu aufgebaut.

So werden keine persönlichen Commander-Daten mit einem Release
ausgeliefert.

## Diagnose und Logdatei

CMDRHelper führt ein eigenes rotierendes Logfile für Diagnose und
Fehlersuche. Wichtige Programm-, Journal-, Datenbank- und
EDSM-Ereignisse werden protokolliert. Das EDSM-Logging wurde so
reduziert, dass reine, von EDSM verworfene Journalereignisse das normale
Log nicht unnötig füllen, während erfolgreiche Übertragungen sowie
Warnungen und Fehler sichtbar bleiben.

## Plattformen

CMDRHelper wird mit Python und PySide6 entwickelt und ist für **Linux
und Windows** vorgesehen. Die Entwicklung erfolgt hauptsächlich unter
Linux; Windows kann über die mitgelieferten Batch-Dateien eingerichtet
werden.

## Voraussetzungen

Python 3 sowie die Pakete aus `requirements.txt`:

``` text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

## Installation unter Linux

``` bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Vorhandene Linux-Startskripte können alternativ verwendet werden.

## Installation unter Windows

Für Windows sind `install.bat` und `start.bat` vorgesehen.

`install.bat` prüft Python 3, erstellt `venv`, aktualisiert pip und
installiert `requirements.txt`. Anschließend wird CMDRHelper über
`start.bat` gestartet.

## Release erstellen

``` bash
./create_release.sh
```

Die Release-Version wird direkt im Skript festgelegt. Das erzeugte ZIP
enthält Programmcode und Assets, aber keine persönliche Datenbank, keine
virtuelle Python-Umgebung sowie keine Git-, Cache- oder Editor-Dateien.

## Version 0.9.0

Wichtige Änderungen seit Version 0.5.5:

### Explorer und Systemkarte

-   Parent-/Child-Struktur der Systemkarte überarbeitet: Sterne, Planeten,
    Monde und Belt Cluster werden entsprechend ihrer Journal-Hierarchie
    angeordnet.
-   neue Funktion **„Alles anzeigen“** mit kompakter Miniaturübersicht des
    gesamten Systems
-   Körper können in der Miniaturübersicht angeklickt werden; die
    Hauptkarte springt anschließend direkt zum gewählten Körper.
-   verbesserte Navigation in großen Systemkarten:
    -   Mausrad verschiebt die Karte horizontal.
    -   rechte Maustaste gedrückt halten und nach oben/unten ziehen
        verschiebt die Karte vertikal.
-   optische Körpergrößen werden stärker anhand des realen Radius
    skaliert.
-   Darstellung und Markierung von BIO, GEO, Terraforming,
    Erstentdeckung und First Mapping weiter verbessert.

### BIO-Auswertung

-   biologische Daten werden getrennt von den normalen
    Kartographie-Werten ausgewertet und angezeigt.
-   Anzeige des Basiswertes vollständig analysierter BIO-Proben
-   Anzeige des möglichen **First-Logged-Gesamtwertes ×5**
-   bekannte BIO-Werte können aus vorhandenen Verkaufsdaten ergänzt
    werden.
-   Arten ohne bekannten Wert werden in der Auswertung kenntlich
    gemacht.

### Missionen

-   Verarbeitung von `MissionRedirected` verbessert.
-   umgeleitete Missionen können Namen, neues Zielsystem bzw. neue
    Zielstation und Informationen zum vorherigen Ziel übernehmen.
-   Missionen können in bestimmten Fällen auch rekonstruiert werden,
    wenn zuvor kein vollständiger `MissionAccepted`-Eintrag vorlag.
-   Missionsspalten sind frei in der Breite einstellbar; die gewählten
    Breiten werden gespeichert.

### Bilder und Screenshots

-   eigener Screenshot-Bereich mit Galerie und Vorschau
-   automatische Konvertierung neuer Elite-Dangerous-BMP-Screenshots
-   Ausgabe als PNG oder JPG
-   optionales Löschen der BMP-Datei nach erfolgreicher Konvertierung
-   einstellbare Helligkeitskorrektur von 0 bis 50 %
-   komfortablere Verwendung des Elite-Screenshotordners unter
    Steam/Proton
-   Galerie wird auch nach extern gelöschten Dateien aktualisiert.
-   verbesserte Sichtbarkeit der Optionen für automatische Konvertierung
    und Löschen

### Online-Dienste

-   automatische EDSM-Journalübertragung weiter integriert und über den
    Statusbereich im Hauptfenster sichtbar
-   Status für Übertragung, Warten, Fehler und deaktiviertes EDSM
-   Inara-Statusanzeige als Vorbereitung für die spätere automatische
    Übertragung

### Bedienung und Stabilität

-   sichtbarer **„Beenden“**-Schalter in der linken Seitenleiste
-   Single-Instance-Sperre verhindert einen versehentlichen zweiten
    gleichzeitigen Programmstart.
-   sichere Miniatur-Systemübersicht ohne direktes Rendern des bereits
    sichtbaren Explorer-Widgets
-   verschiedene Verbesserungen an Oberfläche, Journalverarbeitung,
    Datenbank und Updateablauf

## Projektstatus

CMDRHelper befindet sich in Entwicklung. Benutzeroberfläche, Datenmodell
und Darstellung können sich noch ändern. Weitere Körpertypen,
Journal-Funktionen, Explorer-Funktionen, Datenquellen und Berechnungen
sind vorgesehen. Linux und Windows werden weiter getestet.

CMDRHelper entstand als persönliches Werkzeug und wird schrittweise zu
einem umfangreicheren Elite-Dangerous-Helper ausgebaut.

## Hinweis zu Elite Dangerous

CMDRHelper ist ein unabhängiges Community-/Hobbyprojekt und kein
offizielles Produkt von Frontier Developments.

**Elite Dangerous** und zugehörige Namen und Inhalte sind Eigentum ihrer
jeweiligen Rechteinhaber.
