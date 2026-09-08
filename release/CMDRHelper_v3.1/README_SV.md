# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Din co-pilot för Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_sv.png)

**Personlig följeslagare för Elite Dangerous – utforskning, navigation och befälhavardata i en överblick**

CMDRHelper är ett fristående skrivbordsprogram som analyserar de lokala Elite Dangerous-journalerna och använder planetära positionsdata från `Status.json`. Det hjälper dig att hitta intressanta himlakroppar, återvända till sparade platser och följa dina resor och fynd. Personliga data bevaras efter omstart och hålls åtskilda per befälhavare.

## Nytt i v3.1 jämfört med v3.0.3

- BIO-förloppet är kompakt: 1/3 gult, 2/3 blått och 3/3 grönt; det slutförda tillståndet ”Klart” är också grönt. Under ”visa automatiskt” har GEO en egen sparad omkopplare: enbart BIO, enbart GEO eller båda tillsammans. Manuellt justerade kolumnbredder i den gemensamma Explorer-tabellen BIO / GEO / ABBAU bevaras när fönstret öppnas igen och efter omstart. Sparade kolumnbredder i popupfönster återställs robustare; ogiltiga värden ersätts med säkra standardbredder.

- Upptäckt och kartläggning skiljs åt och gäller ditt skanningstillfälle: ”Redan upptäckt vid din skanning” och ”Redan kartlagd vid din skanning”. Saknade uppgifter förblir Okända. First Discovery- och First Mapping-kandidater gäller bara vid skanningen; ett historiskt Nej bevisar inte att himlakroppen fortfarande är oupptäckt eller okartlagd i dag. Din egen kartläggning bekräftar ingen officiell förstakartläggning. EDSM-kännedom hålls separat.

- ”EDSM-status-HUD” under ”visa automatiskt” är AV som standard. Efter ankomst till ett system visas ett kort meddelande över Elite i cirka 2,5 sekunder. ”EDSM: KÄNT” betyder en giltig EDSM-träff för systemet. ”EDSM: OKÄNT” betyder ett giltigt EDSM-svar utan systemträff. ”EDSM: INGET SVAR” betyder nätverksfel, HTTP-fel, timeout eller ogiltigt svar, aldrig en bekräftad avsaknad av träff. Kännedom i EDSM är inte samma sak som officiell upptäckt i Elite; namn på första upptäckare eller rapportör utlovas inte. Meddelandet fungerar oberoende av navigations- och last-HUD.

- Besökshistoriken tar med Location, FSDJump och CarrierJump även vid löpande journaluppdatering. Flera platshändelser under en sammanhängande vistelse räknas som ett besök: A → A → A räknas en gång. En verklig återkomst bevaras: A → B → C → A räknas som fyra besök.

- Slutförd egen DSS-kartläggning sparar nu tillförlitligt tidpunkten, använda sonder och effektivitetsmålet. Senare skanningar gör inte längre att befintliga uppgifter förloras.

- Lastfönstret anpassar automatiskt höjden efter innehållet. Vid många poster begränsas höjden och tabellen kan rullas; vald bredd och fönsterposition bevaras. Den befintliga omkopplaren ”Lastutrymmets HUD” finns nu under ”visa automatiskt”, utan en extra omkopplare i lastfönstret.

- För befintliga installationer räcker normalt: installera uppdateringen → starta CMDRHelper. Nödvändiga historiska rättelser av BIO-data, besök och DSS-metadata körs automatiskt; databasen säkerhetskopieras före reparationer som skriver data. Reparationerna är versionsstyrda och idempotenta: lyckade revisioner körs inte om fullständigt vid varje start. Rekonstruktion kräver Elite-journaler som finns kvar, är läsbara och entydigt kan kopplas till en commander. Saknade källor hittas inte på eller räknas som framgång; öppna reparationer provas igen vid nästa start. Databasradering, manuella skript och ny import behövs normalt inte.

## Explorer

Explorer visar det aktuella systemet i tre vyer:

- **Systemkarta:** grafisk visning av kända stjärnor, planeter och månar. Klicka på en himlakropp för att öppna detaljerna. ”Visa alla” öppnar systemöversikten.
- **Värdelista:** Värdelistan visar uppskattningar utifrån den sparade skanningen, inte garanterade återstående utbetalningar. Förstabonuser förblir obekräftade. Verktygstips i karta och lista samt kroppsdetaljer använder samma tidsbestämda tillstånd.
- **BIO / GEO / ABBAU:** biologiska och geologiska signaler, planetära gruvplatser och belagda personliga fynd.

