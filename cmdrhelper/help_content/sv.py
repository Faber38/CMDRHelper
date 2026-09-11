"""Swedish content for contextual help."""


HELP_TOPICS = {
    "materials": (
        'Material',
        """<h2>Material</h2>
<h3>CMDRHelper v3.2</h3>
<p>Materialhantering för engineering: alla 146 material i Raw, Manufactured och Encoded, med grader, kapacitet och undantag. Aktuellt lager per commander, sökning, filter, fem diskreta radbakgrunder och sparade kolumnbredder och ordning ger överblick. Okänt lager skiljs från noll.</p>
<p>Odyssey-inventarium: den fjärde materialfliken innehåller 223 katalogidentiteter för varor, komponenter, data och förbrukningsvaror. Skeppsförråd, ryggsäck och tillförlitlig totalsumma hålls isär; uppdragsstaplar, uppdragsstatus och engineering-användning visas. Positiva antal visas i guld. Namn utan översättning visas på engelska.</p>
<p>Sökning efter materialhandlare (Hitta materialhandlare → Öppna ruttplaneraren): på begäran söker Spansh separat efter Raw, Manufactured och Encoded från commanderns aktuella system. Carriers utesluts och stationsdetaljer kontrolleras. Avståndet i ly är direkt mellan systemen; gemenskapsdata garanterar inte åtkomst. Överföring till ruttplaneraren anger bara målsystemet och startar ingen rutt. Ingen sökning efter Odyssey-handlare.</p>
<p>Det här huvudområdet visar ingenjörsmaterialen för den commander som visas för tillfället. Valet i CMDR-vyn gäller även här; andra commanders data hålls åtskilda.</p>
<h3>Tre kategorier</h3>
<p>Flikarna Råmaterial, Tillverkade material och Kodade data innehåller alla 146 katalogmaterial, inklusive Guardian- och Thargoid-material. Listan sorteras efter grad och alfabetiskt inom varje grad.</p>
<h3>Bestånd och staplar</h3>
<p>Siffrorna visar bestånd / maximum, till exempel Vanadin 244 / 250. Den tillhörande stapeln visar 97,6 %. Även material som du aldrig har ägt visas med 0 när beståndet är tillförlitligt känt.</p>
<p>Tomma bestånd markeras med dämpat rött, låga bestånd med gult/orange och nästan fulla eller fulla bestånd med grönt. Siffrorna förblir synliga oavsett färgerna.</p>
<h3>Sökning och filter</h3>
<p>Sökningen tar hänsyn till det visade och det engelska materialnamnet. Den kan kombineras med alla filter: Alla, Tomt (0), Lågt (över 0 till och med 20 %), Nästan fullt (från 80 % till under 100 %) och Fullt (100 %). Värden mellan 20 % och 80 % visas bara under Alla. Flikar och filter återställs vid nästa start.</p>
<h3>Okända värden</h3>
<p>Utan ett tillförlitligt fullständigt bestånd visas till exempel ? / 250. Om maximum är okänt kan det stå 12 / ?. I båda fallen visas varken procent eller stapel; sådana material visas enbart under Alla. En okänd grad visas i en egen grupp sist i listan.</p>
<h3>Löpande uppdatering</h3>
<p>Nya journalhändelser uppdaterar beståndet automatiskt, även efter materialbyten, ingenjörsarbete, syntes eller materialbelöningar. Under den första inläsningen visas ett laddningsmeddelande. Nyligen insamlat material markeras kort med en uppgift som Vanadin +1; förbrukning ger inget insamlingsmeddelande.</p>
<h3>Materialnamn</h3>
<p>Om ett materialnamn ännu inte finns på det valda språket visas dess engelska visningsnamn. Interna journalsymboler ersätter inte befintliga visningsnamn.</p>
<h3>Odyssey</h3>
<p>Den fjärde fliken under Material innehåller Varor, Komponenter, Data och Förbrukningsvaror. Skeppsförråd och Ryggsäck visar sina bestånd separat. Totalt visar summan endast när båda tillstånden stämmer överens på ett tillförlitligt sätt. Ett föråldrat ryggsäcksbestånd visas avsiktligt inte som aktuellt och räknas inte in i totalen; ? betyder okänt bestånd eller ett bestånd som för närvarande inte kan rekonstrueras tillförlitligt. Gränsen 1000 gäller varje kategori i skeppsförrådet, inte enskilda föremål. Exemplet för ingenjörsmaterial ovan definierar inget individuellt maximum för Odyssey-föremål. För förbrukningsvaror finns ännu ingen fullständigt validerad kapacitetsregel, så ingen obekräftad kapacitet visas.</p>
<p>Användning visar föremålets användningsmarkeringar. Uppdrag betyder att den specifika inventariestapeln är kopplad till ett uppdrag, inte att föremålstypen generellt är ett uppdragsföremål. Vanliga och uppdragsbundna staplar hålls åtskilda. Även efter att uppdraget har slutförts förblir föremålet markerat så länge journalen listar det i beståndet; ett slutfört uppdrag tar inte automatiskt bort det. Verktygstipset visar uppdragsnummer och känd status. Ingenjörsarbete betyder att den statiska Odyssey-katalogen känner till minst en bekräftad användning: dräktuppgradering, vapenuppgradering, dräktmodifiering, vapenmodifiering eller upplåsning av en ingenjör. De enskilda användningarna visas i verktygstipset. Avsaknad av markering betyder inte att föremålet är oanvändbart eller enbart kan handlas. Även Powerplay-föremål och andra specialföremål kan visas.</p>
<p>Sökningen hittar de visade lokala och engelska material-/föremålsnamnen. De sex Odyssey-filtren är Alla (alla föremål), Uppdrag (staplar kopplade till ett uppdrag), Ingenjörsarbete (föremål med bekräftad ingenjörsanvändning), Ryggsäck (ryggsäcksbestånd större än noll), Skeppsförråd (förrådsbestånd större än noll) och Bestånd 0 (tillförlitligt känt totalbestånd på 0). Okänt bestånd ? är inte 0 och ingår inte i Bestånd 0. Om en namnöversättning saknas används det engelska namnet, så vissa namn kan fortfarande visas på engelska i det valda språket. Detta är avsiktligt och är inget översättningsfel i beståndslogiken.</p>
<p>Beståndet uppdateras automatiskt i bakgrunden. Bekräftade nya insamlingar kan markeras kort. Vid byte av commander tas gamla bestånd omedelbart bort. Underflikar, filter, kolumnbredder och kolumnordning sparas separat för Odyssey.</p>""",
    ),'overview': ('Översikt',
              '<h2>Översikt</h2>\n'
              '<p>Översikten är startsidan för CMDRHelper. Den sammanfattar den viktigaste '
              'informationen om den för närvarande aktiva befälhavaren och visar med ett ögonkast '
              'om journalen, platsen och onlinetjänsterna är korrekt igenkända.</p>\n'
              '\n'
              '<h3>Befälhavare & skepp</h3>\n'
              '<p>Befälhavaren som känns igen från Elite Dangerous Journal och det fartyg som för '
              'närvarande används visas här.</p>\n'
              '<p>CMDRHelper tilldelar personuppgifter till respektive befäl baserat på Frontier '
              'ID (FID). Detta håller data från olika befälhavare åtskilda från varandra.</p>\n'
              '<p>Vid byte av befälhavare laddas den sparade informationen associerad med den nya '
              'befälhavaren.</p>\n'
              '\n'
              '<p>CMDRHelper visar det spelläge som Elite senast rapporterade. Open, Solo och Privat grupp identifieras från LoadGame. För privata grupper visas gruppnamnet som Elite rapporterade utan ändringar. Detta betyder inte att Elite körs just nu.</p>\n'
              '<h3>tidning</h3>\n'
              '<p>CMDRHelper använder Elite Dangerouss journalfiler som sin huvudsakliga '
              'datakälla.</p>\n'
              '<p>Journaldisplayen informerar om journalfiler har hittats och tilldelats den '
              'aktiva befälhavaren. Nya kompletta journalanteckningar bearbetas automatiskt under '
              'spelet.</p>\n'
              '<p>Journalområden som redan har bearbetats sparas så att CMDRHelper inte behöver '
              'utvärdera varje journal helt igen nästa gång den startas.</p>\n'
              '\n'
              '<h3>Nuvarande plats</h3>\n'
              '<p>Visar det för närvarande kända stjärnsystemet och - såvitt känt från journalen - '
              'den exakta platsen för befälhavaren.</p>\n'
              '<p>Platsen uppdateras av händelser som hopp, dockning och andra positionsrapporter '
              'och lagras på kommando-för-kommando basis.</p>\n'
              '\n'
              '<h3>Uppdrag</h3>\n'
              '<p>Detta område visar antalet för närvarande kända öppna uppdrag.</p>\n'
              '<p>"Uppdrag"-knappen eller menyalternativet tar dig till den fullständiga '
              'uppdragsvyn med kända uppdragsmål och statusinformation.</p>\n'
              '\n'
              '<h3>Last Stand</h3>\n'
              '<p>"Sista tillstånd" sammanfattar det senast kända ihållande befälhavartillståndet. '
              'Detta gör att viktig information kan återställas även efter omstart av Elite '
              'Dangerous eller CMDRHelper.</p>\n'
              '\n'
              '<h3>Slutliga system</h3>\n'
              '<p>System som nyligen har besökts eller identifierats från tidskriften visas '
              'här.</p>\n'
              '<p>Listan fungerar som en snabb översikt över befälhavarens senaste resa.</p>\n'
              '<p>Besökshistoriken tar med Location, FSDJump och CarrierJump även vid löpande journaluppdatering. Flera platshändelser under en sammanhängande vistelse räknas som ett besök: A → A → A räknas en gång. En verklig återkomst bevaras: A → B → C → A räknas som fyra besök.</p>\n\n'
              '<h3>Onlinestatus</h3>\n'
              '<p>Det finns ytterligare statusindikatorer högst upp i huvudfönstret:</p>\n'
              '<ul>\n'
              '<li><b>Journal erkänd</b>– CMDRHelper upptäckte en giltig journalkälla och '
              'befälhavares identitet.</li>\n'
              '<li><b>EDSM</b>– visar aktuell status för EDSM-överföringen för den aktiva '
              'journalen FID.</li>\n'
              '<li><b>INARA</b>– visar aktuell status för Inara-överföringen för den aktiva '
              'journalen FID.</li>\n'
              '</ul>\n'
              '<p>Onlineåtkomstdata hanteras separat för varje befälhavare. En befälhavare '
              'använder aldrig automatiskt en annan befälhavares API-Key.</p>\n'
              '\n'
              '<h3>Viktigt för flera befälhavare</h3>\n'
              '<p>Livedatan beror alltid på befälhavaren som tydligt identifierades av den '
              'aktuella Elite Dangerous journalsessionen.</p>\n'
              '<p>Att bara visa en annan befälhavare i en vy ändrar inte den aktiva '
              'direktbefälhavaren eller påverkar någon EDSM- eller Inara-sändning.</p>\n'
              '\n'
              '<h3>Dricks</h3>\n'
              '<p>Om befälhavaren, fartyget eller platsen inte stämmer överens med spelets '
              'nuvarande tillstånd, kontrollera först journalvisningen högst upp och kontrollera '
              'sedan journalmappen som är inställd under "Inställningar".</p>'
              '<p>Öppet visas i rött, Solo i guld och Privat grupp i grönt, med det rapporterade gruppnamnet. Läget återskapas från tillgängliga journaler och uppdateras med nya LoadGame-poster.</p>\n<p>Ett klick på en post under senaste system kopierar systemnamnet till urklipp. ”✓ Kopierat: &lt;System&gt;” visas en kort stund.</p>\n'),
 'missions': ('Uppdrag',
              '<h2>Uppdrag</h2>\n'
              '<p>Uppdragsvyn visar uppdragen för den för närvarande visade befälhavaren som är '
              'känd från Elite Dangerous Journal. CMDRHelper sparar uppdragsdata på '
              'kommando-för-kommando-basis så att öppna uppdrag behålls även efter en omstart av '
              'Elite Dangerous eller CMDRHelper.</p>\n'
              '\n'
              '<h3>Öppna uppdrag</h3>\n'
              '<p>Nya uppdrag kommer ut<code>MissionAccepted</code>övertagits och sparats '
              'permanent.</p>\n'
              '<p>Så länge det inte finns något slutgiltigt uppdragsevenemang förblir uppdraget '
              'öppet. En ny spelsession utan uppdragslista kanske inte automatiskt tar bort kända '
              'öppna uppdrag.</p>\n'
              '\n'
              '<h3>Uppdragsstatus</h3>\n'
              '<p>CMDRHelper bearbetar bland annat följande statusändringar:</p>\n'
              '<ul>\n'
              '<li>Uppdrag accepterat</li>\n'
              '<li>Uppdraget avslutat</li>\n'
              '<li>Uppdraget misslyckades</li>\n'
              '<li>Uppdraget avbröts</li>\n'
              '<li>Uppdragsmålet avleds</li>\n'
              '<li>Framsteg med stödda last-/depåuppdrag</li>\n'
              '</ul>\n'
              '<p>En sista händelse ändrar bara det associerade uppdraget.</p>\n'
              '\n'
              '<h3>Uppdrag från tidskriften</h3>\n'
              '<p>Elite Dangerous ger uppdragsinformation om olika journalhändelser. CMDRHelper '
              'slår samman dessa händelser till ett beständigt uppdragstillstånd.</p>\n'
              '<p>En verklig full mission händelse kan fungera som en auktoritativ ögonblicksbild. '
              'Om en sådan händelse saknas kommer äldre öppna uppdrag inte att stängas av enbart '
              'av denna anledning.</p>\n'
              '\n'
              '<h3>Destinationer och platser</h3>\n'
              '<p>I den mån Elite tillhandahåller informationen i journalen visar CMDRHelper:</p>\n'
              '<ul>\n'
              '<li>Målsystem</li>\n'
              '<li>Destinationsstation eller destination</li>\n'
              '<li>Målplanet eller kropp</li>\n'
              '<li>Uppdragsbeteckning</li>\n'
              '<li>kända framsteg</li>\n'
              '<li>aktuell status</li>\n'
              '</ul>\n'
              '<p>Inte varje uppdrag ger all information. Saknade data är inte uppfunna av '
              'CMDRHelper.</p>\n'
              '\n'
              '<h3>Uthållighet och starta om</h3>\n'
              '<p>Öppna uppdrag sparas i den befälhavarerelaterade databasen.</p>\n'
              '<p>Detta innebär att de behålls även om:</p>\n'
              '<ul>\n'
              '<li>Elite Dangerous avslutas och startas om senare</li>\n'
              '<li>CMDRHelper är stängd däremellan</li>\n'
              '<li>Den nya journalsessionen innehåller initialt inga uppdragshändelser</li>\n'
              '</ul>\n'
              '<p>Endast en dokumenterad uppdragshändelse ändrar det sparade tillståndet.</p>\n'
              '\n'
              '<h3>Flera befälhavare</h3>\n'
              '<p>Uppdragen är strikt åtskilda av befälhavaren.</p>\n'
              '<p>En uppdragshändelse tilldelas endast befälhavaren vars journalsession har '
              'identifierats unikt. Uppdrag från en annan befälhavare får inte visas eller '
              'ändras.</p>\n'
              '\n'
              '<h3>Föräldralösa eller inte längre giltiga uppdrag</h3>\n'
              '<p>Om äldre journaldata eller en tidigare import håller ett uppdrag öppet trots att '
              'det inte längre finns i spelet, kan den befintliga funktionen för '
              'återställning/rensning av föräldralösa uppdrag användas.</p>\n'
              '<p>Denna funktion bör endast användas om det är tydligt att det visade uppdraget '
              'inte längre är aktivt.</p>\n'
              '\n'
              '<h3>Onlinetjänster</h3>\n'
              '<p>Uppdragshändelser som stöds kan dessutom överföras till Inara om en giltig och '
              'aktiverad Inara-åtkomst är inställd för den aktiva journalen FID.</p>\n'
              '<p>En saknad eller oåtkomlig Inara-anslutning påverkar inte den lokala '
              'uppdragslagringen.</p>\n'
              '\n'
              '<h3>Dricks</h3>\n'
              '<p>Om ett uppdrag inte visas eller visar en felaktig status, kontrollera först om '
              'Elite Dangerous redan har skrivit motsvarande uppdragshändelse till journalen.</p>\n'
              '<p>CMDRHelper kan bara visa information som journalen faktiskt tillhandahåller '
              'eller som redan har lagrats från tidigare unika uppdragshändelser.</p>'),
 'explorer': ('Utforskare',
              '<h2>Utforskare</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Systemöversikt: den nya Elite-inspirerade vyn ersätter miniatyröversikten i Explorer och Krönika. Stjärnor och planeter bildar huvudstrukturen med månar som grenar nedanför; flerstjärnesystem förblir lättlästa. Zoom, rullning, anpassning till fönstret och klick på himlakroppar ger tillgång till detaljer.</p>\n<p>Kompakta asteroidbälten: kluster grupperas till bälten i översikten och de vanliga systemkartorna i Explorer och Krönika. Alla enskilda klusterdata bevaras.</p>\n<p>Korrigerad kartografi: en skanning efter DSS-kartläggning återställer inte längre osålda utforskningsvärden, kartläggningstid eller effektivitet. Felaktiga poster repareras vid start från tillgängliga journaler med entydig commander-koppling. Saknade källor lämnar reparationen öppen; databasen behöver inte raderas.</p>\n'
              '<p>Utforskaren utvärderar de system och himlakroppar som upptäckts och skannades av '
              'den aktiva befälhavaren. Den kombinerar din egen Elite Dangerous-journaldata med '
              'redan tillgänglig ytterligare information och visar utforskning, kartografi, '
              'biologiska/geologiska signaler och data från gruvdrift på ytan tillsammans.</p>\n'
              '\n'
              '<h3>Nuvarande system</h3>\n'
              '<p>Den nuvarande kunskapsnivån om systemet sammanfattas i det övre området.</p>\n'
              '<p>Dessa inkluderar bland annat:</p>\n'
              '<ul>\n'
              '<li>välkända och till och med antecknade kroppar i journalen</li>\n'
              '<li>befintliga signaler</li>\n'
              '<li>Skanna värden</li>\n'
              '<li>kartografivärde redan uppnått</li>\n'
              '<li>möjligt totalvärde om det är fullt kartlagt</li>\n'
              '<li>BIO-status och uppskattade BIO-värden</li>\n'
              '<li>Kartografi och BIO-data som ännu inte har lämnats in</li>\n'
              '</ul>\n'
              '<p>Värdena som visas är baserade på faktiskt tillgängliga data. Saknad information '
              'presenteras inte som en separat upptäckt.</p>\n'
              '\n'
              '<h3>Systemkarta</h3>\n'
              '<p>Systemkartan representerar grafiskt stjärnor, planeter, månar och andra kända '
              'kroppar i det nuvarande systemet.</p>\n'
              '<p>En kropp kan klickas för att öppna dess detaljerade vy.</p>\n'
              '<p>Displayen visar bland annat kroppstyp, avstånd och – om tillgängligt – '
              'skannings- och kartografivärden samt speciella prospekteringsegenskaper.</p>\n'
              '\n'
              '<h3>ORGANISK ×N</h3>\n'
              '<p>BIO ×N anger antalet biologiska signaler från en kropp som rapporterats av '
              'spelet.</p>\n'
              '<p>Siffran anger initialt bara hur många biologiska signaler eller släkten som '
              'rapporterats. Det betyder inte automatiskt att alla biologiska arter redan har '
              'hittats eller analyserats.</p>\n'
              '<p>Faktiska egna organiska upptäckter hålls separat.</p>\n'
              '\n'
              '<h3>GEO ×N</h3>\n'
              '<p>GEO ×N visar antalet geologiska signaler från en kropp som rapporterats av '
              'spelet.</p>\n'
              '<p>Dessa kan till exempel inkludera geologiska egenskaper som fumaroler eller '
              'gejsrar. CMDRHelper visar endast den information som framgår av befintlig '
              'journal/kroppsdata.</p>\n'
              '\n'
              '<h3>ABBAU ×N</h3>\n'
              '<p>ABBAU ×N visar antalet planetariska gruvplatser för en kropp som rapporterats av '
              'Elite Dangerous.</p>\n'
              '<p>Exempel:</p>\n'
              '<p><b>ABBAU ×24</b></p>\n'
              '<p>betyder att 24 planetariska gruvplatser har rapporterats för denna kropp.</p>\n'
              '<p>Siffran säger inte vilken råvara som kan utvinnas på en enda plats.</p>\n'
              '\n'
              '<h3>Egna gruvfynd</h3>\n'
              '<p>Om befälhavaren faktiskt har utfört ytbrytning med Rhino, lagrar CMDRHelper de '
              'personliga fynden som dokumenterats separat.</p>\n'
              '<p>Man skiljer mellan:</p>\n'
              '<ul>\n'
              '<li>faktiskt erhållna varor, t.ex. B. Koppar i ton</li>\n'
              '<li>sekundära material som samlats in under gruvdrift</li>\n'
              '<li>kroppens allmänna ytmaterial</li>\n'
              '</ul>\n'
              '<p>Ett exempel på ett personligt fynd skulle vara:</p>\n'
              '<p><b>Koppar – 56 t</b></p>\n'
              '<p>Denna information betyder att befälhavaren faktiskt utvann 56 ton koppar '
              'där.</p>\n'
              '<p>De personliga gruvfynden sparas för varje befäl och blandas inte med andra '
              'befälhavares fynd.</p>\n'
              '\n'
              '<h3>Kroppsytmaterial</h3>\n'
              '<p><code>Scan.Materials</code>beskriver en kropps allmänna '
              'ytmaterialsammansättning.</p>\n'
              '<p>Till exempel kan järn, nickel, svavel eller andra material visas med '
              'procentvärden.</p>\n'
              '<p>Dessa värden ska inte förväxlas med råvarorna i en planetarisk gruvdepå. '
              'Frontier tillhandahåller ingen dokumenterad direkt koppling mellan dessa allmänna '
              'kroppsmaterial och innehållet på en enskild gruvplats i Journalen.</p>\n'
              '\n'
              '<h3>Terraformning</h3>\n'
              '<p>Symbolen eller etiketten för terraforming visar att en kropp anses vara en '
              'terraforming-kandidat baserat på tillgängliga data.</p>\n'
              '\n'
              '<h3>Första upptäckten</h3>\n'
              '<p>”Redan upptäckt vid din skanning” beskriver tillståndet före din skanning då. Ja betyder tidigare upptäckt, Nej betyder ännu inte upptäckt då; saknade uppgifter förblir Okända. ★ markerar en First Discovery-kandidat vid skanningstillfället, inte en garanterad officiell förstaupptäckt som fortfarande är tillgänglig i dag.</p>\n<p>Ett historiskt WasDiscovered=false eller WasMapped=false betyder inte att himlakroppen fortfarande är oupptäckt eller okartlagd i dag. Uppgifterna förblir historiska efter dataförsäljning eller återbesök. Kännedom i EDSM är separat information och bevisar ingen officiell upptäckt i Elite. Ingen officiell första upptäckare härleds ur detta.</p>\n'
              '\n'
              '<h3>Första kartläggningen</h3>\n'
              '<p>CMDRHelper skiljer mellan:</p>\n'
              '<ul>\n'
              '<li>◉ First Mapping-kandidat vid skanningstillfället: ännu inte kartlagd när du skannade</li>\n<li>◎ Kartlagd av dig: din egen slutförda DSS-kartläggning är registrerad</li>\n<li>◉✓ Kandidat vid skanningen och egen kartläggning belagda; officiell förstakartläggning obekräftad</li>\n'
              '</ul>\n'
              '<p>”Redan kartlagd vid din skanning” bedöms oberoende av upptäckt. Saknade uppgifter förblir Okända. En redan upptäckt himlakropp kan ha varit okartlagd vid skanningen. Din egen kartläggning bekräftar ingen officiell First Mapping-märkning; vid flera besök är inte heller ordningen i förhållande till den sparade skanningen alltid belagd.</p>\n<p>Slutförd egen DSS-kartläggning sparar nu tillförlitligt tidpunkten, använda sonder och effektivitetsmålet. Senare skanningar gör inte längre att befintliga uppgifter förloras.</p>\n'
              '\n'
              '<h3>Country bar</h3>\n'
              '<p>Landbarhetsindikatorn identifierar kroppar på vilka, enligt kända data, landning '
              'är möjlig.</p>\n'
              '\n'
              '<h3>Guldramar / värdefulla kroppar</h3>\n'
              '<p>Särskilt värdefulla kroppar kan markeras i utforskarens display.</p>\n'
              '<p>Guldramen markerar en uppskattad kartläggningssumma över den inställda tröskeln. Den är ingen First Discovery-markering och bekräftar varken osålda data eller förstabonuser som fortfarande är tillgängliga i dag.</p>\n'
              '<p>Det ersätter inte den detaljerade visningen av kroppens värde.</p>\n'
              '\n'
              '<h3>Lista över värden</h3>\n'
              '<p>Värdelistan visar uppskattningar utifrån den sparade skanningen, inte garanterade återstående utbetalningar. Förstabonuser förblir obekräftade. Verktygstips i karta och lista samt kroppsdetaljer använder samma tidsbestämda tillstånd.</p>\n'
              '<p>Den är särskilt lämplig för att snabbt jämföra intressanta eller värdefulla '
              'kroppar i ett system.</p>\n'
              '\n'
              '<h3>ORGANISK / GEO / NEDBRYTNING</h3>\n'
              '<p>Denna syn grupperar kroppar med biologiska, geologiska eller planetariska '
              'nedbrytningssignaler.</p>\n'
              '<p>Detta gör att intressanta kroppar inte behöver sökas individuellt i den '
              'kompletta systemkartan.</p>\n'
              '<p>Om du har dina egna gruvdata kan dina personliga gruvfynd också vara '
              'synliga.</p>\n'
              '<p>Manuellt justerade kolumnbredder i den gemensamma Explorer-tabellen BIO / GEO / ABBAU bevaras när fönstret öppnas igen och efter omstart. Sparade kolumnbredder i popupfönster återställs robustare; ogiltiga värden ersätts med säkra standardbredder.</p>\n\n'
              '<h3>Kroppsdetalj</h3>\n'
              '<p>Genom att klicka på en kropp öppnas den detaljerade vyn.</p>\n'
              '<p>Såvitt känt kan följande förekomma där:</p>\n'
              '<ul>\n'
              '<li>Kroppstyp</li>\n'
              '<li>massa</li>\n'
              '<li>avstånd</li>\n'
              '<li>Allvar</li>\n'
              '<li>atmosfär</li>\n'
              '<li>Landbarhet</li>\n'
              '<li>Terraforming status</li>\n'
              '<li>BIO/GEO-signaler</li>\n'
              '<li>planetära gruvplatser</li>\n'
              '<li>Ytmaterial</li>\n'
              '<li>egna gruvfynd</li>\n'
              '<li>Skanningsvärde</li>\n'
              '<li>kartografiskt värde</li>\n'
              '<li>nuvarande värde</li>\n'
              '</ul>\n'
              '<p>Alla kroppar har inte all information.</p>\n'
              '\n'
              '<h3>BIO-prognoser</h3>\n'
              '<p>CMDRHelper kan uppskatta möjliga biologiska upptäckter baserat på befintliga '
              'data om lämpliga kroppar.</p>\n'
              '<p>Förutsägelser är inte en garanti för att en viss art faktiskt kommer att finnas. '
              'De fungerar som ett beslutsfattande stöd för prospektering.</p>\n'
              '<p>Uppskattade BIO-värden är också förutsägelser och behandlas separat från '
              'faktiska bekräftade fynd.</p>\n'
              '\n'
              '<h3>Ännu inte inlämnat</h3>\n'
              '<p>CMDRHelper upprätthåller befälhavarerelaterade kända kartografi- och BIO-data '
              'som ännu inte har skickats in.</p>\n'
              '<p>Kartografiförsäljning och biologiska royalties redovisas med hjälp av '
              'motsvarande journalhändelser.</p>\n'
              '<p>Kartografidata som redan har sålts ska inte visas som öppna igen efter '
              'rekonstruktion.</p>\n'
              '\n'
              '<h3>Visa bil</h3>\n'
              '<p>Utforskartips som stöds som värdefulla kroppar eller BIO-fynd kan visas '
              'automatiskt med omkopplarna i det vänstra sidofältet.</p>\n'
              '<p>Dessa små live-fönster fungerar som ytterligare tips medan du spelar och '
              'ersätter inte hela Explorer-vyn.</p>\n'
              '<p>”Cargo” visar det bekräftade innehållet i det Ship eller SRV som bestäms av den aktiva Journal-FID:n. SRV Cargo övertas aldrig som Ship Cargo; Limpets räknas in i den totala lasten och visas separat i tabellen Namn | Antal.</p>\n'
              '<p>BIO-förloppet är kompakt: 1/3 gult, 2/3 blått och 3/3 grönt; det slutförda tillståndet ”Klart” är också grönt. Under ”visa automatiskt” har GEO en egen sparad omkopplare: enbart BIO, enbart GEO eller båda tillsammans.</p>\n<p>Lastfönstret anpassar automatiskt höjden efter innehållet. Vid många poster begränsas höjden och tabellen kan rullas; vald bredd och fönsterposition bevaras. Den befintliga omkopplaren ”Lastutrymmets HUD” finns nu under ”visa automatiskt”, utan en extra omkopplare i lastfönstret.</p>\n\n'
              '<h3>Flera befälhavare</h3>\n'
              '<p>Personliga prospekteringsresultat, kartografi, BIO-fynd och egna ytgruvfynd '
              'tilldelas respektive befäl.</p>\n'
              '<p>Globala astronomiska egenskaper hos en kropp - till exempel antalet kända '
              'planetariska gruvplatser - förblir egenskaper hos kroppen själv.</p>\n'
              '\n'
              '<h3>Dricks</h3>\n'
              '<p>Om du har en intressant kropp är det värt att klicka på den detaljerade vyn. '
              'Detta är det bästa stället att skilja mellan allmänna kroppsdata, möjliga '
              'prospekteringsresultat och faktiska fynd dokumenterade av din egen '
              'befälhavare.</p>'
              """

<h3>★ Favoriter</h3>
<p>Knappen ”★ Favoriter” högst upp i Explorer öppnar ett eget, återanvändbart favoritfönster. Där sparar du system, planeter/månar och platser på ytan för den aktiva befälhavaren.</p>
<p>Den rullningsbara listan, alfabetiskt sorterad efter namn, visar namn, typ, system, himlakropp och latitud/longitud där det är relevant, kategori och en liten bildförhandsvisning. Fritextsökning, typfilter och kategorifilter kan användas tillsammans. Sökningen omfattar namn, system, himlakropp och anteckning.</p>
<p>”Öppna / Visa” visar de sparade uppgifterna, anteckningen och en större bildförhandsvisning. ”Visa i Explorer” öppnar den befintliga systemöversikten eller himlakroppens detaljvy om favoriten tillhör det aktuella Explorer-systemet och motsvarande data finns. För andra system förblir favoritens sparade data synliga; ingen systemrutt beräknas.</p>

<h3>Spara ett system, en planet eller aktuell position</h3>
<ul>
<li>”★ Spara aktuellt system” sparar det aktuella systemet utan ytkoordinater.</li>
<li>”★ Spara planet / måne” låter dig välja en känd planet eller måne i det aktuella systemet. Den här favoriten får inte heller några ytkoordinater.</li>
<li>”★ Spara aktuell position” finns högst upp i favoritfönstret bredvid de två andra sparalternativen och är även tillgänglig i planetnavigatorn. I favoritfönstret är knappen alltid synlig och är inaktiverad utan giltiga aktuella planetära positionsdata och en aktiv befälhavare. Vid klick låses befälhavare, system, himlakropp, latitud och longitud. Senare rörelser i spelet ändrar inte dessa värden i den öppna dialogrutan.</li>
</ul>
<p>Ange ett valfritt namn och välj exakt en kategori: Bio, Geo, Gruvdrift, Utsikt, Landningsplats, Intressant eller Övrigt. Anteckning och bild är valfria. Kända tekniska ID:n överförs internt; du behöver inte ange dem. Även latitud eller longitud 0,0 är giltiga koordinater.</p>
<p>”Redigera” ändrar namn, kategori, anteckning och bild. System, himlakropp och sparade koordinater behålls. Om du vill spara en annan plats på ytan skapar du en ny favorit på den positionen.</p>

<h3>Snabbfavorit utan mus</h3>
<p>Under ”Inställningar → Snabbfavorit” kan du fritt ange, ändra eller ta bort en global snabbtangent. Efter installationen är den som standard ”Inte tilldelad”: CMDRHelper registrerar ingen tangent utan att du ber om det. Tilldelningen sparas. Om en kombination redan används eller inte är tillgänglig på ditt system visas ett felmeddelande; en tidigare fungerande tilldelning behålls.</p>
<p>På Linux/X11 och Windows fungerar snabbtangenten även när Elite har fokus – till fots, i SRV:n och i skeppet. En tangenttryckning sparar omedelbart den aktuella positionen på ytan för den aktiva befälhavaren, utan dialogruta och utan att använda musen. Befälhavare, system, himlakropp och aktuella Latitude-/Longitude-värden fryses i det ögonblicket. Utan giltiga aktuella planetkoordinater sparas ingenting; tidigare koordinater återanvänds inte.</p>
<p>Favoriten får ett unikt tillfälligt namn, till exempel ”Markör 07.09.2026 06:32:15”, och kategorin ”Övrigt”. I det vanliga favoritfönstret kan du senare byta namn på den, tilldela en annan kategori, lägga till en anteckning eller en bild. Ingen skärmbild tas eller importeras automatiskt.</p>
<p>I ungefär två sekunder visas ”★ FAVORIT SPARAD” direkt över det aktiva Elite-fönstret med himlakropp och koordinater; om positionen saknas visas ”⚠ INGA PLANETKOORDINATER” en kort stund. Visningen tar inte fokus och fångar inte upp inmatning. Den fungerar även när navigations-HUD:en är avstängd och försvinner sedan helt. När HUD:en är påslagen finns den vanliga navigationsvisningen kvar efteråt. Den sparade inställningen för HUD-reglaget ändras inte. Visningen använder samma överläggslösning och plattformskrav som navigations-HUD:en.</p>

<h3>Favoritbilder</h3>
<p>Favoritbilder är separata från området Bilder. ”Välj bild …” tillåter PNG, JPEG och WebP. Först när du sparar kopierar CMDRHelper den valda bilden till sin egen mapp för favoritbilder. Originalfilen varken flyttas eller ändras.</p>
<p>”Använd senaste skärmbilden” läser vid varje klick in den inställda källmappen för skärmbilder på nytt och söker efter läsbara skärmbilder med typiska Elite-filnamn. Utan inställning används de vanliga Elite-skärmbildsmapparna i Windows eller Steam/Proton. Även den aktiva befälhavarens mapp i den inställda konverteringsdestinationen söks igenom efter motsvarande konverterade Elite-skärmbilder. En konverterad skärmbild kan därför fortfarande hittas om dess ursprungliga BMP har raderats. Den senaste tagningstidpunkten bestäms av en entydig tidsangivelse i filnamnet, annars av filtiden; för konverterade bilder används tagningstiden som sparats i namnet i stället för konverteringstidpunkten. CMDRHelper tar inte själv skärmbilder och söker inte i godtyckliga bildmappar.</p>
<p>Före användning visas filnamn, tagningstid och en nyladdad förhandsvisning. Bekräfta med ”Använd den här bilden”. Om ingen lämplig skärmbild hittas kan du fortfarande använda ”Välj bild …”. Elite-skärmbilder i BMP-format sparas som en intern PNG-kopia.</p>
<p>En bild kan ersättas i redigeringsdialogen eller väljas bort med ”Ta bort bild”. När du sparar tas den interna kopian som inte längre används bort. Om en bildfil saknas kan favoriten fortfarande användas utan förhandsvisning.</p>

<h3>Favoritmål och befälhavare</h3>
<p>”▶ Till rutten” anger favoritens kända system som mål i ruttplaneraren. Starten följer befintligt beteende med aktuellt AppState; en manuellt angiven start behålls. Ingen rutt beräknas automatiskt. ”◎ Till koordinaterna” startar befintlig planetnavigering till platsen på ytan med befintlig HUD när system, himlakropp och giltiga koordinater är sparade. Resan till systemet och ytnavigeringen är två separata steg, utan automatisk reseföljd. Utan ytkoordinater är bara rutten tillgänglig; åtgärder som saknar nödvändiga data döljs.</p>
<p>För platser på ytan skickar ”◎ Till koordinaterna” den sparade himlakroppen, latituden, longituden och favoritnamnet till den befintliga planetnavigatorn. Det nya målet ersätter det föregående. Favoriter har ingen egen navigationslogik. Navigatorn avgör fortfarande själv: matchande giltiga planetära data aktiverar navigationen; annars väntar den på dessa data.</p>
<p>Favoriter tillhör enbart den aktiva befälhavaren. Vid byte av befälhavare uppdateras listan och en öppen redigeringsdialog förkastas. Ett mål som fortfarande hanteras som den föregående befälhavarens favoritmål avslutas. Befälhavarvalet i krönikan utökar inte den här favoritlistan.</p>
<p>”Ta bort” kräver bekräftelse och tar bara bort favoritposten och dess interna bildkopia. Den ursprungliga skärmbilden eller den valda originalbilden och alla Explorer-, journal- och himlakroppsdata bevaras.</p>"""),
 'chronicle': (
        'Krönika',
        """<h2>Krönika</h2>
<h3>CMDRHelper v3.2</h3>
<p>Systemöversikt: den nya Elite-inspirerade vyn ersätter miniatyröversikten i Explorer och Krönika. Stjärnor och planeter bildar huvudstrukturen med månar som grenar nedanför; flerstjärnesystem förblir lättlästa. Zoom, rullning, anpassning till fönstret och klick på himlakroppar ger tillgång till detaljer.</p>
<p>Kompakta asteroidbälten: kluster grupperas till bälten i översikten och de vanliga systemkartorna i Explorer och Krönika. Alla enskilda klusterdata bevaras.</p>
<p>Krönikan är befälhavarens personliga rese- och upptäcktshistoria. Den använder den permanent lagrade journalinformationen för att hitta system som redan har besökts, för att rumsligt representera dem och för att söka efter kända upptäckter.</p>

<h3>System besökt</h3>
<p>Krönikan visar de besökta systemen och deras platser i galaxen som befälhavaren känner till.</p>
<p>Om tillgängligt beaktas det första och sista besöket samt känd kroppsinformation.</p>
<p>Med en aktiv period avser besöksantal, första besök och senaste besök i kartvyn de filtrerade faktiska systembesöken.</p>
<p>Krönikan är därför inte bara en karta, utan också ett verktyg för att hitta tidigare resmål och upptäckter.</p>

<h3>3D karta</h3>
<p>De besökta systemen är rumsligt representerade med hjälp av deras galaktiska X/Y/Z-koordinater.</p>
<p>Bruksanvisningen finns direkt ovanför kartan:</p>
<ul>
<li>Håll ned vänster musknapp → rotera vy</li>
<li>håll ned mittenknappen och dra → rita upp ett zoomfönster</li>
<li>Håll ner höger musknapp → flytta vy</li>
</ul>
<p>Den lilla axeldisplayen hjälper till med orientering i rymden.</p>

<h3>Aktuell position</h3>
<p>Med "Current Position" kan kartvyn justeras eller återgå till den aktuella kända platsen för den aktiva befälhavaren.</p>
<p>Först tillämpas de aktuella filtren. Vyn centreras på det aktuella systemet endast om det finns med i den resulterande kartan.</p>
<p>Annars visas ”Det aktuella systemet ingår inte i detta filterurval.” Filtren tas inte bort av detta.</p>

<h3>Justera</h3>
<p>”Justera” återställer orienteringen till en vy ovanifrån av det galaktiska planet. Förskjutning och zoom behålls.</p>
<p>Det är användbart om många rotationer har gjort kartan svåröverskådlig.</p>

<h3>Uppdatera Krönika</h3>
<p>”Uppdatera Krönika” läser in krönikedata på nytt med de aktuella kombinerade filtren och uppdaterar visningen. Fritext, aktiverade datumgränser och gruvfilter utvärderas tillsammans igen; aktiva filter ignoreras inte.</p>
<p>Funktionen ändrar inte journalfiler eller skapar nya prospekteringsdata. Den uppdaterar helt enkelt historikvisningen baserat på befintliga CMDRHelper-data.</p>

<h3>Fritextsökning</h3>
<p>Redan känt innehåll kan sökas i fältet "Sökhistorik...".</p>
<p>Sökningen tar hänsyn till – om tillgängligt i databasen – bland annat:</p>
<ul>
<li>Systemnamn</li>
<li>Kroppsegenskaper</li>
<li>biologiska data</li>
<li>Material</li>
<li>Codex data</li>
</ul>
<p>Fritext, period och gruvdrift finns i ett gemensamt filterområde. ”Tillämpa” utvärderar de inställda filtren tillsammans. Enter i fritextfältet startar samma kombinerade filtrering som ”Tillämpa”.</p>

<h3>Period Från/Till (UTC)</h3>
<p>Aktivera ”Från” och ”Till” med respektive kryssruta och välj önskat datum. Det går även att använda bara en gräns. Utan aktiverad kryssruta finns ingen tidsbegränsning på den sidan; om ingen av rutorna är aktiverad begränsas ingen period.</p>
<ul>
<li><b>Från:</b> Från början av den valda UTC-kalenderdagen, inklusive.</li>
<li><b>Till:</b> Hela den valda UTC-kalenderdagen räknas med, fram till precis före början av nästa dag.</li>
</ul>
<p>UTC är koordinerad universell tid. Datumgränserna avser UTC-kalenderdagar, inte kalenderdagar i din lokala tidszon.</p>
<p>Filtreringen använder faktiska systembesök från <code>system_visits</code>. Ett faktiskt besök av den berörda befälhavaren inom perioden krävs. De lagrade uppgifterna <code>first_seen</code> och <code>last_seen</code> ersätter inte ett verkligt besök: det räcker inte att perioden bara ligger mellan ett tidigare första besök och ett senare sista besök.</p>
<p>Perioden filtrerar besök, inte enskilda upptäckts-, BIO-, GEO- eller gruvhändelser. Kända fynduppgifter och utvunna mängder förblir lagrade totalvärden. Från/Till kan användas ensamma eller tillsammans med fritext och gruvfilter.</p>
<p>Om Från ligger efter Till visas ”Från-datumet får inte ligga efter Till-datumet.” Ingen databasfråga startas. Korrigera datumgränserna och tillämpa filtren igen.</p>

<h3>Sökresultat</h3>
<p>Träffar visas i den befintliga resultatlistan under krönikakortet.</p>
<p>Beroende på typ av träff kan system och kropp samt ytterligare information dyka upp.</p>
<p>En träff kan användas för att hitta motsvarande system eller organ som redan är känt och för att öppna den befintliga detaljerade informationen.</p>

<h3>Inga träffar</h3>
<p>Om en giltig filtrering inte hittar några träffar töms kartan och rutterna. Träfflistan töms och döljs, detaljvisningen återställs och ett eventuellt öppet systemdetaljfönster i krönikan stängs.</p>
<p>Gamla resultat förblir inte synliga. Kontrollera då kombinationen av söktext, period och gruvfilter samt vilken befälhavare som används för den aktuella vyn.</p>

<h3>Planetära gruvplatser</h3>
<p>Filtret "Planetära gruvplatser" kan användas för att specifikt söka efter kända kroppar för vilka Elite Dangerous har rapporterat planetariska gruvplatser.</p>
<p>Den underliggande displayen motsvarar den som är känd från Explorer:</p>
<p><b>ABBAU ×N</b></p>
<p>Numret tillhör kroppen själv och är inte relaterat till befälhavaren.</p>

<h3>Åtminstone</h3>
<p>Genom att använda "Åtminstone" kan du ange det minsta antalet planetariska gruvplatser en kropp ska ha.</p>
<p>Exempel:</p>
<p><b>Minst 20</b></p>
<p>visar bara kända kroppar med minst:</p>
<p><b>ABBAU ×20</b></p>
<p>Detta gör det möjligt att specifikt lokalisera särskilt omfattande gruvområden.</p>

<h3>Mina gruvfynd</h3>
<p>Med ”Egna gruvfynd” begränsas sökningen till kroppar på vilka befälhavaren i fråga bevisligen själv har utfört ytbrytning.</p>
<p>Denna information kommer från den personliga gruvans historia och är strikt åtskilda av befälhavaren.</p>
<p>En kropp kan därför ha globala ABBAU ×N-signaler utan att den egna befälhavaren redan har tagit bort något där.</p>

<h3>Handelsvara</h3>
<p>Om "Egna gruvfynd" är aktiverat är valet "Råmaterial" också tillgängligt.</p>
<p>Listan innehåller bara varor som befälhavaren i fråga faktiskt redan har vunnit från ytbrytning.</p>
<p>Detta är inte en teoretisk lista över alla möjliga gruvråvaror.</p>
<p>För FABER38 kan listan till exempel innehålla:</p>
<ul>
<li>Alla</li>
<li>koppar</li>
</ul>
<p>Om ytterligare råvaror faktiskt bryts senare, kommer de automatiskt att visas i ditt personliga urval.</p>

<h3>Riktat sökande efter råvaror</h3>
<p>Till exempel, om "Copper" väljs och sedan "Apply" trycks, kommer historiken endast att visa kroppar på vilka befälhavaren i fråga bevisligen har brutit koppar.</p>
<p>Exempel:</p>
<p><b>Prua Hypai NV-E c28-66 / 2 — ABBAU ×24 — koppar 56 t</b></p>
<p>Det innebär att krönikan kan användas som en personlig platsdatabas: en råvara som redan har bryts kan hittas igen senare.</p>

<h3>Alla råvaror</h3>
<p>Med "Råmaterial: Alla" beaktas alla matchande personliga gruvupptäckter på ytan.</p>
<p>Om flera varor är kända på en kropp kan de visas tillsammans med de kvantiteter de hittills har erhållit.</p>
<p>Exempel:</p>
<p><b>ABBAU ×24 — Helium-3 18 t, koppar 56 t</b></p>
<p>Kvantiteterna är de personliga gruvvärdena för respektive befälhavare, som faktiskt dokumenteras från journalhändelser.</p>
<p>Även med en aktiv period förblir personliga utvunna mängder lagrade totalmängder. <b>Koppar 56 t</b> betyder inte automatiskt <b>56 t under den valda perioden</b>. Perioden kräver ett motsvarande systembesök men begränsar inte den visade utvunna mängden till den perioden.</p>

<h3>Kombinera filter</h3>
<p>Fritext, aktiverade Från-/Till-gränser och gruvfilter kan kombineras. En träff måste uppfylla de inställda villkoren tillsammans.</p>
<p>Till exempel:</p>
<ul>
<li>Planetära gruvplatser aktiva</li>
<li>Minst 20</li>
<li>Egna gruvfynd aktiva</li>
<li>Råvara koppar</li>
</ul>
<p>söker efter kända kroppar med minst 20 planetariska gruvplatser där befälhavaren i fråga redan själv har brutit koppar.</p>
<p>Ytterligare söktext tas också med. Om en period också anges måste den visade befälhavaren faktiskt ha besökt det berörda systemet under perioden; själva kopparutvinningen behöver inte ha skett under den perioden.</p>

<h3>Tillämpa</h3>
<p>”Tillämpa” utför en gemensam filtrering med alla aktuella sök-, period- och gruvfilter:</p>
<ul>
<li>Fritext</li>
<li>Från, om aktiverat</li>
<li>Till, om aktiverat</li>
<li>Planetära gruvplatser</li>
<li>Minsta antal</li>
<li>Mina gruvfynd</li>
<li>Handelsvara, om ”Mina gruvfynd” är aktiverat</li>
</ul>
<p>Enter i fritextfältet utför exakt samma filtrering. Utan fritext och gruvfilter läses den vanliga kartan in för de markerade kartbefälhavarna, vid behov begränsad av Från/Till.</p>

<h3>Återställ</h3>
<p>”Återställ” återställer det gemensamma filterområdet till utgångsläget:</p>
<ul>
<li>Fritexten töms.</li>
<li>Från och Till inaktiveras; datumfälten visar åter dagens datum och är inaktiverade.</li>
<li>Planetära gruvplatser inaktiveras.</li>
<li>Minsta antal sätts till 0.</li>
<li>Mina gruvfynd inaktiveras.</li>
<li>Handelsvara återställs till ”Alla”.</li>
</ul>
<p>Valet av befälhavare behålls. Därefter läses den vanliga krönikan in på nytt för detta karturval; tidigare sökträffar och detaljvisningar återställs.</p>

<h3>Val av befälhavare</h3>
<p>Krönikan kan visa data från olika välkända befälhavare.</p>
<p>Det finns två separata urvalsbegrepp:</p>
<ul>
<li><b>Kartans val av befälhavare:</b> Befälhavarnas kryssrutor avgör vilka befälhavarrutter som visas i den vanliga kartan utan fritext-/gruvsökning. En aktiverad period tas med.</li>
<li><b>Visad befälhavare:</b> Personliga fritext-/gruvsökningar använder den visade befälhavaren (<code>viewed_commander_id</code>), annars den aktiva befälhavaren. Även de personliga handelsvarulistorna följer denna befälhavare.</li>
</ul>
<p>Men personlig information som dina egna gruvfynd och råvarulistor utvärderas alltid separat för den befälhavare som faktiskt visas.</p>
<p>En befälhavare ser inga gruvfyndigheter i sitt råvaruval som uteslutande tillhör en annan befälhavare.</p>

<h3>Alla befälhavare</h3>
<p>Kart-/krönikavisningen kan ta hänsyn till flera befälhavare.</p>
<p>”Alla befälhavare” avser kartans val av befälhavare. Befälhavarnas kryssrutor utökar inte automatiskt personliga fritext-/gruvsökningar till flera befälhavare.</p>
<p>Detta ändrar inte den personliga tilldelningen av befälhavarerelaterade uppgifter. Globala astronomiska egenskaper hos ett system eller kropp förblir delade, personliga fynd förblir separata.</p>

<h3>Sökhjälp / legend</h3>
<p>Ytterligare information om krönikasökningen och innebörden av displayen kan nås via "Sökhjälp / legend".</p>
<p>Ett sökord som du klickar på förs in i sökfältet och körs tillsammans med de period-/gruvfilter som redan är inställda.</p>
<p>Denna kontextrelaterade huvudhjälp kompletterar de korta bruksanvisningar som finns där.</p>

<h3>Tips</h3>
<p>Krönikan är särskilt lämplig för att hitta intressanta platser som upptäckts under en längre resa.</p>
<p>För ytbrytning, till exempel, kan den svara:</p>
<p>"På vilken planet har jag någonsin brutit koppar?"</p>
<p>eller:</p>
<p>"Vilka av mina kända planeter har ett särskilt stort antal gruvplatser?"</p>""",
    ),
 'jump_tip': (
        'Analys',
        """
<h2>Analys</h2>
<p>Analysen använder din personliga utforskningshistorik. Systemanalys bedömer ett angivet procedurgenererat systemnamn; Historiska data behåller den tidigare kodanalysen med historiska träffar och ny utvärdering. Båda ger beslutsstöd, inte garantier för fynd.</p>
<h3>Jämförelseunderlag</h3>
<p>Masskoden ger grunduppskattningen. Region och familj förfinar den försiktigt. Små lokala urval jämnas mot det större dataunderlaget. Lite data innebär osäkerhet, inte ett dåligt omdöme. Otillräckligt undersökta system räknas inte som negativa träffar.</p>
<h3>Potentialindex</h3>
<p>Potentialindex 100 motsvarar ditt personliga historiska genomsnitt av dämpad utforskningspotential. Indexet är inte en procentsannolikhet. Ett enhetligt kartläggningsscenario och dämpade extremvärden möjliggör jämförelse; median och utjämnad potential är uppskattade krediter, inte garanterad inkomst.</p>
<h3>Särskilda fynd</h3>
<p>Det sista systemnumret bedöms inte: Plio Aip KN-B d13-201 tillhör familjen Plio Aip KN-B d13. BIO är informativt och ingår inte i huvudbedömningen. Saknade analyser bevisar inte nollvärden.</p>
<h3>Systemanalys</h3>
<p>Ange ett system och välj Analysera eller tryck på Enter. Använd aktuellt system hämtar namnet från befintlig spelstatus. Analysen räknas om endast på användarens begäran. Jämförelseunderlag och resultat anger nivån; utan lokala jämförelser används överordnad erfarenhet. Datakvaliteten visas separat från rekommendationen.</p>
<p>Historiska träffar per systemkod. Värdena beskriver din hittillsvarande utforskningserfarenhet och är ingen direkt prognos för ett enskilt målsystem. Dataunderlag och tillförlitlighet beskriver hur pålitliga jämförelsedata är, utifrån urvalet och dess fördelning mellan sektorer.</p>
""",
    ),
 'route_planner': ('Ruttplanerare',
                   '<h2>Ruttplanerare</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Förbättrad ruttplanerare: starten följer automatiskt det aktuella systemet tills du anger en manuellt; tömning av fältet återställer automatiken. Skepp och carriers använder exakt validerade ID64-adresser utan att välja liknande namn. ”Unable to find route” förklaras som att ingen rutt hittades; kontrollera mål, räckvidd och ruttinställningar.</p>\n'
                   '<p>Ruttplaneraren stöder planering av längre resor med fartyg eller Fleet '
                   'Carrier. CMDRHelper kan använda extern ruttdata från Spansh och förbereda den '
                   'planerade rutten för vidare användning.</p>\n'
                   '\n'
                   '<h3>Starta och avsluta</h3>\n'
                   '<p>Ett start- och målsystem krävs för ruttberäkning.</p>\n'
                   '<p>I den mån det är möjligt kan CMDRHelper använda befälhavarens nuvarande '
                   'kända system som utgångspunkt. Start och mål bör kontrolleras före '
                   'beräkning.</p>\n'
                   '\n'
                   '<h3>Skicka eller Fleet Carrier</h3>\n'
                   '<p>Ruttplaneraren skiljer mellan resor med ett vanligt fartyg och med en Fleet '
                   'Carrier.</p>\n'
                   '<p>Båda använder olika krav och beräkningsmetoder. Därför måste lämplig '
                   'rutttyp väljas innan du planerar.</p>\n'
                   '\n'
                   '<h3>Fartygsrutt</h3>\n'
                   '<p>För en fartygsrutt beaktas de hoppegenskaper som är kända eller angivna för '
                   'det aktiva fartyget.</p>\n'
                   '<p>Beroende på tillgängliga data kan FSD-data, fartygsdata, massa, bränsle och '
                   'andra hoppparametrar inkluderas i planeringen.</p>\n'
                   '<p>En beräknad rutt är ett planeringshjälp. Ändringar av skeppet eller dess '
                   'massa kan ändra det faktiska hoppavståndet som kan uppnås i spelet.</p>\n'
                   '\n'
                   '<h3>Fleet carrier route</h3>\n'
                   '<p>Fleet Carrier har andra hoppregler än vanliga fartyg.</p>\n'
                   '<p>CMDRHelper använder den utsedda Spansh operatörsplaneringen för motsvarande '
                   'rutter.</p>\n'
                   '<p>Rutten används för att planera hoppsekvensen. Faktisk tritiumförbrukning '
                   'och tillgängligt räckvidd kan också bero på massa och aktuell '
                   'bärarstatus.</p>\n'
                   '\n'
                   '<h3>Spansh</h3>\n'
                   '<p>För själva ruttberäkningen kan CMDRHelper använda den externa tjänsten '
                   'Spansh.</p>\n'
                   '<p>Begäran behandlas i bakgrunden så att gränssnittet förblir funktionsdugligt '
                   'under en längre beräkning.</p>\n'
                   '<p>CMDRHelper har inget inflytande på tillgängligheten eller svarstiden för '
                   'den externa tjänsten.</p>\n'
                   '\n'
                   '<h3>beräkning</h3>\n'
                   '<p>Efter start av en beräkning skickas begäran vidare till den valda '
                   'ruttplaneraren.</p>\n'
                   '<p>Beroende på rutt och tjänst kan beräkningen ta lite tid. Under denna tid '
                   'bör ingen andra identisk beräkning startas i onödan.</p>\n'
                   '\n'
                   '<h3>Resultat</h3>\n'
                   '<p>En framgångsrikt beräknad rutt visar de avsedda systemen eller '
                   'hopppunkterna i deras ordning.</p>\n'
                   '<p>Beroende på rutttyp visas ytterligare information om distans, hopp, bränsle '
                   'eller tritium och annan tillgänglig ruttdata.</p>\n'
                   '\n'
                   '<h3>Rutt och nuvarande befäl</h3>\n'
                   '<p>Det nuvarande systemet och fartyget kan - så länge de är tydligt kända i '
                   'den aktiva AppState - användas för förhandstilldelning eller för att stödja '
                   'planering.</p>\n'
                   '<p>Den faktiska rutten förblir dock en plan och ändrar inte några journal- '
                   'eller befäldata.</p>\n'
                   '\n'
                   '<h3>CTSVision export</h3>\n'
                   '<p>Beräknade transportrutter för flottan kan exporteras som CSV för '
                   'CTSVision.</p>\n'
                   '<p>Detta innebär att en operatörsrutt planerad i CMDRHelper sedan kan användas '
                   'i CTSVision för hoppkontroll eller ruttbearbetning där.</p>\n'
                   '<p>Exporten ändrar inte rutten i CMDRHelper.</p>\n'
                   '\n'
                   '<h3>CSV-fil</h3>\n'
                   '<p>Den exporterade filen innehåller ruttdata som krävs för CTSVision i avsedd '
                   'ordning.</p>\n'
                   '<p>Filen ska inte ändras strukturellt på ett okontrollerat sätt efter export '
                   'om den sedan ska läsas in av CTSVision.</p>\n'
                   '\n'
                   '<h3>Fel och externa tjänster</h3>\n'
                   '<p>Om Spansh inte kan nås eller tjänsten returnerar ett fel, visar CMDRHelper '
                   'ett motsvarande felmeddelande.</p>\n'
                   '<p>Ett fel i online-ruttberäkning ändrar inte lokal befälhavare eller '
                   'journaldata.</p>\n'
                   '\n'
                   '<h3>Ruttplanerare och hopptips</h3>\n'
                   '<p>Hopptips och ruttplanerare fyller olika uppgifter:</p>\n'
                   '<ul>\n'
                   '<li>Jump tip utvärderar möjliga intressanta prospekteringsmål baserat på '
                   'befintlig data.</li>\n'
                   '<li>Ruttplanerare beräknar en specifik rutt mellan start och '
                   'destination.</li>\n'
                   '</ul>\n'
                   '<p>Ett bra hopptips är därför inte automatiskt en del av en optimal rutt.</p>\n'
                   '\n'
                   '<h3>Flera befälhavare</h3>\n'
                   '<p>Om befälhavarerelaterade data som nuvarande system eller fartyg används '
                   'kommer detta från den aktiva live AppState och måste tydligt tilldelas '
                   'dit.</p>\n'
                   '<p>Att bara titta på en annan befälhavare i CMDR-vyn ändrar inte '
                   'ruttplaneraren till deras system eller fartyg.</p>\n'
                   '<p>En ruttberäkning i sig ändrar inte en annan befälhavares '
                   'personuppgifter.</p>\n'
                   '\n'
                   '<h3>Dricks</h3>\n'
                   '<p>Innan en lång resa, kontrollera alltid igen:</p>\n'
                   '<ul>\n'
                   '<li>Startsystem</li>\n'
                   '<li>Målsystem</li>\n'
                   '<li>Rutttyp fartyg/transportör</li>\n'
                   '<li>för fartygsrutter, det underliggande fartyget, FSD och '
                   'hoppparametrar</li>\n'
                   '<li>för transportrutter, den tillgängliga tritiumreserven</li>\n'
                   '</ul>\n'
                   '<p>För transportörsresor är det tillrådligt att även planera tillräckliga '
                   'reserver för återresan eller oplanerade omvägar.</p>'),
 'images': ('Bilder',
            '<h2>Bilder</h2>\n'
            '<p>Avsnittet "Bilder" hanterar skärmbilder tagna med Elite Dangerous. CMDRHelper kan '
            'automatiskt känna igen nya inspelningar, bearbeta dem och lagra dem i ett galleri '
            'baserat på kommandot.</p>\n'
            '\n'
            '<h3>Källmapp</h3>\n'
            '<p>Källmappen är mappen där Elite Dangerous sparar sina skärmbilder i '
            'BMP-format.</p>\n'
            '<p>CMDRHelper kan övervaka denna mapp efter nya BMP-filer. För att automatisk '
            'bearbetning ska fungera måste rätt skärmbildsmapp ställas in.</p>\n'
            '\n'
            '<h3>Destinationsmapp</h3>\n'
            '<p>Målmappen är den gemensamma rotmappen för bilderna som behandlas av '
            'CMDRHelper.</p>\n'
            '<p>Användaren ställer in denna rotmapp. CMDRHelper skapar automatiskt de nödvändiga '
            'befälhavarrelaterade undermapparna under bearbetningen.</p>\n'
            '\n'
            '<h3>Automatisk bearbetning</h3>\n'
            '<p>Om "Konvertera automatiskt" är aktiverat och giltiga käll- och målmappar är '
            'inställda, kontrollerar CMDRHelper regelbundet källmappen efter nya '
            'BMP-skärmdumpar.</p>\n'
            '<p>När de är aktiverade markeras befintliga BMP-filer initialt som kända och '
            'konverteras inte automatiskt utan att bli tillfrågade. Den separata funktionen för '
            'att konvertera befintliga BMP är tillgänglig för detta.</p>\n'
            '<p>En ny fil ställs inte i kö förrän den har samma storlek som inte är noll i två på '
            'varandra följande kontroller. Som ett resultat av detta bearbetas inte en '
            'skrivoperation som fortfarande pågår omedelbart.</p>\n'
            '\n'
            '<h3>Bildkonvertering</h3>\n'
            '<p>Som källa bearbetar CMDRHelper BMP-filer. "PNG" eller "JPG" kan väljas som '
            'målformat.</p>\n'
            '<p>JPG-filer sparas på kvalitetsnivå 95. PNG-filer sparas på ett optimerat sätt.</p>\n'
            '<p>Som standard behålls den ursprungliga BMP-filen. Om "Ta bort BMP efter '
            'konvertering" är aktiverat, kommer käll-BMP bara att raderas efter att målbilden har '
            'sparats.</p>\n'
            '\n'
            '<h3>Gör bilden ljusare</h3>\n'
            '<p>Ljusstyrkan justeras från 0 till 50 procent med hjälp av ett skjutreglage och ett '
            'länkat nummerfält. Inställningen sparas.</p>\n'
            '<p>Den tillämpas automatiskt under varje konvertering som påbörjas därefter - både '
            'för nyligen övervakade och manuellt initierade befintliga BMP-filer. 0 procent tar '
            'över den ursprungliga ljusstyrkan; högre värden ökar ljusstyrkan för den genererade '
            'PNG- eller JPG-bilden i enlighet därmed.</p>\n'
            '<p>Funktionen är inte en ren förhandsgranskning och tillämpas inte på en bild som '
            'valts i galleriet. Den ändrade ljusstyrkan sparas i den nya målfilen.</p>\n'
            '<p>Käll-BMP förblir oförändrad om inte radering av BMP-filen också aktiveras. '
            'Journal, befälhavare och prospekteringsdata ändras inte.</p>\n'
            '\n'
            '<h3>Commander-relaterad lagring</h3>\n'
            '<p>Nya skärmdumpar tilldelas den faktiska spelande Commander baserat på '
            'journalidentiteten som finns i den aktiva live AppState.</p>\n'
            '<p>Mappstrukturen innehåller befälhavarens namn och Frontier ID, till exempel:</p>\n'
            '<p><b>FABER38_F12520967/</b></p>\n'
            '<p>FID håller uppgiften tydlig även med flera befälhavare. Detta gör att två '
            'befälhavare med samma namn kan särskiljas.</p>\n'
            '\n'
            '<h3>filnamn</h3>\n'
            '<p>Nya bearbetade bilder får ett namn med tidpunkten för fångst, befälhavarens namn '
            'och - om tillgängligt - det stjärnsystem som är känt vid köning.</p>\n'
            '<p>Exempel:</p>\n'
            '<p><b>2026-09-04_13-18-22_FABER38_Prua-Hypai-RB-D-c29-71.png</b></p>\n'
            '<p>FID finns i det befälhavarerelaterade mappnamnet, inte igen i bildfilens '
            'namn.</p>\n'
            '\n'
            '<h3>Säkra filnamn</h3>\n'
            '<p>CMDRHelper rensar kommando- och systemnamn för användning som fil- och '
            'mappkomponenter.</p>\n'
            '<p>Olaglig kontroll och Windows-tecken ersätts, blanksteg förenas, problematiska '
            'punkter eller efterföljande mellanslag tas bort och reserverade Windows-namn som CON '
            'eller NUL säkras.</p>\n'
            '\n'
            '<h3>Inspelningstid</h3>\n'
            '<p>För namngivning använder CMDRHelper modifieringstiden för den stabila igenkända '
            'BMP-filen. Endast om detta inte går att läsa kommer den aktuella tiden att '
            'användas.</p>\n'
            '<p>Det betyder att namnet vanligtvis beror på källfilen och inte på den efterföljande '
            'konverteringstiden.</p>\n'
            '\n'
            '<h3>Flera bilder på samma sekund</h3>\n'
            '<p>Om det avsedda filnamnet redan finns eller är reserverat för en pågående '
            'konvertering, lägger CMDRHelper till det '
            'kontinuerligt<code>_2</code>,<code>_3</code>,<code>_4</code>och så vidare.</p>\n'
            '<p>Detta innebär att en annan skärmdump med samma tidsstämpel inte kommer att skriva '
            'över en befintlig målbild.</p>\n'
            '\n'
            '<h3>Befälhavarebyte under bearbetning</h3>\n'
            '<p>Commander, FID och systemet fångas tillsammans när en skärmdump köar.</p>\n'
            '<p>Ett senare byte av befäl ändrar inte tilldelningen av denna redan väntande bild. '
            'Detta innebär att en skärmdump av FABER38 inte skrivs till mappen för en annan '
            'befälhavare.</p>\n'
            '\n'
            '<h3>galleri</h3>\n'
            '<p>Galleriet visar PNG-, JPG- och JPEG-filer från de kataloger som är kopplade till '
            'det valda filtret. Nya, raderade eller flyttade bilder upptäcks regelbundet.</p>\n'
            '<p>Gallerifiltret ändrar inte lagringsplatsen eller kommandots tilldelning av '
            'filerna.</p>\n'
            '\n'
            '<h3>Nuvarande befälhavare</h3>\n'
            '<p>Filtret Current Commander visar bilder från mappen för kommandon som för '
            'närvarande visas i CMDR-vyn.</p>\n'
            '<p>Befälhavaren i fråga bestämmer endast gallerivisningen. Å andra sidan använder du '
            'den aktiva journalidentiteten när du ställer i kö när du tilldelar en ny '
            'live-skärmdump.</p>\n'
            '\n'
            '<h3>Alla befälhavare</h3>\n'
            '<p>Filtret "Alla befälhavare" visar bilderna från de giltiga undermapparna för alla '
            'kända befälhavare tillsammans. Den speciella mappen för inspelningar utan erkänd '
            'identitet beaktas också.</p>\n'
            '<p>Filerna flyttas eller sammanfogas inte.</p>\n'
            '\n'
            '<h3>Ej tilldelad</h3>\n'
            '<p>Filtret Otilldelad visar bildfiler som stöds direkt i den delade '
            'målrotmappen.</p>\n'
            '<p>I synnerhet förblir äldre bilder utan befälhavarerelaterade undermappar synliga. '
            'CMDRHelper försöker inte gissa sin tillhörighet i efterhand.</p>\n'
            '\n'
            '<h3>Befintliga bilder</h3>\n'
            '<p>Bilder som redan finns i rotmappen flyttas inte automatiskt eller byter namn.</p>\n'
            '<p>De förblir tillgängliga via "Unassigned" så länge de är tillgängliga som PNG, JPG '
            'eller JPEG.</p>\n'
            '\n'
            '<h3>Välj och visa bild</h3>\n'
            '<p>Ett enkelt klick på en förhandsgranskningsbild visar bilden skalad i '
            'förhandsgranskningsområdet och visar dess filnamn.</p>\n'
            '<p>Ett dubbelklick öppnar filen med operativsystemsapplikationen inställd för '
            'bilder.</p>\n'
            '<p>Flera bilder kan markeras samtidigt. När du ändrar fönsterstorleken skalas '
            'förhandsgranskningen av den aktuella bilden så att den passar.</p>\n'
            '\n'
            '<h3>Ta bort bild</h3>\n'
            '<p>Markerade bilder kan raderas med "Radera markerade" eller Delete-tangenten. Innan '
            'du raderar visas en säkerhetsfråga; Utan ett urval påpekas först det nödvändiga '
            'urvalet.</p>\n'
            '<p>Endast de valda PNG/JPG/JPEG-målfilerna tas bort från katalogerna för det aktuella '
            'gallerifiltret. Den ursprungliga BMP-källfilen påverkas inte.</p>\n'
            '\n'
            '<h3>Öppna målmappen</h3>\n'
            '<p>"Öppna målmapp" öppnar lagringsplatsen i filhanteraren och skapar den delade '
            'rotmappen vid behov.</p>\n'
            '<p>Filtret "Current Commander" öppnar sin befintliga Commander-undermapp. Om det inte '
            'finns ännu eller om ett annat filter är aktivt kommer den delade rotmappen att '
            'öppnas.</p>\n'
            '\n'
            '<h3>Säkerhet för bildvägar</h3>\n'
            '<p>Innan du raderar, kontrollerar CMDRHelper den kanoniska sökvägen för varje fil. '
            'Den måste finnas i den konfigurerade målmappen och direkt i en katalog som tillåts av '
            'det aktuella gallerifiltret.</p>\n'
            '<p>Symboliska länkar används inte som kommandomappar eller galleribilder och tas inte '
            'bort via galleriet. Banor utanför målområdet och genomfartsvägar avvisas.</p>\n'
            '\n'
            '<h3>Om ingen befälhavare upptäcktes</h3>\n'
            '<p>Om Commander och FID saknas när en ny inspelning köas, kommer filen inte att '
            'parkeras och kommer inte att tilldelas en känd Commander.</p>\n'
            '<p>Det kommer att finnas i undermappen<b>UNKNOWN_UNKNOWN/</b>bearbetade; filnamnet '
            'används också för Commander<b>OKÄND</b>. Den här mappen kan visas via Alla '
            'befälhavare, inte genom filtret för icke-allokerad rotmapp.</p>\n'
            '\n'
            '<h3>Flera befälhavare</h3>\n'
            '<p>Två separata regler gäller för bildhantering:</p>\n'
            '<ul>\n'
            '<li><b>Spara nya bilder:</b>Den aktiva journalidentiteten med Commander och FID i kö '
            'bestämmer målmappen.</li>\n'
            '<li><b>Visa bilder:</b>Den befälhavare som visas eller det valda gallerifiltret '
            'bestämmer vilka bilder som visas.</li>\n'
            '</ul>\n'
            '<p>Detta innebär att en annan befälhavares galleri kan ses medan FABER38 spelas utan '
            'att nya skärmdumpar hamnar i mappen hos befälhavaren i fråga.</p>\n'
            '\n'
            '<h3>Dricks</h3>\n'
            '<p>Det räcker med en delad skärmbildsrotmapp. CMDRHelper separerar automatiskt '
            'nybearbetade bilder i Commander och FID.</p>\n'
            '<p>Med "Current Commander", "All Commanders" och "Unassigned" kan du växla mellan '
            'personligt galleri, undermappar för alla kommandon och äldre bilder i rotmappen.</p>\n'
            '<p>Högre ljusstyrka kan hjälpa till med mörka foton; det påverkar den nyskapade '
            'målbilden under konverteringen.</p>'),
 'commander_view': ('CMDR-vy',
                    '<h2>CMDR-vy</h2>\n'
                    '<p>CMDR-vyn sammanfattar en befälhavares permanent lagrade personliga '
                    'information.</p>\n'
                    '<p>Det låter dig också växla mellan de kända befälhavarna för CMDRHelper och '
                    'se deras egna data. Personlig information separeras med Frontier ID '
                    '(FID).</p>\n'
                    '\n'
                    '<h3>Välj Commander</h3>\n'
                    '<p>Om flera befäl är kända kan du använda valet ovan för att avgöra vems '
                    'sparade information som visas. Denna befälhavare är den betraktade '
                    'befälhavaren.</p>\n'
                    '<p>Displayen markerar den som antingen "Live Active" eller "View Only".</p>\n'
                    '\n'
                    '<h3>Anses som Commander och Live Commander</h3>\n'
                    '<p>Att välja en annan befälhavare i CMDR-vyn gör den inte till den aktiva '
                    'journalbefälhavaren.</p>\n'
                    '<p>Den levande befälhavaren bestäms uteslutande från den för närvarande unikt '
                    'identifierade Elite Dangerous journalsessionen. På så sätt kan historiken för '
                    'en annan befälhavare ses medan Elite Dangerous fortsätter att köra med '
                    'FABER38.</p>\n'
                    '\n'
                    '<h3>Frontier ID (FID)</h3>\n'
                    '<p>FID är den stabila Frontier-identifieraren för en befälhavare.</p>\n'
                    '<p>CMDRHelper använder det och det interna befäl-ID:t som lösts från det för '
                    'att separera personuppgifter på ett säkert sätt. Befälhavare med liknande '
                    'eller identiska namn förblir också åtskilda.</p>\n'
                    '\n'
                    '<h3>Översikt</h3>\n'
                    '<p>Fliken "Översikt" visar endast permanent sparad information för '
                    'befälhavaren i fråga:</p>\n'
                    '<ul>\n'
                    '<li>Befälhavarens namn, FID och status "Live active" eller "View only"</li>\n'
                    '<li>första och sista kända tidpunkten</li>\n'
                    '<li>Antal besökta system, bio- och geo-upptäckter, codex-poster och '
                    'kartografiförsäljning</li>\n'
                    '<li>Senast kända plats och antal öppna uppdrag</li>\n'
                    '<li>nuvarande eller sista fartyget</li>\n'
                    '<li>Fleet Carrier och transportörens plats</li>\n'
                    '<li>Tillgångar</li>\n'
                    '<li>öppna biodata och öppna kartografiska data inklusive befintliga '
                    'uppskattningar</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Tillgångar/krediter</h3>\n'
                    '<p>Fältet "Tillgångar" visar det senast sparade saldot för befälhavaren i '
                    'fråga från en lämplig journalhändelse, formaterad som t.ex.<b>1 234 567 '
                    'kr</b>.</p>\n'
                    '<p>CMDRHelper lägger inte till fiktiva inkomster eller utgifter om det inte '
                    'finns någon ny, säker journalstatus.</p>\n'
                    '\n'
                    '<h3>legosoldatmynt</h3>\n'
                    '<p>Legosoldatmynten kommer från MercCoins-fälten som tillhandahålls av Elite '
                    'Dangerous<code>Statistics → Bank_Account</code>och sparas '
                    'commander-relaterade som en Frontier ögonblicksbild.</p>\n'
                    '<p>Synliga är:</p>\n'
                    '<ul>\n'
                    '<li>Nuvarande</li>\n'
                    '<li>Totalt spenderat</li>\n'
                    '<li>Teknik</li>\n'
                    '<li>utrustning</li>\n'
                    '<li>Rapporterad av Frontier: tjänat totalt</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Aktuell och upplagor</h3>\n'
                    '<p>"Aktuell" visar<code>MercCoins_Current</code>. "Total Spent" tar '
                    'över<code>MercCoins_Total_Spent</code>.</p>\n'
                    '<p>"Engineering" och "Equipment" visar andelarna som rapporteras separat av '
                    'Frontier<code>MercCoins_Spent_On_Engineering</code>och<code>MercCoins_Spent_On_MercGear</code>.</p>\n'
                    '<p>För FABER38, till exempel, en aktuell inventering av<b>1 275</b>, '
                    'totalt<b>220</b>spenderat och borta<b>220</b>anmäld för ingenjörsarbete.</p>\n'
                    '\n'
                    '<h3>Överlag välförtjänt</h3>\n'
                    '<p>"Rapporterat av Frontier: tjänat totalt" '
                    'visar<code>MercCoins_Total_Earned</code>. CMDRHelper beräknar inte sin egen '
                    'balansräkning utifrån detta.</p>\n'
                    '<p>Frontier:s ackumulerade värde behöver inte matematiskt matcha det aktuella '
                    'lagret och de rapporterade kostnaderna. Till exempel kan 1 275 aktuella, 25 '
                    'totala intjänade och 220 totala spenderade rapporteras samtidigt.</p>\n'
                    '<p>CMDRHelper korrigerar inte dessa värden, men visar de individuella '
                    'Frontier-räknarna oförändrade.</p>\n'
                    '\n'
                    '<h3>Varför inte ha en egen MercCoins balansräkning?</h3>\n'
                    '<p>Elite Dangerous tillhandahåller inte en unik journalpost för varje enskilt '
                    'mottagande eller utgift av legosoldatmynt. MercCoins visas som summor i '
                    'Statistics.</p>\n'
                    '<p>En självberäknad bokningshistorik skulle därför inte vara tillförlitlig. '
                    'CMDRHelper sparar den senaste kända Frontier ögonblicksbilden istället.</p>\n'
                    '\n'
                    '<h3>Uppdrag</h3>\n'
                    '<p>Fliken "Uppdrag" visar de sparade uppdragen för befälhavaren i fråga som '
                    'en tabell med status, uppdragsnamn, mål, utgångstid och belöning.</p>\n'
                    '\n'
                    '<h3>utforskning</h3>\n'
                    '<p>Fliken Utforskning visar öppna biodata, öppna kartografidata, biologiska '
                    'upptäckter, första fotfall, självkarterade och effektivt kartlagda kroppar '
                    'och antalet besökta system.</p>\n'
                    '<p>Den dedikerade "Chronicle"-fliken i CMDR-vyn är för närvarande fortfarande '
                    'en platshållare. Hela krönikan finns i huvudmenyn med samma namn.</p>\n'
                    '\n'
                    '<h3>Fartyg/flotta</h3>\n'
                    '<p>Fliken "Fartyg" visar initialt det aktiva eller senast använda fartyget '
                    'med fartygsnamn, fartygstyp, plats och ShipID.</p>\n'
                    '<p>Befälhavarens sparade skepp visas under dem som utbyggbara kort. De kan '
                    'sorteras stigande eller fallande efter:</p>\n'
                    '<ul>\n'
                    '<li>senast eller för närvarande använd</li>\n'
                    '<li>Fartygsnamn eller fartygstyp</li>\n'
                    '<li>maximalt hoppområde</li>\n'
                    '<li>Lastkapacitet eller tom massa</li>\n'
                    '<li>senast kända plats eller tid</li>\n'
                    '</ul>\n'
                    '<p>Du kan också filtrera för alla fartyg, fartyg med en fordonshangar eller '
                    'fartyg med en stridshangar.</p>\n'
                    '\n'
                    '<h3>Fartygsdetaljer</h3>\n'
                    '<p>En öppnad fartygskarta visar - om den sparas - fartygs-ID, ShipID, plats, '
                    'senaste tid, maximalt hoppområde, FSD och Guardian booster, massa, last- och '
                    'tankkapaciteter samt lastningstid och status.</p>\n'
                    '<p>Om moduldata finns tillgänglig sammanfattas även fordons- och '
                    'jaktplanshangar, sköldgenerator och sköldförstärkare, '
                    'Guardian-sköldförstärkningar, vapen, skrov- och modulförstärkningar samt '
                    'passagerarhytter.</p>\n'
                    '<p>Laddningsstatusen kan vara komplett, ofullständig eller inaktuell. Saknad '
                    'information visas som "–" och är inte påhittad.</p>\n'
                    '\n'
                    '<h3>Fleet Carrier</h3>\n'
                    '<p>För en sparad anpassad Fleet Carrier visar vyn operatörens namn, '
                    'anropssignal, operatörs-ID, senaste plats och tidpunkten för den senaste '
                    'uppdateringen.</p>\n'
                    '\n'
                    '<h3>Ihållande befälhavarstat</h3>\n'
                    '<p>Viktig befälhavarinformation förblir permanent sparad. Detta gör att kända '
                    'värden kan visas igen efter en omstart av CMDRHelper eller Elite Dangerous '
                    'utan att fullständigt utvärdera varje journal igen.</p>\n'
                    '<p>Nya unika journalhändelser uppdaterar det sparade tillståndet.</p>\n'
                    '\n'
                    '<h3>Historisk rekonstruktion</h3>\n'
                    '<p>För funktioner som läggs till senare kan CMDRHelper söka i befintliga '
                    'journalområden som tydligt är tilldelade en befälhavare en gång efter '
                    'information som redan är känd.</p>\n'
                    '<p>Till exempel kan äldre MercCoins ögonblicksbilder användas. Upprepade '
                    'kontroller är inte avsedda att producera dubbletter av data och ändrar inte '
                    'normala journalläsningspositioner.</p>\n'
                    '\n'
                    '<h3>Flera befälhavare</h3>\n'
                    '<p>I synnerhet förblir följande separata när det gäller befälhavare:</p>\n'
                    '<ul>\n'
                    '<li>Tillgångar och uppdrag</li>\n'
                    '<li>egen kartografi och ekologiska fynd</li>\n'
                    '<li>Surface mining historia och legosoldater mynt</li>\n'
                    '<li>Online-referenser</li>\n'
                    '<li>befälhavarerelaterade skärmdumpar</li>\n'
                    '</ul>\n'
                    '<p>Globala astronomiska egenskaper hos ett system eller en kropp kan dock '
                    'användas tillsammans.</p>\n'
                    '\n'
                    '<h3>Inverkan på andra åsikter</h3>\n'
                    '<p>Genom att ändra befälhavaren i fråga uppdateras själva CMDR-vyn, valet av '
                    'personligt gruvråmaterial i krönikan och, med lämpligt filter, '
                    'skärmbildsgalleriet.</p>\n'
                    '<p>Den ersätter inte den faktiska befälhavaren för journalbearbetning eller '
                    'onlineuppladdningar.</p>\n'
                    '\n'
                    '<h3>Inara och EDSM</h3>\n'
                    '<p>Inara- och EDSM-åtkomster hanteras separat per befälhavare respektive '
                    'FID.</p>\n'
                    '<p>Att bara titta på en befälhavare startar inte en överföring med deras '
                    'API-Key. Endast den aktiva tidskriften FID är relevant för '
                    'liveuppladdningar.</p>\n'
                    '<p>Åtkomstdata hanteras under "Inställningar" i området för '
                    'onlinetjänster.</p>\n'
                    '\n'
                    '<h3>Dricks</h3>\n'
                    '<p>Använd CMDR-vyn om du vill se sparad personlig information för en specifik '
                    'befälhavare.</p>\n'
                    '<p><b>CMDR-vy = Vem vill jag se?</b></p>\n'
                    '<p><b>Active Journal-FID = Vem spelar egentligen just nu?</b></p>\n'
                    '<p>Denna separation förhindrar att personlig data eller onlineuppladdningar '
                    'från olika befälhavare blandas ihop.</p>'),
 'settings': ('Inställningar',
              '<h2>Inställningar</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Bättre uppdateringsinformation: Ja/Nej-fönstret visar installerad och tillgänglig version samt upp till sex nyheter när en sammanfattning finns. Långa listor kan rullas och åtgärderna förblir tillgängliga. Vyn följer med v3.2; en oförändrad v3.1-klient visar den ännu inte.</p>\n'
              '<p>Området "Inställningar" avgör hur CMDRHelper fungerar med Elite Dangerous, '
              'journalfiler, databas, onlinetjänster, gränssnitt och uppdateringar.</p>\n'
              '<p>Ändringar av referenser och sökvägar bör göras noggrant. Commander-relaterade '
              'inställningar hanteras separat av Frontier ID vid behov.</p>\n'
              '\n'
              '<h3>tidning</h3>\n'
              '<p>Journalmappen är en av de viktigaste inställningarna. Den måste peka på mappen '
              'där Elite Dangerous<code>Journal*.logg</code>filer för den Windows- eller '
              'Proton-profil som används.</p>\n'
              '<p>Tidskrifterna ger bland annat:</p>\n'
              '<ul>\n'
              '<li>Befälhavarens identitet, plats och resor</li>\n'
              '<li>Uppdrag, fartyg och tillgångar</li>\n'
              '<li>Utforskning, kartografi och BIO-data</li>\n'
              '<li>Ytbrytning, legosoldatsmynt och andra stater som stöds</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Journalvisning och drift</h3>\n'
              '<p>Journalgruppen visar mappuppsättningen, antalet hittade tidskrifter, äldsta och '
              'senaste tidskrifter, namnet på den senaste filen och tidpunkten för den senast '
              'lästa posten.</p>\n'
              '<p>"Välj journalmapp" ändrar mappen. "Läs nu" utlöser den normala uppdateringen '
              'omedelbart.</p>\n'
              '<p>Tydligt identifierbara sessioner tilldelas med FID. Nya kompletta poster '
              'bearbetas stegvis; Säkra läspositioner förhindrar att varje journal läses om i sin '
              'helhet i onödan nästa gång den startas.</p>\n'
              '\n'
              '<h3>databas</h3>\n'
              '<p>CMDRHelper lagrar nödvändig data permanent i en lokal SQLite-databas. Detta '
              'inkluderar globala system- och kroppsdata samt information som uttryckligen '
              'tilldelats en befälhavare.</p>\n'
              '<p>Inställningssidan visar statistik om sparad data. Databasen ska inte redigeras '
              'manuellt medan CMDRHelper körs.</p>\n'
              '\n'
              '<h3>Importera journalarkiv</h3>\n'
              '<p>"Importera journalarkiv" jämför fullständigt journalfilerna i den inställda '
              'journalmappen med databasen. Redan kända journalområden beaktas baserat på den '
              'sparade importinformationen och dupliceras inte blint som ny data.</p>\n'
              '<p>Under en manuellt synlig import visas förloppet, numret och den för närvarande '
              'bearbetade filen. Efter slutförandet rapporterar CMDRHelper importerade eller redan '
              'kända data eller ett fel.</p>\n'
              '<p>Arkivimporten tjänar också till att återlära stödd historisk information från '
              'tydligt tilldelade tidskrifter.</p>\n'
              '\n'
              '<h3>Befälhavarerelaterade data</h3>\n'
              '<p>CMDRHelper separerar personlig information baserat på FID och tillhörande '
              'interna Commander ID. Dessa inkluderar, men är inte begränsade till, uppdrag, '
              'tillgångar, MercCoins, personlig utforskning och onlineåtkomst.</p>\n'
              '<p>En okänd eller tvetydig journalsession får inte godtyckligt tilldelas en '
              'befälhavare.</p>\n'
              '\n'
              '<h3>Onlinetjänster</h3>\n'
              '<p>CMDRHelper stöder EDSM och Inara. Båda åtkomsterna bearbetas och sparas separat '
              'för varje känd befälhavare eller varje FID.</p>\n'
              '<p>Valet i inställningarna avgör bara vems åtkomst som för närvarande redigeras '
              'eller testas. Endast befälhavaren tydligt identifierad av den aktiva '
              'journalsessionen får skicka live.</p>\n'
              '\n'
              '<h3>EDSM åtkomst för</h3>\n'
              '<p>"EDSM åtkomst för:" väljer kommandot som ska redigeras. Valet kommer att visa '
              '"set up" eller "not set up" beroende på om en API-Key är lagrad.</p>\n'
              '<p>Synliga är befälhavarens namn, dolt API-Key-fält, "Använd EDSM", ett '
              'anslutningstest och dess senaste teststatus.</p>\n'
              '<p>Varje befälhavare behöver sin egen lämpliga EDSM-åtkomst. Valet byter inte '
              'direktuppladdningsprogrammet till den här kommandon.</p>\n'
              '\n'
              '<h3>Använd och testa EDSM</h3>\n'
              '<p>"Använd EDSM" aktiverar eller inaktiverar tjänsten för den valda FID. Saknade '
              'eller inaktiverade autentiseringsuppgifter påverkar inte lokal '
              'journalbehandling.</p>\n'
              '<p>"Testa EDSM-anslutning" kontrollerar åtkomstdata som för närvarande är synliga i '
              'formuläret. Ett lyckat test bekräftar anslutningen, men ändrar inte den aktiva '
              'journalen FID eller live commander.</p>\n'
              '\n'
              '<h3>Inara åtkomst för</h3>\n'
              '<p>"Inara Access for:" följer samma multi-CMDR-princip. Aktivering, '
              'Inara-kommandantnamn och API-Key sparas separat för varje FID.</p>\n'
              '<p>Även här visar valet "inställt" eller "ej inställt". En nyckel från en '
              'befälhavare används inte automatiskt för en annan befälhavare.</p>\n'
              '\n'
              '<h3>Använd och testa Inara</h3>\n'
              '<p>Med Inara inställd och aktiverad för den aktiva journalen FID, kan CMDRHelper '
              'överföra de resor, plats, uppdrag och fartygshändelser som stöds. Alla '
              'journalhändelser skickas inte till Inara.</p>\n'
              '<p>"Testa Inara-anslutning" kontrollerar de för närvarande synliga åtkomstdata utan '
              'att ändra live-kommandot.</p>\n'
              '\n'
              '<h3>Inara utkorg</h3>\n'
              '<p>Inara-händelser som stöds flaggas ständigt i en utkorg innan '
              'nätverksöverföring.</p>\n'
              '<p>Tillfälliga fel gör att dessa poster kan bevaras för senare försök. Arbetaren '
              'bearbetar endast utkorgen för den unikt aktiva journalen FID; Anmälningar från '
              'andra befäl är inte inkluderade.</p>\n'
              '\n'
              '<h3>Onlinestatus i rubriken</h3>\n'
              '<p>EDSM visar för närvarande:</p>\n'
              '<ul>\n'
              '<li><b>EDSM</b>– kan inte användas eller avaktiveras för den aktiva FID</li>\n'
              '<li><b>EDSM väntar</b>– ställ in och utan pågående överföring</li>\n'
              '<li><b>EDSM transmission</b>– den senaste EDSM-bearbetningskörningen avslutades '
              'utan fel; Verktygstipset anger om händelser har skickats, journaldata bearbetats '
              'eller ingen ny data hittades</li>\n'
              '<li><b>EDSM-fel</b>– den senaste överföringsstatusen är felaktig</li>\n'
              '</ul>\n'
              '<p>Det finns för närvarande ingen ytterligare, separat märkt tillstånd "EDSM aktiv" '
              'för EDSM.</p>\n'
              '<p>Inara särskiljer mer exakt:</p>\n'
              '<ul>\n'
              '<li><b>INARA ute</b>– inaktiverad för den aktiva journalen FID</li>\n'
              '<li><b>INARA redo</b>– inställd, men fortfarande utan bekräftad överföring i denna '
              'session</li>\n'
              '<li><b>INARA transmission</b>– arbetaren skickar för närvarande</li>\n'
              '<li><b>INARA aktiv</b>– den senaste faktiska överföringen har bekräftats</li>\n'
              '<li><b>INARA-fel</b>– det senaste överföringsförsöket misslyckades</li>\n'
              '</ul>\n'
              '\n'
              '<h3>API-Key säkerhet</h3>\n'
              '<p>API-Key är personliga referenser. Inmatningsfälten är dolda; De lagras i '
              'applikationsinställningarna och inte i CMDRHelper-databasen.</p>\n'
              '<p>Nycklar ska inte publiceras, delas i skärmdumpar eller läggas till offentliga '
              'arkiv.</p>\n'
              '\n'
              '<h3>Bilder/skärmdumpar</h3>\n'
              '<p>Källmapp, Destinationsmapp, PNG/JPG, Automatisk bearbetning, BMP-radering och '
              'Ljusning från 0 till 50 procent finns uteslutande i huvudmenyn för bilder, inte på '
              'sidan Inställningar.</p>\n'
              '<p>Den kontextkänsliga hjälpen "Bilder" beskriver dessa alternativ i detalj.</p>\n'
              '\n'
              '<h3>yta</h3>\n'
              '<p>Gränssnittsgruppen inkluderar utseende, språk, teckensnitt, teckenstorlek och '
              'värdetröskel för värdefulla utforskarkroppar.</p>\n'
              '\n'
              '<h3>Mörkt och ljust läge</h3>\n'
              '<p>Du kan växla direkt mellan mörkt och ljust utseende. Temat appliceras omedelbart '
              'på gränssnittet och befintliga system- och historikkort och sparas.</p>\n'
              '\n'
              '<h3>Språk</h3>\n'
              '<p>Gränssnittet erbjuder tolv språk att välja mellan. "Spara språk" sparar valet; '
              'En omstart av CMDRHelper krävs då för en helt enhetlig konvertering av befintliga '
              'widgets.</p>\n'
              '\n'
              '<h3>Teckensnitt och teckenstorlek</h3>\n'
              '<p>Teckensnittsfamilj och teckenstorlek från 7 till 24 pt kan väljas och '
              'sparas.</p>\n'
              '<p>Båda ändringarna träder i kraft först efter en omstart. Gränssnittet indikerar '
              'detta uttryckligen.</p>\n'
              '\n'
              '<h3>Värdetröskel</h3>\n'
              '<p>Utforskarens värdetröskel bestämmer det uppskattade kreditvärdet från vilket '
              'organ lyfts fram som särskilt värdefulla. Ändringen sparas omedelbart och '
              'uppdaterar motsvarande Explorer-display.</p>\n'
              '\n'
              '<h3>Göm automatiskt</h3>\n'
              '<p>"Precious Bodies" och "BIO-fynd" är stadigt placerade i det vänstra sidofältet, '
              'inte på sidan Inställningar.</p>\n'
              '<p>Omkopplarna sparas och styr de små live-tipsfönster som stöds under utforskning. '
              'Värdetröskeln för värdefulla kroppar ställs in i gränssnittsinställningarna.</p>\n'
              '\n'
              '<p>Cargo-fönstret använder uteslutande det Cargo-snapshot som bekräftats för den aktiva Journal-FID:n. Commandern som visas i CMDR View och viewed_commander_id påverkar inte detta live-fönster. För ett Ship visas lastat / maximum · ledigt; om CargoCapacity är okänd uppskattas inget värde.</p>\n'
              '<p>”EDSM-status-HUD” under ”visa automatiskt” är AV som standard. Efter ankomst till ett system visas ett kort meddelande över Elite i cirka 2,5 sekunder. Flera Location-händelser under samma vistelse ger inga dubbla meddelanden; en verklig återkomst får kontrolleras igen.</p>\n<p>”EDSM: KÄNT” betyder en giltig EDSM-träff för systemet. ”EDSM: OKÄNT” betyder ett giltigt EDSM-svar utan systemträff. ”EDSM: INGET SVAR” betyder nätverksfel, HTTP-fel, timeout eller ogiltigt svar, aldrig en bekräftad avsaknad av träff. Kännedom i EDSM är inte samma sak som officiell upptäckt i Elite; namn på första upptäckare eller rapportör utlovas inte.</p>\n<p>Meddelandet fungerar oberoende av navigations- och last-HUD. Permanenta HUD-visningar och snabbfavoritmeddelanden bevaras. Förfrågan blockerar inte gränssnittet; sena svar för redan lämnade system förkastas.</p>\n\n'
              '<h3>Uppdateringar</h3>\n'
              '<p>Uppdateringsgruppen visar installerad version och GitHub-status. Check Now söker '
              'manuellt efter en ny schemalagd CMDRHelper-version; Dessutom sker en fördröjd '
              'automatisk kontroll efter start.</p>\n'
              '<p>Om en ny version är tillgänglig kommer CMDRHelper att fråga innan du laddar ner '
              'och installerar. En meddelad databasuppdatering visas separat i denna dialog.</p>\n'
              '<p>För befintliga installationer räcker normalt: installera uppdateringen → starta CMDRHelper. Nödvändiga historiska rättelser av BIO-data, besök och DSS-metadata körs automatiskt; databasen säkerhetskopieras före reparationer som skriver data. Reparationerna är versionsstyrda och idempotenta: lyckade revisioner körs inte om fullständigt vid varje start. Rekonstruktion kräver Elite-journaler som finns kvar, är läsbara och entydigt kan kopplas till en commander. Saknade källor hittas inte på eller räknas som framgång; öppna reparationer provas igen vid nästa start. Databasradering, manuella skript och ny import behövs normalt inte.</p>\n\n'
              '<h3>Nedladdningsförlopp</h3>\n'
              '<p>Nedladdningen körs i bakgrunden. Om den totala storleken är känd visar '
              'CMDRHelper filnamn, mottagen och total MiB, procent, överföringshastighet och '
              'beräknad återstående tid.</p>\n'
              '<p>Utan en känd total storlek fungerar förloppsindikatorn i upptaget läge och '
              'fortsätter att visa mängden mottagen data och - om det går att fastställa - '
              'hastigheten. Före installationen kontrolleras den nedladdade ZIP-filen.</p>\n'
              '\n'
              '<h3>Avbryt uppdatering</h3>\n'
              '<p>"Avbryt nedladdning" avslutar en pågående nedladdning på ett kontrollerat sätt. '
              'En avbruten, ofullständig eller ogiltig nedladdning kommer inte att '
              'installeras.</p>\n'
              '\n'
              '<h3>Uppdatera på Windows</h3>\n'
              '<p>På Windows fortsätter den faktiska uppdateringsprocessen oavsett den '
              'ursprungliga startkonsolen. En konsolavstängning bör därför inte oavsiktligt '
              'avsluta den.</p>\n'
              '<p>Om ett fel uppstår efter att filändringar har börjat, försöker den befintliga '
              'säkerhetskopieringen att återställa den tidigare versionen.</p>\n'
              '\n'
              '<h3>Starta om efter uppdatering</h3>\n'
              '<p>Efter lyckad installation startar uppdateringsprogrammet CMDRHelper om via den '
              'avsedda startvägen och kontrollerar kort om den nya processen körs stabilt.</p>\n'
              '<p>Om en release kräver en engångsuppdatering av databasen kommer journalarkivet '
              'också att omvärderas efter omstarten.</p>\n'
              '\n'
              '<h3>Flera befälhavare</h3>\n'
              '<p><b>Val av inställningar = Vems onlineåtkomst redigerar jag?</b></p>\n'
              '<p><b>Active Journal-FID = Vem får sända live?</b></p>\n'
              '<p>Varken onlinekontovalet eller CMDR-vyn får byta en liveuppladdare till en '
              'befälhavare som endast kan ses.</p>\n'
              '\n'
              '<h3>Hjälp</h3>\n'
              '<p>"? Hjälp" finns i det vänstra sidofältet ovanför "auto show" och öppnar hjälpen '
              'för det aktuella huvudmenyområdet.</p>\n'
              '<p>I området "Inställningar" öppnar knappen denna inställningshjälp direkt.</p>\n'
              '\n'
              '<h3>Dricks</h3>\n'
              '<p>Om du installerar om eller har problem, kontrollera först:</p>\n'
              '<ul>\n'
              '<li>korrekt journalmapp och erkänd befälhavaridentitet</li>\n'
              '<li>önskat språk, tema, teckensnitt och utforskarvärde</li>\n'
              '<li>Onlineåtkomst till rätt FID</li>\n'
              '<li>Vid bildproblem, käll- och målmappar i huvudmenyn "Bilder".</li>\n'
              '</ul>\n'
              '<p>Om det finns flera befäl, var alltid uppmärksam på vilken FID den synliga '
              'online-åtkomstinformationen gäller.</p>'),
    "planet_navigation": (
        'Planetnavigering',
        """<h2>Planetnavigering</h2>
<p>Planetnavigatorn hjälper dig uteslutande att flyga till en bestämd latitud/longitud på en planet eller måne. Du anger ett koordinatmål och får avstånd och riktning dit.</p>
<p>Den är inte en interstellär ruttplanerare och hanterar varken system- eller hoppnavigering. Du styr ditt skepp själv.</p>

<h3>Öppna navigatorn och ange ett mål</h3>
<p>Öppna ”Planetnavigering” i översikten och välj ”Manuell inmatning …”.</p>
<ul>
<li><b>Himlakropp:</b> Välj målplaneten eller målmånen i listan eller använd den himlakropp som redan identifierats. Du kan också skriva in namnet själv om det ännu inte finns i listan. Om du är osäker, använd hela namnet inklusive systemnamnet.</li>
<li><b>Latitud:</b> Ange målets latitud mellan −90° och +90°.</li>
<li><b>Longitud:</b> Ange målets longitud mellan −180° och +180°. Var uppmärksam på tecknet för båda koordinaterna.</li>
<li><b>Målnamn:</b> Du kan ange en valfri beteckning för att lättare känna igen målet.</li>
</ul>
<p>Med ”Sätt mål” bekräftar du inmatningen. Du behöver inte ange tekniska ID:n som BodyID och SystemAddress; de är inte vanliga användarinmatningar.</p>

<h3>När startar kompassen?</h3>
<p>Så snart ett mål är satt och Elite levererar giltiga planetära positionsdata för rätt himlakropp aktiveras navigeringen automatiskt. Du behöver inte trycka på någon separat startknapp.</p>
<p>Om dessa data fortfarande saknas eller tillhör en annan himlakropp väntar navigatorn med ”Väntar på planetkoordinater …”. Du kan ange ett mål redan innan dessa data kommer.</p>

<h3>Planetglob: mer än 380 km</h3>
<p>När målavståndet är större än 380 km visar navigatorn planetgloben.</p>
<ul>
<li>Den <b>vita cirkeln</b> markerar din egen position.</li>
<li>Den <b>lilla målpunkten</b> är orange när målet ligger på planetens synliga sida.</li>
<li>Om målet ligger på den dolda baksidan visas målpunkten i rött.</li>
<li>Din position ligger fast i visningen. Planeten och målet visas i förhållande till din position och orientering.</li>
</ul>
<p>Den vita pilen pekar framåt; den gula pilen visar den relativa riktningen till målet. Globen är en schematisk orienteringshjälp, inte en geografiskt exakt terrängvy. En röd punkt betyder globens baksida, inte automatiskt ”bakom ditt skepp”.</p>

<h3>Perspektivrutnät: upp till och med 380 km</h3>
<p>Vid ett målavstånd på upp till och med 380 km växlar visningen automatiskt till ett lutande perspektivrutnät. Om avståndet åter ökar till över 380 km visas globen igen.</p>
<p>Tvärlinjerna bildar ett <b>avståndsrutnät i steg om 50 km</b>. Målpunkten ritas in i rutnätet enligt avstånd och relativ riktning. Perspektivet hjälper dig under den fortsatta inflygningen; lutningen gör att avstånden ser tätare ut bakåt. För den faktiska kursen att styra, följ även målkurs och relativ riktning.</p>

<h3>Läsa navigeringsvärdena rätt</h3>
<ul>
<li><b>Målavstånd:</b> Den stora visningen visar återstående avstånd till målet längs den tänkta planetytan.</li>
<li><b>Målkoordinater:</b> Koordinatparet som angetts för målet, först latitud och sedan longitud. Det förblir oförändrat medan du rör dig.</li>
<li><b>Aktuella koordinater:</b> Ditt senast bekräftade koordinatpar från Elite, också latitud / longitud.</li>
<li><b>Avstånd längs ytan:</b> Samma ytavstånd som målavståndet, eventuellt mer exakt avrundat i detaljvisningen. Det är inte en andra sträcka eller ett direkt rumsligt avstånd genom luften.</li>
<li><b>Bäring:</b> Den absoluta riktningen till målet från din aktuella position, som kompassvinkel: 000° är norr, 090° öster, 180° söder och 270° väster.</li>
<li><b>Styrkurs:</b> Din aktuella orientering som Elite anger den. Den visar åt vilket håll du är riktad just nu och behöver ännu inte stämma med bäringen.</li>
<li><b>Relativ riktning:</b> Skillnaden mellan din orientering och bäringen, till exempel ”23° höger”, ”10° vänster” eller ”Rakt fram”. Vid 180° ligger målet bakom dig.</li>
<li><b>Målkurs:</b> Den framhävda bäringen som en absolut kurs du kan vrida till i Elite-HUD:en. Den är inte en ytterligare vridningsvinkel.</li>
</ul>
<p>Exempel: Med styrkurs 051° och målkurs 074° vrider du 23° åt höger tills Elite-kompassen visar ungefär 074°. Under den fortsatta flygningen kan bäring och målkurs ändras; följ de uppdaterade värdena.</p>
<p>På samma position som målet, vid en pol eller på den exakt motsatta punkten på planeten kan riktningen vara obestämd. Då visar navigatorn motsvarande meddelande i stället för en påhittad kurs.</p>

<h3>Fönsterstorlek</h3>
<p>Navigatorfönstrets storlek kan ändras fritt. Globen eller perspektivrutnätet anpassas proportionellt till det tillgängliga utrymmet. Minimistorleken håller detaljvärdena läsbara; globen förblir rund. Fönstrets position och storlek sparas.</p>

<h3>Aktivera navigerings-HUD</h3>
<p>Till vänster i huvudfönstret markerar du kryssrutan under <b>visa automatiskt → Navigerings-HUD</b>. Vid giltig planetnavigering visas HUD:en direkt över det synliga Elite-fönstret i förgrunden.</p>
<p>Den visar tre rader:</p>
<ul>
<li>relativ riktning</li>
<li>målkurs</li>
<li>avstånd</li>
</ul>
<p>HUD:en är transparent, släpper igenom klick och tar inte fokus: den täcker inte spelet med en ogenomskinlig yta, fångar inte upp musklick och tar inte inmatningsfokus från Elite när den visas automatiskt.</p>
<p>Utan giltig navigering eller en entydig riktning blir den automatiskt osynlig. Den döljs även när Elite är minimerat eller inte ligger i förgrunden. Kryssrutan i sidofältet kan ändå förbli markerad; den anger din önskan om automatisk visning, inte den aktuella synligheten.</p>
<p>HUD:en är bara en extra visning. Den vanliga navigatorn fungerar oberoende av den, även när HUD:en är avstängd eller otillgänglig.</p>

<h3>Sätta ett nytt mål</h3>
<p>På samma himlakropp kan du när som helst öppna ”Manuell inmatning …” igen och ange andra koordinater. Det nya målet ersätter det tidigare navigeringsmålet. Med motsvarande positionsdata uppdateras kompassen omedelbart.</p>
<p>Med ”Avsluta navigering” tar du bort det aktuella målet. För en ny inflygning anger du helt enkelt ett nytt mål.</p>

<h3>Dataålder och begränsningar</h3>
<p>Navigeringen bygger på statusdata från Elite. Uppdateringar kan komma med fördröjning beroende på spelets tillstånd. Åldersvisningen i navigatorn visar hur lång tid som gått sedan det senaste bekräftade statusmeddelandet.</p>
<p>Ytavståndet beskriver den kortaste bågen på ett tänkt klot. Det är inte en terräng- eller vägrutt. Navigatorn känner inte till hinder eller terränghöjder längs sträckan; flyghöjd, säker hastighet och att undvika hinder är fortfarande ditt ansvar.</p>

<h3>Tips</h3>
<p>Kontrollera himlakroppens namn och målkoordinaternas tecken före inflygningen. Rikta sedan in dig efter målkursen i Elite-kompassen och följ relativ riktning och avstånd. Om navigatorn väntar, kontrollera om Elite redan levererar planetkoordinater för målhimlakroppen.</p>""",
    ),
}

DIALOG_TITLE = 'Hjälp – {area}'
CLOSE_LABEL = 'Stäng'
