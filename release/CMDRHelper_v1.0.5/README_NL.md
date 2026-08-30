# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Jouw co-piloot voor Elite Dangerous](/docs/cmdrh.png)

**Persoonlijke metgezel voor Elite Dangerous -- exploratie,
systeemanalyse en Commander-gegevens in één oogopslag**

CMDRHelper is een zelfstandig desktopprogramma voor **Elite Dangerous**
dat informatie uit de lokale Journal-bestanden van het spel analyseert
en overzichtelijk weergeeft. Het doel is een persoonlijke helper die
tijdens het verkennen van een systeem snel laat zien wat al bekend is,
welke hemellichamen interessant zijn en welke ontdekkingen en mappings
je zelf hebt uitgevoerd.

Het project is nog steeds actief in ontwikkeling.

## Functieoverzicht

### Elite Dangerous-Journals

CMDRHelper leest de lokale Journal-bestanden en verwerkt onder andere
sterrenstelsels, sterren, planeten, manen, Belt Clusters, scans,
mappings en biologische en geologische signalen. De eigen gegevens van
de Commander blijven daarbij te onderscheiden van aanvullende externe
informatie.

### Missies

CMDRHelper analyseert missie-events uit de Elite Dangerous-Journals en
toont actieve missies overzichtelijk. De missiestatus en bijbehorende
Journal-events worden gevolgd.

Ook missieaanbiedingen die tijdens het spelen via NPC-berichten
(`ReceiveText`) binnenkomen, kunnen worden herkend en meegenomen in de
verdere toewijzing van missies. Omdat Elite Dangerous niet voor ieder
missietype alle informatie in hetzelfde Journal-event levert, wordt de
toewijzing stap voor stap opgebouwd uit de beschikbare Journal-gegevens.

### Systeem- en Explorer-weergave

De bekende hemellichamen van een systeem worden grafisch weergegeven en
kunnen direct worden geselecteerd. CMDRHelper kan onder andere tonen:

-   naam en type van het hemellichaam
-   afstand binnen het systeem
-   zelf gescand of alleen extern bekend
-   al ontdekt en gemapt
-   mogelijke eerste ontdekking en mogelijke First Mapping
-   door de Commander gemapt
-   efficiënte mapping
-   biologische en geologische signalen
-   scan- en mappingwaarden

BIO-signalen worden duidelijk op het betreffende hemellichaam
gemarkeerd. De toewijzing gebeurt per systeem, zodat BodyID's uit
verschillende sterrenstelsels niet door elkaar worden gehaald.

### Detailweergave van hemellichamen

Door op een hemellichaam te klikken wordt een detailweergave geopend.
Afhankelijk van de beschikbare gegevens worden lichaamstype, massa,
afstand, zwaartekracht, atmosfeer, vulkanisme, landbaarheid,
terraforming-status, materialen, BIO-/GEO-signalen, scanwaarde,
mappingwaarde en ontdekkingsstatus weergegeven.

Ontbrekende informatie wordt als onbekend weergegeven en niet als zekere
informatie gepresenteerd.

## Grafische weergave van hemellichamen

CMDRHelper beschikt over eigen grafische weergaven voor talrijke typen
hemellichamen, waaronder High Metal Content Worlds, Metal Rich Bodies,
Rocky Bodies, Icy Bodies, Rocky Ice Worlds, Earth-like Worlds, Water
Worlds, Ammonia Worlds, meerdere klassen gasreuzen, gasreuzen met op
water of ammoniak gebaseerd leven, heliumrijke gasreuzen, verschillende
sterklassen en Belt Clusters.

Normale PNG-afbeeldingen worden gebruikt in de overzichten. Voor veel
hemellichamen is daarnaast een **2:1-equirectangulaire `_texture.png`**
beschikbaar voor de geanimeerde detailweergave.

### Roterende 3D-planeten

Geschikte 2:1-texturen worden op een roterende bol geprojecteerd. De
CPU-renderer werkt met **PySide6 en NumPy** zonder extra afhankelijkheid
van OpenGL/PyOpenGL. Hij omvat bolprojectie, langzame rotatie,
belichting, randverduistering en een atmosferische rand.

### Geanimeerde levensvormen

Voor gasreuzen met leven zijn verschillende animaties beschikbaar:

**Water Life:** cyaan-/turkooiskleurige zwevende organismen met gloed en
bewegende staarten.