Analyserna skiljer rapporterade signaler från faktiska egna fynd. **BIO ×N** är det rapporterade antalet signaler, ingen bekräftelse på fullständigt analyserade arter. **GRUVDRIFT ×N** räknar planetära gruvplatser utan att avslöja deras enskilda råvaruinnehåll. Personligen utvunna handelsvaror, sekundära material insamlade vid gruvdrift och himlakroppens allmänna materialsammansättning hålls åtskilda.

Explorer visar också uppskattade BIO-värden, framsteg i egna analyser och osålda kartografi- och BIO-data. Värdena bygger på tillgänglig journal- och himlakroppsinformation; saknade data visas inte som egna upptäckter. Kompletterande EDSM-data är extern information som ska skiljas från egna fynd.

Himlakroppsdetaljerna innehåller tillgängliga fysikaliska egenskaper, atmosfär, ringar, material och upptäcktsinformation. Avbildningarna använder lämpliga texturer och animationer för vissa särskilda astronomiska objekt. Cargo-området visar känd last och kapacitet för det skepp eller den SRV som används nu; för Rhino är last och personliga gruvfynd fortsatt olika uppgifter.

Högst upp i Explorer finns **★ Favoriter | Planetnavigering | Visa allt**. Favoriter och planetnavigation öppnar egna fönster; de tre Explorer-vyerna finns kvar tillgängliga.

## Planetnavigation

Planetnavigatorn hjälper dig enbart att flyga till en viss **latitud/longitud på en planet eller måne**. För resor mellan stjärnsystem finns den separata ruttplaneraren.

### Ange ett mål och flyg

Välj målets himlakropp eller använd den aktuella, som identifieras automatiskt när det är möjligt. Ange latitud och longitud samt valfritt ett målnamn. Du behöver inte ange tekniska uppgifter som BodyID eller SystemAddress. Även **0,0** är en giltig koordinat.

Så snart Elite levererar giltiga planetära positionsdata för rätt himlakropp aktiveras kompassen automatiskt. Utan motsvarande data visar navigatorn ett vänteläge. Du kan när som helst ange ett nytt koordinatmål på samma himlakropp; det ersätter det föregående målet.

### Visning under inflygningen

| Målavstånd | Visning |
| --- | --- |
| **Mer än 380 km** | Planetglob med den egna positionen som en vit cirkel och målet som en liten punkt. Målet är orange på den synliga sidan och rött på den dolda baksidan. Spelarpositionen ligger fast i visningen; planet och mål visas relativt den. |
| **Till och med 380 km** | Automatisk växling till ett lutande perspektivrutnät med **50-km-avståndsintervall** och målets inritade position för den fortsatta inflygningen. |

Navigatorfönstret kan storleksändras fritt. Globen eller perspektivrutnätet anpassas proportionellt till det tillgängliga utrymmet; detaljvärdena förblir läsbara.

### Förstå navigationsvärdena

- **Målkoordinater:** målets sparade latitud och longitud.
- **Aktuella koordinater:** din senaste giltiga planetära position.
- **Målavstånd / Avstånd över ytan:** beräknat avstånd till målet över klotytan; den stora avståndsvisningen och detaljvärdet visar samma avstånd med olika avrundning.
- **Bäring:** absolut riktning från aktuell position till målet.
- **Heading:** din aktuella orientering som Elite rapporterar.
- **Relativ riktning:** skillnaden mellan heading och bäring, exempelvis ”23° höger”, ”vänster” eller ”rakt fram”.
- **Målkurs:** den absoluta kurs du kan svänga till i Elite-HUD:en. Den motsvarar bäringen och är ingen ytterligare relativ svängvinkel.

Exempel: **Heading 051° → Målkurs 074° = 23° höger**.

Navigationen beror på spelets statusdata; uppdateringar kan komma fördröjt beroende på spelläget. Ytavståndet är ingen terräng- eller vägrutt. Hinder och terränghöjder längs sträckan beaktas inte.

## Navigations-HUD

Till vänster under **visa automatiskt → Navigations-HUD** kan du aktivera en valfri extra visning direkt ovanpå Elite. Vid giltig planetnavigation visar den:

- relativ riktning,
- absolut målkurs,
- avstånd.

HUD:en är transparent, släpper igenom klick och tar inte fokus: den tar varken musklick eller inmatningsfokus från spelet. Utan giltig navigation blir den automatiskt osynlig; sidofältets kryssruta kan vara fortsatt aktiverad. Den vanliga navigatorn fungerar oberoende av HUD:en.

HUD:en har testats i spelet under **Linux/X11** och **Windows 11 med Elite**. I Windows matchas flera bildskärmar genom deras geometri och Elite-fönstrets position, inte genom matchande bildskärmsnamn.

## Favoriter

**Explorer → ★ Favoriter** öppnar ett eget, återanvändbart fönster. Favoriter tillhör den **aktiva befälhavaren**. Byte av befälhavare uppdaterar vyn; befälhavarvalet i krönikan utökar inte favoritlistan.

### Spara tre typer

Den övre åtgärdsraden erbjuder:

| Åtgärd | Sparad favorit |
| --- | --- |
| **★ Spara aktuellt system** | Det aktuella systemet utan ytkoordinater. |
| **★ Spara planet / måne** | En vald känd planet eller måne i det aktuella systemet utan ytkoordinater. |
| **★ Spara aktuell position** | En plats på ytan med aktuellt system, himlakropp, latitud och longitud. |

Positionsknappen är alltid synlig och bara tillgänglig med giltiga aktuella planetära positionsdata och en aktiv befälhavare. **Klicket låser befälhavare, system, himlakropp och koordinater innan redigeringsdialogen öppnas.** Senare rörelser i spelet ändrar inte positionen. Samma sparflöde finns i planetnavigatorn. Kända interna ID:n följer med automatiskt; inga koordinater hittas på.

Välj ett namn och exakt en kategori: **Bio, Geo, Gruvdrift, Utsikt, Landningsplats, Intressant eller Övrigt**. Anteckning och bild är valfria.

### Hitta, visa och redigera

Den rullningsbara listan, alfabetiskt sorterad efter namn, visar namn, typ, system, himlakropp och koordinater där det är relevant, kategori och liten bildförhandsvisning. **Fritextsökning, typ- och kategorifilter** kan kombineras. Sökningen omfattar namn, system, himlakropp och anteckning.

**Öppna / Visa** visar sparade uppgifter, anteckningen och en större bildförhandsvisning. **Visa i Explorer** använder befintlig systemöversikt eller himlakroppens detaljvy om favoriten tillhör det aktuella Explorer-systemet och motsvarande data finns. För andra system förblir favoritens sparade uppgifter tillgängliga.

**Redigera** ändrar namn, kategori, anteckning och bild. System, himlakropp och sparade koordinater ersätts inte med livevärden. För en annan position skapar du en ny ytfavorit.

**Ta bort** kräver bekräftelse och tar bara bort favoritposten och dess interna bildkopia. Explorer-, journal- och himlakroppsdata bevaras.

### Favoritbilder och senaste skärmbild

Favoritbilder är **helt åtskilda från det vanliga området Bilder**. CMDRHelper hanterar en egen intern kopia i favoritbildsmappen (`data/favorites/images/` vid standardlagring). Originalet varken flyttas eller ändras.

- **Välj bild …** tar emot PNG, JPEG eller WebP och visar en förhandsvisning. Den interna kopian skapas först när du sparar.
- **Använd senaste skärmbilden** läser vid varje klick den faktiska källmappen på nytt. Även motsvarande konverterade Elite-skärmbilder i den aktiva befälhavarens mapp under den inställda konverteringsdestinationen beaktas. Därmed finns en ny skärmbild kvar tillgänglig om den automatiska konverteringen redan raderat dess BMP.
- Läsbara filer med motsvarande Elite- eller konverteringsnamn erbjuds, inte godtyckliga bilder från allmänna bildmappar. Ordningen bestäms av en entydig tagningstid i filnamnet, annars av filtiden. För konverterade bilder används tagningstiden i namnet, inte konverteringstidpunkten.
- Innan du accepterar en hittad skärmbild visas filnamn, tagningstid och en nyladdad förhandsvisning. Bekräfta med **Använd den här bilden**. Om ingen lämplig skärmbild hittas finns det manuella bildvalet kvar. CMDRHelper tar inte själv skärmbilder.

