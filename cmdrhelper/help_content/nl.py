"""Dutch content for contextual help."""


HELP_TOPICS = {
    "materials": (
        'Materialen',
        """<h2>Materialen</h2>
<h3>CMDRHelper v3.2</h3>
<p>Engineering-materiaalbeheer: alle 146 materialen in Raw, Manufactured en Encoded, met graden, capaciteiten en uitzonderingen. Actuele voorraad per commander, zoeken, filters, vijf subtiele rijachtergronden en opgeslagen kolombreedtes en volgorde bieden overzicht. Onbekende voorraad blijft onderscheiden van nul.</p>
<p>Odyssey-inventaris: het vierde tabblad bevat 223 catalogusidentiteiten voor goederen, componenten, gegevens en verbruiksartikelen. Scheepskluis, rugzak en betrouwbaar totaal blijven gescheiden; missiestapels, missiestatus en engineeringgebruik zijn zichtbaar. Positieve aantallen zijn goudkleurig. Ontbrekende naamvertalingen vallen terug op Engels.</p>
<p>Materiaalhandelaren zoeken (Handelaar zoeken → Open routeplanner): op verzoek zoekt Spansh afzonderlijk naar Raw, Manufactured en Encoded vanuit het huidige commandersysteem. Carriers worden uitgesloten en stationdetails gecontroleerd. De afstand in ly is rechtstreeks tussen systemen; gemeenschapsgegevens garanderen geen toegang. Doorsturen naar de routeplanner stelt alleen het doelsysteem in en start geen route. Er is geen zoekfunctie voor Odyssey-handelaren.</p>
<p>Dit hoofdonderdeel toont de engineeringmaterialen van de commander die momenteel wordt bekeken. De selectie in de CMDR-weergave geldt ook hier; de gegevens van andere commanders blijven gescheiden.</p>
<h3>Drie categorieën</h3>
<p>De tabbladen Grondstoffen, Vervaardigde materialen en Gecodeerde gegevens bevatten alle 146 catalogusmaterialen, inclusief Guardian- en Thargoid-materialen. De lijst is gesorteerd op graad en binnen elke graad alfabetisch.</p>
<h3>Voorraad en balken</h3>
<p>De getallen tonen voorraad / maximum, bijvoorbeeld Vanadium 244 / 250. De bijbehorende balk toont 97,6 %. Ook materialen die je nooit hebt bezeten verschijnen met 0 als de voorraad betrouwbaar bekend is.</p>
<p>Lege voorraden zijn subtiel rood gemarkeerd, lage voorraden geel/oranje en bijna volle of volle voorraden groen. De getallen blijven onafhankelijk van de kleuren zichtbaar.</p>
<h3>Zoeken en filters</h3>
<p>De zoekfunctie houdt rekening met de weergegeven en de Engelse materiaalnaam. Zoeken kan met alle filters worden gecombineerd: Alle, Leeg (0), Laag (meer dan 0 tot en met 20 %), Bijna vol (vanaf 80 % tot minder dan 100 %) en Vol (100 %). Waarden tussen 20 % en 80 % verschijnen alleen onder Alle. Tabbladen en filters worden bij de volgende start hersteld.</p>
<h3>Onbekende waarden</h3>
<p>Zonder betrouwbare volledige voorraad verschijnt bijvoorbeeld ? / 250. Bij een onbekend maximum verschijnt bijvoorbeeld 12 / ?. In beide gevallen is er geen percentage of balk; deze materialen verschijnen uitsluitend onder Alle. Een onbekende graad staat in een aparte groep aan het einde van de lijst.</p>
<h3>Live bijwerken</h3>
<p>Nieuwe journaalgebeurtenissen werken de voorraad automatisch bij, ook na materiaalruil, engineering, synthese of materiaalbeloningen. Tijdens het eerste inlezen verschijnt een laadmelding. Nieuw verzameld materiaal wordt kort gemarkeerd met een aanduiding zoals Vanadium +1; verbruik veroorzaakt geen verzamelmelding.</p>
<h3>Materiaalnamen</h3>
<p>Als een materiaalnaam nog niet beschikbaar is in de gekozen taal, verschijnt de Engelse weergavenaam. Interne journaalsymbolen vervangen geen bestaande weergavenamen.</p>
<h3>Odyssey</h3>
<p>Het vierde tabblad onder Materialen bevat Goederen, Componenten, Data en Verbruiksartikelen. Scheepskluis en Rugzak tonen hun voorraden afzonderlijk. Totaal toont de som alleen wanneer beide toestanden betrouwbaar bij elkaar passen. Een verouderde rugzakvoorraad wordt bewust niet als actueel weergegeven of bij het totaal opgeteld; ? betekent een onbekende of momenteel niet betrouwbaar te reconstrueren voorraad. De grens van 1000 geldt per scheepskluiscategorie, niet voor afzonderlijke voorwerpen. Het bovenstaande voorbeeld voor engineeringmaterialen bepaalt geen individueel maximum voor Odyssey-voorwerpen. Voor verbruiksartikelen bestaat nog geen volledig gevalideerde capaciteitsregel; er wordt daarom geen onbevestigde capaciteit getoond.</p>
<p>Gebruik toont de gebruiksaanduidingen van het voorwerp. Missie betekent dat de concrete inventarisstapel aan een missie is gekoppeld, niet dat het voorwerptype in het algemeen een missievoorwerp is. Gewone en missiegebonden stapels blijven gescheiden. Ook na voltooiing van een missie blijft een voorwerp gemarkeerd zolang het journaal het in de voorraad vermeldt; voltooiing verwijdert het niet automatisch. De tooltip toont het missienummer en de bekende status. Engineering betekent dat de statische Odyssey-catalogus minstens één bevestigd gebruik kent: pakupgrade, wapenupgrade, pakmodificatie, wapenmodificatie of het ontgrendelen van een ingenieur. De afzonderlijke toepassingen staan in de tooltip. Een ontbrekende aanduiding betekent niet dat het voorwerp nutteloos of uitsluitend verhandelbaar is. Ook Powerplay-voorwerpen en andere bijzondere voorwerpen kunnen worden weergegeven.</p>
<p>De zoekfunctie vindt de weergegeven lokale en Engelse materiaal-/voorwerpnamen. De zes Odyssey-filters zijn Alle (alle voorwerpen), Missie (stapels met een missiekoppeling), Engineering (voorwerpen met bevestigd engineeringgebruik), Rugzak (rugzakvoorraad groter dan nul), Scheepskluis (kluisvoorraad groter dan nul) en Voorraad 0 (betrouwbaar bekende totale voorraad van 0). Onbekende voorraad ? is niet 0 en valt niet onder Voorraad 0. Ontbrekende naamvertalingen vallen terug op het Engels, zodat sommige namen in de gekozen taal Engels kunnen blijven. Dit is bedoeld en is geen vertaalfout in de voorraadlogica.</p>
<p>De voorraad wordt op de achtergrond automatisch bijgewerkt. Bevestigde nieuwe vondsten kunnen kort worden gemarkeerd. Bij een commanderwissel worden oude voorraden direct verwijderd. Subtabbladen, filters, kolombreedtes en kolomvolgorde worden voor Odyssey afzonderlijk opgeslagen.</p>""",
    ),'overview': ('Overzicht',
              '<h2>Overzicht</h2>\n'
              '<p>Het overzicht is de startpagina van CMDRHelper. Het vat de belangrijkste '
              'informatie over de momenteel actieve commandant samen en laat in één oogopslag zien '
              'of het journaal, de locatie en de onlinediensten correct worden herkend.</p>\n'
              '\n'
              '<h3>Commandant & schip</h3>\n'
              '<p>De commandant die wordt herkend uit het Elite Dangerous Journal en het schip dat '
              'momenteel in gebruik is, worden hier weergegeven.</p>\n'
              '<p>CMDRHelper wijst persoonlijke gegevens toe aan de betreffende commandant op '
              'basis van de Frontier ID (FID). Hierdoor blijven gegevens van verschillende '
              'commandanten van elkaar gescheiden.</p>\n'
              '<p>Bij het wisselen van commandant wordt de opgeslagen informatie geladen die bij '
              'de nieuwe commandant hoort.</p>\n'
              '\n'
              '<p>CMDRHelper toont de spelmodus die Elite het laatst heeft gemeld. Open, Solo en Privégroep worden herkend via LoadGame. Bij privégroepen wordt de door Elite gemelde groepsnaam ongewijzigd weergegeven. Dit betekent niet dat Elite momenteel actief is.</p>\n'
              '<h3>tijdschrift</h3>\n'
              '<p>CMDRHelper gebruikt de journaalbestanden van Elite Dangerous als belangrijkste '
              'gegevensbron.</p>\n'
              '<p>De journaalweergave informeert of journaalbestanden zijn gevonden en toegewezen '
              'aan de actieve commandant. Nieuwe volledige journaalposten worden automatisch '
              'verwerkt tijdens het spelen.</p>\n'
              '<p>Reeds verwerkte journaalgebieden worden opgeslagen, zodat CMDRHelper bij de '
              'volgende start niet elk journaal opnieuw volledig hoeft te beoordelen.</p>\n'
              '\n'
              '<h3>Huidige locatie</h3>\n'
              '<p>Toont het momenteel bekende sterrenstelsel en – voor zover bekend uit het '
              'journaal – de exacte locatie van de commandant.</p>\n'
              '<p>De locatie wordt bijgewerkt door gebeurtenissen zoals sprongen, aanmeren en '
              'andere positierapporten en per commando opgeslagen.</p>\n'
              '\n'
              '<h3>Missies</h3>\n'
              '<p>Dit gebied toont het aantal momenteel bekende open missies.</p>\n'
              '<p>De knop ‘Missies’ of het menu-item brengt je naar het volledige missieoverzicht '
              'met de bekende missiedoelstellingen en statusinformatie.</p>\n'
              '\n'
              '<h3>Laatste stand</h3>\n'
              '<p>‘Laatste staat’ vat de laatst bekende persistente commandantstaat samen. '
              'Hierdoor kan belangrijke informatie worden hersteld, zelfs na het opnieuw opstarten '
              'van Elite Dangerous of CMDRHelper.</p>\n'
              '\n'
              '<h3>Laatste systemen</h3>\n'
              '<p>Hier worden onlangs bezochte of uit het tijdschrift herkende systemen '
              'weergegeven.</p>\n'
              '<p>De lijst dient als een snel overzicht van de recente reis van de '
              'commandant.</p>\n'
              '<p>De bezoekgeschiedenis verwerkt Location, FSDJump en CarrierJump ook tijdens live journalupdates. Meerdere locatiegebeurtenissen tijdens één ononderbroken verblijf tellen als één bezoek: A → A → A telt eenmaal. Een echte terugkeer blijft behouden: A → B → C → A telt vier bezoeken.</p>\n\n'
              '<h3>Onlinestatus</h3>\n'
              '<p>Er zijn extra statusindicatoren bovenaan het hoofdvenster:</p>\n'
              '<ul>\n'
              '<li><b>Journaal herkend</b>– CMDRHelper heeft een geldige journaalbron en '
              'commandantidentiteit gedetecteerd.</li>\n'
              '<li><b>EDSM</b>– toont de huidige status van de EDSM-verzending voor het actieve '
              'journaal FID.</li>\n'
              '<li><b>INARA</b>– toont de huidige status van de Inara-verzending voor het actieve '
              'journaal FID.</li>\n'
              '</ul>\n'
              '<p>Onlinetoegangsgegevens worden voor elke commandant afzonderlijk beheerd. Een '
              'commandant gebruikt nooit automatisch de API-Key van een andere commandant.</p>\n'
              '\n'
              '<h3>Belangrijk voor meerdere commandanten</h3>\n'
              '<p>De live gegevens zijn altijd afhankelijk van de commandant die duidelijk werd '
              'geïdentificeerd door de huidige Elite Dangerous journaalsessie.</p>\n'
              '<p>Alleen het weergeven van een andere commandant in een weergave verandert de '
              'actieve live-commandant niet en heeft geen invloed op een EDSM- of '
              'Inara-uitzending.</p>\n'
              '\n'
              '<h3>Tip</h3>\n'
              '<p>Als de commandant, het schip of de locatie niet overeenkomt met de huidige '
              'status van het spel, controleer dan eerst de journaalweergave bovenaan en '
              'controleer vervolgens de journaalmap die is ingesteld onder “Instellingen”.</p>'
              '<p>Open verschijnt in rood, Solo in goud en Privégroep in groen, met de gemelde groepsnaam. De modus wordt uit beschikbare journalen gereconstrueerd en bij nieuwe LoadGame-vermeldingen bijgewerkt.</p>\n<p>Een enkele klik op een vermelding bij recente systemen kopieert de systeemnaam naar het klembord. “✓ Gekopieerd: &lt;Systeem&gt;” verschijnt kort.</p>\n'),
 'missions': ('Missies',
              '<h2>Missies</h2>\n'
              '<p>De missieweergave toont de missies van de momenteel bekeken commandant bekend '
              'uit het Elite Dangerous Journal. CMDRHelper slaat missiegegevens op per '
              'commandobasis op, zodat open missies behouden blijven, zelfs na een herstart van '
              'Elite Dangerous of CMDRHelper.</p>\n'
              '\n'
              '<h3>Open missies</h3>\n'
              '<p>Er komen nieuwe missies uit<code>MissionAccepted</code>overgenomen en permanent '
              'opgeslagen.</p>\n'
              '<p>Zolang er geen laatste missiegebeurtenis is, blijft de missie open. Een nieuwe '
              'spelsessie zonder missielijst verwijdert mogelijk niet automatisch bekende open '
              'missies.</p>\n'
              '\n'
              '<h3>Missiestatus</h3>\n'
              '<p>CMDRHelper verwerkt onder meer de volgende statuswijzigingen:</p>\n'
              '<ul>\n'
              '<li>Missie geaccepteerd</li>\n'
              '<li>Missie voltooid</li>\n'
              '<li>Missie mislukt</li>\n'
              '<li>Missie afgebroken</li>\n'
              '<li>Missiedoel omgeleid</li>\n'
              '<li>Vooruitgang bij ondersteunde vracht-/depotmissies</li>\n'
              '</ul>\n'
              '<p>Een laatste gebeurtenis verandert alleen de bijbehorende missie.</p>\n'
              '\n'
              '<h3>Missies van het tijdschrift</h3>\n'
              '<p>Elite Dangerous biedt missie-informatie over verschillende dagboekevenementen. '
              'CMDRHelper voegt deze gebeurtenissen samen tot een aanhoudende missiestatus.</p>\n'
              '<p>Een echte volledige missie-gebeurtenis kan dienen als een gezaghebbende '
              'momentopname. Als een dergelijk evenement ontbreekt, zullen oudere open missies '
              'alleen om deze reden niet worden gesloten.</p>\n'
              '\n'
              '<h3>Bestemmingen en plaatsen</h3>\n'
              '<p>Voor zover Elite de informatie in het tijdschrift verstrekt, toont CMDRHelper '
              'het volgende:</p>\n'
              '<ul>\n'
              '<li>Doelsysteem</li>\n'
              '<li>Bestemmingsstation of bestemming</li>\n'
              '<li>Doelplaneet of lichaam</li>\n'
              '<li>Missie-aanduiding</li>\n'
              '<li>bekende vooruitgang</li>\n'
              '<li>huidige status</li>\n'
              '</ul>\n'
              '<p>Niet elke missie levert alle informatie op. Ontbrekende gegevens zijn niet '
              'bedacht door CMDRHelper.</p>\n'
              '\n'
              '<h3>Volharding en herstart</h3>\n'
              '<p>Open missies worden opgeslagen in de commandantgerelateerde database.</p>\n'
              '<p>Dit betekent dat ze behouden blijven, zelfs als:</p>\n'
              '<ul>\n'
              '<li>Elite Dangerous wordt beëindigd en later opnieuw gestart</li>\n'
              '<li>CMDRHelper is daartussen gesloten</li>\n'
              '<li>De nieuwe journaalsessie bevat aanvankelijk geen missiegebeurtenissen</li>\n'
              '</ul>\n'
              '<p>Alleen een gedocumenteerde missiegebeurtenis verandert de opgeslagen '
              'status.</p>\n'
              '\n'
              '<h3>Verschillende commandanten</h3>\n'
              '<p>Missies worden strikt gescheiden door de commandant.</p>\n'
              '<p>Een missiegebeurtenis wordt alleen toegewezen aan de commandant wiens '
              'dagboeksessie uniek is geïdentificeerd. Missies van een andere commandant mogen '
              'niet worden weergegeven of aangepast.</p>\n'
              '\n'
              '<h3>Verweesde of niet langer geldige missies</h3>\n'
              '<p>Als oudere dagboekgegevens of een eerdere import een missie openhouden, ook al '
              'bestaat deze niet meer in het spel, kan de bestaande functie voor het opnieuw '
              'instellen/opschonen van verweesde missies worden gebruikt.</p>\n'
              '<p>Deze functie mag alleen worden gebruikt als duidelijk is dat de weergegeven '
              'missie niet langer actief is.</p>\n'
              '\n'
              '<h3>Onlinediensten</h3>\n'
              '<p>Ondersteunde missiegebeurtenissen kunnen bovendien naar Inara worden verzonden '
              'als er een geldige en geactiveerde Inara-toegang is ingesteld voor het actieve '
              'journaal FID.</p>\n'
              '<p>Een ontbrekende of onbereikbare Inara-verbinding heeft geen invloed op de lokale '
              'missieopslag.</p>\n'
              '\n'
              '<h3>Tip</h3>\n'
              '<p>Als een missie niet verschijnt of een onjuiste status vertoont, controleer dan '
              'eerst of Elite Dangerous de bijbehorende missiegebeurtenis al naar het journaal '
              'heeft geschreven.</p>\n'
              '<p>CMDRHelper kan alleen informatie weergeven die het journaal daadwerkelijk levert '
              'of die al is opgeslagen uit eerdere unieke missiegebeurtenissen.</p>'),
 'explorer': ('Ontdekkingsreiziger',
              '<h2>Ontdekkingsreiziger</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Systeemoverzicht: de nieuwe Elite-achtige weergave vervangt het miniatuuroverzicht in Explorer en Kroniek. Sterren en planeten vormen de hoofdstructuur met manen daaronder; meervoudige sterrenstelsels blijven leesbaar. Zoomen, scrollen, passend maken en klikken op hemellichamen geven toegang tot details.</p>\n<p>Compacte asteroïdengordels: clusters worden gegroepeerd tot gordels in het overzicht en de gewone systeemkaarten van Explorer en Kroniek. Alle afzonderlijke clustergegevens blijven bewaard.</p>\n<p>Cartografie hersteld: een scan na DSS-kartering zet onverkochte verkenningswaarden, karteringstijd en efficiëntie niet meer terug. Onjuiste registraties worden bij het starten hersteld uit beschikbare journals met eenduidige toewijzing. Zonder die bronnen blijft herstel openstaan; de database hoeft niet verwijderd te worden.</p>\n'
              '<p>De Explorer evalueert de systemen en hemellichamen die door de actieve '
              'commandant zijn ontdekt en gescand. Het combineert uw eigen Elite '
              'Dangerous-dagboekgegevens met reeds beschikbare aanvullende informatie en geeft '
              'gegevens over onderzoek, cartografie, biologische/geologische signalen en '
              'dagbouwgegevens samen weer.</p>\n'
              '\n'
              '<h3>Huidig \u200b\u200bsysteem</h3>\n'
              '<p>Het huidige kennisniveau over het systeem wordt in het bovenste gedeelte '
              'samengevat.</p>\n'
              '<p>Deze omvatten onder meer:</p>\n'
              '<ul>\n'
              '<li>bekende en zelfs opgenomen lichamen in het tijdschrift</li>\n'
              '<li>bestaande signalen</li>\n'
              '<li>Waarden scannen</li>\n'
              '<li>cartografische waarde al bereikt</li>\n'
              '<li>mogelijke totale waarde indien volledig in kaart gebracht</li>\n'
              '<li>BIO-status en geschatte BIO-waarden</li>\n'
              '<li>Cartografie- en BIO-gegevens die nog niet zijn ingediend</li>\n'
              '</ul>\n'
              '<p>De getoonde waarden zijn gebaseerd op de daadwerkelijk beschikbare gegevens. '
              'Ontbrekende informatie wordt niet als een afzonderlijke ontdekking '
              'gepresenteerd.</p>\n'
              '\n'
              '<h3>Systeemkaart</h3>\n'
              '<p>De systeemkaart geeft grafisch sterren, planeten, manen en andere bekende '
              'lichamen in het huidige systeem weer.</p>\n'
              '<p>Er kan op een lichaam worden geklikt om de gedetailleerde weergave ervan te '
              'openen.</p>\n'
              '<p>Het display toont onder meer lichaamstype, afstand en – indien beschikbaar – '
              'scan- en cartografiewaarden, evenals speciale verkenningseigenschappen.</p>\n'
              '\n'
              '<h3>BIOLOGISCH ×N</h3>\n'
              '<p>BIO ×N geeft het aantal biologische signalen van een lichaam aan dat door het '
              'spel wordt gerapporteerd.</p>\n'
              '<p>Het getal geeft in eerste instantie alleen aan hoeveel biologische signalen of '
              'geslachten zijn gerapporteerd. Het betekent niet automatisch dat alle biologische '
              'soorten al zijn gevonden of geanalyseerd.</p>\n'
              '<p>Werkelijke eigen organische ontdekkingen worden apart bewaard.</p>\n'
              '\n'
              '<h3>GEO×N</h3>\n'
              '<p>GEO ×N toont het aantal geologische signalen van een lichaam dat door het spel '
              'wordt gerapporteerd.</p>\n'
              '<p>Deze kunnen bijvoorbeeld geologische kenmerken omvatten, zoals fumarolen of '
              'geisers. CMDRHelper geeft alleen de informatie weer die blijkt uit de bestaande '
              'journaal-/bodygegevens.</p>\n'
              '\n'
              '<h3>ABBAU ×N</h3>\n'
              '<p>ABBAU ×N toont het aantal planetaire mijnlocaties van een lichaam gerapporteerd '
              'door Elite Dangerous.</p>\n'
              '<p>Voorbeeld:</p>\n'
              '<p><b>ABBAU ×24</b></p>\n'
              '<p>betekent dat er voor dit lichaam 24 planetaire mijnlocaties zijn '
              'gerapporteerd.</p>\n'
              '<p>Het getal zegt niet welke grondstof op één locatie gewonnen kan worden.</p>\n'
              '\n'
              '<h3>Eigen mijnvondsten</h3>\n'
              '<p>Als de commandant daadwerkelijk dagbouw heeft uitgevoerd met de Rhino, slaat de '
              'CMDRHelper de persoonlijke bevindingen apart gedocumenteerd op.</p>\n'
              '<p>Er wordt onderscheid gemaakt tussen:</p>\n'
              '<ul>\n'
              '<li>feitelijk verkregen goederen, b.v. B. Koper in tonnen</li>\n'
              '<li>secundaire materialen verzameld tijdens de mijnbouw</li>\n'
              '<li>algemene oppervlaktematerialen van het lichaam</li>\n'
              '</ul>\n'
              '<p>Een voorbeeld van een persoonlijke vondst zou zijn:</p>\n'
              '<p><b>Koper – 56 t</b></p>\n'
              '<p>Uit deze informatie blijkt dat deze commandant daar daadwerkelijk 56 ton koper '
              'heeft gewonnen.</p>\n'
              '<p>De persoonlijke mijnvondsten worden per commandant bewaard en worden niet '
              'vermengd met de vondsten van andere commandanten.</p>\n'
              '\n'
              '<h3>Materialen van het lichaamsoppervlak</h3>\n'
              '<p><code>Scan.Materials</code>beschrijft de algemene '
              'oppervlaktemateriaalsamenstelling van een lichaam.</p>\n'
              '<p>IJzer, nikkel, zwavel of andere materialen kunnen bijvoorbeeld met procentuele '
              'waarden worden weergegeven.</p>\n'
              '<p>Deze waarden mogen niet worden verward met de grondstoffen van een planetair '
              'mijndepot. Frontier biedt geen enkel gedocumenteerd direct verband tussen deze '
              'algemene lichaamsmaterialen en de inhoud van een individuele mijnsite in het '
              'Journal.</p>\n'
              '\n'
              '<h3>Terraforming</h3>\n'
              '<p>Het symbool of label voor terraforming geeft aan dat een lichaam op basis van de '
              'beschikbare gegevens als kandidaat voor terraforming wordt beschouwd.</p>\n'
              '\n'
              '<h3>Eerste ontdekking</h3>\n'
              '<p>‘Al ontdekt tijdens jouw scan’ beschrijft de toestand vóór je scan van destijds. Ja betekent eerder ontdekt, Nee betekent toen nog niet ontdekt; ontbrekende informatie blijft Onbekend. ★ markeert een First Discovery-kandidaat op het scantijdstip, geen gegarandeerde officiële eerste claim die vandaag nog beschikbaar is.</p>\n<p>Een historische WasDiscovered=false of WasMapped=false betekent niet dat het hemellichaam vandaag nog onontdekt of ongekarteerd is. Ook na gegevensverkoop of een herbezoek blijven dit historische waarnemingen. Bekendheid bij EDSM is afzonderlijke informatie en bewijst geen officiële ontdekking in Elite. Er wordt geen officiële eerste ontdekker uit afgeleid.</p>\n'
              '\n'
              '<h3>Eerste mapping</h3>\n'
              '<p>CMDRHelper maakt onderscheid tussen:</p>\n'
              '<ul>\n'
              '<li>◉ First Mapping-kandidaat op het scantijdstip: nog niet gekarteerd toen je het scande</li>\n<li>◎ Door jou gekarteerd: je eigen voltooide DSS-kartering is vastgelegd</li>\n<li>◉✓ Kandidaat bij de scan en eigen kartering vastgelegd; officiële eerste claim onbevestigd</li>\n'
              '</ul>\n'
              '<p>‘Al in kaart gebracht tijdens jouw scan’ wordt los van ontdekking beoordeeld. Ontbrekende informatie blijft Onbekend. Een al ontdekt hemellichaam kan bij de scan nog ongekarteerd zijn geweest. Je eigen kartering bevestigt geen officiële First Mapping-tag; na meerdere bezoeken is ook de volgorde ten opzichte van de opgeslagen scan niet altijd aangetoond.</p>\n<p>Na je eigen voltooide DSS-kartering worden het karteringstijdstip, gebruikte sondes en efficiëntiedoel betrouwbaar opgeslagen. Latere scans laten bestaande gegevens niet meer verloren gaan.</p>\n'
              '\n'
              '<h3>Landelijke bar</h3>\n'
              '<p>De landbaarheidsindicator identificeert lichamen waarop, volgens bekende '
              'gegevens, landen mogelijk is.</p>\n'
              '\n'
              '<h3>Gouden lijsten / waardevolle lichamen</h3>\n'
              '<p>Bijzonder waardevolle lichamen kunnen in het verkennersdisplay worden '
              'gemarkeerd.</p>\n'
              '<p>De gouden rand markeert een karteringsschatting boven de ingestelde drempel. Het is geen First Discovery-markering en bevestigt geen onverkochte gegevens of eerste bonussen die vandaag nog beschikbaar zijn.</p>\n'
              '<p>Het vervangt niet de gedetailleerde weergave van de lichaamswaarde.</p>\n'
              '\n'
              '<h3>Lijst met waarden</h3>\n'
              '<p>De waardelijst toont schattingen op basis van de opgeslagen scan, geen gegarandeerde openstaande uitbetalingen. Eerste bonussen blijven onbevestigd. Tooltips in kaart en lijst en de lichaamsdetails gebruiken dezelfde tijdgebonden toestanden.</p>\n'
              '<p>Het is met name geschikt om snel interessante of waardevolle instanties in een '
              'systeem te vergelijken.</p>\n'
              '\n'
              '<h3>BIOLOGISCH / GEO / DEGRADATIE</h3>\n'
              '<p>Deze visie groepeert lichamen met biologische, geologische of planetaire '
              'degradatiesignalen.</p>\n'
              '<p>Dit betekent dat interessante lichamen niet individueel in de volledige '
              'systeemkaart hoeven te worden opgezocht.</p>\n'
              '<p>Als u over uw eigen mijnbouwgegevens beschikt, kunnen uw persoonlijke '
              'mijnvondsten ook zichtbaar zijn.</p>\n'
              '<p>Handmatig aangepaste kolombreedtes van de gezamenlijke Explorer-tabel BIO / GEO / ABBAU blijven na heropenen en herstarten behouden. Opgeslagen popupkolommen worden robuuster hersteld; ongeldige waarden vallen terug op veilige standaardbreedtes.</p>\n\n'
              '<h3>Lichaamsdetail</h3>\n'
              '<p>Als u op een lichaam klikt, wordt de detailweergave geopend.</p>\n'
              '<p>Voor zover bekend kan daar het volgende voorkomen:</p>\n'
              '<ul>\n'
              '<li>Lichaamstype</li>\n'
              '<li>massa</li>\n'
              '<li>afstand</li>\n'
              '<li>Zwaartekracht</li>\n'
              '<li>sfeer</li>\n'
              '<li>Landbaarheid</li>\n'
              '<li>Terraforming-status</li>\n'
              '<li>BIO/GEO-signalen</li>\n'
              '<li>planetaire mijnsites</li>\n'
              '<li>Oppervlaktematerialen</li>\n'
              '<li>eigen mijnvondsten</li>\n'
              '<li>Waarde scannen</li>\n'
              '<li>cartografische waarde</li>\n'
              '<li>huidige waarde</li>\n'
              '</ul>\n'
              '<p>Niet ieder lichaam beschikt over alle informatie.</p>\n'
              '\n'
              '<h3>BIO-voorspellingen</h3>\n'
              '<p>CMDRHelper kan mogelijke biologische ontdekkingen schatten op basis van de '
              'bestaande gegevens over geschikte lichamen.</p>\n'
              '<p>Voorspellingen zijn geen garantie dat een bepaalde soort daadwerkelijk aanwezig '
              'zal zijn. Ze dienen als hulpmiddel bij het nemen van beslissingen bij '
              'verkenning.</p>\n'
              '<p>Geschatte BIO-waarden zijn ook voorspellingen en worden afzonderlijk van '
              'feitelijk bevestigde bevindingen behandeld.</p>\n'
              '\n'
              '<h3>Nog niet ingediend</h3>\n'
              '<p>CMDRHelper houdt commandantgerelateerde bekende cartografie- en BIO-gegevens bij '
              'die nog niet zijn ingediend.</p>\n'
              "<p>De verkopen van cartografie en biologische royalty's worden verantwoord op basis "
              'van de overeenkomstige tijdschriftgebeurtenissen.</p>\n'
              '<p>Reeds verkochte cartografische gegevens mogen na reconstructie niet meer als '
              'open worden weergegeven.</p>\n'
              '\n'
              '<h3>Showauto</h3>\n'
              '<p>Ondersteunde Explorer-hints zoals Waardevolle Lichamen of BIO-vondsten kunnen '
              'automatisch worden weergegeven met behulp van de schakelaars in de '
              'linkerzijbalk.</p>\n'
              '<p>Deze kleine livevensters dienen als extra hints tijdens het spelen en vervangen '
              'niet de volledige Explorer-weergave.</p>\n'
              '<p>“Cargo” toont de bevestigde inhoud van het Ship of de SRV die door de actieve Journal-FID wordt bepaald. SRV Cargo wordt nooit als Ship Cargo overgenomen; Limpets tellen mee voor de totale belading en worden apart weergegeven in de tabel Naam | Aantal.</p>\n'
              '<p>BIO-voortgang is compact: 1/3 geel, 2/3 blauw en 3/3 groen; de voltooide toestand ‘Voltooid’ is eveneens groen. Onder ‘automatisch tonen’ heeft GEO een eigen opgeslagen schakelaar: alleen BIO, alleen GEO of beide samen.</p>\n<p>Het vrachtvenster past zijn hoogte automatisch aan de inhoud aan. Bij veel regels blijft de hoogte begrensd en kan de tabel scrollen; je gekozen breedte en vensterpositie blijven behouden. De bestaande schakelaar ‘Vracht-HUD’ staat nu onder ‘automatisch tonen’, zonder extra schakelaar in het vrachtvenster.</p>\n\n'
              '<h3>Verschillende commandanten</h3>\n'
              '<p>Persoonlijke exploratieresultaten, cartografie, BIO-vondsten en eigen vondsten '
              'in de dagbouw worden toegewezen aan de betreffende commandant.</p>\n'
              '<p>Mondiale astronomische eigenschappen van een lichaam – bijvoorbeeld het aantal '
              'bekende planetaire mijnlocaties – blijven eigenschappen van het lichaam zelf.</p>\n'
              '\n'
              '<h3>Tip</h3>\n'
              '<p>Als je een interessant lichaam hebt, is het de moeite waard om op de '
              'gedetailleerde weergave te klikken. Dit is de beste plaats om onderscheid te maken '
              'tussen algemene lichaamsgegevens, mogelijke verkenningsresultaten en daadwerkelijke '
              'vondsten gedocumenteerd door uw eigen commandant.</p>'
              """

<h3>★ Favorieten</h3>
<p>De knop ‘★ Favorieten’ bovenaan de Explorer opent een eigen, herbruikbaar favorietenvenster. Hier sla je systemen, planeten/manen en oppervlaktelocaties op voor de actieve commander.</p>
<p>De schuifbare lijst, alfabetisch gesorteerd op naam, toont naam, type, systeem, waar van toepassing hemellichaam en breedte-/lengtegraad, categorie en een kleine afbeeldingsvoorvertoning. Vrij zoeken, het typefilter en het categoriefilter kunnen samen worden gebruikt. De zoekopdracht doorzoekt naam, systeem, hemellichaam en notitie.</p>
<p>‘Openen / Tonen’ toont de opgeslagen gegevens, de notitie en een grotere afbeeldingsvoorvertoning. ‘In Explorer tonen’ opent het bestaande systeemoverzicht of de detailweergave van het hemellichaam als de favoriet bij het huidige Explorer-systeem hoort en bijpassende gegevens beschikbaar zijn. Voor andere systemen blijven de opgeslagen favorietgegevens zichtbaar; er wordt geen systeemroute berekend.</p>

<h3>Een systeem, planeet of huidige locatie opslaan</h3>
<ul>
<li>‘★ Huidig systeem opslaan’ slaat het huidige systeem op zonder oppervlaktecoördinaten.</li>
<li>‘★ Planeet / maan opslaan’ laat je een bekende planeet of maan in het huidige systeem kiezen. Ook deze favoriet krijgt geen oppervlaktecoördinaten.</li>
<li>‘★ Huidige locatie opslaan’ staat bovenaan het favorietenvenster naast de twee andere opslagopties en is ook beschikbaar in de planeetnavigator. In het favorietenvenster blijft de knop altijd zichtbaar en is deze uitgeschakeld zonder geldige actuele planetaire positiegegevens en een actieve commander. Bij het klikken worden commander, systeem, hemellichaam, breedtegraad en lengtegraad vastgelegd. Latere bewegingen in het spel veranderen deze waarden in het geopende dialoogvenster niet.</li>
</ul>
<p>Voer een zelfgekozen naam in en kies precies één categorie: Bio, Geo, Mijnbouw, Uitzicht, Landingsplaats, Interessant of Overig. Een notitie en een afbeelding zijn optioneel. Bekende technische ID’s worden intern overgenomen; je hoeft ze niet in te voeren. Ook breedtegraad of lengtegraad 0,0 zijn geldige coördinaten.</p>
<p>‘Bewerken’ wijzigt naam, categorie, notitie en afbeelding. Systeem, hemellichaam en opgeslagen coördinaten blijven behouden. Wil je een andere oppervlaktelocatie opslaan, maak dan op die positie een nieuwe favoriet aan.</p>

<h3>Snelle favoriet zonder muis</h3>
<p>Onder ‘Instellingen → Snelle favoriet’ kun je vrij een globale sneltoets instellen, wijzigen of verwijderen. Na installatie is deze standaard ‘Niet toegewezen’: CMDRHelper registreert geen toets zonder dat je daarom vraagt. De toewijzing wordt opgeslagen. Als een combinatie al in gebruik is of op je systeem niet beschikbaar is, verschijnt er een foutmelding; een eerder werkende toewijzing blijft behouden.</p>
<p>Op Linux/X11 en Windows werkt de sneltoets ook terwijl Elite de focus heeft – te voet, in de SRV en in het schip. Een toetsaanslag slaat de huidige locatie op het oppervlak onmiddellijk op voor de actieve commandant, zonder dialoogvenster en zonder muisbediening. Commandant, systeem, hemellichaam en de huidige Latitude-/Longitude-waarden worden op dat moment vastgelegd. Zonder geldige actuele planetaire coördinaten wordt niets opgeslagen; eerdere coördinaten worden niet opnieuw gebruikt.</p>
<p>De favoriet krijgt een unieke voorlopige naam, zoals ‘Markering 07.09.2026 06:32:15’, en de categorie ‘Overig’. In het normale favorietenvenster kun je deze later een andere naam geven, aan een andere categorie toewijzen, een notitie toevoegen of een afbeelding toevoegen. Er wordt geen screenshot automatisch gemaakt of geïmporteerd.</p>
<p>Gedurende ongeveer twee seconden verschijnt ‘★ FAVORIET OPGESLAGEN’ direct boven het actieve Elite-venster met het hemellichaam en de coördinaten; als de locatie ontbreekt, verschijnt kort ‘⚠ GEEN PLANETAIRE COÖRDINATEN’. De weergave neemt geen focus over en onderschept geen invoer. Deze werkt ook als de navigatie-HUD is uitgeschakeld en verdwijnt daarna volledig. Als de HUD is ingeschakeld, blijft daarna de normale navigatieweergave over. De opgeslagen instelling van de HUD-schakelaar wordt niet gewijzigd. De weergave gebruikt dezelfde overlay-infrastructuur en platformvereisten als de navigatie-HUD.</p>

<h3>Favorietafbeeldingen</h3>
<p>Favorietafbeeldingen staan los van het onderdeel Afbeeldingen. ‘Afbeelding kiezen …’ staat PNG, JPEG en WebP toe. Pas bij het opslaan kopieert CMDRHelper de gekozen afbeelding naar zijn eigen map voor favorietafbeeldingen. Het oorspronkelijke bestand wordt niet verplaatst of gewijzigd.</p>
<p>‘Laatste screenshot gebruiken’ leest bij elke klik de ingestelde screenshotbronmap opnieuw in en zoekt leesbare screenshots met typische Elite-bestandsnamen. Zonder instelling worden de gebruikelijke Elite-screenshotmappen onder Windows of Steam/Proton meegenomen. Ook de map van de actieve commander in de ingestelde conversiebestemming wordt doorzocht op bijpassende geconverteerde Elite-screenshots. Zo blijft een geconverteerd screenshot vindbaar als de oorspronkelijke BMP is verwijderd. De nieuwste opnametijd wordt bepaald door een ondubbelzinnige tijdsaanduiding in de bestandsnaam, anders door de bestandstijd; bij geconverteerde afbeeldingen telt de opnametijd in de naam in plaats van het conversietijdstip. CMDRHelper maakt zelf geen screenshots en doorzoekt geen willekeurige afbeeldingsmappen.</p>
<p>Vóór gebruik worden bestandsnaam, opnametijd en een vers geladen voorvertoning getoond. Bevestig met ‘Deze afbeelding gebruiken’. Als geen geschikt screenshot wordt gevonden, kun je nog steeds ‘Afbeelding kiezen …’ gebruiken. Elite-BMP-screenshots worden als interne PNG-kopie opgeslagen.</p>
<p>Een afbeelding kan in het bewerkingsvenster worden vervangen of met ‘Afbeelding verwijderen’ worden gedeselecteerd. Bij het opslaan wordt de niet meer gebruikte interne kopie verwijderd. Ontbreekt een afbeeldingsbestand, dan blijft de favoriet zonder voorvertoning bruikbaar.</p>

<h3>Favorietdoel en commander</h3>
<p>‘▶ Naar route’ stelt het bekende systeem van de favoriet in als bestemming in de routeplanner. Het vertrek volgt het bestaande gedrag met de huidige AppState; een handmatig ingevoerd vertrek blijft behouden. Er wordt geen route automatisch berekend. ‘◎ Naar coördinaten’ start de bestaande planeetnavigatie naar de oppervlaktelocatie met de bestaande HUD als systeem, hemellichaam en geldige coördinaten zijn opgeslagen. De reis naar het systeem en oppervlaktenavigatie zijn twee afzonderlijke stappen, zonder automatische reisvolgorde. Zonder oppervlaktecoördinaten is alleen de route beschikbaar; acties waarvoor vereiste gegevens ontbreken worden verborgen.</p>
<p>Voor oppervlaktelocaties geeft ‘◎ Naar coördinaten’ het opgeslagen hemellichaam, de breedtegraad, lengtegraad en favorietnaam door aan de bestaande planeetnavigator. Het nieuwe doel vervangt het vorige. Favorieten hebben geen eigen navigatielogica. De navigator blijft zelf beslissen: bijpassende geldige planetaire gegevens activeren de navigatie; anders wacht hij op die gegevens.</p>
<p>Favorieten behoren uitsluitend tot de actieve commander. Bij een commanderwissel wordt de lijst bijgewerkt en een geopend bewerkingsvenster verworpen. Een doel dat nog als favorietdoel van de vorige commander wordt beheerd, wordt beëindigd. De commanderselectie in de kroniek breidt deze favorietenlijst niet uit.</p>
<p>‘Verwijderen’ vraagt om bevestiging en verwijdert alleen de favorietregistratie en de bijbehorende interne afbeeldingskopie. Het oorspronkelijke screenshot of de gekozen originele afbeelding en alle Explorer-, journal- en hemellichaamgegevens blijven behouden.</p>"""),
 'chronicle': (
        'Kroniek',
        """<h2>Kroniek</h2>
<h3>CMDRHelper v3.2</h3>
<p>Systeemoverzicht: de nieuwe Elite-achtige weergave vervangt het miniatuuroverzicht in Explorer en Kroniek. Sterren en planeten vormen de hoofdstructuur met manen daaronder; meervoudige sterrenstelsels blijven leesbaar. Zoomen, scrollen, passend maken en klikken op hemellichamen geven toegang tot details.</p>
<p>Compacte asteroïdengordels: clusters worden gegroepeerd tot gordels in het overzicht en de gewone systeemkaarten van Explorer en Kroniek. Alle afzonderlijke clustergegevens blijven bewaard.</p>
<p>De kroniek is de persoonlijke reis- en ontdekkingsgeschiedenis van de commandant. Het gebruikt de permanent opgeslagen journaalinformatie om reeds bezochte systemen te vinden, deze ruimtelijk weer te geven en te zoeken naar bekende ontdekkingen.</p>

<h3>Systemen bezocht</h3>
<p>De Chronicle toont de bezochte systemen en hun locaties in het sterrenstelsel die bekend zijn bij de commandant.</p>
<p>Indien beschikbaar wordt rekening gehouden met het eerste en laatste bezoek en met bekende lichaamsinformatie.</p>
<p>Bij een actieve periode hebben het aantal bezoeken, het eerste bezoek en het laatste bezoek in de kaartweergave betrekking op de gefilterde daadwerkelijke systeembezoeken.</p>
<p>De kroniek is dus niet alleen een kaart, maar ook een hulpmiddel voor het vinden van eerdere reisbestemmingen en ontdekkingen.</p>

<h3>3D-kaart</h3>
<p>De bezochte systemen worden ruimtelijk weergegeven met behulp van hun galactische X/Y/Z-coördinaten.</p>
<p>De gebruiksaanwijzing bevindt zich direct boven de kaart:</p>
<ul>
<li>Houd de linkermuisknop ingedrukt → weergave roteren</li>
<li>houd de middelste muisknop ingedrukt en sleep → trek een zoomvenster</li>
<li>Houd de rechtermuisknop ingedrukt → weergave verplaatsen</li>
</ul>
<p>Het kleine asdisplay helpt bij de oriëntatie in de ruimte.</p>

<h3>Huidige positie</h3>
<p>Met “Huidige positie” kan de kaartweergave worden uitgelijnd of teruggezet naar de momenteel bekende locatie van de actieve commandant.</p>
<p>Eerst worden de huidige filters toegepast. Er wordt alleen op het huidige systeem gecentreerd als het in de resulterende kaart voorkomt.</p>
<p>Anders verschijnt ‘Het huidige systeem valt niet binnen deze filterselectie.’ De filters worden hierdoor niet opgeheven.</p>

<h3>Uitlijnen</h3>
<p>‘Uitlijnen’ herstelt de oriëntatie naar een bovenaanzicht van het galactische vlak. Verschuiving en zoom blijven behouden.</p>
<p>Dit is handig als de kaart na veel draaien onoverzichtelijk is geworden.</p>

<h3>Kroniek vernieuwen</h3>
<p>‘Kroniek vernieuwen’ laadt de kroniekgegevens opnieuw op basis van de huidige gecombineerde filters en werkt de weergave bij. Vrije tekst, ingeschakelde datumgrenzen en mijnbouwfilters worden opnieuw samen beoordeeld; actieve filters worden niet genegeerd.</p>
<p>De functie wijzigt geen journaalbestanden en creëert geen nieuwe verkenningsgegevens. Het werkt eenvoudigweg de geschiedenisweergave bij op basis van de bestaande CMDRHelper-gegevens.</p>

<h3>Vrij zoeken op tekst</h3>
<p>Reeds bekende inhoud kan worden doorzocht met behulp van het veld "Zoekgeschiedenis...".</p>
<p>Bij het zoeken wordt – indien beschikbaar in de database – onder meer rekening gehouden met:</p>
<ul>
<li>Systeemnamen</li>
<li>Lichaamskenmerken</li>
<li>biologische gegevens</li>
<li>Materialen</li>
<li>Codex-gegevens</li>
</ul>
<p>Vrije tekst, periode en mijnbouw staan in één gezamenlijk filtergebied. ‘Toepassen’ beoordeelt de ingestelde filters samen. Enter in het vrije tekstveld start dezelfde gecombineerde filtering als ‘Toepassen’.</p>

<h3>Periode Van/Tot (UTC)</h3>
<p>Schakel ‘Van’ en ‘Tot’ elk met het bijbehorende selectievakje in en kies de gewenste datum. Ook slechts één grens is mogelijk. Zonder ingeschakeld vakje geldt aan die kant geen tijdsbeperking; zonder beide vakjes wordt geen periode beperkt.</p>
<ul>
<li><b>Van:</b> Vanaf het begin van de gekozen UTC-kalenderdag, inclusief.</li>
<li><b>Tot:</b> De volledige gekozen UTC-kalenderdag telt mee, tot vlak vóór het begin van de volgende dag.</li>
</ul>
<p>UTC is de gecoördineerde wereldtijd. De datumgrenzen gelden voor UTC-kalenderdagen, niet voor kalenderdagen in je lokale tijdzone.</p>
<p>Er wordt gefilterd op daadwerkelijke systeembezoeken uit <code>system_visits</code>. Een daadwerkelijk bezoek van de betreffende commandant binnen de periode is vereist. De opgeslagen gegevens <code>first_seen</code> en <code>last_seen</code> vervangen geen echt bezoek: een periode die alleen tussen een eerder eerste en een later laatste bezoek ligt, is niet voldoende.</p>
<p>De periode filtert bezoeken, niet afzonderlijke ontdekkings-, BIO-, GEO- of mijnbouwgebeurtenissen. Bekende vondstgegevens en mijnbouwhoeveelheden blijven opgeslagen totalen. Van/Tot kan zowel zelfstandig als samen met vrije tekst en mijnbouw worden gebruikt.</p>
<p>Als Van na Tot ligt, verschijnt ‘De Van-datum mag niet na de Tot-datum liggen.’ Er wordt geen databasequery gestart. Corrigeer de datumgrenzen en pas de filters opnieuw toe.</p>

<h3>Zoekresultaten</h3>
<p>Hits worden weergegeven in de bestaande resultatenlijst onder de kroniekkaart.</p>
<p>Afhankelijk van het type treffer, kunnen systeem en body, evenals aanvullende informatie verschijnen.</p>
<p>Een hit kan worden gebruikt om het overeenkomstige systeem of de instantie die al bekend is te vinden en om de bestaande gedetailleerde informatie te openen.</p>

<h3>Geen resultaten</h3>
<p>Als een geldige filtering geen resultaten oplevert, worden kaart en routes leeggemaakt. De resultatenlijst wordt leeggemaakt en verborgen, de detailweergave wordt gereset en een geopend kroniekvenster met systeemdetails wordt gesloten.</p>
<p>Oude resultaten blijven niet zichtbaar. Controleer dan de combinatie van zoektekst, periode en mijnbouwfilters, en de commandant die voor de betreffende weergave wordt gebruikt.</p>

<h3>Planetaire mijnbouwlocaties</h3>
<p>Het filter “Planetaire mijnlocaties” kan worden gebruikt om specifiek te zoeken naar bekende lichamen waarvoor Elite Dangerous planetaire mijnlocaties heeft gerapporteerd.</p>
<p>De onderliggende weergave komt overeen met die bekend uit Explorer:</p>
<p><b>ABBAU ×N</b></p>
<p>Het nummer behoort toe aan de instantie zelf en is niet gerelateerd aan de commandant.</p>

<h3>Ten minste</h3>
<p>Met ‘Ten minste’ kunt u het minimumaantal planetaire mijnlocaties specificeren dat een lichaam moet hebben.</p>
<p>Voorbeeld:</p>
<p><b>Minstens 20</b></p>
<p>toont alleen bekende lichamen met minimaal:</p>
<p><b>ABBAU ×20</b></p>
<p>Dit maakt het mogelijk om bijzonder uitgestrekte mijngebieden specifiek te lokaliseren.</p>

<h3>Mijn mijnbouwvondsten</h3>
<p>Bij ‘Eigen mijnbouwvondsten’ beperkt de zoektocht zich tot lichamen waarop de betreffende commandant aantoonbaar zelf dagbouw heeft uitgevoerd.</p>
<p>Deze informatie komt uit de persoonlijke geschiedenis van de dagbouw en wordt strikt gescheiden door de commandant.</p>
<p>Een lichaam kan dus over mondiale ABBAU ×N-signalen beschikken zonder dat de eigen commandant daar al iets heeft verwijderd.</p>

<h3>Handelswaar</h3>
<p>Als “Eigen mijnvondsten” is geactiveerd, is de selectie “Grondstof” ook beschikbaar.</p>
<p>Op de lijst staan ​​alleen grondstoffen die de betreffende commandant feitelijk al heeft gewonnen uit de dagbouw.</p>
<p>Dit is geen theoretische lijst van alle mogelijke mijnbouwgrondstoffen.</p>
<p>Voor FABER38 kan de keuzelijst bijvoorbeeld bevatten:</p>
<ul>
<li>Alle</li>
<li>koper</li>
</ul>
<p>Als er later daadwerkelijk extra grondstoffen worden gewonnen, verschijnen deze automatisch in uw persoonlijke selectie.</p>

<h3>Gericht zoeken naar grondstoffen</h3>
<p>Als bijvoorbeeld ‘Koper’ wordt geselecteerd en vervolgens op ‘Toepassen’ wordt gedrukt, toont de historie alleen lichamen waarop de betreffende commandant aantoonbaar koper heeft gedolven.</p>
<p>Voorbeeld:</p>
<p><b>Prua Hypai NV-E c28-66 / 2 — ABBAU ×24 — koper 56 t</b></p>
<p>Dit betekent dat de kroniek kan worden gebruikt als persoonlijke locatiedatabase: een grondstof die al is gedolven, kan later opnieuw worden gevonden.</p>

<h3>Alle grondstoffen</h3>
<p>Met “Raw Material: All” wordt rekening gehouden met alle overeenkomende persoonlijke ontdekkingen op het gebied van dagbouw.</p>
<p>Als er meerdere goederen op een lichaam bekend zijn, kunnen deze worden weergegeven samen met de hoeveelheden die ze tot nu toe hebben verkregen.</p>
<p>Voorbeeld:</p>
<p><b>ABBAU ×24 — Helium-3 18 t, koper 56 t</b></p>
<p>De hoeveelheden zijn de persoonlijke mijnwaarden van de betreffende commandant, die feitelijk zijn gedocumenteerd uit dagboekgebeurtenissen.</p>
<p>Ook bij een actieve periode blijven persoonlijke mijnbouwhoeveelheden opgeslagen totaalhoeveelheden. <b>Koper 56 t</b> betekent niet automatisch <b>56 t in de geselecteerde periode</b>. De periode vereist een passend systeembezoek, maar beperkt de weergegeven gewonnen hoeveelheid niet tot die periode.</p>

<h3>Combineer filters</h3>
<p>Vrije tekst, ingeschakelde Van-/Tot-grenzen en mijnbouwfilters kunnen worden gecombineerd. Een resultaat moet tegelijkertijd aan de ingestelde voorwaarden voldoen.</p>
<p>Bijvoorbeeld:</p>
<ul>
<li>Planetaire mijnsites actief</li>
<li>Minstens 20</li>
<li>Eigen mijnbouwvondsten actief</li>
<li>Grondstof koper</li>
</ul>
<p>zoekt naar bekende lichamen met minstens 20 planetaire mijnlocaties waar de commandant in kwestie zelf al koper heeft gedolven.</p>
<p>Extra zoektekst wordt eveneens meegenomen. Als daarnaast een periode is ingesteld, moet de bekeken commandant het bijbehorende systeem daadwerkelijk in die periode hebben bezocht; de koperwinning zelf hoeft niet in die periode te hebben plaatsgevonden.</p>

<h3>Toepassen</h3>
<p>‘Toepassen’ voert een gezamenlijke filtering uit met alle momenteel ingestelde zoek-, periode- en mijnbouwfilters:</p>
<ul>
<li>Vrije tekst</li>
<li>Van, indien ingeschakeld</li>
<li>Tot, indien ingeschakeld</li>
<li>Planetaire mijnbouwlocaties</li>
<li>Minimumaantal</li>
<li>Mijn mijnbouwvondsten</li>
<li>Handelswaar, als ‘Mijn mijnbouwvondsten’ is ingeschakeld</li>
</ul>
<p>Enter in het vrije tekstveld voert precies dezelfde filtering uit. Zonder vrije tekst en mijnbouwfilters wordt de normale kaart geladen voor de aangevinkte kaartcommandanten, indien van toepassing beperkt door Van/Tot.</p>

<h3>Resetten</h3>
<p>‘Resetten’ zet het gezamenlijke filtergebied terug naar de begintoestand:</p>
<ul>
<li>Vrije tekst wordt gewist.</li>
<li>Van en Tot worden uitgeschakeld; de datumvelden tonen weer de datum van vandaag en zijn uitgeschakeld.</li>
<li>Planetaire mijnbouwlocaties wordt uitgeschakeld.</li>
<li>Het minimumaantal wordt op 0 gezet.</li>
<li>Mijn mijnbouwvondsten wordt uitgeschakeld.</li>
<li>Handelswaar wordt teruggezet op ‘Alle’.</li>
</ul>
<p>De commandantselectie blijft behouden. Vervolgens wordt de normale kroniek opnieuw geladen voor deze kaartselectie; eerdere zoekresultaten en detailweergaven worden gereset.</p>

<h3>Commandant selectie</h3>
<p>De kroniek kan gegevens van verschillende bekende commandanten weergeven.</p>
<p>Daarbij zijn er twee afzonderlijke selectieconcepten:</p>
<ul>
<li><b>Commandantselectie van de kaart:</b> De commandantvakjes bepalen welke commandantroutes in de normale kaart zonder vrije tekst-/mijnbouwzoekopdracht worden getoond. Een ingeschakelde periode wordt meegenomen.</li>
<li><b>Bekeken commandant:</b> Persoonlijke vrije tekst-/mijnbouwzoekopdrachten gebruiken de bekeken commandant (<code>viewed_commander_id</code>), anders de actieve commandant. Ook de persoonlijke handelswaarlijsten volgen deze commandant.</li>
</ul>
<p>Persoonlijke gegevens zoals uw eigen mijnvondsten en grondstoffenlijsten worden echter altijd apart beoordeeld voor de daadwerkelijk bekeken commandant.</p>
<p>Een commandant ziet in zijn grondstoffenselectie geen mijnvondsten terug die exclusief toebehoren aan een andere commandant.</p>

<h3>Alle commandanten</h3>
<p>De kaart-/kroniekweergave kan rekening houden met meerdere commandanten.</p>
<p>‘Alle commandanten’ heeft betrekking op de commandantselectie van de kaart. De commandantvakjes breiden persoonlijke vrije tekst-/mijnbouwzoekopdrachten niet automatisch uit naar meerdere commandanten.</p>
<p>Dit verandert niets aan de persoonlijke toewijzing van commandantgerelateerde gegevens. Mondiale astronomische eigenschappen van een systeem of lichaam blijven gedeeld, persoonlijke bevindingen blijven gescheiden.</p>

<h3>Zoekhulp / legenda</h3>
<p>Extra informatie over het zoeken naar kronieken en de betekenis van de weergave kunt u vinden via “Zoekhulp/legenda”.</p>
<p>Een aangeklikte zoekterm wordt in het zoekveld overgenomen en samen met de reeds ingestelde periode-/mijnbouwfilters uitgevoerd.</p>
<p>Deze contextgebonden hoofdhulp is een aanvulling op de daar beschikbare korte bedieningshandleidingen.</p>

<h3>Tip</h3>
<p>De kroniek is bijzonder geschikt voor het vinden van interessante plekken die tijdens een langere reis zijn ontdekt.</p>
<p>Voor dagbouw kan het bijvoorbeeld het volgende beantwoorden:</p>
<p>“Op welke planeet heb ik ooit koper gewonnen?”</p>
<p>of:</p>
<p>"Welke van mijn bekende planeten hebben een bijzonder groot aantal mijnsites?"</p>""",
    ),
 'jump_tip': (
        'Analyse',
        """
<h2>Analyse</h2>
<p>Analyse gebruikt je persoonlijke exploratiegeschiedenis. Systeemanalyse beoordeelt een ingevoerde procedurele systeemnaam; Historische gegevens behoudt de eerdere codeanalyse met historische treffers en opnieuw evalueren. Beide helpen bij beslissingen en garanderen geen ontdekkingen.</p>
<h3>Vergelijkingsbasis</h3>
<p>De massacode levert de basisschatting. Regio en familie verfijnen die voorzichtig. Kleine lokale steekproeven worden naar de grotere gegevensbasis afgevlakt. Weinig gegevens betekent onzekerheid, niet een slechte beoordeling. Onvoldoende onderzochte systemen tellen niet als negatieve treffers.</p>
<h3>Potentieelindex</h3>
<p>Potentieelindex 100 staat voor je persoonlijke historische gemiddelde van afgezwakt exploratiepotentieel. De index is geen procentuele kans. Een uniform karteringsscenario en afgezwakte uitschieters maken vergelijking mogelijk; mediaan en afgevlakt potentieel zijn geschatte credits, geen gegarandeerde opbrengsten.</p>
<h3>Bijzondere vondsten</h3>
<p>Het laatste systeemnummer wordt niet beoordeeld: Plio Aip KN-B d13-201 behoort tot familie Plio Aip KN-B d13. BIO is informatief en telt niet mee in de hoofdbeoordeling. Ontbrekende analyses bewijzen geen nulwaarden.</p>
<h3>Systeemanalyse</h3>
<p>Voer een systeem in en kies Analyseren of druk op Enter. Huidig systeem gebruiken neemt de naam uit de bestaande spelstatus. Alleen een gebruikersactie herberekent de analyse. Vergelijkingsbasis en resultaten vermelden hun niveau; zonder lokale vergelijkingen wordt bovenliggende ervaring gebruikt. Gegevenskwaliteit staat los van de aanbeveling.</p>
<p>Historische treffers per systeemcode. Deze waarden beschrijven je verkenningservaring tot nu toe en zijn geen directe voorspelling voor een afzonderlijk doelsysteem. Gegevensbasis en bewijskracht beschrijven de betrouwbaarheid van de vergelijkingsgegevens op basis van de beschikbare steekproef en de spreiding over sectoren.</p>
""",
    ),
 'route_planner': ('Routeplanner',
                   '<h2>Routeplanner</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Verbeterde routeplanner: het vertrek volgt automatisch het huidige systeem totdat je handmatig een vertrek invult; leegmaken herstelt de automatische werking. Schepen en carriers gebruiken exact gecontroleerde ID64-adressen, zonder vergelijkbare namen te kiezen. ‘Unable to find route’ betekent dat geen route is gevonden; controleer doelen, bereik en route-instellingen.</p>\n'
                   '<p>De routeplanner ondersteunt het plannen van langere reizen per schip of '
                   'Fleet Carrier. CMDRHelper kan externe routegegevens van Spansh gebruiken en de '
                   'geplande route voorbereiden voor verder gebruik.</p>\n'
                   '\n'
                   '<h3>Begin en eind</h3>\n'
                   '<p>Voor de routeberekening is een start- en bestemmingssysteem vereist.</p>\n'
                   '<p>Voor zover mogelijk kan CMDRHelper het huidige bekende systeem van de '
                   'commandant als uitgangspunt nemen. Start en finish moeten vóór de berekening '
                   'worden gecontroleerd.</p>\n'
                   '\n'
                   '<h3>Verzenden of Fleet Carrier</h3>\n'
                   '<p>De routeplanner maakt onderscheid tussen tochten met een normaal schip en '
                   'met een Fleet Carrier.</p>\n'
                   '<p>Beiden hanteren verschillende eisen en berekeningsmethoden. Daarom moet '
                   'vóór het plannen het juiste routetype worden geselecteerd.</p>\n'
                   '\n'
                   '<h3>Scheepsroute</h3>\n'
                   '<p>Bij een scheepsroute wordt rekening gehouden met de voor het actieve schip '
                   'bekende of ingevoerde sprongeigenschappen.</p>\n'
                   '<p>Afhankelijk van de beschikbare gegevens kunnen FSD-gegevens, '
                   'scheepsgegevens, massa, brandstof en andere sprongparameters in de planning '
                   'worden opgenomen.</p>\n'
                   '<p>Een berekende route is een planningshulpmiddel. Veranderingen aan het schip '
                   'of de massa ervan kunnen de daadwerkelijk bereikbare sprongafstand in het spel '
                   'veranderen.</p>\n'
                   '\n'
                   '<h3>Route van vlootvervoerders</h3>\n'
                   '<p>Fleet Carrier hebben andere springregels dan normale schepen.</p>\n'
                   '<p>CMDRHelper gebruikt de aangewezen Spansh-vervoerdersplanning voor '
                   'overeenkomstige routes.</p>\n'
                   '<p>De route wordt gebruikt om de sprongreeks te plannen. Het werkelijke '
                   'tritiumverbruik en het beschikbare bereik kunnen ook afhankelijk zijn van de '
                   'massa en de huidige vervoerderstatus.</p>\n'
                   '\n'
                   '<h3>Spansh</h3>\n'
                   '<p>Voor de daadwerkelijke routeberekening kan CMDRHelper gebruik maken van de '
                   'externe service Spansh.</p>\n'
                   '<p>Het verzoek wordt op de achtergrond verwerkt, zodat de interface ook '
                   'tijdens een langere berekening operationeel blijft.</p>\n'
                   '<p>CMDRHelper heeft geen invloed op de beschikbaarheid of responstijd van de '
                   'externe dienst.</p>\n'
                   '\n'
                   '<h3>berekening</h3>\n'
                   '<p>Na het starten van een berekening wordt de aanvraag doorgegeven aan de '
                   'geselecteerde routeplanner.</p>\n'
                   '<p>Afhankelijk van de route en dienst kan de berekening enige tijd duren. '
                   'Gedurende deze tijd mag geen tweede identieke berekening onnodig worden '
                   'gestart.</p>\n'
                   '\n'
                   '<h3>Resultaat</h3>\n'
                   '<p>Een succesvol berekende route toont de beoogde systemen of sprongpunten in '
                   'hun volgorde.</p>\n'
                   '<p>Afhankelijk van het routetype verschijnt aanvullende informatie over '
                   'afstand, sprongen, brandstof of tritium en andere beschikbare '
                   'routegegevens.</p>\n'
                   '\n'
                   '<h3>Route en huidige commandant</h3>\n'
                   '<p>Het huidige systeem en schip kunnen – zolang ze duidelijk bekend zijn in de '
                   'actieve AppState – worden gebruikt voor voorbezetting of ter ondersteuning van '
                   'de planning.</p>\n'
                   '<p>De daadwerkelijke route blijft echter een plan en verandert niets aan '
                   'journaal- of commandantgegevens.</p>\n'
                   '\n'
                   '<h3>CTSVision-export</h3>\n'
                   '<p>Berekende routes van wagenparkvervoerders kunnen worden geëxporteerd als '
                   'CSV voor CTSVision.</p>\n'
                   '<p>Dit betekent dat een in CMDRHelper geplande transportroute vervolgens in '
                   'CTSVision kan worden gebruikt voor sprongbesturing of routeverwerking '
                   'daar.</p>\n'
                   '<p>De export verandert de route in CMDRHelper niet.</p>\n'
                   '\n'
                   '<h3>CSV-bestand</h3>\n'
                   '<p>Het geëxporteerde bestand bevat de routegegevens die nodig zijn voor '
                   'CTSVision in de beoogde volgorde.</p>\n'
                   '<p>Het bestand mag na het exporteren niet ongecontroleerd structureel worden '
                   'gewijzigd, als het vervolgens door CTSVision moet worden ingelezen.</p>\n'
                   '\n'
                   '<h3>Fouten en externe services</h3>\n'
                   '<p>Als Spansh niet kan worden bereikt of de service een fout retourneert, '
                   'geeft CMDRHelper een overeenkomstige foutmelding weer.</p>\n'
                   '<p>Een fout in de online routeberekening verandert de lokale commandant- of '
                   'journaalgegevens niet.</p>\n'
                   '\n'
                   '<h3>Routeplanner en springtip</h3>\n'
                   '<p>Jumptip en routeplanner vervullen verschillende taken:</p>\n'
                   '<ul>\n'
                   '<li>Jump tip evalueert mogelijke interessante verkenningsdoelen op basis van '
                   'bestaande gegevens.</li>\n'
                   '<li>Routeplanner berekent een specifieke route tussen start en '
                   'bestemming.</li>\n'
                   '</ul>\n'
                   '<p>Een goede springtip hoort dus niet automatisch bij een optimaal '
                   'traject.</p>\n'
                   '\n'
                   '<h3>Verschillende commandanten</h3>\n'
                   '<p>Als er gebruik wordt gemaakt van commandantgerelateerde gegevens zoals '
                   'huidig \u200b\u200bsysteem of schip, komt deze uit de actieve live AppState en '
                   'moet daar duidelijk worden toegewezen.</p>\n'
                   '<p>Door simpelweg naar een andere commandant te kijken in de CMDR-weergave, '
                   'wordt de routeplanner niet naar zijn/haar systeem of schip '
                   'overgeschakeld.</p>\n'
                   '<p>Een routeberekening zelf verandert niets aan de persoonsgegevens van een '
                   'andere commandant.</p>\n'
                   '\n'
                   '<h3>Tip</h3>\n'
                   '<p>Controleer vóór een lange reis altijd nogmaals:</p>\n'
                   '<ul>\n'
                   '<li>Startsysteem</li>\n'
                   '<li>Doelsysteem</li>\n'
                   '<li>Routetype schip/vervoerder</li>\n'
                   '<li>voor scheepsroutes het onderliggende schip, FSD en sprongparameters</li>\n'
                   '<li>voor vliegroutes: de beschikbare tritiumreserve</li>\n'
                   '</ul>\n'
                   '<p>Bij wagenparkreizen is het raadzaam om ook voor de terugreis of ongeplande '
                   'omwegen voldoende reserve te plannen.</p>'),
 'images': ('Afbeeldingen',
            '<h2>Afbeeldingen</h2>\n'
            '<p>In het gedeelte "Afbeeldingen" worden de schermafbeeldingen beheerd die zijn '
            'gemaakt met Elite Dangerous. CMDRHelper kan nieuwe opnames automatisch herkennen, '
            'verwerken en opslaan in een galerij op basis van de commandant.</p>\n'
            '\n'
            '<h3>Bronmap</h3>\n'
            '<p>De bronmap is de map waarin Elite Dangerous de schermafbeeldingen in BMP-formaat '
            'opslaat.</p>\n'
            '<p>CMDRHelper kan deze map controleren op nieuwe BMP-bestanden. Om automatische '
            'verwerking te laten werken, moet de juiste screenshot-map worden ingesteld.</p>\n'
            '\n'
            '<h3>Bestemmingsmap</h3>\n'
            '<p>De doelmap is de algemene hoofdmap voor de afbeeldingen die door CMDRHelper worden '
            'verwerkt.</p>\n'
            '<p>De gebruiker stelt deze hoofdmap in. CMDRHelper maakt tijdens de verwerking '
            'automatisch de vereiste Commander-gerelateerde submappen aan.</p>\n'
            '\n'
            '<h3>Automatische verwerking</h3>\n'
            '<p>Als “Automatisch converteren” is geactiveerd en geldige bron- en doelmappen zijn '
            'ingesteld, controleert CMDRHelper regelmatig de bronmap op nieuwe '
            'BMP-screenshots.</p>\n'
            '<p>Indien geactiveerd, worden bestaande BMP-bestanden in eerste instantie als bekend '
            'gemarkeerd en worden ze niet automatisch ongevraagd geconverteerd. Hiervoor is de '
            "aparte functie voor het omzetten van bestaande BMP's beschikbaar.</p>\n"
            '<p>Een nieuw bestand wordt pas in de wachtrij geplaatst als het bij twee '
            'opeenvolgende controles dezelfde grootte heeft die niet nul is. Als gevolg hiervan '
            'wordt een schrijfbewerking die nog bezig is, niet onmiddellijk verwerkt.</p>\n'
            '\n'
            '<h3>Beeldconversie</h3>\n'
            '<p>Als bron verwerkt CMDRHelper BMP-bestanden. Als doelformaat kan “PNG” of “JPG” '
            'worden geselecteerd.</p>\n'
            '<p>JPG-bestanden worden opgeslagen op kwaliteitsniveau 95. PNG-bestanden worden '
            'geoptimaliseerd opgeslagen.</p>\n'
            '<p>Standaard wordt het originele BMP-bestand behouden. Als “BMP na conversie '
            'verwijderen” is geactiveerd, wordt de bron-BMP pas verwijderd nadat de doelafbeelding '
            'succesvol is opgeslagen.</p>\n'
            '\n'
            '<h3>Beeld helderder maken</h3>\n'
            '<p>De helderheid wordt aangepast van 0 tot 50 procent met behulp van een '
            'schuifregelaar en een gekoppeld cijferveld. De instelling wordt opgeslagen.</p>\n'
            '<p>Het wordt automatisch toegepast tijdens elke conversie die daarna wordt gestart - '
            'zowel voor nieuw gecontroleerde als voor handmatig geïnitieerde bestaande '
            'BMP-bestanden. 0 procent neemt de oorspronkelijke helderheid over; hogere waarden '
            'verhogen de helderheid van de gegenereerde PNG- of JPG-afbeelding '
            'dienovereenkomstig.</p>\n'
            '<p>De functie is geen puur voorbeeld en wordt vervolgens niet toegepast op een '
            'afbeelding die in de galerij is geselecteerd. De gewijzigde helderheid wordt in het '
            'nieuwe doelbestand opgeslagen.</p>\n'
            '<p>Het bron-BMP blijft ongewijzigd tenzij het verwijderen van het BMP-bestand ook '
            'wordt geactiveerd. Journaal-, commandant- en verkenningsgegevens worden niet '
            'gewijzigd.</p>\n'
            '\n'
            '<h3>Commander-gerelateerde opslag</h3>\n'
            '<p>Nieuwe schermafbeeldingen worden toegewezen aan de daadwerkelijk spelende '
            'Commander op basis van de dagboekidentiteit die aanwezig is in de actieve live '
            'AppState.</p>\n'
            '<p>De mapstructuur bevat de naam van de commandant en het Frontier-ID, '
            'bijvoorbeeld:</p>\n'
            '<p><b>FABER38_F12520967/</b></p>\n'
            '<p>De FID houdt de opdracht ook met meerdere commandanten overzichtelijk. Hierdoor '
            'kunnen twee commandanten met dezelfde naam worden onderscheiden.</p>\n'
            '\n'
            '<h3>bestandsnamen</h3>\n'
            '<p>Nieuwe verwerkte beelden krijgen een naam met het tijdstip van vastleggen, de naam '
            'van de commandant en – indien beschikbaar – het sterrensysteem dat bekend is tijdens '
            'het in de rij staan.</p>\n'
            '<p>Voorbeeld:</p>\n'
            '<p><b>2026-09-04_13-18-22_FABER38_Prua-Hypai-RB-D-c29-71.png</b></p>\n'
            '<p>De FID staat in de Commander-gerelateerde mapnaam, niet opnieuw in de naam van het '
            'afbeeldingsbestand.</p>\n'
            '\n'
            '<h3>Veilige bestandsnamen</h3>\n'
            '<p>CMDRHelper zuivert commandant- en systeemnamen voor gebruik als bestands- en '
            'mapcomponenten.</p>\n'
            '<p>Illegale controle en Windows-tekens worden vervangen, witruimte wordt verenigd, '
            'problematische punten of volgspaties worden verwijderd en gereserveerde Windows-namen '
            'zoals CON of NUL worden beveiligd.</p>\n'
            '\n'
            '<h3>Opnametijd</h3>\n'
            '<p>Voor de naamgeving gebruikt CMDRHelper de wijzigingstijd van het stabiele herkende '
            'BMP-bestand. Alleen als deze niet kan worden afgelezen, wordt de huidige tijd '
            'gebruikt.</p>\n'
            '<p>Dit betekent dat de naam meestal afhankelijk is van het bronbestand en niet van de '
            'daaropvolgende conversietijd.</p>\n'
            '\n'
            '<h3>Meerdere afbeeldingen in dezelfde seconde</h3>\n'
            '<p>Als de beoogde bestandsnaam al bestaat of gereserveerd is voor een lopende '
            'conversie, voegt CMDRHelper deze voortdurend '
            'toe<code>_2</code>,<code>_3</code>,<code>_4</code>enzovoort.</p>\n'
            '<p>Dit betekent dat een andere schermafbeelding met hetzelfde tijdstempel een '
            'bestaande doelafbeelding niet zal overschrijven.</p>\n'
            '\n'
            '<h3>Commandantwissel tijdens verwerking</h3>\n'
            '<p>Commander, FID en systeem worden samen vastgelegd tijdens het in de wachtrij '
            'plaatsen van een screenshot.</p>\n'
            '<p>Een latere wisseling van commandant verandert niets aan de toewijzing van dit toch '
            'al wachtende beeld. Dit betekent dat een screenshot van FABER38 vervolgens niet naar '
            'de map van een andere commandant wordt geschreven.</p>\n'
            '\n'
            '<h3>galerij</h3>\n'
            '<p>De galerij toont PNG-, JPG- en JPEG-bestanden uit de mappen die aan het '
            'geselecteerde filter zijn gekoppeld. Nieuwe, verwijderde of verplaatste afbeeldingen '
            'worden regelmatig gedetecteerd.</p>\n'
            '<p>Het galerijfilter verandert de opslaglocatie of commandanttoewijzing van de '
            'bestanden niet.</p>\n'
            '\n'
            '<h3>Huidige commandant</h3>\n'
            '<p>Het filter Huidige commandant toont afbeeldingen uit de map van de commandant die '
            'momenteel wordt bekeken in de CMDR-weergave.</p>\n'
            '<p>De betreffende commandant bepaalt alleen de galeriepresentatie. Aan de andere kant '
            'wordt bij het toewijzen van een nieuw live-screenshot de dagboekidentiteit gebruikt '
            'die actief is tijdens het in de wachtrij plaatsen.</p>\n'
            '\n'
            '<h3>Alle commandanten</h3>\n'
            '<p>Het filter “Alle Commanders” toont de afbeeldingen uit de geldige submappen van '
            'alle bekende commandanten samen. Er wordt ook rekening gehouden met de speciale map '
            'voor opnames zonder erkende identiteit.</p>\n'
            '<p>De bestanden worden niet verplaatst of samengevoegd.</p>\n'
            '\n'
            '<h3>Niet toegewezen</h3>\n'
            '<p>Het filter Niet-toegewezen toont ondersteunde afbeeldingsbestanden die zich '
            'rechtstreeks in de gedeelde doelhoofdmap bevinden.</p>\n'
            '<p>Met name oudere afbeeldingen zonder Commander-gerelateerde submappen blijven '
            'zichtbaar. CMDRHelper probeert achteraf niet te raden waar ze mee verbonden '
            'zijn.</p>\n'
            '\n'
            '<h3>Bestaande afbeeldingen</h3>\n'
            '<p>Afbeeldingen die al in de hoofdmap staan, worden niet automatisch verplaatst of '
            'hernoemd.</p>\n'
            '<p>Ze blijven toegankelijk via “Niet toegewezen” zolang ze beschikbaar zijn als PNG, '
            'JPG of JPEG.</p>\n'
            '\n'
            '<h3>Selecteer en bekijk afbeelding</h3>\n'
            '<p>Een simpele klik op een voorbeeldafbeelding toont de afbeelding geschaald in het '
            'voorbeeldgebied en geeft de bestandsnaam weer.</p>\n'
            '<p>Een dubbelklik opent het bestand met de besturingssysteemapplicatie ingesteld voor '
            'afbeeldingen.</p>\n'
            '<p>Er kunnen meerdere afbeeldingen tegelijkertijd worden gemarkeerd. Wanneer u de '
            'venstergrootte wijzigt, wordt het voorbeeld van de huidige afbeelding aangepast zodat '
            'deze past.</p>\n'
            '\n'
            '<h3>Afbeelding verwijderen</h3>\n'
            '<p>Gemarkeerde beelden kunnen worden verwijderd met behulp van “Geselecteerde '
            'verwijderen” of de Delete-toets. Voordat er wordt verwijderd, verschijnt er een '
            'beveiligingsvraag; Zonder selectie wordt eerst de noodzakelijke selectie '
            'aangegeven.</p>\n'
            '<p>Alleen de geselecteerde PNG/JPG/JPEG-doelbestanden worden verwijderd uit de mappen '
            'van het huidige galerijfilter. Het originele BMP-bronbestand wordt niet '
            'beïnvloed.</p>\n'
            '\n'
            '<h3>Doelmap openen</h3>\n'
            '<p>“Doelmap openen” opent de opslaglocatie in Bestandsbeheer en maakt indien nodig de '
            'gedeelde hoofdmap aan.</p>\n'
            '<p>Het filter “Huidige Commander” opent de bestaande Commander-submap. Als deze nog '
            'niet bestaat of er is een ander filter actief, wordt de gedeelde hoofdmap '
            'geopend.</p>\n'
            '\n'
            '<h3>Beveiliging van afbeeldingspaden</h3>\n'
            '<p>Voordat CMDRHelper het bestand verwijdert, controleert het het canonieke pad van '
            'elk bestand. Het moet zich in de geconfigureerde doelmap bevinden en rechtstreeks in '
            'een map die is toegestaan \u200b\u200bdoor het huidige galerijfilter.</p>\n'
            '<p>Symbolische links worden niet gebruikt als commandantmappen of galerijafbeeldingen '
            'en worden niet via de galerij verwijderd. Paden buiten het doelgebied en '
            'verplaatsingspaden worden afgewezen.</p>\n'
            '\n'
            '<h3>Als er geen commandant werd gedetecteerd</h3>\n'
            '<p>Als Commander en FID ontbreken bij het in de wachtrij plaatsen van een nieuwe '
            'opname, wordt het bestand niet in de wacht gezet en niet toegewezen aan een bekende '
            'Commander.</p>\n'
            '<p>Het zal in de submap staan<b>UNKNOWN_UNKNOWN/</b>verwerkt; de bestandsnaam die ook '
            'voor de Commander wordt gebruikt<b>ONBEKEND</b>. Deze map kan worden bekeken via Alle '
            'Commanders, niet via het filter voor de niet-toegewezen hoofdmap.</p>\n'
            '\n'
            '<h3>Verschillende commandanten</h3>\n'
            '<p>Voor beeldbeheer gelden twee afzonderlijke regels:</p>\n'
            '<ul>\n'
            '<li><b>Nieuwe afbeeldingen opslaan:</b>De actieve journaalidentiteit met Commander en '
            'FID wanneer deze in de wachtrij staat, bepaalt de doelmap.</li>\n'
            '<li><b>Afbeeldingen bekijken:</b>De bekeken commandant of het geselecteerde '
            'galerijfilter bepaalt de zichtbare afbeeldingen.</li>\n'
            '</ul>\n'
            '<p>Dit betekent dat de galerij van een andere commandant kan worden bekeken terwijl '
            'FABER38 wordt afgespeeld, zonder dat er nieuwe screenshots in de map van de '
            'betreffende commandant terechtkomen.</p>\n'
            '\n'
            '<h3>Tip</h3>\n'
            '<p>Een gedeelde screenshot-hoofdmap is voldoende. CMDRHelper scheidt nieuw verwerkte '
            'afbeeldingen automatisch in Commander en FID.</p>\n'
            '<p>Met "Huidige Commander", "Alle Commanders" en "Niet toegewezen" kunt u schakelen '
            'tussen persoonlijke galerij, de submappen van alle commandanten en oudere '
            'afbeeldingen in de hoofdmap.</p>\n'
            "<p>Een hogere helderheid kan helpen bij donkere foto's; het beïnvloedt de nieuw "
            'gemaakte doelafbeelding tijdens de conversie.</p>'),
 'commander_view': ('CMDR-weergave',
                    '<h2>CMDR-weergave</h2>\n'
                    '<p>De CMDR-weergave vat de permanent opgeslagen persoonlijke informatie van '
                    'een commandant samen.</p>\n'
                    '<p>Ook kunt u hiermee schakelen tussen de bekende CMDRHelper-commandanten en '
                    'hun eigen gegevens bekijken. Persoonlijke informatie wordt gescheiden met '
                    'behulp van de Frontier ID (FID).</p>\n'
                    '\n'
                    '<h3>Selecteer Commandant</h3>\n'
                    '<p>Als er meerdere commandanten bekend zijn, kunt u met bovenstaande selectie '
                    'bepalen wiens opgeslagen informatie wordt weergegeven. Deze commandant is de '
                    'beschouwde commandant.</p>\n'
                    '<p>Het display markeert het als “Live Active” of “View Only”.</p>\n'
                    '\n'
                    '<h3>Beschouwd als Commander en Live Commander</h3>\n'
                    '<p>Als u een andere commandant in de CMDR-weergave selecteert, wordt deze '
                    'niet de actieve journaalcommandant.</p>\n'
                    '<p>De live commandant wordt uitsluitend bepaald op basis van de momenteel '
                    'uniek geïdentificeerde Elite Dangerous-journaalsessie. Zo kan de historie van '
                    'een andere commandant worden bekeken terwijl Elite Dangerous blijft draaien '
                    'met FABER38.</p>\n'
                    '\n'
                    '<h3>Frontier-ID (FID)</h3>\n'
                    '<p>De FID is de stabiele Frontier-identificatie van een commandant.</p>\n'
                    '<p>CMDRHelper gebruikt het en de interne commandant-ID die daaruit is '
                    'afgeleid om persoonlijke gegevens veilig te scheiden. Commandanten met '
                    'vergelijkbare of identieke namen blijven ook gescheiden.</p>\n'
                    '\n'
                    '<h3>Overzicht</h3>\n'
                    '<p>Het tabblad “Overzicht” toont alleen permanent opgeslagen informatie van '
                    'de betreffende commandant:</p>\n'
                    '<ul>\n'
                    '<li>Commandernaam, FID en status “Live actief” of “Alleen bekijken”</li>\n'
                    '<li>eerste en laatst bekende tijdstip</li>\n'
                    '<li>Aantal bezochte systemen, bio- en geo-ontdekkingen, codex-inzendingen en '
                    'cartografie-verkopen</li>\n'
                    '<li>Laatst bekende locatie en aantal open missies</li>\n'
                    '<li>huidige of laatste schip</li>\n'
                    '<li>Fleet Carrier en transportlocatie</li>\n'
                    '<li>Activa</li>\n'
                    '<li>open biodata en open cartografische gegevens, inclusief bestaande '
                    'schattingen</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Activa/Kredieten</h3>\n'
                    '<p>Het veld “Activa” toont het meest recentelijk opgeslagen tegoed van de '
                    'betreffende commandant uit een desbetreffende journaalgebeurtenis, opgemaakt '
                    'als bijvoorbeeld<b>1.234.567 cr</b>.</p>\n'
                    '<p>CMDRHelper telt geen fictieve inkomsten of uitgaven op als er geen nieuwe, '
                    'veilige tijdschriftstatus is.</p>\n'
                    '\n'
                    '<h3>Huurlingen munten</h3>\n'
                    '<p>De huurlingenmunten zijn afkomstig uit de MercCoins-velden van Elite '
                    'Dangerous<code>Statistics → Bank_Account</code>en worden '
                    'commandantgerelateerd opgeslagen als een Frontier-snapshot.</p>\n'
                    '<p>Zichtbaar zijn:</p>\n'
                    '<ul>\n'
                    '<li>Huidig</li>\n'
                    '<li>Totaal uitgegeven</li>\n'
                    '<li>Engineering</li>\n'
                    '<li>apparatuur</li>\n'
                    '<li>Gerapporteerd door Frontier: overall verdiend</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Actueel en edities</h3>\n'
                    "<p>'Huidige' shows<code>MercCoins_Huidige</code>. “Total Spent” neemt het "
                    'over<code>MercCoins_Totaal_Uitgegeven</code>.</p>\n'
                    '<p>“Engineering” en “Apparatuur” tonen de aandelen die afzonderlijk worden '
                    'gerapporteerd door '
                    'Frontier<code>MercCoins_Spent_On_Engineering</code>En<code>MercCoins_Spent_On_MercGear</code>.</p>\n'
                    '<p>Voor FABER38 bijvoorbeeld een actuele inventaris van<b>1.275</b>, in '
                    'totaal<b>220</b>besteed en weg<b>220</b>gemeld voor techniek.</p>\n'
                    '\n'
                    '<h3>Kortom verdiend</h3>\n'
                    "<p>'Gerapporteerd door Frontier: overall "
                    "verdiend'-shows<code>MercCoins_Totaal_Verdiend</code>. CMDRHelper berekent "
                    'hieruit niet zijn eigen balans.</p>\n'
                    '<p>De cumulatieve waarde van Frontier hoeft niet wiskundig overeen te komen '
                    'met de huidige voorraad en gerapporteerde uitgaven. Er kunnen bijvoorbeeld '
                    'tegelijkertijd 1.275 huidige, 25 totaal verdiende en 220 totale uitgaven '
                    'worden gerapporteerd.</p>\n'
                    '<p>CMDRHelper corrigeert deze waarden niet, maar geeft de afzonderlijke '
                    'Frontier-tellers ongewijzigd weer.</p>\n'
                    '\n'
                    '<h3>Waarom heeft u geen eigen MercCoins-balans?</h3>\n'
                    '<p>Elite Dangerous biedt geen unieke journaalboeking voor elke individuele '
                    'ontvangst of uitgave van huursoldaten. De MercCoins verschijnen als totalen '
                    'in Statistics.</p>\n'
                    '<p>Een zelfberekende boekingsgeschiedenis zou daarom niet betrouwbaar zijn. '
                    'CMDRHelper slaat in plaats daarvan de laatst bekende Frontier-momentopname '
                    'op.</p>\n'
                    '\n'
                    '<h3>Missies</h3>\n'
                    '<p>Op het tabblad ‘Missies’ worden de opgeslagen missies van de betreffende '
                    'commandant weergegeven als een tabel met status, missienaam, doelstelling, '
                    'vervaltijd en beloning.</p>\n'
                    '\n'
                    '<h3>verkenning</h3>\n'
                    '<p>Het tabblad Verkenning toont open persoonsgegevens, open cartografische '
                    'gegevens, bioontdekkingen, eerste voetstappen, zelf in kaart gebrachte en '
                    'efficiënt in kaart gebrachte lichamen en het aantal bezochte systemen.</p>\n'
                    '<p>Het speciale tabblad ‘Kroniek’ binnen de CMDR-weergave is momenteel nog '
                    'steeds een tijdelijke aanduiding. De volledige kroniek is te vinden in het '
                    'gelijknamige hoofdmenu-item.</p>\n'
                    '\n'
                    '<h3>Schepen/vloot</h3>\n'
                    '<p>Het tabblad “Schepen” toont in eerste instantie het actieve of meest '
                    'recent gebruikte schip met scheepsnaam, scheepstype, locatie en ShipID.</p>\n'
                    '<p>De opgeslagen schepen van de betreffende commandant verschijnen daaronder '
                    'als uitbreidbare kaarten. Ze kunnen oplopend of aflopend worden gesorteerd '
                    'op:</p>\n'
                    '<ul>\n'
                    '<li>laatst of momenteel gebruikt</li>\n'
                    '<li>Scheepsnaam of scheepstype</li>\n'
                    '<li>maximaal springbereik</li>\n'
                    '<li>Laadvermogen of lege massa</li>\n'
                    '<li>laatst bekende locatie of tijd</li>\n'
                    '</ul>\n'
                    '<p>Je kunt ook filteren op alle schepen, schepen met een voertuighangar of '
                    'schepen met een jachthangar.</p>\n'
                    '\n'
                    '<h3>Scheepsgegevens</h3>\n'
                    '<p>Een geopende scheepskaart toont - indien opgeslagen - scheeps-ID, ShipID, '
                    'locatie, laatste keer, maximaal sprongbereik, FSD- en Guardian-booster, '
                    'massa, vracht- en tankcapaciteiten, evenals de laadtijd en -status.</p>\n'
                    '<p>Als modulegegevens beschikbaar zijn, worden voertuig- en gevechtshangar, '
                    'schildgenerator en schildbooster, Guardian-schildversterkingen, wapens, romp- '
                    'en moduleversterkingen en passagierscabines ook samengevat.</p>\n'
                    '<p>De uitrustingsstatus kan compleet, onvolledig of verouderd zijn. '
                    'Ontbrekende informatie wordt weergegeven als “–” en is niet aangevuld.</p>\n'
                    '\n'
                    '<h3>Fleet Carrier</h3>\n'
                    '<p>Voor een opgeslagen aangepaste Fleet Carrier toont de weergave de naam van '
                    'de provider, de roepnaam, de provider-ID, de laatste locatie en het tijdstip '
                    'van de laatste update.</p>\n'
                    '\n'
                    '<h3>Aanhoudende commandantstaat</h3>\n'
                    '<p>Belangrijke commandantinformatie blijft permanent opgeslagen. Hierdoor '
                    'kunnen bekende waarden na een herstart van CMDRHelper of Elite Dangerous '
                    'opnieuw worden weergegeven zonder elk journaal opnieuw volledig te '
                    'evalueren.</p>\n'
                    '<p>Nieuwe unieke journaalgebeurtenissen werken de opgeslagen status bij.</p>\n'
                    '\n'
                    '<h3>Historische reconstructie</h3>\n'
                    '<p>Voor functies die later worden toegevoegd, kan de CMDRHelper bestaande '
                    'journaalgebieden die duidelijk aan een commandant zijn toegewezen, eenmalig '
                    'doorzoeken op informatie die al bekend is.</p>\n'
                    '<p>Er kunnen bijvoorbeeld oudere MercCoins-snapshots worden overgenomen. '
                    'Herhaalde controles zijn niet bedoeld om dubbele gegevens te produceren en '
                    'veranderen de normale leesposities van journaal niet.</p>\n'
                    '\n'
                    '<h3>Verschillende commandanten</h3>\n'
                    '<p>In het bijzonder blijven de volgende gescheiden in termen van '
                    'commandanten:</p>\n'
                    '<ul>\n'
                    '<li>Activa en missies</li>\n'
                    '<li>eigen cartografie en organische vondsten</li>\n'
                    '<li>Geschiedenis van mijnbouw en huurlingenmunten</li>\n'
                    '<li>Online inloggegevens</li>\n'
                    '<li>commandant-gerelateerde schermafbeeldingen</li>\n'
                    '</ul>\n'
                    '<p>Globale astronomische eigenschappen van een systeem of lichaam kunnen '
                    'echter samen worden gebruikt.</p>\n'
                    '\n'
                    '<h3>Impact op andere opvattingen</h3>\n'
                    '<p>Als u de commandant in kwestie wijzigt, worden de CMDR-weergave zelf, de '
                    'persoonlijke mijnbouwgrondstofselectie van de kroniek en, met het juiste '
                    'filter, de screenshotgalerij bijgewerkt.</p>\n'
                    '<p>Het vervangt niet de daadwerkelijke live-commandant voor '
                    'journaalverwerking of online uploads.</p>\n'
                    '\n'
                    '<h3>Inara en EDSM</h3>\n'
                    '<p>De toegangen tot de Inara en EDSM worden afzonderlijk per commandant en '
                    'FID beheerd.</p>\n'
                    '<p>Alleen al door naar een commandant te kijken, wordt er geen transmissie '
                    'gestart met hun API-Key. Alleen het actieve dagboek FID is relevant voor live '
                    'uploads.</p>\n'
                    '<p>De toegangsgegevens worden beheerd onder “Instellingen” in het gedeelte '
                    'Onlinediensten.</p>\n'
                    '\n'
                    '<h3>Tip</h3>\n'
                    '<p>Gebruik de CMDR-weergave als u opgeslagen persoonlijke informatie van een '
                    'specifieke commandant wilt bekijken.</p>\n'
                    '<p><b>CMDR-weergave = Wie wil ik bekijken?</b></p>\n'
                    '<p><b>Active Journal-FID = Wie speelt er momenteel eigenlijk?</b></p>\n'
                    '<p>Deze scheiding voorkomt dat persoonlijke gegevens of online uploads van '
                    'verschillende commandanten met elkaar worden vermengd.</p>'),
 'settings': ('Instellingen',
              '<h2>Instellingen</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Betere update-informatie: het Ja/Nee-venster toont geïnstalleerde en beschikbare versie plus maximaal zes wijzigingen als een samenvatting bestaat. Lange lijsten scrollen en acties blijven bereikbaar. Deze weergave wordt met v3.2 geïnstalleerd; een ongewijzigde v3.1-client toont haar nog niet.</p>\n'
              '<p>Het gebied “Instellingen” bepaalt hoe CMDRHelper werkt met Elite Dangerous, '
              'journaalbestanden, database, online services, interface en updates.</p>\n'
              '<p>Wijzigingen in referenties en paden moeten zorgvuldig worden aangebracht. '
              'Commander-gerelateerde instellingen worden indien nodig afzonderlijk beheerd door '
              'Frontier ID.</p>\n'
              '\n'
              '<h3>tijdschrift</h3>\n'
              '<p>De journaalmap is een van de belangrijkste instellingen. Het moet verwijzen naar '
              'de map waarin Elite Dangerous het<code>Journaal*.log</code>bestanden van het '
              'gebruikte Windows- of Proton-profiel.</p>\n'
              '<p>De tijdschriften bieden onder meer:</p>\n'
              '<ul>\n'
              '<li>Identiteit, locatie en reizen van de commandant</li>\n'
              '<li>Missies, schepen en activa</li>\n'
              '<li>Exploratie, cartografie en BIO-gegevens</li>\n'
              '<li>Oppervlaktemijnbouw, huurlingenmunten en andere ondersteunde staten</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Journaalweergave en bediening</h3>\n'
              '<p>De dagboekgroep toont de mappenset, het aantal gevonden tijdschriften, de oudste '
              'en nieuwste dagboeken, de naam van het nieuwste bestand en het tijdstip van de '
              'laatste gelezen vermelding.</p>\n'
              '<p>“Selecteer dagboekmap” wijzigt de map. “Nu lezen” activeert onmiddellijk de '
              'normale update.</p>\n'
              '<p>Duidelijk herkenbare sessies worden toegewezen met behulp van FID. Nieuwe '
              'volledige boekingen worden stapsgewijs verwerkt; Veilige leesposities voorkomen dat '
              'elk tijdschrift de volgende keer dat het wordt gestart, onnodig in zijn geheel '
              'wordt herlezen.</p>\n'
              '\n'
              '<h3>database</h3>\n'
              '<p>CMDRHelper slaat de vereiste gegevens permanent op in een lokale '
              'SQLite-database. Dit omvat mondiale systeem- en lichaamsgegevens, evenals '
              'informatie die expliciet aan een commandant is toegewezen.</p>\n'
              '<p>De instellingenpagina toont statistieken over de opgeslagen gegevens. De '
              'database mag niet handmatig worden bewerkt terwijl CMDRHelper actief is.</p>\n'
              '\n'
              '<h3>Tijdschriftenarchief importeren</h3>\n'
              '<p>“Importeer journaalarchief” vergelijkt de journaalbestanden van de ingestelde '
              'journaalmap volledig met de database. Reeds bekende journaalgebieden worden op '
              'basis van de opgeslagen importinformatie in aanmerking genomen en niet blindelings '
              'gedupliceerd als nieuwe gegevens.</p>\n'
              '<p>Tijdens een handmatig zichtbare import worden de voortgang, het aantal en het '
              'momenteel verwerkte bestand weergegeven. Na voltooiing rapporteert CMDRHelper '
              'geïmporteerde of reeds bekende gegevens of een fout.</p>\n'
              '<p>De archiefimport dient ook om ondersteunde historische informatie uit duidelijk '
              'toegewezen tijdschriften opnieuw te leren.</p>\n'
              '\n'
              '<h3>Commandantgerelateerde gegevens</h3>\n'
              '<p>CMDRHelper scheidt persoonlijke informatie op basis van de FID en de '
              'bijbehorende interne Commander-ID. Deze omvatten, maar zijn niet beperkt tot, '
              'missies, middelen, MercCoins, persoonlijke verkenning en online toegang.</p>\n'
              '<p>Een onbekende of dubbelzinnige journaalsessie mag niet willekeurig aan een '
              'commandant worden toegewezen.</p>\n'
              '\n'
              '<h3>Onlinediensten</h3>\n'
              '<p>CMDRHelper ondersteunt EDSM en Inara. Beide toegangen worden voor elke bekende '
              'commandant of elke FID afzonderlijk verwerkt en opgeslagen.</p>\n'
              '<p>De selectie in de instellingen bepaalt alleen wiens toegang momenteel wordt '
              'bewerkt of getest. Alleen de commandant die duidelijk geïdentificeerd is door de '
              'actieve journaalsessie mag live zenden.</p>\n'
              '\n'
              '<h3>EDSM toegang voor</h3>\n'
              '<p>“EDSM access for:” selecteert de commandant die moet worden bewerkt. De selectie '
              'toont ‘set up’ of ‘not set up’, afhankelijk van of er een API-Key is '
              'opgeslagen.</p>\n'
              '<p>Zichtbaar zijn de naam van de commandant, het verborgen veld API-Key, "Gebruik '
              'EDSM", een verbindingstest en de laatste teststatus ervan.</p>\n'
              '<p>Elke commandant heeft zijn eigen geschikte EDSM-toegang nodig. De selectie '
              'schakelt de live-uploader niet over naar deze commandant.</p>\n'
              '\n'
              '<h3>Gebruik en test EDSM</h3>\n'
              '<p>“Gebruik EDSM” schakelt de service voor de geselecteerde FID in of uit. '
              'Ontbrekende of gedeactiveerde inloggegevens hebben geen invloed op de lokale '
              'journaalverwerking.</p>\n'
              '<p>“Test EDSM-verbinding” controleert de toegangsgegevens die momenteel zichtbaar '
              'zijn in het formulier. Een succesvolle test bevestigt de verbinding, maar verandert '
              'niets aan het actieve journaal FID of live commandant.</p>\n'
              '\n'
              '<h3>Inara-toegang voor</h3>\n'
              '<p>“Inara Access for:” volgt hetzelfde multi-CMDR-principe. Activering, '
              'Inara-commandantnaam en API-Key worden voor elke FID afzonderlijk opgeslagen.</p>\n'
              '<p>Ook hier staat bij de selectie ‘ingesteld’ of ‘niet ingesteld’. Een sleutel van '
              'de ene commandant wordt niet automatisch gebruikt voor een andere commandant.</p>\n'
              '\n'
              '<h3>Gebruik en test Inara</h3>\n'
              '<p>Als Inara is ingesteld en ingeschakeld voor het actieve journaal FID, kan '
              'CMDRHelper de ondersteunde reis-, locatie-, missie- en scheepsgebeurtenissen '
              'verzenden. Niet elke journaalgebeurtenis wordt naar Inara verzonden.</p>\n'
              '<p>"Test Inara-verbinding" controleert de momenteel zichtbare toegangsgegevens '
              'zonder de live-commandant te wijzigen.</p>\n'
              '\n'
              '<h3>Inara-uitbox</h3>\n'
              '<p>Ondersteunde Inara-gebeurtenissen worden voortdurend gemarkeerd in een postvak '
              'UIT voordat ze via het netwerk worden verzonden.</p>\n'
              '<p>Door tijdelijke fouten kunnen deze vermeldingen worden bewaard voor latere '
              'pogingen. De medewerker verwerkt alleen de outbox van het uniek actieve journaal '
              'FID; Inzendingen van andere commandanten zijn niet inbegrepen.</p>\n'
              '\n'
              '<h3>Onlinestatus in de header</h3>\n'
              '<p>EDSM toont momenteel:</p>\n'
              '<ul>\n'
              '<li><b>EDSM</b>– kan niet worden gebruikt of gedeactiveerd voor de actieve '
              'FID</li>\n'
              '<li><b>EDSM wacht</b>– ingesteld en zonder voortdurende verzending</li>\n'
              '<li><b>EDSM-transmissie</b>– de laatste verwerkingsrun EDSM is zonder fouten '
              'geëindigd; In de tooltip wordt aangegeven of gebeurtenissen zijn verzonden, '
              'journaalgegevens zijn verwerkt of er geen nieuwe gegevens zijn gevonden</li>\n'
              '<li><b>EDSM-fout</b>– de laatste verzendstatus is onjuist</li>\n'
              '</ul>\n'
              '<p>Er is momenteel geen aanvullende, afzonderlijk gelabelde status “EDSM actief” '
              'voor EDSM.</p>\n'
              '<p>Inara onderscheidt nauwkeuriger:</p>\n'
              '<ul>\n'
              '<li><b>INARA uit</b>– uitgeschakeld voor het actieve journaal FID</li>\n'
              '<li><b>INARA klaar</b>– ingesteld, maar nog steeds zonder bevestigde verzending in '
              'deze sessie</li>\n'
              '<li><b>INARA-transmissie</b>– de werknemer verzendt momenteel</li>\n'
              '<li><b>INARA actief</b>– de laatste daadwerkelijke overdracht is succesvol '
              'bevestigd</li>\n'
              '<li><b>INARA-fout</b>– de laatste overdrachtspoging is mislukt</li>\n'
              '</ul>\n'
              '\n'
              '<h3>API-Key-beveiliging</h3>\n'
              "<p>API-Key's zijn persoonlijke inloggegevens. De invoervelden zijn verborgen; Ze "
              'worden Commander-gerelateerd opgeslagen in de applicatie-instellingen en niet in de '
              'CMDRHelper-database.</p>\n'
              '<p>Sleutels mogen niet worden gepubliceerd, gedeeld in schermafbeeldingen of '
              'toegevoegd aan openbare opslagplaatsen.</p>\n'
              '\n'
              '<h3>Afbeeldingen/screenshots</h3>\n'
              '<p>Bronmap, Bestemmingsmap, PNG/JPG, Automatische verwerking, BMP verwijderen en '
              'Helderder maken van 0 tot 50 procent bevinden zich uitsluitend in het hoofdmenu '
              'Afbeeldingen, niet op de pagina Instellingen.</p>\n'
              '<p>De contextgevoelige help “Afbeeldingen” beschrijft deze opties in detail.</p>\n'
              '\n'
              '<h3>oppervlak</h3>\n'
              '<p>De interfacegroep omvat het uiterlijk, de taal, het lettertype, de lettergrootte '
              'en de waardedrempel voor waardevolle verkenners.</p>\n'
              '\n'
              '<h3>Donkere en lichte modus</h3>\n'
              '<p>Je kunt direct wisselen tussen donkere en lichte weergave. Het thema wordt '
              'onmiddellijk toegepast op de interface en bestaande systeem- en geschiedeniskaarten '
              'en opgeslagen.</p>\n'
              '\n'
              '<h3>Taal</h3>\n'
              '<p>De interface biedt twaalf talen om uit te kiezen. “Taal opslaan” slaat de '
              'selectie op; Voor een volledig uniforme conversie van bestaande widgets is dan een '
              'herstart van CMDRHelper vereist.</p>\n'
              '\n'
              '<h3>Lettertype en lettergrootte</h3>\n'
              '<p>Lettertypefamilie en lettergrootte van 7 tot 24 pt kunnen worden geselecteerd en '
              'opgeslagen.</p>\n'
              '<p>Beide wijzigingen worden pas volledig van kracht na een herstart. De interface '
              'geeft dit expliciet aan.</p>\n'
              '\n'
              '<h3>Waardedrempel</h3>\n'
              '<p>De Explorer-waardedrempel bepaalt de geschatte kredietwaarde waarvan lichamen '
              'als bijzonder waardevol worden gemarkeerd. De wijziging wordt onmiddellijk '
              'opgeslagen en werkt het bijbehorende Explorer-display bij.</p>\n'
              '\n'
              '<h3>Automatisch verbergen</h3>\n'
              '<p>“Precious Bodies” en “BIO Finds” bevinden zich stevig in de linkerzijbalk, niet '
              'op de pagina Instellingen.</p>\n'
              '<p>De schakelaars worden opgeslagen en besturen de ondersteunde kleine live '
              'hintvensters tijdens verkenning. De waardedrempel voor Waardevolle Lichamen wordt '
              'ingesteld in de interface-instellingen.</p>\n'
              '\n'
              '<p>Het Cargo-venster gebruikt uitsluitend de Cargo-snapshot die voor de actieve Journal-FID is bevestigd. De commander die in CMDR View wordt bekeken en viewed_commander_id beïnvloeden dit livevenster niet. Voor een Ship wordt bezet / maximaal · vrij getoond; als CargoCapacity onbekend is, wordt geen waarde geschat.</p>\n'
              '<p>‘EDSM-status-HUD’ onder ‘automatisch tonen’ staat standaard UIT. Na binnenkomst in een systeem verschijnt ongeveer 2,5 seconden een melding boven Elite. Meerdere Location-gebeurtenissen tijdens hetzelfde verblijf geven geen dubbele melding; een echte terugkeer mag opnieuw worden gecontroleerd.</p>\n<p>‘EDSM: BEKEND’ betekent een geldige EDSM-treffer voor het systeem. ‘EDSM: NIET BEKEND’ betekent een geldig EDSM-antwoord zonder systeemtreffer. ‘EDSM: GEEN ANTWOORD’ betekent een netwerk-, HTTP- of timeoutfout of ongeldig antwoord, nooit een bevestigde afwezigheid van een treffer. EDSM-bekendheid is geen officiële ontdekking in Elite; namen van eerste ontdekkers of melders worden niet beloofd.</p>\n<p>De melding werkt onafhankelijk van navigatie- en vracht-HUD. Permanente HUD-informatie en snel-favorietmeldingen blijven behouden. De aanvraag blokkeert de interface niet; late antwoorden voor al verlaten systemen worden verworpen.</p>\n\n'
              '<h3>Updates</h3>\n'
              '<p>De updategroep toont de geïnstalleerde versie en GitHub-status. Nu controleren '
              'controleert handmatig op een nieuwe geplande CMDRHelper-versie; Daarnaast vindt er '
              'na de start een uitgestelde automatische controle plaats.</p>\n'
              '<p>Als er een nieuwe versie beschikbaar is, zal CMDRHelper dit vragen voordat het '
              'wordt gedownload en geïnstalleerd. Een aangekondigde database-update wordt '
              'afzonderlijk in dit dialoogvenster weergegeven.</p>\n'
              '<p>Voor bestaande installaties volstaat normaal: update installeren → CMDRHelper starten. Noodzakelijke historische correcties voor BIO-gegevens, bezoeken en DSS-metadata lopen automatisch; vóór gegevensherstel met schrijfacties wordt een databaseback-up gemaakt. Reparaties hebben versies en zijn idempotent: geslaagde revisies worden niet bij elke start opnieuw volledig uitgevoerd. Reconstructie vereist Elite-journals die nog bestaan, leesbaar zijn en eenduidig aan een commander kunnen worden gekoppeld. Ontbrekende bronnen worden niet verzonnen of als succes behandeld; open reparaties worden bij de volgende start opnieuw geprobeerd. De database wissen, handmatige scripts en herimport zijn normaal niet nodig.</p>\n\n'
              '<h3>Voortgang downloaden</h3>\n'
              '<p>De download wordt op de achtergrond uitgevoerd. Als de totale grootte bekend is, '
              'toont CMDRHelper de bestandsnaam, ontvangen en totale MiB, percentage, '
              'overdrachtssnelheid en geschatte resterende tijd.</p>\n'
              '<p>Zonder bekende totale omvang werkt de voortgangsbalk in de bezetmodus en blijft '
              'de hoeveelheid ontvangen gegevens en – indien bepaalbaar – de snelheid weergeven. '
              'Vóór de installatie wordt de gedownloade ZIP gecontroleerd.</p>\n'
              '\n'
              '<h3>Update annuleren</h3>\n'
              '<p>Met “Download annuleren” wordt een lopende download gecontroleerd beëindigd. Een '
              'afgebroken, onvolledige of ongeldige download wordt niet geïnstalleerd.</p>\n'
              '\n'
              '<h3>Updaten op Windows</h3>\n'
              '<p>Op Windows gaat het daadwerkelijke updateproces door, ongeacht de '
              'oorspronkelijke startconsole. Het afsluiten van de console mag er daarom niet '
              'onbedoeld een einde aan maken.</p>\n'
              '<p>Als er een fout optreedt nadat de bestandswijzigingen zijn begonnen, probeert de '
              'bestaande rollback-back-up de vorige versie te herstellen.</p>\n'
              '\n'
              '<h3>Herstart na update</h3>\n'
              '<p>Na een succesvolle installatie start de updater CMDRHelper opnieuw op via het '
              'beoogde startpad en controleert kort of het nieuwe proces stabiel draait.</p>\n'
              '<p>Als voor een release een eenmalige database-update nodig is, wordt het '
              'tijdschriftarchief ook na de herstart opnieuw geëvalueerd.</p>\n'
              '\n'
              '<h3>Verschillende commandanten</h3>\n'
              '<p><b>Instellingenselectie = Wiens online toegang bewerk ik?</b></p>\n'
              '<p><b>Active Journal-FID = Wie mag live uitzenden?</b></p>\n'
              '<p>Noch de online accountselectie, noch de CMDR-weergave mogen een live uploader '
              'omschakelen naar een alleen-bekeken commandant.</p>\n'
              '\n'
              '<h3>Hulp</h3>\n'
              '<p>"? Help" bevindt zich in de linkerzijbalk boven "autoshow" en opent de hulp van '
              'het momenteel zichtbare hoofdmenugebied.</p>\n'
              '<p>In het gebied "Instellingen" opent de knop deze instellingenhulp direct.</p>\n'
              '\n'
              '<h3>Tip</h3>\n'
              '<p>Als u opnieuw installeert of problemen ondervindt, controleer dan eerst:</p>\n'
              '<ul>\n'
              '<li>correcte journaalmap en erkende identiteit van de commandant</li>\n'
              '<li>gewenste taal, thema, lettertype en verkennerwaardedrempel</li>\n'
              '<li>Online toegang tot de juiste FID</li>\n'
              '<li>In geval van beeldproblemen, bron- en doelmappen in het hoofdmenu '
              '“Afbeeldingen”.</li>\n'
              '</ul>\n'
              '<p>Als er meerdere commandanten zijn, let dan altijd op voor welke FID de zichtbare '
              'online toegangsgegevens gelden.</p>'),
    "planet_navigation": (
        'Planeetnavigatie',
        """<h2>Planeetnavigatie</h2>
<p>De planeetnavigator helpt je uitsluitend om naar een bepaalde breedtegraad/lengtegraad op een planeet of maan te vliegen. Je geeft een coördinatendoel op en krijgt de afstand en richting ernaartoe.</p>
<p>Het is geen interstellaire routeplanner en hij verzorgt geen systeem- of sprongnavigatie. Je bestuurt je schip zelf.</p>

<h3>De navigator openen en een doel invoeren</h3>
<p>Open in het overzicht ‘Planeetnavigatie’ en kies ‘Handmatige invoer …’.</p>
<ul>
<li><b>Hemellichaam:</b> Kies de doelplaneet of doelmaan uit de lijst of gebruik het al herkende hemellichaam. Je kunt de naam ook zelf invoeren als die nog niet in de lijst staat. Gebruik bij twijfel de volledige naam, inclusief de systeemnaam.</li>
<li><b>Breedtegraad:</b> Voer de breedtegraad van het doel in tussen −90° en +90°.</li>
<li><b>Lengtegraad:</b> Voer de lengtegraad van het doel in tussen −180° en +180°. Let bij beide coördinaten op het teken.</li>
<li><b>Doelnaam:</b> Je kunt optioneel een naam invoeren om je doel gemakkelijker te herkennen.</li>
</ul>
<p>Met ‘Doel instellen’ bevestig je de invoer. Technische ID’s zoals BodyID en SystemAddress hoef je niet in te voeren; het zijn geen normale gebruikersinvoeren.</p>

<h3>Wanneer start het kompas?</h3>
<p>Zodra een doel is ingesteld en Elite geldige planetaire positiegegevens voor het bijbehorende hemellichaam levert, wordt de navigatie automatisch actief. Je hoeft niet op een aparte startknop te drukken.</p>
<p>Als deze gegevens nog ontbreken of bij een ander hemellichaam horen, wacht de navigator met ‘Wachten op planetaire coördinaten …’. Je kunt al een doel invoeren voordat deze gegevens binnenkomen.</p>

<h3>Planeetbol: meer dan 380 km</h3>
<p>Bij een doelafstand groter dan 380 km toont de navigator de planeetbol.</p>
<ul>
<li>De <b>witte cirkel</b> markeert je eigen positie.</li>
<li>Het <b>kleine doelpunt</b> is oranje als het doel aan de zichtbare kant van de planeet ligt.</li>
<li>Als het doel aan de verborgen achterkant ligt, wordt het doelpunt rood weergegeven.</li>
<li>Je positie blijft vast in de weergave. De planeet en het doel worden weergegeven ten opzichte van je positie en oriëntatie.</li>
</ul>
<p>De witte pijl wijst vooruit; de gele pijl wijst in de relatieve doelrichting. De bol is een schematisch oriëntatiehulpmiddel, geen geografisch nauwkeurige terreinweergave. Een rood punt betekent de achterkant van de bol, niet automatisch ‘achter je schip’.</p>

<h3>Perspectiefraster: tot en met 380 km</h3>
<p>Bij een doelafstand tot en met 380 km schakelt de weergave automatisch over op een gekanteld perspectiefraster. Als de afstand weer boven 380 km komt, verschijnt de bol opnieuw.</p>
<p>De dwarslijnen vormen een <b>afstandenraster in stappen van 50 km</b>. Het doelpunt wordt binnen het raster getekend volgens afstand en relatieve richting. Het perspectief helpt bij de verdere nadering; door de kanteling lijken de afstanden naar achteren dichter op elkaar te liggen. Let voor de werkelijke stuurkoers ook op de doelkoers en relatieve richting.</p>

<h3>Navigatiewaarden goed lezen</h3>
<ul>
<li><b>Doelafstand:</b> De grote weergave toont de resterende afstand tot het doel langs het denkbeeldige planeetoppervlak.</li>
<li><b>Doelcoördinaten:</b> Het ingevoerde coördinatenpaar van het doel, eerst breedtegraad, dan lengtegraad. Het blijft onveranderd terwijl je beweegt.</li>
<li><b>Huidige coördinaten:</b> Je laatst bevestigde coördinatenpaar uit Elite, eveneens breedtegraad / lengtegraad.</li>
<li><b>Afstand over het oppervlak:</b> Dezelfde oppervlakteafstand als de doelafstand, eventueel nauwkeuriger afgerond in de detailweergave. Dit is geen tweede route en geen directe ruimtelijke afstand door de lucht.</li>
<li><b>Peiling:</b> De absolute richting naar het doel vanaf je huidige positie, als kompashoek: 000° is noord, 090° oost, 180° zuid en 270° west.</li>
<li><b>Voorliggende koers:</b> Je huidige oriëntatie zoals Elite die levert. Deze geeft aan waarheen je nu gericht bent en hoeft nog niet overeen te komen met de peiling.</li>
<li><b>Relatieve richting:</b> Het verschil tussen je oriëntatie en de peiling, bijvoorbeeld ‘23° rechts’, ‘10° links’ of ‘Rechtdoor’. Bij 180° ligt het doel achter je.</li>
<li><b>Doelkoers:</b> De uitgelichte peiling als absolute koers waarnaar je kunt draaien in de Elite-HUD. Het is geen extra draaihoek.</li>
</ul>
<p>Voorbeeld: bij een voorliggende koers van 051° en een doelkoers van 074° draai je 23° naar rechts totdat je Elite-kompas ongeveer 074° aangeeft. Tijdens de verdere vlucht kunnen peiling en doelkoers veranderen; volg de bijgewerkte waarden.</p>
<p>Op dezelfde positie als het doel, op een pool of op het exact tegenoverliggende punt op de planeet kan de richting onbepaald zijn. De navigator toont dan de bijbehorende melding in plaats van een verzonnen koers.</p>

<h3>Venstergrootte</h3>
<p>Het navigatorvenster is vrij schaalbaar. De bol of het perspectiefraster past zich proportioneel aan de beschikbare ruimte aan. De minimumgrootte houdt de detailwaarden leesbaar; de bol blijft rond. De positie en grootte van het venster worden opgeslagen.</p>

<h3>De navigatie-HUD inschakelen</h3>
<p>Vink links in het hoofdvenster het vakje aan onder <b>automatisch tonen → Navigatie-HUD</b>. Bij geldige planeetnavigatie verschijnt de HUD direct boven het zichtbare Elite-venster op de voorgrond.</p>
<p>Hij toont drie regels:</p>
<ul>
<li>relatieve richting</li>
<li>doelkoers</li>
<li>afstand</li>
</ul>
<p>De HUD is transparant, laat klikken door en neemt geen focus over: hij bedekt het spel niet met een ondoorzichtig vlak, onderschept geen muisklikken en neemt de invoerfocus niet van Elite over wanneer hij automatisch verschijnt.</p>
<p>Zonder geldige navigatie of eenduidige richting wordt hij automatisch onzichtbaar. Ook als Elite geminimaliseerd is of niet op de voorgrond staat, wordt hij verborgen. Het vinkje in de zijbalk kan toch aan blijven; het geeft je wens voor automatische weergave aan, niet de huidige zichtbaarheid.</p>
<p>De HUD is slechts een extra weergave. De normale navigator werkt er onafhankelijk van, ook als de HUD is uitgeschakeld of niet beschikbaar is.</p>

<h3>Een nieuw doel instellen</h3>
<p>Op hetzelfde hemellichaam kun je op elk moment opnieuw ‘Handmatige invoer …’ openen en andere coördinaten instellen. Het nieuwe doel vervangt het vorige navigatiedoel. Met bijbehorende positiegegevens wordt het kompas onmiddellijk bijgewerkt.</p>
<p>Met ‘Navigatie beëindigen’ verwijder je het huidige doel. Voor een volgende nadering stel je gewoon een nieuw doel in.</p>

<h3>Actualiteit van gegevens en beperkingen</h3>
<p>De navigatie is gebaseerd op de statusgegevens van Elite. Updates kunnen afhankelijk van de speltoestand vertraagd binnenkomen. De ouderdomsweergave in de navigator toont hoe lang geleden de laatste bevestigde statusmelding was.</p>
<p>De oppervlakteafstand beschrijft de kortste boog op een denkbeeldige bol. Het is geen terrein- of wegroute. De navigator kent geen obstakels of terreinhoogten langs de route; vlieghoogte, veilige snelheid en het vermijden van obstakels blijven jouw verantwoordelijkheid.</p>

<h3>Tip</h3>
<p>Controleer vóór de nadering de naam van het hemellichaam en de tekens van de doelcoördinaten. Richt je vervolgens op de doelkoers in het Elite-kompas en houd relatieve richting en afstand in de gaten. Als de navigator wacht, controleer dan of Elite al planetaire coördinaten voor het doelhemellichaam levert.</p>""",
    ),
}

DIALOG_TITLE = 'Hulp – {area}'
CLOSE_LABEL = 'Sluiten'