**Ammonia Life:** afzonderlijke violet-/amberkleurige, halftransparante
organismen met een pulserende kern, korte filamenten en langzamere
beweging.

### Geanimeerde Belt Clusters

Belt Clusters worden niet als bollen weergegeven. De detailweergave
genereert een procedureel asteroïdenveld met afzonderlijke asteroïden,
verschillende groottes en dieptes, eigen rotatie, individuele drift,
parallaxeffect, kraters en subtiele stof- en deeltjeseffecten.

## EDSM als aanvullende gegevensbron

CMDRHelper kan eigen Journal-gegevens onderscheiden van EDSM-informatie.
De bron wordt overeenkomstig gemarkeerd als eigen Journal, EDSM of eigen
Journal + EDSM. Eigen Journal-gegevens zijn bijzonder belangrijk omdat
ze laten zien wat de betreffende Commander daadwerkelijk zelf heeft
gescand of gemapt.

CMDRHelper kan nieuwe Journal-gegevens automatisch naar EDSM
overbrengen. Daarbij wordt rekening gehouden met de actuele dynamische
EDSM Discard-lijst, zodat alleen events worden verzonden die EDSM wil
ontvangen. De voortgang van de overdracht wordt per Journal-bestand
veilig opgeslagen. Bij de eerste activering worden reeds bestaande oude
Journals niet opnieuw volledig verzonden.

De EDSM-status wordt direct bovenaan het overzicht weergegeven. Een
groene indicator geeft aan dat de overdracht werkt; fouten worden rood
weergegeven en bovendien in het CMDRHelper-log vastgelegd.

## Lokale database

CMDRHelper gebruikt SQLite. Daarbij gelden de volgende regels:

-   `cmdrhelper/database.py` is programmacode en maakt deel uit van de
    release.
-   `data/cmdrhelper.db` bevat persoonlijke Commander-gegevens en wordt
    **niet** meegeleverd.
-   Bij een nieuwe installatie wordt de lokale database opnieuw
    opgebouwd voor de betreffende gebruiker.

Zo worden geen persoonlijke Commander-gegevens met een release
meegeleverd.

## Diagnose en logbestand

CMDRHelper houdt een eigen roterend logbestand bij voor diagnose en
foutopsporing. Belangrijke programma-, Journal-, database- en
EDSM-events worden gelogd. De EDSM-logging is verminderd, zodat gewone
Journal-events die alleen door EDSM worden genegeerd het normale log
niet onnodig vullen, terwijl geslaagde overdrachten, waarschuwingen en
fouten zichtbaar blijven.

## Platformen

CMDRHelper wordt ontwikkeld met Python en PySide6 en is bedoeld voor
**Linux en Windows**. De ontwikkeling vindt voornamelijk onder Linux
plaats; Windows kan met de meegeleverde batchbestanden worden ingericht.

## Vereisten

Python 3 en de pakketten uit `requirements.txt`:

``` text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

## Installatie onder Linux

``` bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Als alternatief kunnen de bestaande Linux-startscripts worden gebruikt.

## Installatie onder Windows

Voor Windows zijn `install.bat` en `start.bat` bedoeld.

`install.bat` controleert Python 3, maakt `venv` aan, werkt pip bij en
installeert `requirements.txt`. Daarna wordt CMDRHelper via `start.bat`
gestart.

## Release maken

``` bash
./create_release.sh
```

De releaseversie wordt direct in het script ingesteld. Het gemaakte
ZIP-bestand bevat programmacode en assets, maar geen persoonlijke
database, geen virtuele Python-omgeving en geen Git-, cache- of
editorbestanden.

## Versie 1.0

Met **Versie 1.0** bereikt CMDRHelper de eerste volledige
ontwikkelingsstatus van de geplande basisomvang.

Belangrijke wijzigingen en uitbreidingen tot en met Versie 1.0:

### Weergave van hemellichamen en sterren voltooid

-   het beeldmateriaal voor ondersteunde typen planeten, sterren en
    speciale objecten is verder aangevuld.
-   extra sterklassen en bijzondere stertypen worden met eigen grafische
    weergaven getoond in plaats van terug te vallen op de algemene
    standaardweergave.
-   voor geschikte hemellichamen blijven roterende 2:1-equirectangulaire
    texturen beschikbaar in de detailweergave.
-   speciale astronomische objecten kunnen in de detailweergave
    bovendien met geschikte video's worden weergegeven.