En bild kan senare ersättas eller tas bort. Interna kopior som inte längre behövs tas bort när favoriten sparas eller raderas. **Favoritåtgärder raderar aldrig den ursprungliga skärmbilden eller en vald originalbild.** Om en intern bildfil saknas kan favoriten användas utan förhandsvisning.

### Ytfavorit som mål

**▶ Till målet** skickar sparad himlakropp, latitud, longitud och favoritnamn till den befintliga planetnavigatorn och ersätter dess tidigare mål. Favoriter har ingen egen navigationslogik. Motsvarande giltiga planetära data startar navigationen; annars väntar navigatorn som vanligt.

Andra befälhavares favoriter kan inte användas som egna mål. Byte av befälhavare avslutar ett mål som fortfarande hanteras som den tidigare befälhavarens favoritmål. System- och himlakroppsfavoriter visar befintlig information utan egen ruttplanering.

## Krönika

Krönikan är din sparade rese- och fyndhistorik. Dess **3D-resekarta** visar besökta system och befälhavarrutter. System- och himlakroppsdetaljer hjälper dig att återfinna känd BIO-, GEO-, material-, Codex- och gruvinformation.

### Kombinerade filter

**Tillämpa** eller **Enter i fritextfältet** kör alla inställda filter tillsammans:

- fritext,
- valfritt **Från** och **Till**,
- **Planetära gruvplatser** och **Minst**,
- **Mina gruvfynd** och **Handelsvara**.

En term från **Sökhjälp / Teckenförklaring** förs in i sökfältet och körs tillsammans med redan inställda period- och gruvfilter.

### Period i UTC

Från och Till aktiveras med var sin kryssruta. En enda gräns är också möjlig; utan aktiverad ruta finns ingen tidsbegränsning på den sidan. **Från** inkluderar början av den valda UTC-kalenderdagen. **Till** omfattar hela den valda UTC-dagen. UTC är den gemensamma tidsbasen, inte din lokala kalendertid.

**Faktiska systembesök** är avgörande: minst ett sparat besök måste ligga inom perioden. Att ett system bara blev känt första eller sista gången ersätter inte ett besök. Med aktiv period avser besöksantal, första och sista besök i kartvyn de filtrerade besöken.

Perioden filtrerar besök, inte enskilda upptäckts-, BIO-, GEO- eller gruvhändelser. Känd fyndinformation och personliga gruvmängder förblir sparade **totalvärden**. **”Koppar 56 t” med aktiv period betyder inte automatiskt ”56 t under denna period”.** Om Från ligger efter Till visas ett felmeddelande; ingen databasfråga startas.

### Befälhavare och uppdatering

**Kartans befälhavarval** avgör vilka befälhavarrutter som visas. Personliga fritext- och gruvsökningar gäller däremot den visade eller aktiva befälhavaren. Kartans kryssrutor utökar inte automatiskt personliga sökningar till flera befälhavare.

**Uppdatera krönikan** läser in data på nytt och kör de aktiva filtren igen. **Aktuell position** tillämpar först det aktuella filterläget och centrerar endast på det aktuella systemet om det finns i resultatkartan. Annars visas ett meddelande; filtren behålls.

**Återställ** tömmer fritext, inaktiverar Från/Till och återställer de synliga datumfälten. Gruvrutorna avmarkeras, minsta antal blir 0 och handelsvara blir Alla. Befälhavarvalet bevaras; därefter laddas den vanliga krönikan.

Vid **inga träffar** töms karta och rutter, träfflistan töms och döljs, detaljvisningen återställs och ett öppet systemdetaljfönster i krönikan stängs. Gamla resultat står inte kvar.

### Kartkontroller

- Dra med vänster musknapp: rotera.
- Dra med höger musknapp: flytta.
- Dra med mittknappen: rita en zoomruta.
- Mushjul: zooma.
- **Justera:** återställ orienteringen till galaktisk vy ovanifrån; förskjutning och zoom behålls.

## Bilder och automatisk skärmbildskonvertering

I **Bilder** ställer du in Elite-skärmbildernas källmapp och konverteringsdestination. Automatisk konvertering omvandlar nytillkomna BMP-skärmbilder till **PNG eller JPEG**. Justerbar uppljusning finns. BMP-filer som redan finns vid start konverteras inte retroaktivt bara genom att övervakningen aktiveras; manuell konvertering finns för dem.