-   neutronensterren, witte dwergen, zwarte gaten en superzware zwarte
    gaten krijgen daardoor een aanzienlijk individuelere weergave.
-   gebruikt extern beeld- en videomateriaal wordt met bron en credit
    gedocumenteerd in het gedeelte **„Beeld- en videomateriaal / Media
    Credits"**.

### Meertaligheid voltooid

-   de vertalingen van de gebruikersinterface zijn voor de ondersteunde
    talen voltooid en op één gemeenschappelijke set sleutels afgestemd.
-   alle **12 interfacetalen** gebruiken dezelfde volledige set
    vertaalsleutels.
-   de automatische vertaalcontrole controleert ontbrekende, extra en
    dubbele sleutels en afwijkende formatterings-placeholders.
-   Duits dient als volledig onderhouden referentie voor de
    gebruikersinterface en verdere documentatie.

### Wijzigingen sinds Versie 0.9.9

### Meertaligheid en vertaalcontrole

-   de gebruikersinterface is omgezet naar een centraal meertalig
    systeem.
-   CMDRHelper ondersteunt nu **12 interfacetalen**: **Duits, Engels,
    Frans, Italiaans, Noors (Bokmål), Zweeds, Fins, Pools, Nederlands,
    Spaans, Turks en Grieks**.
-   de taal kan in de instellingen worden gekozen en opgeslagen; de
    taalnamen worden in het keuzeveld elk in hun eigen taal weergegeven.
-   ontbrekende vertalingen gebruiken een vastgelegde fallback-volgorde:
    **geselecteerde taal → Engels → Duits → vertaalsleutel**.
-   de vertalingen bevinden zich centraal in de taalbestanden onder
    `cmdrhelper/i18n/`.
-   het nieuwe ontwikkelaarshulpmiddel `tools/check_i18n.py` controleert
    automatisch:
    -   in het programma gebruikte `tr("...")`-sleutels,
    -   ontbrekende of extra vertaalsleutels,
    -   dubbele sleutels,
    -   afwijkende formatterings-placeholders zoals `{system}` of
        `{count}`.
-   onder Linux wordt de i18n-controle bij het starten automatisch via
    `start.sh` uitgevoerd. Gevonden vertaalproblemen worden duidelijk
    gemeld, maar blokkeren het starten van het programma niet.
-   missie- en Journal-verwerking blijven gescheiden van de gekozen
    CMDRHelper-interfacetaal, zodat interne Elite Dangerous-gegevens
    niet afhankelijk worden van gelokaliseerde weergaveteksten.

### Explorer en systeemkaart

-   de Parent-/Child-structuur van de systeemkaart is herzien: sterren,
    planeten, manen en Belt Clusters worden volgens hun
    Journal-hiërarchie gerangschikt.
-   nieuwe functie **„Alles tonen"** met een compact miniatuuroverzicht
    van het volledige systeem.
-   hemellichamen kunnen in het miniatuuroverzicht worden aangeklikt; de
    hoofdkaart springt daarna direct naar het gekozen hemellichaam.
-   verbeterde navigatie in grote systeemkaarten:
    -   het muiswiel verplaatst de kaart horizontaal.
    -   houd de rechtermuisknop ingedrukt en sleep omhoog/omlaag om de
        kaart verticaal te verplaatsen.
-   de visuele grootte van hemellichamen wordt sterker geschaald op
    basis van de werkelijke straal.
-   de weergave en markering van BIO, GEO, Terraforming, eerste
    ontdekking en First Mapping zijn verder verbeterd.
-   nieuwe **waardelijst** in Explorer: planeten en manen worden per
    regel gesorteerd op hun actuele geschatte mappingwaarde.
-   de waardelijst maakt nu duidelijk onderscheid tussen **First Mapping
    mogelijk**, **al gemapt** en **zelf gemapt**.
-   de momenteel behaalde mappingwaarde wordt gericht in de waardelijst
    benadrukt, terwijl status en metadata bewust rustiger worden
    weergegeven.
-   nieuwe aanduiding **„Nog niet ingeleverd"** voor openstaande
    cartografie- en BIO-waarden over alle systemen sinds de laatste
    verkoop; cartografie en BIO worden afzonderlijk gereset.
-   openstaande Explorer-waarden worden in het hoofdvenster geel
    gemarkeerd, zodat nog niet verkochte gegevens direct herkenbaar
    zijn.

### Explorer-livevensters

-   nieuwe vrij positioneerbare **livevensters voor waardevolle
    hemellichamen en BIO-vondsten**, die tijdens het verkennen
    automatisch verschijnen.
-   positie en grootte van de livevensters worden opgeslagen en bij de
    volgende weergave opnieuw gebruikt.
-   bij de overgang naar een ander sterrenstelsel worden de livevensters
    automatisch gesloten en leeggemaakt; ze verschijnen pas weer zodra
    in het nieuwe systeem passende gegevens worden herkend.
-   het venster **„Waardevolle hemellichamen"** neemt automatisch alle
    planeten en manen op waarvan de momenteel haalbare mappingwaarde de
    in de instellingen gekozen drempel bereikt.
-   dezelfde instelbare drempel bestuurt nu de gele markering in de
    waardelijst, het livevenster voor waardevolle hemellichamen en het
    **gouden kader in de systeemkaart**.
-   het **BIO-livevenster** toont tijdens het spelen compact de
    hemellichamen, herkende geslachten of soorten, scanvoortgang en
    bekende Vista Genomics-waarden.
-   BIO-vondsten gebruiken dezelfde kleurlogica als in het hoofdvenster:
    grijs = via DSS/FSS herkend, wit = eerste monster, geel = tweede
    monster, groen = analyse voltooid.
-   bij gedeeltelijk bepaalde BIO-signalen wordt een planeet automatisch
    uitgeklapt en worden de afzonderlijke vondsten op eigen regels
    weergegeven; nog onbekende signalen blijven zichtbaar.
-   zodra alle BIO-soorten op een hemellichaam volledig zijn
    geanalyseerd, wordt de planeet weer samengevouwen tot één compacte
    groene samenvattingsregel.
-   algemene DSS/FSS-geslachtsnamen worden automatisch vervangen door de
    concrete BIO-soort zodra deze via `ScanOrganic` bekend is.
-   bekende afzonderlijke waarden worden direct bij de betreffende
    BIO-vondst weergegeven; volledig bekende hemellichamen tonen
    bovendien de totale waarde.
-   de livevensters hebben een subtiele roodbruine achtergrond, zodat ze
    tijdens het spelen duidelijk van het CMDRHelper-hoofdvenster te
    onderscheiden zijn.

### BIO-analyse

-   biologische gegevens worden afzonderlijk van de normale
    cartografiewaarden geanalyseerd en weergegeven.
-   aparte **BIO-planetenlijst** met alle hemellichamen waarop
    biologische signalen zijn aangetroffen.
-   BIO-geslachten uit `SAASignalsFound` of `FSSBodySignals` worden ook
    achteraf uit bestaande Journals geïmporteerd.
-   concrete BIO-soorten en varianten uit `ScanOrganic` worden direct in
    de lijst weergegeven.
-   de scanvoortgang per BIO-vondst wordt met kleuren weergegeven:
    -   grijs = alleen bekend via DSS/FSS
    -   wit = eerste monster
    -   geel = tweede monster
    -   groen = derde monster / analyse voltooid
-   de bekende Vista Genomics-basiswaarde wordt al weergegeven zodra een
    BIO-soort eenduidig is bepaald.
-   weergave van de basiswaarde van volledig geanalyseerde BIO-monsters.
-   weergave van de mogelijke **First Logged-totaalwaarde ×5**.
-   bekende BIO-waarden kunnen met reeds aanwezige verkoopgegevens
    worden aangevuld.
-   soorten zonder bekende waarde worden in de analyse gemarkeerd.
-   de BIO-status maakt onderscheid tussen open, bezocht en volledig
    geanalyseerd.

### Missies

-   de verwerking van `MissionRedirected` is verbeterd.
-   omgeleide missies kunnen naam, nieuw doelsysteem of nieuw
    doelstation en informatie over het vorige doel overnemen.
-   missies kunnen in bepaalde gevallen ook worden gereconstrueerd als
    eerder geen volledige `MissionAccepted`-vermelding aanwezig was.
-   de breedte van de missiekolommen kan vrij worden aangepast; de
    gekozen breedtes worden opgeslagen.
-   weergave van de **totale beloning van alle momenteel openstaande
    missies**.

### Afbeeldingen en screenshots