Konverterade filnamn innehåller tagningstid, befälhavare och system, och filerna lagras per befälhavare. Automatisk tilldelning följer den aktiva journalbefälhavaren. Ett annat val i galleriet ändrar inte denna aktiva befälhavare.

Alternativet att **radera ursprunglig BMP efter lyckad konvertering** tillhör enbart denna konvertering och har en egen inställning. Det är oberoende av hanteringen av favoritbilder.

Galleriet visar motsvarande konverterade bilder med förhandsvisning. Det läses in på nytt när det visas igen; uppdatering beaktar också de aktuella filerna. Val och stor förhandsvisning uppdateras tillsammans. Om den valda bilden försvinner väljs en befintlig bild eller förhandsvisningen töms. Bilder-området har även eget bildval och radering med bekräftelse.

## Andra vyer

- **Översikt:** aktiv befälhavare, skepp, plats, journalidentifiering, öppna uppdrag och onlinestatus.
- **Uppdrag:** beständigt sparade öppna uppdrag med kända mål, framsteg och slutförandestatus. Saknade uppgifter fylls inte i eller hittas på.
- **CMDR:** tillgångar, grader, statistik, MercCoins, skepp/flotta och känd Fleet Carrier-position. MercCoins visas som totaler rapporterade av Frontier, inte som ett självberäknat saldo.
- **Ruttplanerare:** separat planering för skepp och Fleet Carrier med Spansh. Beräknade carrierrutter kan exporteras som CSV för CTSVision. Beräkningen kräver anslutning till den externa tjänsten.

## Befälhavare, lokala data och onlinetjänster

CMDRHelper identifierar den aktiva befälhavaren med Frontier-ID från den aktuella journalsessionen. Personlig utforskning, uppdrag, tillgångar, favoriter och onlineuppgifter lagras separat. Att bara visa en annan befälhavare ändrar varken livebefälhavaren eller tilldelningen av uppladdningar.

Den lokala SQLite-databasen bevarar kända system, himlakroppar och personlig historik över omstarter. Nya fullständiga journalposter behandlas under spel; sparade läspositioner undviker onödig omläsning. Om plats eller befälhavare inte stämmer, kontrollera först journalidentifieringen och journalmappen i inställningarna.

**EDSM** kan ge kompletterande systemdata. Journaldata som stöds kan skickas till **EDSM och Inara** när tjänsten konfigurerats och aktiverats med den aktiva befälhavarens egna uppgifter. En befälhavare använder inte automatiskt någon annans API-nyckel. Lokal lagring fungerar oberoende av tillgänglig onlineanslutning.

## Språk och kontexthjälp

Gränssnittet stöder **12 språk**: **DE, EN, FR, IT, NO, SV, FI, PL, NL, ES, TR, EL** – tyska, engelska, franska, italienska, norska, svenska, finska, polska, nederländska, spanska, turkiska och grekiska.

Det finns för närvarande **937 UI-i18n-nycklar per språk**. **? Hjälp** erbjuder **10 utförliga kontextuella hjälpämnen på alla 12 språk**. Favoriter ingår i Explorer-hjälpen; planetnavigation har ett eget ämne direkt tillgängligt från navigatorn. Hjälpen använder aktuellt gränssnittsspråk och behåller tyska som reserv om en katalog eller post saknas.

## Förutsättningar

| Plattform | Python |
| --- | --- |
| **Windows** | **Python 3.10 eller senare, x64 krävs.** Ingen konstgjord övre gräns för befintliga versioner. Faktiska paket- och importkontroller avgör sedan om miljön fungerar. |
| **Linux** | **Python 3.10 eller senare**, 64-bit rekommenderas. venv-modulen för Python-versionen måste finnas. |

De nödvändiga paketen finns i `requirements.txt`:

```text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

Installationen laddar ned dessa beroenden. Lokala Elite-filer måste vara åtkomliga för journalanalys och planetnavigation. På Linux kan Elite köras via Steam/Proton; de faktiska journal- och skärmbildssökvägarna ställs in i CMDRHelper. Linux-HUD-stödet ovan avser X11.

## Installation på Linux

Packa upp hela projektet eller utgåvan och kör i projektmappen:

```bash
./install.sh
./start.sh
```

Skripten använder enbart den här installationens lokala `venv`. De följer symboliska skriptlänkar, kontrollerar Python och pip och kan reparera en skadad lokal miljö utan att röra personliga data eller Elite-journaler. Saknade systempaket installeras inte automatiskt; installationsprogrammet rapporterar om venv-modulen saknas. Det befintliga installationssättet för Linux är oförändrat.

## Installation på Windows

1. Packa upp hela ZIP-filen i en egen mapp.
2. Starta **install.bat**, som anropar medföljande **install-windows.ps1**.
3. Efter lyckad installation startar du CMDRHelper med **start.bat**.

Befintlig **Python från 3.10 och senare, x64**, accepteras utan konstgjort versionstak. En framtida Python-version avvisas inte enbart på grund av versionsnumret. En lämplig befintlig Python eller användbar lokal venv förhindrar onödig automatisk Python-installation.

Om ingen lämplig Python finns erbjuder installationsprogrammet, efter samtycke, automatisk installation via **winget**. Den fasta versionsserien **Python 3.14 x64** är medvetet vald för detta; valet är separat från den öppna regeln för befintliga Python-versioner. Om automatisk installation inte är möjlig rapporteras felet.

Installationsprogrammet skapar, kontrollerar eller reparerar bara den **lokala venv-miljön för denna CMDRHelper-kopia**, installerar beroendena och kör **pip check** samt importkontroller för **PySide6, PySide6.QtWidgets, numpy och PIL**. Bara dessa faktiska kontroller avgör om miljön är användbar. Om de misslyckas avbryts installationen med ett begripligt felmeddelande. Andra virtuella miljöer repareras eller ersätts inte.

## Diagnostik och distributionspaket

Vid problem hjälper journal- och onlinestatusindikatorerna samt loggfilerna i mappen `logs`. Personliga data lagras lokalt; säkerhetskopiering av favoriter kräver även deras interna bildkopior utöver databasen.

Använd `./create_release.sh` för att skapa ett eget distributionspaket. Programversionen hanteras centralt i `cmdrhelper/version.py` och läses av distributionsskriptet. Paketet innehåller programkod och resurser, men ingen personlig databas, venv, Git- eller cachefiler.

## Bild- och videomaterial / Media Credits

CMDRHelper använder visualiseringar från **NASA Scientific Visualization
Studio (NASA SVS)** för vissa speciella astronomiska objekt. Respektive
media förblir rättighetsinnehavarnas egendom och krediteras enligt
uppgifterna på NASA SVS-sidorna.

### Neutronstjärna

-   CMDRHelper-fil: `star_neutron.webm`
-   Källa: NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatörer: Walt Feimer (KBR Wyle Services, LLC) och Lisa Poje
    (USRA)
-   Källa: https://svs.gsfc.nasa.gov/20267/

### Svart hål

-   CMDRHelper-fil: `black_hole.mp4` respektive den videofiländelse som
    används i projektet
-   Källa: NASA Scientific Visualization Studio, **Black Hole Accretion
    Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Källa: https://svs.gsfc.nasa.gov/13326/

### Supermassivt svart hål

-   CMDRHelper-fil: `black_hole_supermassive.mp4` respektive den
    videofiländelse som används i projektet
-   Källa: NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Källa: https://svs.gsfc.nasa.gov/14576/

### Vit dvärg

-   CMDRHelper-fil: `star_white_dwarf.webm`
-   använt NASA-medium: **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Källa: NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatör: Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Källa: https://svs.gsfc.nasa.gov/20344/

Angivandet av dessa källor och credits innebär inte att CMDRHelper
stöds, certifieras eller ges ut av NASA. För vidare användning av
NASA-medier gäller respektive anvisningar och reproduktionsriktlinjer
från originalkällorna.

## Licens

CMDRHelper är fri programvara och publiceras under **GNU General Public
License Version 3 (GPL-3.0)**.

Källkoden får användas, ändras och distribueras vidare enligt villkoren
i GPL-3.0. Vid distribution av härledda versioner gäller också villkoren
i GPL-3.0.

Copyright © 2026 **Holger Mangold (Faber38)**.

De fullständiga licensvillkoren finns i filen `LICENSE`.

## Information om Elite Dangerous

CMDRHelper är ett oberoende community-/hobbyprojekt och inte en
officiell produkt från Frontier Developments.

**Elite Dangerous** och tillhörande namn och innehåll tillhör sina
respektive rättighetsinnehavare.