-   eigen screenshotgedeelte met galerij en voorbeeldweergave.
-   automatische conversie van nieuwe Elite Dangerous-BMP-screenshots.
-   uitvoer als PNG of JPG.
-   optioneel verwijderen van het BMP-bestand na succesvolle conversie.
-   instelbare helderheidscorrectie van 0 tot 50%.
-   comfortabeler gebruik van de Elite-screenshotmap onder Steam/Proton.
-   de galerij wordt ook bijgewerkt nadat bestanden extern zijn
    verwijderd.
-   verbeterde zichtbaarheid van de opties voor automatische conversie
    en verwijderen.

### Onlinediensten

-   de automatische EDSM-Journal-overdracht is verder geïntegreerd en
    zichtbaar via het statusgedeelte in het hoofdvenster.
-   status voor overdracht, wachten, fout en uitgeschakelde EDSM.
-   Inara-statusweergave als voorbereiding op latere automatische
    overdracht.

### Bediening en stabiliteit

-   lettertype en lettergrootte van de interface kunnen in de
    instellingen worden gekozen en na een herstart op de volledige
    interface worden toegepast.
-   de instellingenpagina is scrollbaar, zodat alle opties ook bij
    kleinere vensterformaten bereikbaar blijven.
-   zichtbare knop **„Afsluiten"** in de linkerzijbalk.
-   de Single Instance-blokkering voorkomt dat per ongeluk
    tegelijkertijd een tweede programma-instantie wordt gestart.
-   veilig miniatuuroverzicht van het systeem zonder directe rendering
    van de reeds zichtbare Explorer-widget.
-   diverse verbeteringen aan interface, Journal-verwerking, database en
    updateproces.

## Projectstatus

CMDRHelper is in ontwikkeling. Gebruikersinterface, datamodel en
weergave kunnen nog veranderen. Meer typen hemellichamen,
Journal-functies, Explorer-functies, gegevensbronnen en berekeningen
zijn gepland. Linux en Windows worden verder getest.

CMDRHelper is ontstaan als persoonlijk hulpmiddel en wordt stap voor
stap uitgebreid tot een uitgebreidere helper voor Elite Dangerous.

## Beeld- en videomateriaal / Media Credits

CMDRHelper gebruikt voor enkele bijzondere astronomische objecten
visualisaties van de **NASA Scientific Visualization Studio (NASA
SVS)**. De betreffende media blijven eigendom van hun rechthebbenden en
worden vermeld volgens de credits op de NASA SVS-pagina's.

### Neutronenster

-   CMDRHelper-bestand: `star_neutron.webm`
-   Bron: NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animators: Walt Feimer (KBR Wyle Services, LLC) en Lisa Poje (USRA)
-   Bron: https://svs.gsfc.nasa.gov/20267/

### Zwart gat

-   CMDRHelper-bestand: `black_hole.mp4` of de video-extensie die in het
    project wordt gebruikt
-   Bron: NASA Scientific Visualization Studio, **Black Hole Accretion
    Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Bron: https://svs.gsfc.nasa.gov/13326/

### Superzwaar zwart gat

-   CMDRHelper-bestand: `black_hole_supermassive.mp4` of de
    video-extensie die in het project wordt gebruikt
-   Bron: NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Bron: https://svs.gsfc.nasa.gov/14576/

### Witte dwerg

-   CMDRHelper-bestand: `star_white_dwarf.webm`
-   gebruikt NASA-medium: **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Bron: NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animator: Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Bron: https://svs.gsfc.nasa.gov/20344/

Het vermelden van deze bronnen en credits betekent niet dat CMDRHelper
door NASA wordt ondersteund, gecertificeerd of uitgegeven. Voor verder
gebruik van NASA-media gelden de betreffende aanwijzingen en
reproductierichtlijnen van de oorspronkelijke bronnen.

## Licentie

CMDRHelper is vrije software en wordt gepubliceerd onder de **GNU
General Public License Version 3 (GPL-3.0)**.

De broncode mag volgens de voorwaarden van de GPL-3.0 worden gebruikt,
gewijzigd en verder verspreid. Ook bij de verspreiding van afgeleide
versies gelden de voorwaarden van de GPL-3.0.

Copyright © 2026 **Holger Mangold (Faber38)**.

De volledige licentievoorwaarden staan in het bestand `LICENSE`.

## Opmerking over Elite Dangerous

CMDRHelper is een onafhankelijk community-/hobbyproject en geen
officieel product van Frontier Developments.

**Elite Dangerous** en de bijbehorende namen en inhoud zijn eigendom van
de respectieve rechthebbenden.
