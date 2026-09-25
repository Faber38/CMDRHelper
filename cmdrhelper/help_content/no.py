"""Norwegian content for contextual help."""


HELP_TOPICS = {
    "materials": (
        'Materialer',
        """<h2>Materialer</h2>
<h3>CMDRHelper</h3>
<p>Materialoversikt for engineering: alle 146 materialer i Raw, Manufactured og Encoded, med grader, kapasitet og unntak. Oppdatert beholdning per commander, søk, filtre, fem diskrete radbakgrunner og lagrede kolonnebredder og rekkefølge gir oversikt. Ukjent beholdning skilles fra null.</p>
<p>Odyssey-beholdning: den fjerde materialfanen inneholder 223 katalogidentiteter for varer, materialer, data og forbruksvarer. Skipslager, ryggsekk og pålitelig total holdes atskilt; oppdragsstabler, oppdragsstatus og engineering-bruk vises. Positive antall er gullfargede. Navn uten oversettelse vises på engelsk.</p>
<p>Søk etter materialhandlere (Finn materialhandler → Åpne ruteplanlegger): på forespørsel søker Spansh separat etter Raw, Manufactured og Encoded fra commanderens nåværende system. Carriers utelates og stasjonsdetaljer kontrolleres. Avstanden i ly er direkte mellom systemene; fellesskapsdata garanterer ikke tilgang. Overføring til ruteplanleggeren setter bare målsystemet og starter ingen rute. Ingen søk etter Odyssey-handlere.</p>
<p>Dette hovedområdet viser ingeniørmaterialene til commanderen som vises for øyeblikket. Valget i CMDR-visningen gjelder også her; dataene til andre commandere holdes atskilt.</p>
<h3>Tre kategorier</h3>
<p>Fanene Råmaterialer, Produserte materialer og Kodede data inneholder alle de 146 katalogmaterialene, inkludert Guardian- og Thargoid-materialer. Listen er sortert etter grad og alfabetisk innenfor hver grad.</p>
<h3>Beholdning og stolper</h3>
<p>Tallene viser beholdning / maksimum, for eksempel Vanadium 244 / 250. Den tilhørende stolpen viser 97,6 %. Også materialer du aldri har eid, vises med 0 når beholdningen er pålitelig kjent.</p>
<p>Tomme beholdninger markeres med dempet rødt, lave beholdninger med gult/oransje og nesten fulle eller fulle beholdninger med grønt. Tallene forblir synlige uavhengig av fargene.</p>
<h3>Søk og filtre</h3>
<p>Søket tar hensyn til det viste og det engelske materialnavnet. Det kan kombineres med alle filtre: Alle, Tom (0), Lav (over 0 til og med 20 %), Nesten full (fra 80 % til under 100 %) og Full (100 %). Verdier mellom 20 % og 80 % vises bare under Alle. Faner og filtre gjenopprettes ved neste oppstart.</p>
<h3>Ukjente verdier</h3>
<p>Uten en pålitelig fullstendig beholdning vises for eksempel ? / 250. Ved ukjent maksimum kan det stå 12 / ?. I begge tilfeller vises verken prosent eller stolpe; slike materialer vises bare under Alle. En ukjent grad vises i en egen gruppe nederst i listen.</p>
<h3>Løpende oppdatering</h3>
<p>Nye journalhendelser oppdaterer beholdningen automatisk, også etter materialbytte, ingeniørarbeid, syntese eller materialbelønninger. Under første innlesing vises en lastemelding. Nylig innsamlet materiale markeres kort med en angivelse som Vanadium +1; forbruk gir ingen innsamlingsmelding.</p>
<h3>Materialnavn</h3>
<p>Hvis et materialnavn ennå ikke finnes på det valgte språket, vises det engelske visningsnavnet. Interne journalsymboler erstatter ikke eksisterende visningsnavn.</p>
<h3>Odyssey</h3>
<p>«Stjålet» merker en beholdningsstabel som uttrykkelig er registrert som stjålet i lagrede Elite-data. Manglende merking bekrefter ikke at den ikke er stjålet. En kjent eieridentifikator vises i verktøytipset som «Eier»; ukjent eiernavn fylles ikke inn.</p>
<p>Verktøytipset «Nåværende tilgjengelighet er ikke bekreftet» viser til en ubekreftet anskaffelseskilde for de aktuelle spesialmaterialene. CMDRHelper kan ikke gi bekreftet, aktuell anskaffelsesinformasjon; det betyr ikke at gjenstanden er umulig å skaffe.</p>

<p>Den fjerde fanen under Materialer inneholder Varer, Materialer, Data og Forbruksvarer. Skap og ryggsekk viser personlige beholdninger. Hangarskip ✎ viser manuelt bekreftet privat beholdning av varer, materialer og data på ditt eget hangarskip. Dobbeltklikk for å bekrefte, korrigere eller sette til ukjent. — betyr ukjent; 0 må bekreftes uttrykkelig. « Totalt » inkluderer skap, ryggsekk og hangarskip bare når verdiene er kjente og samstemte. Ved flere stabler vises hangarskipets beholdning én gang i sammendraget; stablene holdes atskilt. Forbruksvarer beholder personlig total uten hangarskip. FCMaterials er ikke en fullstendig hangarskipsbeholdning og brukes ikke som det. Skapgrensen på 1000 gjelder per kategori, ikke per gjenstand. Hangarskipets beholdning beregnes fra sist bekreftede verdi. Skapendringer motposteres bare på eget hangarskip, etter fratrekk av uttrykkelige personlige transaksjoner. Kjøp og salg hos bartenderen, særlig fra andre spillere, kan endre faktisk beholdning uten automatisk registrering. Dobbeltklikk for å bekrefte på nytt ved behov. Total bruker en beregning fra sist bekreftet hangarskipsbeholdning, ikke en garantert direkteavlesning. Det private Odyssey-lageret deler 1 000 plasser mellom varer, materialer og data. Beholdningssummen er kjent først når alle posisjoner og ekstra materialer er bekreftet, også nuller. Ellers vises et minimum. Ved overskridelse beholdes verdiene og Totalt blir ukjent. Skap, ryggsekk og markedsreservasjoner er ikke hangarskipets private materialbeholdning.<br><b>! – Sett opp hangarskipets beholdning</b><br>Dobbeltklikk i kolonnen Hangarskip og angi aktuell mengde for HVER posisjon. Bekreft også ALLE tomme posisjoner uttrykkelig med 0.<br>— = ennå ikke bekreftet / ukjent<br>0 = uttrykkelig bekreftet tom beholdning</p>
<p>Åpne kjøpsordrer hos bartenderen reserverer lagerplass. Belegget i spillet kan derfor overstige materialbeholdningen. Reservasjoner er ikke materialer og inngår ikke i materialtotalene. Uten tilstrekkelig aktuelle markedsdata er belegget ukjent. Andre spilleres handler kan endre øyeblikksbildet.</p>
<p>Bruk viser gjenstandens bruksmerking. Oppdrag betyr at den konkrete beholdningsstabelen er knyttet til et oppdrag, ikke at gjenstandstypen generelt er en oppdragsgjenstand. Vanlige og oppdragsbundne stabler holdes atskilt. Også etter at oppdraget er fullført, forblir gjenstanden merket så lenge journalen fører den i beholdningen; fullføring fjerner den ikke automatisk. Verktøytipset viser oppdragsnummeret og kjent status. Ingeniørarbeid betyr at den statiske Odyssey-katalogen kjenner minst én bekreftet bruk: draktoppgradering, våpenoppgradering, draktmodifikasjon, våpenmodifikasjon eller opplåsing av en ingeniør. De enkelte bruksområdene vises i verktøytipset. Manglende merking betyr ikke at gjenstanden er ubrukelig eller bare kan handles. Powerplay-gjenstander og andre spesialgjenstander kan også vises.</p>
<p>Søket finner de viste lokale og engelske material-/gjenstandsnavnene. De seks Odyssey-filtrene er Alle (alle gjenstander), Oppdrag (stabler knyttet til et oppdrag), Ingeniørarbeid (gjenstander med bekreftet ingeniørbruk), Ryggsekk (ryggsekkbeholdning større enn null), Skipslager (lagerbeholdning større enn null) og Beholdning 0 (pålitelig kjent totalbeholdning på 0). Ukjent beholdning — er ikke 0 og tas ikke med i Beholdning 0. Manglende navneoversettelser erstattes med det engelske navnet, så enkelte navn kan fortsatt vises på engelsk i det valgte språket. Dette er tilsiktet og er ingen oversettelsesfeil i beholdningslogikken.</p>
<p>Den personlige beholdningen oppdateres automatisk i bakgrunnen. Bekreftede nye innsamlinger kan markeres kort. Ved bytte av commander fjernes gamle beholdninger umiddelbart. Underfaner, filtre, kolonnebredder og kolonnerekkefølge lagres separat for Odyssey.</p>
<h3>Mining</h3>
<p>Materialer → Mining er den sentrale oversikten over 57 kjente, omsettelige gruvevarer, atskilt fra engineering-materialer. Én tabell dekker både utvinning på planetoverflater og i asteroider/ringer. Faste referansepriser er kun veiledende, ikke direkte markedspriser.</p>
<p><b>Kolonner</b><br><b>Råvare:</b> varens eller råstoffets navn.<br><b>SRV:</b> bekreftet beholdning i SRV.<br><b>Skip:</b> bekreftet beholdning i skipet.<br><b>Carrier:</b> beholdning på din egen carrier; Elite leverer ingen fullstendig personlig lagerliste, så startbeholdningen må bekreftes manuelt.<br><b>Totalt:</b> SRV + Skip + Carrier, bare når alle tre beholdninger er kjent. Ellers —; ukjent er ikke null.<br><b>Snittpris Cr/t:</b> fast referanseverdi uten garanti for dagens salgspris. Manglende referansepriser forblir ukjente.<br><b>Verdiklasse:</b> HØY fra 100 000 Cr/t; MIDDELS ved 25 000–99 999 Cr/t; LAV under 25 000 Cr/t. Ukjent pris gir ingen verdiklasse.</p>
<p><b>Bekrefte carrierbeholdning</b><br>Elite Dangerous gir ikke CMDRHelper en fullstendig personlig lagerliste for carrieren. Slik angir du et kjent utgangspunkt for en vare: 1. Dobbeltklikk på carrier-cellen. 2. Oppgi dagens beholdning som et heltall fra 0 og oppover. 3. Bruk verdien for å bekrefte den manuelt. 4. CMDRHelper følger deretter automatisk entydige CargoTransfer-hendelser mellom skipet og din egen carrier. Verktøytipset viser den manuelle bekreftelsen og eventuell senere oppdatering.</p>
<p><b>— = ukjent beholdning</b><br>Uten en bekreftet startbeholdning kan enkeltstående overføringer ikke gi en pålitelig absolutt carrierbeholdning. Dobbeltklikk når som helst for å endre, korrigere eller tilbakestille verdien til ukjent. Hvis en overføring ville gi et motstridende eller negativt resultat, blir beholdningen ukjent igjen og må bekreftes manuelt på nytt.</p>
<p><b>Skip og SRV</b><br>SRV- og skipsbeholdning rekonstrueres separat fra bekreftede lastdata. Ukjente mengder forblir —. Fullstendige lastøyeblikksbilder har forrang fremfor beregnede endringer.</p>
<p><b>↻ Oppdater</b><br>SRV-beholdning og skipsbeholdning oppdateres separat fra bekreftede data. Bekreftet carrierbeholdning bevares uavhengig av dette. Vanlige direkteoppdateringer fortsetter automatisk. Grønt betyr klar eller vellykket, fargeanimasjonen viser pågående oppdatering, og rødt betyr et mislykket forsøk. Manglende eller ikke verifiserbare data vises ikke som tom beholdning.</p>
<p><b>Kombinere filtre</b><br>Råstoffsøket filtrerer etter navn. Verdiklassen tilbyr Alle, HØY, MIDDELS og LAV; opprinnelse tilbyr Alle, Planetarisk gruvedrift og Asteroider/Ringer. «Kun på lager» viser en vare hvis minst én kjent beholdning i SRV, skip eller carrier er positiv. Ukjente beholdninger regnes ikke som 0 og skjuler ikke en kjent positiv beholdning et annet sted. Søk, verdiklasse, opprinnelse og beholdningsfilter kan kombineres.</p>
<p><b>ABBAU ×N i utforskeren</b><br>Et klikk åpner Materialer → Mining og setter opprinnelsesfilteret automatisk til Planetarisk gruvedrift. Det finnes ingen ekstra Mining-tabell i utforskeren.</p>
<p><b>Sortering og bredder</b><br>Klikk på kolonneoverskriftene for stigende eller synkende sortering. Beholdninger og priser sorteres numerisk, med ukjente verdier til slutt. Dra kolonnegrensene med musen for å endre breddene. Sortering, kolonnebredder og filtrene for verdiklasse, opprinnelse og Kun på lager lagres.</p>
<p><b>Opprinnelse</b><br>Surface betyr utvinning på planetoverflater; Asteroid betyr gruvedrift i asteroider/ringer. Noen råstoffer finnes begge steder (Both) og vises i begge passende opprinnelsesfiltre.</p>""",
    ),'overview': ('Oversikt',
              '<h2>Oversikt</h2>\n'
              '<p>Oversikten er hjemmesiden til CMDRHelper. Den oppsummerer den viktigste '
              'informasjonen om den aktive fartøysjefen og viser med et blikk om journalen, '
              'lokasjonen og nettjenestene er korrekt gjenkjent.</p>\n'
              '\n'
              '<h3>Kommandør og skip</h3>\n'
              '<p>Fartøysjefen gjenkjent fra Elite Dangerous Journal og skipet som er i bruk vises '
              'her.</p>\n'
              '<p>CMDRHelper tildeler personlige data til den respektive fartøysjefen basert på '
              'Frontier ID (FID). Dette holder data fra forskjellige sjefer atskilt fra '
              'hverandre.</p>\n'
              '<p>Ved endring av fartøysjefen lastes den lagrede informasjonen knyttet til den nye '
              'fartøysjefen.</p>\n'
              '\n'
              '<p>CMDRHelper viser spillmodusen som Elite sist rapporterte. Open, Solo og Privat gruppe gjenkjennes fra LoadGame. For private grupper vises gruppenavnet som Elite rapporterte, uendret. Dette betyr ikke at Elite kjører akkurat nå.</p>\n'
              '<h3>journal</h3>\n'
              '<p>CMDRHelper bruker Elite Dangerous sine journalfiler som sin hoveddatakilde.</p>\n'
              '<p>Journalvisningen informerer om journalfiler er funnet og tildelt den aktive '
              'sjefen. Nye komplette journaloppføringer blir automatisk behandlet under '
              'spilling.</p>\n'
              '<p>Journalområder som allerede er behandlet lagres slik at CMDRHelper ikke trenger '
              'å fullstendig evaluere hver journal på nytt neste gang den startes.</p>\n'
              '\n'
              '<h3>Gjeldende plassering</h3>\n'
              '<p>Viser det for øyeblikket kjente stjernesystemet og - så vidt kjent fra journalen '
              '- eksakt plassering av fartøysjefen.</p>\n'
              '<p>Plasseringen oppdateres av hendelser som hopp, dokking og andre '
              'posisjonsrapporter og lagres på kommando-for-kommando-basis.</p>\n'
              '\n'
              '<h3>Oppdrag</h3>\n'
              '<p>Dette området viser antall kjente åpne oppdrag.</p>\n'
              '<p>«Oppdrag →» åpner hovedområdet «Oppdrag og belønninger» med '
              'kjente oppdragsmål og statusinformasjon.</p>\n'
              '\n'
              '<h3>Siste stand</h3>\n'
              '<p>"Siste tilstand" oppsummerer den siste kjente vedvarende sjefstilstanden. Dette '
              'gjør at viktig informasjon kan gjenopprettes selv etter omstart av Elite Dangerous '
              'eller CMDRHelper.</p>\n'
              '\n'
              '<h3>Nylig besøkte systemer</h3>\n'
              '<p>Systemer som nylig er besøkt eller gjenkjent fra journalen, vises her.</p>\n'
              '<p>Listen fungerer som en rask oversikt over fartøysjefens siste reise.</p>\n'
              '<p>Besøkshistorikken tar med Location, FSDJump og CarrierJump også under løpende journaloppdatering. Flere stedshendelser under ett sammenhengende opphold teller som ett besøk: A → A → A teller én gang. En faktisk retur beholdes: A → B → C → A teller fire besøk.</p>\n\n'
              '<h3>Online status</h3>\n'
              '<p>Det er flere statusindikatorer øverst i hovedvinduet:</p>\n'
              '<ul>\n'
              '<li><b>Journal anerkjent</b>– CMDRHelper oppdaget en gyldig journalkilde og '
              'sjefsidentitet.</li>\n'
              '<li><b>EDSM</b>– viser gjeldende status for EDSM-overføringen for den aktive '
              'journalen FID.</li>\n'
              '<li><b>INARA</b>– viser gjeldende status for Inara-overføringen for den aktive '
              'journalen FID.</li>\n'
              '</ul>\n'
              '<p>Online tilgangsdata administreres separat for hver sjef. En fartøysjef bruker '
              'aldri automatisk en annen farmands API-Key.</p>\n'
              '\n'
              '<h3>Viktig for flere befal</h3>\n'
              '<p>Live-dataene avhenger alltid av fartøysjefen som ble tydelig identifisert av den '
              'gjeldende Elite Dangerous-journaløkten.</p>\n'
              '<p>Bare å vise en annen kommando i en visning endrer ikke den aktive '
              'direktekommandøren eller påvirker noen EDSM- eller Inara-sendinger.</p>\n'
              '\n'
              '<h3>Tips</h3>\n'
              '<p>Hvis fartøysjefen, skipet eller plasseringen ikke samsvarer med gjeldende status '
              'i spillet, sjekk først journalvisningen øverst og sjekk deretter journalmappen satt '
              'under "Innstillinger".</p>'
              '<p>Open vises i rødt, Solo i gull og Privat gruppe i grønt, med det rapporterte gruppenavnet. Modusen rekonstrueres fra tilgjengelige journaler og oppdateres med nye LoadGame-oppføringer.</p>\n<p>Ett klikk på en oppføring under siste systemer kopierer systemnavnet til utklippstavlen. «✓ Kopiert: &lt;System&gt;» vises kort. Ikonet ⧉ rett ved siden av hvert systemnavn kopierer også bare dette navnet til utklippstavlen.</p>\n'),
 'missions': (
        'Oppdrag og belønninger',
        """<h2>Oppdrag og belønninger</h2>
<p>Denne hovedsiden viser oppdrag og observerte belønninger for den aktive kommandøren i journalen. Valg av en annen kommandør i den separate CMDR-visningen endrer ikke denne siden. Dataene holdes atskilt for hver kommandør.</p>

<h3>Slik bruker du siden</h3>
<ol>
<li>Åpne «Oppdrag og belønninger» og velg et oppdrag i listen.</li>
<li>Se på «Status» og «OPPDRAGSDETALJER». Bruk «Neste steg» som veiledning.</li>
<li>Bruk ved behov «Oppdater journal» for å lese tilgjengelige journaldata på nytt.</li>
<li>Vurder oppdragsbelønninger, «Dusører» og «Kampobligasjoner» hver for seg.</li>
</ol>

<h3>Liste og detaljer</h3>
<p>Listen inneholder bekreftede åpne oppdrag og registrerte foreløpige tilbud fra møter. Den viser oppdrag, system, planet / sted, status, neste steg, belønning og frist. Når du velger en rad, vises tilgjengelige detaljer om mål og fremdrift. Opplysninger som mangler i journalen, forblir ukjente; foreløpige tilbud har ukjent frist.</p>

<h3>Oppdragsstatus</h3>
<p>Statusen følger tilgjengelige oppdrags-, posisjons- og fremdriftsdata. Ikke alle oppdragstyper gir alle mellomstadier.</p>
<ul>
<li><b>Oppdrag akseptert / Underveis:</b> Oppdraget er kjent; ankomst til målet er ennå ikke registrert.</li>
<li><b>I målsystemet:</b> Du er i målsystemet, men ikke fremme ved det identifiserte oppdragsmålet.</li>
<li><b>Ved oppdragsmålet:</b> Den aktuelle målstasjonen eller det aktuelle himmellegemet er nådd.</li>
<li><b>Mål endret:</b> Et nytt oppdragsmål er meldt.</li>
<li><b>Last hentet:</b> Henting av oppdragslast er registrert.</li>
<li><b>Levering pågår:</b> En levering er registrert; kjent fremdrift i mengder vises.</li>
<li><b>Oppgave fullført / Data mottatt:</b> Oppgaven eller datainnsamlingen er utført. Oppdraget kan fortsatt være åpent, for eksempel med «Tilbake til oppdragsterminalen». Dette bekrefter ikke at belønningen er utbetalt.</li>
</ul>
<p>Registrert fullføring, mislykket oppdrag eller avbrudd fjerner det aktuelle oppdraget fra listen over åpne oppdrag. En ny fullstendig oppdragsoversikt kan identifisere eldre oppføringer som ikke lenger aktive.</p>

<h3>Total belønning</h3>
<p>«Total belønning» summerer kjente kredittbelønninger for bekreftede åpne oppdrag. Dette er ikke en allerede utbetalt saldo. Foreløpige tilbud fra møter, dusører og kampobligasjoner er ikke inkludert.</p>

<h3>Oppdrag fra møter</h3>
<p>Støttede møter i verdensrommet kan vises som foreløpige tilbud av typen «Oppdrag fra møte», selv uten en endelig MissionID. «Tilbudt belønning» er derfor ennå ikke en bekreftet belønning for et åpent oppdrag og inngår ikke i totalbelønningen.</p>
<p>Hvis senere journaldata entydig knytter et tilbud til et oppdrag, slås de sammen. Ved tvil forblir tilbudet foreløpig. Ubekreftede tilbud skjules lokalt etter 24 timer; dette sier ikke noe om oppdragsfristen i spillet.</p>

<h3>Dusører</h3>
<p>Her vises lokalt observerte dusører med totalbeløp og beløp per fraksjon. Visningen kjenner bare registrerte data, ikke en garantert fullstendig saldo fra spillet. «Registrering fra nå av.» markerer starten på registreringen; hull varsles med «Ikke fullstendig synkronisert: enkelte hendelser kan mangle.».</p>
<p>En registrert dusørinnløsning eller død nullstiller hele den lokale dusørsaldoen, uavhengig av oppdragsstatus.</p>

<h3>Kampobligasjoner</h3>
<p>Her vises observerte kampobligasjoner per fraksjon der innløsning ennå ikke er registrert. En eventuell saldo fra før registreringen startet, mangler. Ved usikkerhet vises «Observert beløp» sammen med «Saldoen er ikke fullstendig bekreftet.».</p>
<p>En entydig tilordnet innløsning fjerner det observerte beløpet for den angitte fraksjonen; andre fraksjoner beholdes. Ved uklar tilordning blir beløpene stående, og «Innløsning oppdaget – kontroller saldoen.» vises. En registrert død fjerner observerte kampobligasjoner.</p>

<h3>Lokal nullstilling</h3>
<p>«Tilbakestill…» i en belønningsdel nullstiller etter bekreftelse bare denne delens lokale saldo for den aktive kommandøren. <b>Dette endrer ingen verdier i Elite Dangerous.</b> Dusører og kampobligasjoner nullstilles hver for seg; oppdrag blir verken ryddet bort eller fullført.</p>

<h3>Oppdatering og omstart</h3>
<p>Kjente åpne oppdrag og lokale belønningssaldoer beholdes etter omstart av Helper. En ny journaløkt uten oppdragsliste fjerner ikke åpne oppdrag automatisk. Hull i registreringen kan særlig føre til ufullstendige belønningssaldoer. «Oppdater journal» kan bare lese eksisterende opplysninger, ikke opprette manglende spilldata.</p>
<p>Den lokale oppdragsvisningen trenger ingen Inara-forbindelse. Med en aktivert forbindelse konfigurert for den aktive kommandøren kan støttede oppdragshendelser også overføres.</p>""",
    ),
 'explorer': ('Utforsker',
              '<h2>Utforsker</h2><p>Overskriften viser også samme EDSM-status som EDSM-status-HUD: blå = kjent i EDSM, gul = ingen EDSM-treff, grå = intet brukbart svar. «EDSM: —» betyr at det ennå ikke finnes et resultat, for eksempel når HUD er slått av eller en forespørsel pågår. Den eksisterende HUD-innstillingen styrer forespørselen. Dette bekrefter ikke en førsteoppdagelse i Elite.</p>\n<h3>CMDRHelper</h3>\n<p>Systemoversikt: den nye Elite-inspirerte visningen erstatter miniatyroversikten i Explorer og Krønike. Stjerner og planeter danner hovedstrukturen med måner som grener under; flerstjernesystemer forblir oversiktlige. Zoom, rulling, tilpass til vinduet og klikk på himmellegemer gir tilgang til detaljer.</p>\n<p>Kompakte asteroidebelter: klynger samles til belter i oversikten og vanlige systemkart i Explorer og Krønike. Alle data om de enkelte klyngene beholdes.</p>\n<p>Korrigert kartografi: en skanning etter DSS-kartlegging nullstiller ikke lenger usolgte utforskningsverdier, kartleggingstid eller effektivitet. Feil registreringer repareres ved oppstart fra tilgjengelige journaler med entydig commander-tilordning. Manglende kilder lar reparasjonen stå åpen; databasen trenger ikke slettes.</p>\n'
              '<p>Utforskeren evaluerer systemene og himmellegemene oppdaget og skannet av den '
              'aktive sjefen. Den kombinerer dine egne Elite Dangerous-journaldata med allerede '
              'tilgjengelig tilleggsinformasjon og viser utforskning, kartografi, '
              'biologiske/geologiske signaler og overflategruvedata sammen.</p>\n'
              '\n'
              '<h3>Nåværende system</h3>\n'
              '<p>Det nåværende kunnskapsnivået om systemet er oppsummert i det øvre området.</p>\n'
              '<p>Disse inkluderer blant annet:</p>\n'
              '<ul>\n'
              '<li>kjente og til og med registrerte kropper i journalen</li>\n'
              '<li>eksisterende signaler</li>\n'
              '<li>Skann verdier</li>\n'
              '<li>kartografiverdi allerede oppnådd</li>\n'
              '<li>mulig totalverdi hvis fullstendig kartlagt</li>\n'
              '<li>BIO-status og estimerte BIO-verdier</li>\n'
              '<li>Kartografi og BIO-data som ennå ikke er sendt inn</li>\n'
              '</ul>\n'
              '<p>Verdiene som vises er basert på faktisk tilgjengelige data. Manglende '
              'informasjon presenteres ikke som et eget funn.</p>\n'
              '\n'
              '<h3>Systemkart</h3>\n'
              '<p>Systemkartet representerer grafisk stjerner, planeter, måner og andre kjente '
              'kropper i det nåværende systemet.</p>\n'
              '<p>En kropp kan klikkes for å åpne dens detaljerte visning.</p>\n'
              '<p>Displayet viser blant annet kroppstype, avstand og – hvis tilgjengelig – '
              'skannings- og kartografiverdier samt spesielle leteegenskaper.</p>\n'
              '\n'
              '<p>«Tilpass automatisk til vinduet» er på som standard og husker valget etter omstart. Hver ny oversikt tilpasses vinduet én gang; aktivering i et åpent vindu tilpasser også én gang. Etterpå kan du fortsatt zoome og flytte visningen manuelt. «Tilpass til vinduet» er fortsatt tilgjengelig for ny manuell tilpasning.</p>\n'
              '\n'
              '<h3>Stasjoner og fasiliteter</h3>\n'
              '<p>Fanen «STASJONER (N)» viser kjente stasjoner og fasiliteter i Explorerens nåværende system som utvidbare kort. Tallet i tittelen teller alle kjente oppføringer, også dem som skjules av filtre. Dette er ikke en fullstendig katalog over galaksens stasjoner.</p>\n'
              '<p>Grunnlaget er lokalt kjente observasjoner fra Elite-journalen. Med Spansh-tillegg aktivert kommer informasjon fra den separate stasjonsbufferen i tillegg. Kilden kan være «Journal», «Spansh» eller «Journal + Spansh»; ved motstridende opplysninger har journalen forrang. Spansh legger ikke til Fleet Carriers her. Din egen carrier kan vises dersom den er kjent lokalt.</p>\n'
              '\n'
              '<h3>Stasjonssøk, filtre og sortering</h3>\n'
              '<p>«Søk etter stasjonsnavn…» søker umiddelbart etter stasjonsnavn eller deler av navn, uavhengig av store og små bokstaver. Et tomt søk begrenser ikke navnene. Søket og begge filtrene må oppfylles samtidig.</p>\n'
              '<ul>\n'
              '<li><b>Type:</b> Begrenser listen til orbitalstasjoner, utposter, overflatestasjoner, bosetninger, megaskip, Fleet Carriers eller andre fasiliteter. «Alle typer» fjerner typebegrensningen.</li>\n'
              '<li><b>Tilhørende himmellegeme:</b> Velger et kjent tilhørende himmellegeme. «Alle himmellegemer» tillater alle steder; «Ukjent» vises når oppføringer ikke kan knyttes sikkert til et kjent legeme.</li>\n'
              '<li><b>Sorter etter:</b> Standard er alfabetisk etter «Navn». Alternativt stigende etter «Type», «Tilhørende himmellegeme» eller «Avstand fra ankomstpunkt». Avstand sorteres numerisk; ukjente avstander eller legemer plasseres sist ved den aktuelle sorteringen.</li>\n'
              '</ul>\n'
              '<p>Det finnes ingen stasjonskolonneoverskrifter å klikke på: valglistene sorterer kortene. Søk, filtre og sortering sender ingen nettforespørsel. Ved systembytte nullstilles søket og type-/legemefiltrene. En tom visning skiller mellom ingen kjente oppføringer og oppføringer som ikke passer filtrene.</p>\n'
              '\n'
              '<h3>Stasjonsdetaljer og tjenester</h3>\n'
              '<p>Klikk på overskriften til et stasjonskort for å åpne eller lukke detaljene. Når kjent vises navn, type, system, tilhørende legeme, MarketID, siste oppdatering og kilde. Dobbeltklikk på forhåndsvisningsbildet åpner bildeviseren.</p>\n'
              '<p>Spansh kan legge til ankomstavstand i lyssekunder, tilhørighet, styreform, kontrollerende fraksjon, økonomidata og antall store, mellomstore og små landingsplattformer. Tidspunkter for stasjonsdata, systemdata og innhenting vises separat når tilgjengelig; ny innhenting garanterer ikke nyere stasjonsdata.</p>\n'
              '<p>Kjente «Tjenester» vises som merkede felt, for eksempel «Marked», «Skipsverft», «Utrustning», «Reparasjon», «Drivstoff» eller «Materialhandler». Kortoverskriften viser høyst tre tjenester og eventuelt antallet øvrige; utvidet vises alle tjenester CMDRHelper kjenner igjen. Manglende opplysninger gjettes ikke og beviser ikke at en tjeneste mangler.</p>\n'
              '\n'
              '<h3>Stasjoner på kartet og oppdatering</h3>\n'
              '<p>Systemkartet og «Systemoversikt» bruker de samme kjente stasjonsopplysningene. Sikkert tilknyttede fasiliteter står ved sitt legeme, andre under «Andre anlegg». Et klikk åpner detaljer eller, for grupper, først en valgliste.</p>\n'
              '<p>I «Systemoversikt» oppdaterer «Oppdater Spansh-data» Spansh-stasjonsinformasjon for systemet som vises i vinduet. Spansh-stasjonsinformasjon må være aktivert og systemets identitet kjent. Statuslinjen viser pågående forespørsler, suksess, feil eller en oppdatering som allerede er utført i dag. Ved feil beholdes lokal informasjon og brukbare bufferdata. Innstillingshjelpen forklarer automatiske forespørsler, buffer og manuell oppdatering.</p>\n'
              '\n'
              '<h3>BIO ×N</h3>\n'
              '<p>BIO ×N angir antall biologiske signaler fra en kropp som er rapportert av '
              'spillet.</p>\n'
              '<p>Tallet indikerer i utgangspunktet bare hvor mange biologiske signaler eller '
              'slekter som ble rapportert. Det betyr ikke automatisk at alle biologiske arter '
              'allerede er funnet eller analysert.</p>\n'
              '<p>Faktiske egne organiske funn holdes separat.</p>\n'
              '\n'
              '<h3>GEO ×N</h3>\n'
              '<p>GEO ×N viser antall geologiske signaler til en kropp rapportert av spillet.</p>\n'
              '<p>Disse kan for eksempel inkludere geologiske trekk som fumaroler eller geysirer. '
              'CMDRHelper viser kun informasjonen som fremkommer fra eksisterende '
              'journal/kroppsdata.</p>\n'
              '\n'
              '<h3>ABBAU ×N</h3>\n'
              '<p>ABBAU ×N viser antall planetariske gruveplasser for en kropp rapportert av Elite '
              'Dangerous.</p>\n'
              '<p>Eksempel:</p>\n'
              '<p><b>ABBAU ×12</b></p>\n'
              '<p>betyr at 12 planetariske gruveplasser er rapportert for denne kroppen.</p>\n'
              '<p>Tallet sier ikke hvilket råstoff som kan utvinnes på et enkelt sted.</p>\n'
              '\n'
              '<h3>Egne gruvefunn</h3>\n'
              '<p>Hvis fartøysjefen faktisk har utført overflategruvedrift med Rhino, lagrer '
              'CMDRHelper de personlige funnene som er dokumentert separat.</p>\n'
              '<p>Det skilles mellom:</p>\n'
              '<ul>\n'
              '<li>faktisk innhentede varer, f.eks. B. Kobber i tonn</li>\n'
              '<li>sekundære materialer samlet under gruvedrift</li>\n'
              '<li>generelle overflatematerialer av kroppen</li>\n'
              '</ul>\n'
              '<p>Et eksempel på et personlig funn kan være:</p>\n'
              '<p><b>Kobber – 40 t</b></p>\n'
              '<p>Denne informasjonen betyr at denne fartøysjefen faktisk hentet ut 40 tonn kobber '
              'der.</p>\n'
              '<p>De personlige gruvefunnene lagres for hver befal og blandes ikke med funnene til '
              'andre befal.</p>\n'
              '\n'
              '<h3>Materialer på kroppsoverflaten</h3>\n'
              '<p><code>Scan.Materials</code>beskriver den generelle '
              'overflatematerialsammensetningen til en kropp.</p>\n'
              '<p>For eksempel kan jern, nikkel, svovel eller andre materialer vises med '
              'prosentverdier.</p>\n'
              '<p>Disse verdiene bør ikke forveksles med råvarene til et planetarisk gruvedepot. '
              'Frontier gir ingen dokumentert direkte assosiasjon mellom disse generelle '
              'kroppsmaterialene og innholdet på et individuelt gruvested i Journal.</p>\n'
              '\n'
              '<h3>Terraforming</h3>\n'
              '<p>Symbolet eller etiketten for terraforming viser at en kropp anses som en '
              'terraforming-kandidat basert på tilgjengelige data.</p>\n'
              '\n'
              '<h3>Første oppdagelse</h3>\n'
              '<p>«Allerede oppdaget ved skanningen din» beskriver tilstanden før skanningen den gangen. Ja betyr oppdaget tidligere, Nei betyr ennå ikke oppdaget da; manglende informasjon forblir Ukjent. ★ markerer en First Discovery-kandidat på skannetidspunktet, ikke et garantert offisielt førstekrav som fortsatt er tilgjengelig i dag.</p>\n<p>En historisk WasDiscovered=false eller WasMapped=false betyr ikke at himmellegemet fortsatt er uoppdaget eller ukartlagt i dag. Opplysningene forblir historiske etter datasalg eller nye besøk. Kjennskap i EDSM er separat informasjon og beviser ingen offisiell oppdagelse i Elite. Ingen offisiell førsteoppdager utledes av dette.</p>\n'
              '\n'
              '<h3>Første kartlegging</h3>\n'
              '<p>CMDRHelper skiller mellom:</p>\n'
              '<ul>\n'
              '<li>◉ First Mapping-kandidat på skannetidspunktet: ennå ikke kartlagt da du skannet</li>\n<li>◎ Kartlagt av deg: din egen fullførte DSS-kartlegging er registrert</li>\n<li>◉✓ Kandidat ved skanning og egen kartlegging dokumentert; offisielt førstekrav ubekreftet</li>\n'
              '</ul>\n'
              '<p>«Allerede kartlagt ved skanningen din» vurderes uavhengig av oppdagelse. Manglende informasjon forblir Ukjent. Et allerede oppdaget himmellegeme kan ha vært ukartlagt ved skanningen. Egen kartlegging bekrefter ikke en offisiell First Mapping-merkelapp; ved flere besøk er heller ikke rekkefølgen i forhold til den lagrede skanningen alltid dokumentert.</p>\n<p>Fullført egen DSS-kartlegging lagrer nå kartleggingstidspunkt, brukte sonder og effektivitetsmål pålitelig. Senere skanninger fører ikke lenger til tap av eksisterende opplysninger.</p>\n'
              '\n'
              '<h3>Landing mulig</h3>\n'
              '<p>Landbarhetsindikatoren identifiserer kropper som, ifølge kjente data, er mulig å '
              'lande på.</p>\n'
              '\n'
              '<h3>Gullrammer / verdifulle kropper</h3>\n'
              '<p>Spesielt verdifulle kropper kan fremheves i utforskerdisplayet.</p>\n'
              '<p>Gullrammen markerer et kartleggingsestimat over den valgte terskelen. Den er ikke en First Discovery-markering og bekrefter verken usolgte data eller førstebonuser som fortsatt er tilgjengelige i dag.</p>\n'
              '<p>Den erstatter ikke den detaljerte visningen av kroppens verdi.</p>\n'
              '\n'
              '<h3>Liste over verdier</h3>\n'
              '<p>Verdilisten viser estimater basert på den lagrede skanningen, ikke garanterte utestående utbetalinger. Førstebonuser forblir ubekreftet. Verktøytips i kart og liste og detaljene for himmellegemet bruker de samme tidfestede tilstandene.</p>\n'
              '<p>Den er spesielt egnet for raskt å sammenligne interessante eller verdifulle '
              'kropper i et system.</p>\n'
              '\n'
              '<h3>BIO / GEO / ABBAU</h3>\n'
              '<p>Denne visningen samler himmellegemer med biologiske, geologiske eller planetariske '
              'gruvesignaler.</p>\n'
              '<p>Dette betyr at interessante kropper ikke trenger å søkes opp individuelt i det '
              'komplette systemkartet.</p>\n'
              '<p>Hvis du har dine egne gruvedata på overflaten, kan dine personlige gruvefunn '
              'også være synlige.</p>\n'
              '<p>Manuelt justerte kolonnebredder i den felles Explorer-tabellen BIO / GEO / ABBAU beholdes ved gjenåpning og omstart. Lagrede kolonnebredder i sprettoppvinduer gjenopprettes mer robust; ugyldige verdier erstattes med trygge standardbredder.</p>\n\n'
              '<h3>Bruke tabellene</h3>\n<p>Klikk på en kolonneoverskrift i verdilisten eller BIO / GEO / ABBAU '
              'for å sortere; klikk igjen for å snu retningen. Dra kolonnegrensene med musen for å endre '
              'breddene. Sortering og kolonnebredder lagres separat for hver tabell. Navn på himmellegemer '
              'sorteres naturlig, for eksempel A 2 før A 10. Avstander, kreditter og antall sorteres numerisk. '
              'Status, analyse og besøkt sorteres etter betydning, ikke alfabetisk.</p>\n\n<h3>Kroppsdetalj</h3>\n'
              '<p>Ved å klikke på en kropp åpnes den detaljerte visningen.</p>\n'
              '<p>Så vidt kjent kan følgende vises der:</p>\n'
              '<ul>\n'
              '<li>Kroppstype</li>\n'
              '<li>masse</li>\n'
              '<li>avstand</li>\n'
              '<li>Tyngdekraften</li>\n'
              '<li>atmosfære</li>\n'
              '<li>Landbarhet</li>\n'
              '<li>Terraforming status</li>\n'
              '<li>BIO/GEO-signaler</li>\n'
              '<li>planetariske gruveplasser</li>\n'
              '<li>Overflatematerialer</li>\n'
              '<li>egne gruvefunn</li>\n'
              '<li>Skanneverdi</li>\n'
              '<li>kartografiverdi</li>\n'
              '<li>nåværende verdi</li>\n'
              '</ul>\n'
              '<p>Ikke alle organer har all informasjonen.</p>\n'
              '\n'
              '<h3>BIO-prognoser</h3>\n'
              '<p>CMDRHelper kan estimere mulige biologiske funn basert på eksisterende data om '
              'egnede kropper.</p>\n'
              '<p>Spådommer er ikke en garanti for at en bestemt art faktisk vil være til stede. '
              'De tjener som beslutningshjelp for leting.</p>\n'
              '<p>Estimerte BIO-verdier er også spådommer og behandles separat fra faktiske '
              'bekreftede funn.</p>\n'
              '\n'
              '<h3>Ikke sendt inn ennå</h3>\n'
              '<p>CMDRHelper vedlikeholder sjefsrelaterte kjente kartografi- og BIO-data som ennå '
              'ikke er sendt inn.</p>\n'
              '<p>Kartografisalg og biologiske royalties regnskapsføres ved å bruke de tilsvarende '
              'journalhendelsene.</p>\n'
              '<p>Kartografidata som allerede er solgt skal ikke vises som åpne igjen etter '
              'rekonstruksjon.</p>\n'
              '\n'
              '<h3>Vis automatisk</h3>\n'
              '<p>Støttede Explorer-tips som verdifulle kropper eller BIO-funn kan vises '
              'automatisk ved hjelp av bryterne i venstre sidefelt.</p>\n'
              '<p>Disse små live-vinduene fungerer som ekstra hint mens du spiller og erstatter '
              'ikke hele Explorer-visningen.</p>\n'
              '<p>«Cargo» viser den bekreftede beholdningen i Ship eller SRV som bestemmes av den aktive Journal-FID-en. SRV Cargo overtas aldri som Ship Cargo; Limpets teller med i total last og vises separat i tabellen Navn | Antall.</p>\n'
              '<p>BIO-fremdriften er kompakt: 1/3 gul, 2/3 blå og 3/3 grønn; fullført tilstand «Ferdig» er også grønn. Under «vis automatisk» har GEO en egen lagret bryter: bare BIO, bare GEO eller begge sammen.</p>\n<p>Lastevinduet tilpasser høyden automatisk til innholdet. Ved mange oppføringer begrenses høyden og tabellen kan rulles; valgt bredde og vindusposisjon beholdes. Den eksisterende bryteren «Lasteroms-HUD» ligger nå under «vis automatisk», uten en ekstra bryter i lastevinduet.</p>\n\n'
              '<h3>Flere befal</h3>\n'
              '<p>Personlige leteresultater, kartografi, BIO-funn og egne gruvefunn på overflaten '
              'tildeles den respektive sjefen.</p>\n'
              '<p>Globale astronomiske egenskaper til en kropp - for eksempel antallet kjente '
              'planetariske gruveplasser - forblir egenskapene til kroppen selv.</p>\n'
              '\n'
              '<h3>Tips</h3>\n'
              '<p>Hvis du har en interessant kropp, er det verdt å klikke på den detaljerte '
              'visningen. Dette er det beste stedet å skille mellom generelle kroppsdata, mulige '
              'leteresultater og faktiske funn dokumentert av din egen sjef.</p>'
              """

<h3>★ Favoritter</h3>
<p>Knappen «★ Favoritter» øverst i Explorer åpner et eget favorittvindu som kan brukes på nytt. Her lagrer du systemer, planeter/måner og steder på overflaten for den aktive kommandøren.</p>
<p>Den rullbare listen, alfabetisk sortert etter navn, viser navn, type, system, himmellegeme og breddegrad/lengdegrad der det er relevant, kategori og en liten bildeforhåndsvisning. Fritekstsøk, typefilter og kategorifilter kan brukes sammen. Søket omfatter navn, system, himmellegeme og notat.</p>
<p>«Åpne / Vis» viser de lagrede opplysningene, notatet og en større bildeforhåndsvisning. «Vis i Explorer» åpner den eksisterende systemoversikten eller detaljvisningen for himmellegemet hvis favoritten tilhører det gjeldende Explorer-systemet og passende data er tilgjengelige. For andre systemer forblir de lagrede favorittdataene synlige; ingen systemrute beregnes.</p>

<h3>Avstandsfilter</h3>
<p>«Avstandsfilter» er avslått som standard. «Maks. avstand:» er først satt til 500 ly og kan justeres fra 1 til 100 000 ly. Avstanden regnes fra det nåværende kjente systemet med lokalt tilgjengelige systemkoordinater. Det gjøres ingen nettforespørsel bare for dette filteret.</p>
<p>Favoritter med kjent avstand utenfor grensen skjules. Favoritter med ukjent avstand forblir synlige. Mangler koordinatene til det nåværende systemet, skjuler avstandsfilteret ingen oppføringer. Søk, type og kategori gjelder fortsatt. Filtreringen oppdateres automatisk etter et systembytte. Bryteren og maksimal avstand lagres.</p>

<h3>Eksportere favoritter</h3>
<p>«Eksporter» lager en portabel ZIP med alle favorittene til den aktive kommandøren, ikke bare oppføringene som vises gjennom søk eller type-, kategori- og avstandsfiltre. favorites.json inneholder de strukturerte favorittdataene; tilgjengelige favorittbilder ligger under images/. Pakken kan overføres mellom Linux og Windows.</p>
<p>Eksisterende favoritter og originalbilder endres ikke. Bilder med identisk innhold lagres bare én gang i pakken. Manglende eller skadede bilder hindrer ikke eksport av favorittdata. Import og eksport tillater maksimalt 32 MiB per fil og 256 MiB totalt for ukomprimert pakkeinnhold.</p>

<h3>Importere favoritter</h3>
<p>«Importer» kontrollerer først ZIP-filen og viser en oversikt over nye og eksisterende favoritter før endringer. Importerte favoritter tilordnes den nåværende aktive kommandøren. Duplikater gjenkjennes etter type, kategori, navn og sted: kjente system-/himmellegeme-ID-er og koordinater, ellers system-/himmellegemenavn. Duplikater inne i pakken regnes også med.</p>
<p>Ett valg gjelder alle oppdagede duplikater: «Hopp over» er standard og bevarer eksisterende oppføringer; «Erstatt eksisterende favoritt» overfører de importerte dataene til den eksisterende favoritten; «Importer som ny oppføring» lager en ekstra oppføring. Avbryt importerer ingenting.</p>
<p>Ugyldige favorittdata stopper hele importen. Ved importfeil rulles databaseendringer tilbake for å unngå delvis import. Manglende eller skadede bilder hindrer ikke import av gyldige data; disse favorittene importeres uten bilde. CMDRHelper håndterer importerte bilder lokalt.</p>

<h3>Lagre et system, en planet eller gjeldende posisjon</h3>
<ul>
<li>«★ Lagre nåværende system» lagrer det gjeldende systemet uten overflatekoordinater.</li>
<li>«★ Lagre planet / måne» lar deg velge en kjent planet eller måne i det gjeldende systemet. Denne favoritten får heller ikke overflatekoordinater.</li>
<li>«★ Lagre nåværende posisjon» står øverst i favorittvinduet ved siden av de to andre lagringsvalgene og er også tilgjengelig i planetnavigatoren. I favorittvinduet er knappen alltid synlig og er deaktivert uten gyldige, aktuelle planetære posisjonsdata og en aktiv kommandør. Ved klikk fryses kommandør, system, himmellegeme, breddegrad og lengdegrad. Senere bevegelser i spillet endrer ikke disse verdiene i den åpne dialogen.</li>
</ul>
<p>Skriv inn et valgfritt navn og velg nøyaktig én kategori: Bio, Geo, Gruvedrift, Utsikt, Landingssted, Interessant eller Annet. Notat og bilde er valgfrie. Kjente tekniske ID-er overføres internt; du trenger ikke skrive dem inn. Breddegrad eller lengdegrad 0,0 er også gyldige koordinater.</p>
<p>«Rediger» endrer navn, kategori, notat og bilde. System, himmellegeme og lagrede koordinater beholdes. Hvis du vil lagre et annet sted på overflaten, oppretter du en ny favoritt på den posisjonen.</p>

<h3>Hurtigfavoritt uten mus</h3>
<p>Under «Innstillinger → Hurtigfavoritt» kan du fritt angi, endre eller fjerne en global hurtigtast. Etter installasjonen er den som standard «Ikke tilordnet»: CMDRHelper registrerer ingen tast uten at du ber om det. Tilordningen lagres. Hvis en kombinasjon allerede er i bruk eller ikke er tilgjengelig på systemet ditt, vises en feilmelding; en tidligere fungerende tilordning beholdes.</p>
<p>På Linux/X11 og Windows fungerer hurtigtasten også mens Elite har fokus – til fots, i SRV-en og i skipet. Ett tastetrykk lagrer den aktuelle posisjonen på overflaten umiddelbart for den aktive kommandanten, uten dialog og uten bruk av mus. Kommandant, system, himmellegeme og gjeldende Latitude-/Longitude-verdier fryses i det øyeblikket. Uten gyldige aktuelle planetkoordinater lagres ingenting; tidligere koordinater brukes ikke på nytt.</p>
<p>Favoritten får et unikt foreløpig navn, for eksempel «Markør 07.09.2026 06:32:15», og kategorien «Annet». I det vanlige favorittvinduet kan du senere gi den nytt navn, tilordne en annen kategori, legge til et notat eller et bilde. Ingen skjermbilder tas eller importeres automatisk.</p>
<p>I omtrent to sekunder vises «★ FAVORITT LAGRET» direkte over det aktive Elite-vinduet med himmellegeme og koordinater; hvis posisjonen mangler, vises «⚠ INGEN PLANETKOORDINATER» kort. Visningen tar ikke fokus og fanger ikke opp inndata. Den fungerer også når navigasjons-HUD-et er slått av, og forsvinner deretter helt. Når HUD-et er slått på, blir den vanlige navigasjonsvisningen stående etterpå. Den lagrede innstillingen for HUD-bryteren endres ikke. Visningen bruker samme overleggsløsning og plattformkrav som navigasjons-HUD-et.</p>

<h3>Favorittbilder</h3>
<p>Favorittbilder er atskilt fra Bilder-området. «Velg bilde …» tillater PNG, JPEG og WebP. Først ved lagring kopierer CMDRHelper det valgte bildet til sin egen mappe for favorittbilder. Originalfilen blir verken flyttet eller endret.</p>
<p>«Bruk siste skjermbilde» leser den konfigurerte kildemappen for skjermbilder på nytt ved hvert klikk og ser etter lesbare skjermbilder med typiske Elite-filnavn. Uten en innstilling tas de vanlige Elite-skjermbildemappene på Windows eller Steam/Proton med. Mappen til den aktive kommandøren i det konfigurerte konverteringsmålet gjennomsøkes også etter passende konverterte Elite-skjermbilder. Dermed kan et konvertert skjermbilde fortsatt finnes hvis den opprinnelige BMP-filen er slettet. Det nyeste opptakstidspunktet bestemmes av en entydig tidsangivelse i filnavnet, ellers av filtiden; for konverterte bilder brukes opptakstiden som er lagret i navnet, ikke konverteringstidspunktet. CMDRHelper tar ikke skjermbilder selv og søker ikke i vilkårlige bildemapper.</p>
<p>Før bruk vises filnavn, opptakstid og en nylastet forhåndsvisning. Bekreft med «Bruk dette bildet». Hvis ingen passende skjermbilder blir funnet, kan du fortsatt bruke «Velg bilde …». Elite-skjermbilder i BMP-format lagres som en intern PNG-kopi.</p>
<p>Et bilde kan erstattes i redigeringsdialogen eller velges bort med «Fjern bilde». Ved lagring slettes den interne kopien som ikke lenger brukes. Hvis en bildefil mangler, kan favoritten fortsatt brukes uten forhåndsvisning.</p>
<p>Favorittbilder kan eksporteres og kopieres lokalt ved import. Delte interne bildekopier beholdes så lenge en annen favoritt trenger dem. Når en import erstatter favoritter, beholdes gamle bildefiler foreløpig som en forholdsregel.</p>

<h3>Favorittmål og kommandør</h3>
<p>«▶ Til ruten» setter favorittens kjente system som mål i ruteplanleggeren. Starten følger eksisterende oppførsel med gjeldende AppState; en manuelt angitt start beholdes. Ingen rute beregnes automatisk. «◎ Til koordinatene» starter eksisterende planetnavigasjon til overflatestedet med eksisterende HUD når system, himmellegeme og gyldige koordinater er lagret. Reisen til systemet og overflatenavigasjonen er to separate trinn, uten automatisk reiseforløp. Uten overflatekoordinater er bare ruten tilgjengelig; handlinger som mangler nødvendige data skjules.</p>
<p>For steder på overflaten sender «◎ Til koordinatene» det lagrede himmellegemet, breddegrad, lengdegrad og favorittnavnet til den eksisterende planetnavigatoren. Det nye målet erstatter det forrige. Favoritter har ingen egen navigasjonslogikk. Navigatoren avgjør fortsatt selv: samsvarende, gyldige planetære data aktiverer navigasjonen; ellers venter den på disse dataene.</p>
<p>Favoritter tilhører bare den aktive kommandøren. Ved kommandørbytte oppdateres listen, og en åpen redigeringsdialog forkastes. Et mål som fortsatt håndteres som den forrige kommandørens favorittmål, avsluttes. Kommandørvalget i kronikken utvider ikke denne favorittlisten.</p>
<p>«Slett» krever bekreftelse og fjerner bare favorittoppføringen og dens interne bildekopi. Det opprinnelige skjermbildet eller det valgte originalbildet og alle Explorer-, journal- og himmellegemedata beholdes.</p>"""),
 'chronicle': (
        'Krønike',
        """<h2>Krønike</h2>
<h3>CMDRHelper</h3>
<p>Systemoversikt: den nye Elite-inspirerte visningen erstatter miniatyroversikten i Explorer og Krønike. Stjerner og planeter danner hovedstrukturen med måner som grener under; flerstjernesystemer forblir oversiktlige. Zoom, rulling, tilpass til vinduet og klikk på himmellegemer gir tilgang til detaljer.</p>
<p>Kompakte asteroidebelter: klynger samles til belter i oversikten og vanlige systemkart i Explorer og Krønike. Alle data om de enkelte klyngene beholdes.</p>
<p>Kronikken er fartøysjefens personlige reise- og oppdagelseshistorie. Den bruker den permanent lagrede journalinformasjonen til å finne systemer som allerede er besøkt, for å representere dem romlig og for å søke etter kjente funn.</p>

<h3>Systemer besøkt</h3>
<p>Krøniken viser systemene som ble besøkt og deres plassering i galaksen kjent for kommandøren.</p>
<p>Hvis tilgjengelig, tas det hensyn til første og siste besøk samt kjent kroppsinformasjon.</p>
<p>Med en aktiv periode gjelder antall besøk, første besøk og siste besøk i kartvisningen de filtrerte faktiske systembesøkene.</p>
<p>Kronikken er derfor ikke bare et kart, men også et verktøy for å finne tidligere reisemål og oppdagelser.</p>

<h3>3D kart</h3>
<p>Systemene som besøkes er romlig representert ved hjelp av deres galaktiske X/Y/Z-koordinater.</p>
<p>Bruksanvisningen er plassert rett over kartet:</p>
<ul>
<li>Hold nede venstre museknapp → roter visning</li>
<li>hold inne midtre museknapp og dra → trekk opp et zoomvindu</li>
<li>Hold nede høyre museknapp → flytt visning</li>
</ul>
<p>Displayet med liten akse hjelper med orientering i rommet.</p>

<p>Bruk musehjulet til å zoome inn eller ut uten noen ekstra tast.</p>
<p>Dobbeltklikk på tom plass i kartet for å gjenopprette den opprinnelige skrå visningen, nullstille forskyvningen og tilpasse alle viste systemer til vinduet. Filtre og valgt system beholdes.</p>
<p>Når du begynner å rotere med venstre museknapp, blir systemet du klikker på, rotasjonspunktet. På tom plass brukes punktet under pekeren på det galaktiske planet; ved nesten vannrett visning brukes i stedet kartets sentrum på dette planet. Innretting roterer også rundt det gjeldende rotasjonspunktet.</p>
<p>Klikk på et system for å åpne detaljvinduet. Der kopierer et venstreklikk på systemnavnet øverst eller kopieringsikonet ⧉ ved siden av bare systemnavnet til utklippstavlen. Et kort ✓ bekrefter kopieringen.</p>

<h3>Nåværende posisjon</h3>
<p>Med "Current Position" kan kartvisningen justeres eller returneres til den gjeldende kjente plasseringen til den aktive fartøysjefen.</p>
<p>Først brukes de gjeldende filterinnstillingene. Visningen sentreres bare på det nåværende systemet hvis det finnes i kartet som blir vist.</p>
<p>Ellers vises «Det nåværende systemet er ikke med i dette filterutvalget.» Filtrene blir ikke fjernet av dette.</p>

<h3>Juster</h3>
<p>«Juster» tilbakestiller orienteringen til en visning ovenfra av det galaktiske planet. Forskyvning og zoom beholdes.</p>
<p>Dette er nyttig hvis mye rotasjon har gjort kartet uoversiktlig.</p>

<h3>Oppdater Krønike</h3>
<p>«Oppdater Krønike» laster krønikedataene på nytt med de gjeldende kombinerte filtrene og oppdaterer visningen. Fritekst, aktiverte datogrenser og gruvefiltre vurderes samlet på nytt; aktive filtre ignoreres ikke.</p>
<p>Funksjonen endrer ikke journalfiler eller oppretter nye letedata. Den oppdaterer ganske enkelt historievisningen basert på eksisterende CMDRHelper-data.</p>

<h3>Fritekstsøk</h3>
<p>Allerede kjent innhold kan søkes i feltet "Søkehistorikk...".</p>
<p>Søket tar blant annet hensyn til – hvis tilgjengelig i databasen –:</p>
<ul>
<li>Systemnavn</li>
<li>Kroppsegenskaper</li>
<li>biologiske data</li>
<li>Materialer</li>
<li>Codex data</li>
</ul>
<p>Fritekst, periode og gruvedrift ligger i ett felles filterområde. «Bruk» vurderer de angitte filtrene samlet. Enter i fritekstfeltet starter den samme kombinerte filtreringen som «Bruk».</p>

<h3>Periode Fra/Til (UTC)</h3>
<p>Aktiver «Fra» og «Til» med hver sin avkryssingsboks, og velg ønsket dato. Det er også mulig å bruke bare én grense. Uten aktivert avkryssing er det ingen tidsbegrensning på den siden; uten begge avkryssingene begrenses ingen periode.</p>
<ul>
<li><b>Fra:</b> Fra starten av den valgte UTC-kalenderdagen, inkludert.</li>
<li><b>Til:</b> Hele den valgte UTC-kalenderdagen tas med, frem til rett før starten av neste dag.</li>
</ul>
<p>UTC er koordinert universaltid. Datogrensene gjelder UTC-kalenderdager, ikke kalenderdager i din lokale tidssone.</p>
<p>Filtreringen bruker faktiske systembesøk fra <code>system_visits</code>. Et faktisk besøk av den aktuelle kommandøren innenfor perioden er nødvendig. De lagrede opplysningene <code>first_seen</code> og <code>last_seen</code> erstatter ikke et reelt besøk: det er ikke nok at perioden bare ligger mellom et tidligere første besøk og et senere siste besøk.</p>
<p>Perioden filtrerer besøk, ikke enkelte oppdagelses-, BIO-, GEO- eller gruvehendelser. Kjente funnopplysninger og utvunne mengder forblir lagrede totalverdier. Fra/Til kan brukes alene eller sammen med fritekst og gruvefiltre.</p>
<p>Hvis Fra er etter Til, vises «Fra-datoen må ikke være etter Til-datoen.» Ingen databasespørring startes. Korriger datogrensene og bruk filtrene på nytt.</p>

<h3>Søkeresultater</h3>
<p>Treff vises i den eksisterende resultatlisten under kronikkkortet.</p>
<p>Avhengig av type treff, kan system og kropp samt tilleggsinformasjon vises.</p>
<p>Et treff kan brukes til å finne det korresponderende systemet eller kroppen som allerede er kjent og for å åpne den eksisterende detaljerte informasjonen.</p>

<h3>Ingen treff</h3>
<p>Hvis en gyldig filtrering ikke finner treff, tømmes kart og ruter. Trefflisten tømmes og skjules, detaljvisningen tilbakestilles, og et eventuelt åpent systemdetaljvindu i krøniken lukkes.</p>
<p>Gamle resultater blir ikke stående synlige. Kontroller da kombinasjonen av søketekst, periode og gruvefiltre samt kommandøren som brukes for den aktuelle visningen.</p>

<h3>Planetære gruveområder</h3>
<p>Filteret "Planetære gruvesteder" kan brukes til å spesifikt søke etter kjente kropper som Elite Dangerous har rapportert planetariske gruvesteder for.</p>
<p>Den underliggende skjermen tilsvarer den kjent fra Explorer:</p>
<p><b>ABBAU ×N</b></p>
<p>Nummeret tilhører selve kroppen og er ikke relatert til fartøysjefen.</p>

<h3>I det minste</h3>
<p>Ved å bruke "Minst" kan du spesifisere minimumsantallet av planetariske gruveplasseringer en kropp skal ha.</p>
<p>Eksempel:</p>
<p><b>Minst 20</b></p>
<p>viser kun kjente kropper med minst:</p>
<p><b>ABBAU ×20</b></p>
<p>Dette gjør det mulig å spesifikt lokalisere spesielt omfattende gruveområder.</p>

<h3>Mine gruvefunn</h3>
<p>Med «Egne gruvefunn» er letinga avgrensa til kroppar der den aktuelle farandsjefen påviselig sjølv har utført gruvedrift.</p>
<p>Denne informasjonen kommer fra personlig overflategruvehistorie og er strengt adskilt av sjefen.</p>
<p>Et organ kan derfor ha globale ABBAU ×N-signaler uten at egen sjef allerede har fjernet noe der.</p>

<h3>Vare</h3>
<p>Hvis "Egne gruvefunn" er aktivert, er valget "Råmateriale" også tilgjengelig.</p>
<p>Listen inneholder kun varer som den aktuelle fartøysjefen faktisk allerede har vunnet fra overflategruvedrift.</p>
<p>Dette er ikke en teoretisk liste over alle mulige gruve råvarer.</p>
<p>For EXAMPLE kan listen for eksempel inneholde:</p>
<ul>
<li>Alle</li>
<li>kopper</li>
</ul>
<p>Hvis ytterligere råvarer faktisk utvinnes senere, vil de automatisk vises i ditt personlige valg.</p>

<h3>Målrettet søk etter råvarer</h3>
<p>For eksempel, hvis "Kobber" er valgt og deretter "Bruk" trykkes, vil historikken kun vise kropper som den aktuelle fartøysjefen beviselig har utvunnet kobber på.</p>
<p>Eksempel:</p>
<p><b>Example System / 2 — ABBAU ×12 — kobber 40 t</b></p>
<p>Dette betyr at kronikken kan brukes som en personlig lokasjonsdatabase: et råmateriale som allerede er utvunnet kan bli funnet igjen senere.</p>

<h3>Alle råvarer</h3>
<p>Med "Råmateriale: Alle" blir alle matchende personlige gruvefunn på overflaten tatt i betraktning.</p>
<p>Hvis flere varer er kjent på en kropp, kan de vises sammen med mengdene de har fått til nå.</p>
<p>Eksempel:</p>
<p><b>ABBAU ×12 — Helium-3 10 t, kobber 40 t</b></p>
<p>Mengdene er de personlige gruveverdiene til den respektive sjefen, som faktisk er dokumentert fra journalhendelser.</p>
<p>Også med en aktiv periode forblir personlige utvunne mengder lagrede totalmengder. <b>Kobber 40 t</b> betyr ikke automatisk <b>40 t i den valgte perioden</b>. Perioden krever et passende systembesøk, men begrenser ikke den viste utvunne mengden til denne perioden.</p>

<h3>Kombiner filtre</h3>
<p>Fritekst, aktiverte Fra-/Til-grenser og gruvefiltre kan kombineres. Et treff må oppfylle de angitte betingelsene samlet.</p>
<p>For eksempel:</p>
<ul>
<li>Planetariske gruveplasser er aktive</li>
<li>Minst 20</li>
<li>Egne gruvefunn aktive</li>
<li>Råstoff kobber</li>
</ul>
<p>leter etter kjente kropper med minst 20 planetariske gruveplasser der vedkommende fartøysjef allerede selv har utvunnet kobber.</p>
<p>Eventuell ekstra søketekst tas også med. Hvis en periode er angitt i tillegg, må kommandøren du viser faktisk ha besøkt det tilhørende systemet i denne perioden; selve kobberutvinningen trenger ikke å ha skjedd i denne perioden.</p>

<h3>Bruk</h3>
<p>«Bruk» utfører en samlet filtrering med alle gjeldende søke-, periode- og gruvefiltre:</p>
<ul>
<li>Fritekst</li>
<li>Fra, hvis aktivert</li>
<li>Til, hvis aktivert</li>
<li>Planetære gruveområder</li>
<li>Minimumsantall</li>
<li>Mine gruvefunn</li>
<li>Vare, hvis «Mine gruvefunn» er aktivert</li>
</ul>
<p>Enter i fritekstfeltet utfører nøyaktig samme filtrering. Uten fritekst og gruvefiltre lastes det vanlige kartet for de avkryssede kartkommandørene, eventuelt begrenset av Fra/Til.</p>

<h3>Tilbakestill</h3>
<p>«Tilbakestill» setter det felles filterområdet tilbake til utgangstilstanden:</p>
<ul>
<li>Fritekst tømmes.</li>
<li>Fra og Til deaktiveres; datofeltene viser dagens dato igjen og er deaktivert.</li>
<li>Planetære gruveområder deaktiveres.</li>
<li>Minimumsantallet settes til 0.</li>
<li>Mine gruvefunn deaktiveres.</li>
<li>Vare settes tilbake til «Alle».</li>
</ul>
<p>Kommandørvalget beholdes. Deretter lastes den vanlige krøniken på nytt for dette kartvalget; tidligere søketreff og detaljvisninger tilbakestilles.</p>

<h3>Kommandørvalg</h3>
<p>Kronikken kan vise data fra ulike kjente befal.</p>
<p>Det finnes to separate valgkonsepter:</p>
<ul>
<li><b>Kommandørvalg for kartet:</b> Kommandøravkryssingene bestemmer hvilke kommandørruter som vises i det vanlige kartet uten fritekst-/gruvesøk. En aktivert periode tas med.</li>
<li><b>Kommandøren som vises:</b> Personlige fritekst-/gruvesøk bruker kommandøren som vises (<code>viewed_commander_id</code>), ellers den aktive kommandøren. Også de personlige varelistene følger denne kommandøren.</li>
</ul>
<p>Personlig informasjon som dine egne gruvefunn og råvarelister blir imidlertid alltid vurdert separat for fartøysjefen som faktisk vises.</p>
<p>En fartøysjef ser ingen gruvefunn i sitt råvareutvalg som utelukkende tilhører en annen fartøysjef.</p>

<h3>Alle kommandører</h3>
<p>Kart-/kronikkvisningen kan ta hensyn til flere kommandoer.</p>
<p>«Alle kommandører» gjelder kommandørvalget for kartet. Kommandøravkryssingene utvider ikke automatisk personlige fritekst-/gruvesøk til flere kommandører.</p>
<p>Dette endrer ikke den personlige tilordningen av befalsrelaterte data. Globale astronomiske egenskaper til et system eller kropp forblir delt, personlige funn forblir atskilt.</p>

<h3>Søkehjelp / legende</h3>
<p>Ytterligere informasjon om kronikksøket og betydningen av displayet kan nås via "Søkehjelp / legende".</p>
<p>Et søkeord du klikker på, settes inn i søkefeltet og kjøres sammen med periode-/gruvefiltrene som allerede er angitt.</p>
<p>Denne kontekstrelaterte hovedhjelpen supplerer den korte bruksanvisningen som er tilgjengelig der.</p>

<h3>Tips</h3>
<p>Kronikken egner seg spesielt godt til å finne interessante steder som ble oppdaget under en lengre tur.</p>
<p>For overflategruvedrift, for eksempel, kan den svare:</p>
<p>"På hvilken planet har jeg noen gang utvunnet kobber?"</p>
<p>eller:</p>
<p>"Hvilke av mine kjente planeter har et spesielt høyt antall gruveplasser?"</p>""",
    ),
 'jump_tip': (
        'Analyse',
        """
<h2>Analyse</h2>
<p>Analysen bruker din personlige utforskningshistorikk. Systemanalyse vurderer et oppgitt prosedyregenerert systemnavn; Historiske data beholder den tidligere kodeanalysen med historiske treff og ny vurdering. Begge er beslutningsstøtte, ikke garantier for funn.</p>
<h3>Sammenligningsgrunnlag</h3>
<p>Massekoden gir grunnanslaget. Region og familie presiserer det forsiktig. Små lokale utvalg jevnes mot det større datagrunnlaget. Lite data betyr usikkerhet, ikke dårlig vurdering. Utilstrekkelig undersøkte systemer teller ikke som negative treff.</p>
<h3>Potensialindeks</h3>
<p>Potensialindeks 100 tilsvarer ditt personlige historiske gjennomsnitt av dempet utforskningspotensial. Indeksen er ikke en prosentsannsynlighet. Et ensartet kartleggingsscenario og dempede ekstremverdier gjør sammenligning mulig; median og utjevnet potensial er anslåtte kreditter, ikke garanterte inntekter.</p>
<h3>Spesielle funn</h3>
<p>Det siste systemnummeret vurderes ikke: Plio Aip KN-B d13-201 tilhører familien Plio Aip KN-B d13. BIO er kun informasjon og inngår ikke i hovedvurderingen. Manglende analyser betyr ikke påviste nullverdier.</p>
<h3>Systemanalyse</h3>
<p>Skriv inn et system og velg Analyser eller trykk Enter. Bruk gjeldende system henter navnet fra eksisterende spilltilstand. Analysen beregnes på nytt bare på brukerhandling. Sammenligningsgrunnlag og resultater angir nivået; uten lokale sammenligninger brukes overordnet erfaring. Datakvalitet vises separat fra anbefalingen.</p>
<p>Feltet «System» lar deg skrive inn et navn fritt. «Bruk gjeldende system» fyller bare ut feltet; start deretter med «Analyser» eller Enter. Navnet kontrolleres lokalt mot det støttede prosedyremessige navnemønsteret. Her finnes verken nettbasert systemoppslag eller valgliste for tvetydige navn.</p>
<p>Tom inndata, et navn som ikke støttes, manglende kvalifiserte sammenligningsdata eller en feil erstatter forrige resultat med en melding. En vellykket analyse viser anbefaling, potensialindeks og lokalt datagrunnlag. Sammenligningstabellen viser massekode, region og familie med systemantall og datagrunnlag; nedenfor vises erfaringsverdier og kjente spesielle funn.</p>
<h3>Historiske data</h3>
<p>Historiske treff etter systemkode. Verdiene beskriver utforskingserfaringen din hittil og er ikke en direkte prognose for et enkelt målsystem. Datagrunnlag og pålitelighet beskriver hvor pålitelige sammenligningsdataene er, ut fra utvalget og fordelingen mellom sektorer.</p>
<p>I «Historiske data» velger du under «Mål» en funntype, ikke et reisemål: for eksempel et utforskningsmål, en BIO-slekt eller BIO-art. Første vurdering skjer når visningen bygges. Etter endring av mål eller minsteantall står den forrige rangeringen til du trykker «Vurder på nytt».</p>
<p>Tallfeltet ved målvalget setter minste utvalg per kode: 1 til 50 undersøkte systemer, i utgangspunktet 3. Koder med færre systemer eller uten historiske treff for valgt funntype utelates fra rangeringen.</p>
<p>Tabellen «Historiske mønstre» viser opptil 50 koder med rang, tidligere suksess (systemer med treff / undersøkte systemer), treffandel og bevisstyrke. Rekkefølgen følger den utjevnede historiske vurderingen, ikke bare treffandelen. Begge tabellene har fast rekkefølge uten kolonnesortering eller detaljhandling. Ingen passende mønstre gir en melding om tomt resultat; en vurderingsfeil tømmer rangeringen og viser en feilmelding. Analyse beregner ingen reiserute.</p>
""",
    ),
 'route_planner': ('Ruteplanlegger',
                   """<h2>Ruteplanlegger</h2>
<h3>Oversikt</h3>
<p>Planleggeren beregner ruter mellom systemer via Spansh. Velg «Skipsrute» eller «Fleet Carrier / CTSVision». Nettforbindelse kreves; CMDRHelper styrer verken skip eller carrier.</p>

<h3>Start og mål</h3>
<p>«Startsystem» følger den aktive kommandørens kjente nåværende system til du skriver inn en egen start. Et tomt felt gjenoppretter dette. Skriv hele navnet i «Målsystem»; et mål fra favoritter klargjør skipsruten uten å beregne den.</p>
<p>Start og mål må identifiseres entydig. Lignende navn brukes ikke som erstatning. Ukjente eller tvetydige navn gir en melding; rett opp inntastingen.</p>

<h3>Skipsrute</h3>
<p>Her er det ingen skipsvelger: kjente data fra det aktive skipet fyller de tekniske feltene. Egne endringer beholdes som manuelle verdier. «Bruk skipsdata» henter tilgjengelige skipsdata på nytt. Se meldingen om komplette, ufullstendige, gamle eller ukjente FSD-data.</p>
<p>Kontroller «Hovedtankkapasitet», «Nåværende last», «Grunnmasse», «Reservetankkapasitet», «Reservebrensel», «Optimal FSD-masse», «Maksimalt FSD-brensel per hopp», «Brenseleffekt», «Brenselmultiplikator» og «Rekkeviddebonus». Disse bestemmer hoppegenskapene; det finnes ikke ett felt for vanlig skipsrekkevidde. Last og utstyr kan endre faktisk rekkevidde.</p>

<h3>Skipsvalg og beregning</h3>
<p>«Rutealgoritme» tilbyr optimistic, pessimistic, fuel, fuel_jumps og guided. Valget sendes til Spansh.</p>
<p>Valgene er «Bruk supercharge/nøytronstjerner», «Skipet starter allerede supercharged», «Bruk FSD-injeksjoner», «Ekskluder sekundærstjerner» og «Fyll drivstoff ved hver scoopbar stjerne»: nøytronstøtte, allerede forsterket start, FSD-injeksjoner, sekundærstjerner og tankstopp. Start med «Beregn skipsrute med Spansh».</p>

<h3>Carrierrute</h3>
<p>«Fleet Carrier / CTSVision» planlegger uten å velge eller styre en bestemt carrier. Fyll inn «Tritium i tanken» og «Tritium i carrier-lageret», til sammen høyst 25 000 t. «Beregnet carrier-masse» viser 25 000 t pluss disse to mengdene.</p>
<p>«Maksimal hopperekkevidde» kan være 1 til 500 ly, med 500 ly som standard. «Beregn rute med Spansh» starter beregningen. Carrierknappen er deaktivert under forespørselen.</p>

<h3>Spansh og ventetid</h3>
<p>Spansh beregner ruten i bakgrunnen. Status viser forespørselen og deretter suksess eller feil. Dette er ruter, ikke handelspriser eller stasjonsinformasjon. Visningen har ingen avbrytknapp for en pågående beregning.</p>

<h3>Ruteresultat</h3>
<p>Listen har fast ruterekkefølge: nummer, system, hoppavstand og gjenværende avstand. Den kan ikke sorteres fritt. Skipsruter viser også forbruk, drivstoff i tanken, nøytron- og tankanvisninger; carrierruter viser tritiumforbruk.</p>
<p>Nedenfor står totalavstand, antall hopp og forbruk eller anslått tritium. Manglende verdier forblir «–». Kontroller planen mot den faktiske tilstanden i spillet.</p>

<h3>Fremdrift og neste mål</h3>
<p>En vellykket beregnet skipsrute tas i bruk automatisk. «Nåværende system», «Neste mål» og «Rutestatus» viser posisjon, neste steg og tilstand. Listen beholdes uten ekstra haker for fullførte steg.</p>
<p>Et gjenkjent skipshopp til neste eller et senere system på ruten flytter fremdriften fremover og kopierer automatisk navnet på systemet etter dette. Gjentatte posisjonsmeldinger og carrierhopp teller ikke som slike fremdriftshopp.</p>
<p>Innlasting av ruten kopierer ikke et navn automatisk. Bruk «Kopier neste mål» først eller senere så lenge et neste mål finnes. Bare systemnavnet kopieres: ingen automatisk innliming eller styring av Elite.</p>

<h3>Avvik og fullføring</h3>
<p>Et hopp utenfor den gjenværende ruten viser «Nåværende system er utenfor ruten». Ruten og forrige neste mål beholdes; ingen automatisk nyberegning skjer. Et senere passende hopp fremover kan gjenoppta ruten. Du kan også bevisst beregne en ny rute.</p>
<p>Ved siste system vises «Rute fullført». «Neste mål» blir «–», kopieringsknappen deaktiveres og ingen flere navn kopieres. Utklippstavlen tømmes ikke. Resultatlisten blir stående.</p>

<h3>CTSVision-eksport</h3>
<p>Bare carrierruten tilbyr «Eksporter for CTSVision». Etter vellykket beregning velger du en ny CSV-fil. Den inneholder ruterekkefølgen og tilgjengelige avstands-, drivstoff-, tritium- og etterfyllingsdata for senere bruk i CTSVision.</p>
<p>Dette er fileksport, ikke direkte forbindelse eller automatisk carrierstyring. Eksisterende filer overskrives ikke. Avbryt i fildialogen oppretter ingen fil; skrivefeil meldes.</p>

<h3>Feil og råd</h3>
<p>Manglende systemer, ufullstendige eller ugyldige skipsparametere og for mye tritium meldes. Påkrevde tank-, masse- og FSD-verdier må være positive; reservedrivstoff må ikke overstige reservetankens kapasitet.</p>
<p>Ingen rute, nettproblemer, for lang ventetid eller ubrukelig Spansh-svar gir også melding, aldri et oppdiktet resultat. Kontroller navn, skipsdata og valg før ny beregning.</p>

<h3>Analyse og kommandør</h3>
<p>«Analyse», med «Systemanalyse» og «Historiske data», vurderer systemer og tilgjengelig erfaring. Ruteplanleggeren beregner den konkrete reisen mellom start og mål.</p>
<p>Forhåndsutfyllingen bruker aktiv kommandør og skip. Å bare vise en annen kommandør i CMDR-visningen endrer ikke dette.</p>"""),
 'images': ('Bilder',
            '<h2>Bilder</h2>\n'
            '<p>"Bilder"-delen administrerer skjermbildene tatt med Elite Dangerous. CMDRHelper '
            'kan automatisk gjenkjenne nye opptak, behandle dem og lagre dem i et galleri basert '
            'på kommandoen.</p>\n'
            '\n'
            '<h3>Kilde mappe</h3>\n'
            '<p>Kildemappen er mappen der Elite Dangerous lagrer skjermbilder i BMP-format.</p>\n'
            '<p>CMDRHelper kan overvåke denne mappen for nye BMP-filer. For at automatisk '
            'behandling skal fungere, må den riktige skjermbildemappen settes.</p>\n'
            '\n'
            '<h3>Destinasjonsmappe</h3>\n'
            '<p>Destinasjonsmappen er den vanlige rotmappen for bildene som behandles av '
            'CMDRHelper.</p>\n'
            '<p>Brukeren angir denne rotmappen. CMDRHelper oppretter automatisk de nødvendige '
            'sjefsrelaterte undermappene under behandlingen.</p>\n'
            '\n'
            '<h3>Lagre innstillinger</h3>\n<p>«Lagre innstillinger» lagrer kilde- og målmappe, utdataformat, lysning og begge avkrysningene. Overvåkingen settes opp på nytt med disse valgene; eksisterende BMP-filer merkes som kjente. Galleriet oppdateres også.</p>\n<p>«Oppdater galleri» laster galleriet på nytt fra eksisterende bildefiler for gjeldende filter. Det starter ingen BMP-konvertering.</p>\n\n<h3>Automatisk behandling</h3>\n'
            '<p>Hvis "Konverter nye BMP-filer automatisk" er aktivert og gyldige kilde- og målmapper er angitt, '
            'sjekker CMDRHelper regelmessig kildemappen for nye BMP-skjermbilder.</p>\n'
            '<p>Når den er aktivert, blir eksisterende BMP-filer i utgangspunktet merket som '
            'kjente og blir ikke automatisk konvertert uten å bli spurt. Den separate funksjonen '
            'for konvertering av eksisterende BMPer er tilgjengelig for dette.</p>\n'
            '<p>En ny fil settes ikke i kø før den har samme størrelse som ikke er null i to '
            'påfølgende kontroller. Som et resultat blir ikke en skriveoperasjon som fortsatt er i '
            'gang behandlet umiddelbart.</p>\n'
            '\n'
            '<h3>Bildekonvertering</h3>\n'
            '<p>Som kilde behandler CMDRHelper BMP-filer. "PNG" eller "JPG" kan velges som '
            'målformat.</p>\n'
            '<p>JPG-filer lagres på kvalitetsnivå 95. PNG-filer lagres på en optimalisert '
            'måte.</p>\n'
            '<p>Som standard beholdes den originale BMP-filen. Hvis "Slett BMP etter vellykket konvertering" '
            'er aktivert, vil kilde-BMP bare bli slettet etter at målbildet er lagret.</p>\n'
            '\n'
            '<h3>Gjør bildet lysere</h3>\n'
            '<p>Lysstyrken justeres fra 0 til 50 prosent ved hjelp av en glidebryter og et koblet '
            'tallfelt. Innstillingen er lagret.</p>\n'
            '<p>Den brukes automatisk under hver konvertering som startes etterpå - både for nylig '
            'overvåkede og manuelt initierte eksisterende BMP-filer. 0 prosent tar over den '
            'opprinnelige lysstyrken; høyere verdier øker lysstyrken til det genererte PNG- eller '
            'JPG-bildet tilsvarende.</p>\n'
            '<p>Funksjonen er ikke en ren forhåndsvisning og brukes ikke senere på et bilde valgt '
            'i galleriet. Den endrede lysstyrken lagres i den nye målfilen.</p>\n'
            '<p>Kilde-BMP forblir uendret med mindre sletting av BMP-filen også er aktivert. '
            'Journal, fartøysjef og letedata endres ikke.</p>\n'
            '\n'
            '<h3>Kommandørrelatert lagring</h3>\n'
            '<p>Nye skjermbilder blir tilordnet den faktiske spillende Commander basert på '
            'journalidentiteten til stede i den aktive live AppState.</p>\n'
            '<p>Mappestrukturen inneholder kommandonavn og Frontier ID, for eksempel:</p>\n'
            '<p><b>EXAMPLE_F12345678/</b></p>\n'
            '<p>FID holder oppdraget klart selv med flere sjefer. Dette gjør at to sjefer med '
            'samme navn kan skilles fra hverandre.</p>\n'
            '\n'
            '<h3>filnavn</h3>\n'
            '<p>Nye behandlede bilder får et navn med fangsttidspunkt, sjefsnavn og - hvis '
            'tilgjengelig - stjernesystemet kjent ved kø.</p>\n'
            '<p>Eksempel:</p>\n'
            '<p><b>2026-09-04_&#8203;13-18-22_&#8203;EXAMPLE_&#8203;Sol.png</b></p>\n'
            '<p>FID er i det kommandorelaterte mappenavnet, ikke igjen i bildefilnavnet.</p>\n'
            '\n'
            '<h3>Sikre filnavn</h3>\n'
            '<p>CMDRHelper renser kommando- og systemnavn for bruk som fil- og '
            'mappekomponenter.</p>\n'
            '<p>Ulovlig kontroll og Windows-tegn erstattes, mellomrom forenes, problematiske '
            'punktum eller etterfølgende mellomrom fjernes, og reserverte Windows-navn som CON '
            'eller NUL er sikret.</p>\n'
            '\n'
            '<h3>Opptakstid</h3>\n'
            '<p>For navngivning bruker CMDRHelper modifikasjonstiden til den stabile gjenkjente '
            'BMP-filen. Kun hvis dette ikke kan leses vil gjeldende tid brukes.</p>\n'
            '<p>Dette betyr at navnet vanligvis avhenger av kildefilen og ikke av den påfølgende '
            'konverteringstiden.</p>\n'
            '\n'
            '<h3>Flere bilder i samme sekund</h3>\n'
            '<p>Hvis det tiltenkte filnavnet allerede eksisterer eller er reservert for en '
            'pågående konvertering, legger CMDRHelper det til '
            'kontinuerlig <code>_2</code>,<code>_3</code>,<code>_4</code> og så videre.</p>\n'
            '<p>Dette betyr at et annet skjermbilde med samme tidsstempel ikke vil overskrive et '
            'eksisterende målbilde.</p>\n'
            '\n'
            '<h3>Fartøyskifte under behandling</h3>\n'
            '<p>Commander, FID og systemet fanges sammen når du setter et skjermbilde i kø.</p>\n'
            '<p>Et senere skifte av befal endrer ikke tildelingen av dette allerede ventende '
            'bildet. Dette betyr at et skjermbilde av EXAMPLE ikke senere blir skrevet til mappen '
            'til en annen sjef.</p>\n'
            '\n'
            '<h3>galleri</h3>\n'
            '<p>Galleriet viser PNG-, JPG- og JPEG-filer fra katalogene knyttet til det valgte '
            'filteret. Nye, slettede eller flyttede bilder oppdages jevnlig.</p>\n'
            '<p>Gallerifilteret endrer ikke lagringsplasseringen eller kommandoen til filene.</p>\n'
            '\n'
            '<h3>Nåværende sjef</h3>\n'
            '<p>Current Commander-filteret viser bilder fra mappen til kommandoen som vises i '
            'CMDR-visningen.</p>\n'
            '<p>Den aktuelle fartøysjefen bestemmer kun gallerivisningen. På den annen side, '
            'tildeling av et nytt live-skjermbilde bruker journalidentiteten som er aktiv når du '
            'står i kø.</p>\n'
            '\n'
            '<h3>Alle befal</h3>\n'
            '<p>"Alle sjefer"-filteret viser bildene fra de gyldige undermappene til alle kjente '
            'sjefer sammen. Den spesielle mappen for opptak uten anerkjent identitet tas også i '
            'betraktning.</p>\n'
            '<p>Filene blir ikke flyttet eller slått sammen.</p>\n'
            '\n'
            '<h3>Ikke tildelt</h3>\n'
            '<p>Utildelt-filteret viser støttede bildefiler som ligger direkte i den delte '
            'målrotmappen.</p>\n'
            '<p>Spesielt forblir eldre bilder uten sjefsrelaterte undermapper synlige. CMDRHelper '
            'prøver ikke å gjette deres tilhørighet i etterkant.</p>\n'
            '\n'
            '<h3>Eksisterende bilder</h3>\n'
            '<p>Bilder som allerede finnes i rotmappen blir ikke automatisk flyttet eller '
            'omdøpt.</p>\n'
            '<p>De forblir tilgjengelige via «Utildelt» så lenge de er tilgjengelige som PNG, JPG '
            'eller JPEG.</p>\n'
            '\n'
            '<h3>Velg og vis bildet</h3>\n'
            '<p>Et enkelt klikk på et forhåndsvisningsbilde viser bildet skalert i '
            'forhåndsvisningsområdet og viser filnavnet.</p>\n'
            '<p>Et dobbeltklikk åpner filen med operativsystemapplikasjonen satt for bilder.</p>\n'
            '<p>Flere bilder kan merkes samtidig. Når du endrer vindusstørrelsen, skaleres '
            'forhåndsvisningen av gjeldende bilde for å passe.</p>\n'
            '\n'
            '<h3>Slett bildet</h3>\n'
            '<p>Merkede bilder kan slettes ved å bruke "Slett valgt" eller slettetasten. Før '
            'sletting vises et sikkerhetsspørsmål; Uten et utvalg påpekes først nødvendig '
            'utvalg.</p>\n'
            '<p>Bare de valgte PNG/JPG/JPEG-målfilene blir slettet fra katalogene til gjeldende '
            'gallerifilter. Den originale BMP-kildefilen påvirkes ikke.</p>\n'
            '\n'
            '<h3>Åpne målmappen</h3>\n'
            '<p>"Åpne målmappe" åpner lagringsstedet i filbehandleren og oppretter den delte '
            'rotmappen om nødvendig.</p>\n'
            '<p>"Current Commander"-filteret åpner sin eksisterende Commander-undermappe. Hvis det '
            'ennå ikke eksisterer eller et annet filter er aktivt, åpnes den delte rotmappen.</p>\n'
            '\n'
            '<h3>Sikkerhet av bildestier</h3>\n'
            '<p>Før du sletter, kontrollerer CMDRHelper den kanoniske banen til hver fil. Den må '
            'være innenfor den konfigurerte målmappen og direkte i en katalog som er tillatt av '
            'gjeldende gallerifilter.</p>\n'
            '<p>Symbolske lenker brukes ikke som kommandomapper eller galleribilder og slettes '
            'ikke via galleriet. Stier utenfor målområdet og kryssingsveier avvises.</p>\n'
            '\n'
            '<h3>Hvis ingen sjef ble oppdaget</h3>\n'
            '<p>Hvis Commander og FID mangler når et nytt opptak settes i kø, vil ikke filen bli '
            'satt på vent og vil ikke bli tildelt en kjent Commander.</p>\n'
            '<p>Det vil være i undermappen <b>UNKNOWN_&#8203;UNKNOWN/</b> behandlet; filnavnet brukes også '
            'for Commander <b>UNKNOWN</b>. Denne mappen kan vises gjennom Alle commandere, ikke '
            'gjennom Uallokert rotmappefilter.</p>\n'
            '\n'
            '<h3>Flere befal</h3>\n'
            '<p>To separate regler gjelder for bildebehandling:</p>\n'
            '<ul>\n'
            '<li><b>Lagre nye bilder:</b> Den aktive journalidentiteten med Commander og FID når de '
            'står i kø, bestemmer målmappen.</li>\n'
            '<li><b>Se bilder:</b> Kommandoen som vises eller det valgte gallerifilteret bestemmer '
            'de synlige bildene.</li>\n'
            '</ul>\n'
            '<p>Dette betyr at galleriet til en annen sjef kan ses mens EXAMPLE spilles uten at '
            'nye skjermbilder havner i mappen til den aktuelle sjefen.</p>\n'
            '\n'
            '<h3>Tips</h3>\n'
            '<p>En delt rotmappe for skjermbilder er tilstrekkelig. CMDRHelper separerer '
            'automatisk nylig behandlede bilder i Commander og FID.</p>\n'
            '<p>Med "Current Commander", "All Commanders" og "Unassigned" kan du bytte mellom '
            'personlig galleri, undermappene til alle kommandoer og eldre bilder i rotmappen.</p>\n'
            '<p>Høyere lysstyrke kan hjelpe med mørke bilder; det påvirker det nyopprettede '
            'målbildet under konverteringen.</p>'),
 'commander_view': (
        'CMDR-visning',
        """<h2>CMDR-visning</h2>
<h3>Velge kommandør</h3>
<p>Valget øverst bestemmer hvem sine lagrede data du ser. ● Live aktiv markerer den aktive journalkommandøren; Kun visning en annen lagret profil. Valget endrer ikke den aktive journalkommandøren: hovedsiden «Oppdrag og belønninger» bruker fortsatt den som faktisk spiller. Personlige data holdes atskilt med FID, også ved like navn. Visning starter ingen overføring til nettjenester.</p>

<h3>Oversikt, formue og MercCoins</h3>
<p>«Oversikt» viser navn, FID, status, første og siste registrering, besøkte systemer, biologiske/geologiske funn, Codex-oppføringer og kartografisalg, posisjon, åpne oppdrag, skip, hangarskip og usolgte bio-/kartografidata med kjente anslag. «Formue» er siste lagrede kredittsaldo. «Mercenary credits» viser Frontiers rapporterte verdier: «Current», «Total spent», «Engineering», «Gear» og «Reported by Frontier: total earned». Tellerne trenger ikke stemme matematisk overens; CMDRHelper korrigerer dem ikke og lager ingen oppdiktet transaksjonshistorikk. Ukjente verdier vises som «–».</p>

<h3>Oppdrag og utforskning</h3>
<p>«Oppdrag» viser den betraktede kommandørens lagrede åpne oppdrag med status, navn, mål, utløpstid og belønning. Tabellen er for visning, uten oppdragsdetaljer eller oppdragshandlinger som på hovedsiden. «Utforskning» viser usolgte bio-/kartografidata, biologiske funn, første fotavtrykk, egen og effektiv kartlegging av himmellegemer og besøkte systemer. «Krønike» er en plassholder her; den fullstendige krøniken åpnes fra hovedmenyen.</p>

<h3>Flåte og skipsdetaljer</h3>
<p>«Skip» viser det nåværende eller sist brukte skipet øverst, deretter kommandørens lagrede flåte. Klikk på overskriften til et skipskort for å utvide detaljene. Sorter stigende/synkende etter bruk, navn, type, hopprekkevidde, lastekapasitet, tommasse, posisjon eller tidspunkt; filtrer alle skip eller skip med kjøretøy-/jagerhangar. Grønt markerer det aktive skipet i sanntid; andre farger grupperer kjente posisjoner. Detaljene omfatter kjennetegn, ShipID, posisjon, tidspunkter, FSD/Guardian-forsterker, rekkevidde, masse, laste-/drivstoffkapasitet og utstyrsstatus (fullstendig, ufullstendig eller foreldet). Kjente moduldata legger til hangarer, skjold og forsterkninger, våpen og passasjerkabiner. Manglende verdier vises som «–».</p>

<h3>Eget hangarskip</h3>
<p>«Egen Fleet Carrier» viser navn, kallesignal, CarrierID, siste posisjon og siste oppdatering for ditt lagrede hangarskip. Dette er ikke handelstilbud eller gruvelagre.</p>

<h3>Personlige bilder av skip og hangarskip</h3>
<p>Bruk «Velg skipsbilde…» i utvidede skipsdetaljer eller «Velg hangarskipbilde…» ved hangarskipet. PNG, JPG/JPEG og WEBP støttes. CMDRHelper lagrer en egen lokal kopi, atskilt per kommandør og skip eller hangarskip, også gjennom omstarter. Et nytt valg erstatter kopien. «Fjern eget bilde» fjerner kopien og tilknytningen; originalfilen beholdes. Uten eget bilde vises en tilgjengelig standardforhåndsvisning eller plassholder. Bildevalg er deaktivert uten entydig identifikasjon av hangarskipet. Skjermbilder tilordnes ikke automatisk.</p>

<h3>Bildeviser</h3>
<p>Dobbeltklikk på et tilgjengelig skips- eller hangarskipbilde for å åpne den separate viseren med bildefilen, ikke bare miniatyrbildet. Bildet tilpasses vinduet med riktige proporsjoner. Du kan forstørre eller maksimere vinduet og lukke det med Esc eller lukkeknappen. Det finnes ingen bildenavigasjon eller zoomkontroll her. Hovedområdet «Bilder» håndterer derimot skjermbilder.</p>

<h3>Slette et skip</h3>
<p>«Slett skip…» krever uttrykkelig bekreftelse; Avbryt er forhåndsvalgt. Handlingen fjerner den lokale skipsoppføringen, lagrede utstyrsdata og den personlige bildekopien. Nåværende eller sist brukte skip og et identifisert aktivt sanntidsskip er beskyttet; sletting er sperret under ny innlesing. Et lokalt slettemerke hindrer gamle journaldata i å gjenopprette skipet med en gang. En ny entydig melding om skipet som aktivt i sanntidsjournalen etter slettingen kan gjenopprette det. Bekreftet ny innlesing kan også fjerne merket. Den slettede personlige bildekopien kommer ikke tilbake.</p>

<h3>Lese inn alle skip på nytt</h3>
<p>«Les inn alle skip på nytt…» kan hente flåteopplysninger fra eksisterende journaler eller finne lokalt slettede skip igjen. Etter bekreftelse leses kjente journalfiler og filer i den valgte journalmappen på nytt for den betraktede kommandøren, bare for flåten. Elite trenger ikke å kjøre. Nyere lagrede opplysninger og skip som mangler i tilgjengelige journaler beholdes; gjenkjente salg tas hensyn til. Ved suksess fjernes kommandørens manuelle slettemerker. Eksisterende personlige bilder beholdes, slettede bilder gjenopprettes ikke. Andre kommandører berøres ikke. Hvis lesing eller innlegging mislykkes, beholdes merkene: kontroller journaltilgangen og prøv igjen.</p>

<h3>Lokale data og sikkerhet</h3>
<p>Lagrede opplysninger kan vises uten nett og etter omstart; de viser sist kjente tilstand. Bilder, sletting og ny innlesing gjelder bare CMDRHelper. De endrer ingen skip, hangarskip eller kreditter i Elite Dangerous og skriver ikke om journalene.</p>""",
    ),
 'settings': ('Innstillinger',
              '<h2>Innstillinger</h2>\n<h3>CMDRHelper</h3>\n<p>Bedre oppdateringsinformasjon: Ja/Nei-vinduet viser installert og tilgjengelig versjon samt opptil seks nyheter når et sammendrag finnes. Lange lister kan rulles og handlingene forblir tilgjengelige.</p>\n'
              '<p>"Innstillinger"-området bestemmer hvordan CMDRHelper fungerer med Elite '
              'Dangerous, journalfiler, database, nettjenester, grensesnitt og oppdateringer.</p>\n'
              '<p>Endringer i legitimasjon og baner bør gjøres nøye. Kommandørrelaterte '
              'innstillinger administreres separat av Frontier ID om nødvendig.</p>\n\n<h3>Hurtigfavoritt</h3>\n<p>Under «Hurtigfavoritt» bruker du «Angi hurtigtast» for å tilordne en global hurtigtast eller «Endre hurtigtast» for å endre den. «Fjern hurtigtast» fjerner tilordningen; utgangspunktet er «Ikke tilordnet». Valget lagres. En registreringskonflikt gir en melding. Tasten lagrer en gyldig nåværende overflateposisjon som commanderens favoritt uten dialog, ikke et skjermbilde. Uten passende posisjonsdata lagres ingenting.</p>\n'
              '\n'
              '<h3>journal</h3>\n'
              '<p>Journalmappen er en av de viktigste innstillingene. Den må peke til mappen der '
              'Elite Dangerous <code>Journal*.log</code> filer av Windows- eller Proton-profilen som '
              'brukes.</p>\n'
              '<p>Journalene gir blant annet:</p>\n'
              '<ul>\n'
              '<li>Fartøysjefens identitet, plassering og reise</li>\n'
              '<li>Oppdrag, skip og eiendeler</li>\n'
              '<li>Utforskning, kartografi og BIO-data</li>\n'
              '<li>Overflategruvedrift, leiesoldatmynter og andre støttede stater</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Journalvisning og betjening</h3>\n'
              '<p>Journalgruppen viser mappesettet, antall journaler som er funnet, eldste og '
              'nyeste journal, navnet på den nyeste filen og tidspunktet for siste leste '
              'oppføring.</p>\n'
              '<p>"Velg journalmappe" endrer mappen. "Les nå" utløser den normale oppdateringen '
              'umiddelbart.</p>\n'
              '<p>Tydelig identifiserbare økter tildeles ved hjelp av FID. Nye komplette '
              'oppføringer behandles trinnvis; Sikre leseposisjoner forhindrer at hver journal '
              'unødvendig leses på nytt i sin helhet neste gang den startes.</p>\n'
              '\n'
              '<h3>database</h3>\n'
              '<p>CMDRHelper lagrer nødvendige data permanent i en lokal SQLite-database. Dette '
              'inkluderer globale system- og kroppsdata samt informasjon som er eksplisitt tildelt '
              'en fartøysjef.</p>\n'
              '<p>Innstillingssiden viser statistikk om de lagrede dataene. Databasen skal ikke '
              'redigeres manuelt mens CMDRHelper kjører.</p>\n'
              '\n'
              '<h3>Importer journalarkiv</h3>\n'
              '<p>"Importer journalarkiv" sammenligner fullstendig journalfilene til den angitte '
              'journalmappen med databasen. Allerede kjente journalområder tas i betraktning '
              'basert på den lagrede importinformasjonen og dupliseres ikke blindt som nye '
              'data.</p>\n'
              '<p>Under en manuelt synlig import vises fremdriften, nummeret og den nåværende '
              'behandlede filen. Etter fullføring rapporterer CMDRHelper importerte eller allerede '
              'kjente data eller en feil.</p>\n'
              '<p>Arkivimporten tjener også til å lære støttet historisk informasjon på nytt fra '
              'tydelig tilordnede journaler.</p>\n'
              '\n'
              '<h3>Kommandørrelaterte data</h3>\n'
              '<p>CMDRHelper skiller personlig informasjon basert på FID og den tilknyttede '
              'interne Commander ID. Disse inkluderer, men er ikke begrenset til, oppdrag, '
              'eiendeler, MercCoins, personlig utforskning og nettilgang.</p>\n'
              '<p>En ukjent eller tvetydig journaløkt kan ikke vilkårlig tildeles en '
              'fartøysjef.</p>\n'
              '\n'
              '<h3>Online tjenester</h3>\n'
              '<p>CMDRHelper støtter EDSM og Inara. Begge tilgangene behandles og lagres separat '
              'for hver kjent sjef eller hver FID.</p>\n'
              '<p>Valget i innstillingene avgjør bare hvem som har tilgang som for øyeblikket blir '
              'redigert eller testet. Bare sjefen som er tydelig identifisert av den aktive '
              'journaløkten, har lov til å sende live.</p>\n'
              '\n'
              '<h3>Spansh-stasjonsinformasjon</h3>\n'
              '<p>Under «NETTJENESTER» aktiverer «Legg til stasjonsinformasjon fra Spansh» valgfrie tilleggsopplysninger om stasjoner og fasiliteter i Explorer og systemvisninger. Valget er av som standard. Bare den offentlige systemidentifikatoren sendes, ikke kommandørinformasjon; ingen egen API-nøkkel kreves. Valget styrer ikke handelsmarkedssøk.</p>\n'
              '<p>Når det er deaktivert, vises bare lokale journalopplysninger, og ingen nye Spansh-stasjonsforespørsler startes; manuell oppdatering er også deaktivert. Eksisterende stasjonsbuffer slettes ikke, men brukes ikke til å supplere visningen. Aktivering gjør bufferdata tilgjengelige igjen uten i seg selv å starte en nettforespørsel.</p>\n'
              '\n'
              '<h3>Automatiske stasjonsforespørsler og buffer</h3>\n'
              '<p>Automatisk kontroll skjer bare ved en ny registrert direkte innreise for den aktive journalkommandøren til et annet system, for eksempel etter et skips- eller carrierhopp eller en ny bekreftet posisjonsmelding. Oppstart, kommandørbytte, arkivimport eller bare åpning av Explorer eller en systemvisning starter ingen automatisk forespørsel.</p>\n'
              '<p>Den separate stasjonsbufferen bevares ved omstart av Helper. En innhenting som er mindre enn 7 dager gammel, regnes som fersk og hindrer en ny automatisk nettforespørsel. Manglende eller eldre data kan oppdateres ved neste kvalifiserende direkte systeminnreise. Det tillates høyst ett automatisk forsøk per system per lokal kalenderdag; også feil teller, selv etter omstart. Alle lagrede systemer oppdateres ikke kontinuerlig i bakgrunnen. Eldre brukbare bufferdata kan fortsatt vises, også uten nett.</p>\n'
              '<p>Denne bufferen inneholder ekstra stasjonsinformasjon, ikke handelsmarkedspriser. Spansh-fellesskapsdata for salg, kjøp og anbefalinger har sin egen midlertidige søkebuffer i RAM. Handelsmarkedsbilder du selv observerer i Elite, lagres separat igjen: de overlever omstart, men er bare gyldige når de er yngre enn 24 timer.</p>\n'
              '\n'
              '<h3>Oppdatere stasjonsdata manuelt</h3>\n'
              '<p>Åpne «Systemoversikt» og velg «Oppdater Spansh-data». Bare Spansh-stasjonsdata for systemet i dette vinduet oppdateres, ikke alle lagrede systemer eller handelsmarkedspriser. Valget må være aktivert; under en pågående forespørsel for systemet er handlingen deaktivert.</p>\n'
              '<p>Manuell oppdatering kan omgå perioden på 7 dager og et mislykket automatisk forsøk samme dag. Hvis systemet allerede ble hentet med hell i dag etter lokal kalender, sendes ingen ny forespørsel: «Spansh-dataene er allerede oppdatert i dag.» Vellykket innhenting fornyer stasjonsbufferen. Ved feil beholdes lokale og brukbare bufferdata, og statuslinjen viser feilen. Et mislykket manuelt forsøk kan gjentas.</p>\n\n<h3>EDSM-legemedata og hurtigbuffer</h3>\n<p>«Bruk EDSM» styrer også utfyllende legemedata for den aktive journalcommanderens nåværende system i Explorer. Etter «Lagre nettilgang» og ved vanlig journaloppdatering lastes en brukbar hurtigbuffer, eller EDSM forespørres i bakgrunnen. Det offentlige legemeoppslaget krever nettverk, men ingen API-nøkkel; journalopplasting er en egen handling.</p>\n<p>Hentede legemedata lagres lokalt per system og kan brukes fra hurtigbufferen i opptil 24 timer, også etter omstart. Eldre data fører til en ny forespørsel ved en passende oppdatering. Når funksjonen er av, utfyller ikke denne hurtigbufferen visningen, og nye legemeforespørsler startes ikke; filene slettes ikke. Lokale journaldata kan fortsatt brukes. Feil ved henting skaper ingen oppdiktede legemer.</p>\n'
              '\n'
              '<h3>EDSM tilgang for</h3>\n'
              '<p>"EDSM tilgang for:" velger kommandoen som skal redigeres. Valget vil vise '
              '"oppsett" eller "ikke satt opp" avhengig av om en API-Key er lagret.</p>\n'
              '<p>Synlige er sjefsnavn, skjult API-Key-felt, "Bruk EDSM", en tilkoblingstest og '
              'dens siste teststatus.</p>\n'
              '<p>Hver sjef trenger sin egen passende EDSM-tilgang. Valget bytter ikke '
              'direkteopplastingsprogrammet til denne kommandoen.</p>\n'
              '\n'
              '<h3>Bruk og test EDSM</h3>\n'
              '<p>"Bruk EDSM" aktiverer eller deaktiverer tjenesten for den valgte FID. Manglende '
              'eller deaktiverte legitimasjon påvirker ikke behandling av lokal journal.</p>\n'
              '<p>"Test EDSM-tilkobling" sjekker tilgangsdataene som for øyeblikket er synlige i '
              'skjemaet. En vellykket test bekrefter forbindelsen, men endrer ikke den aktive '
              'journalen FID eller live-kommandøren.</p>\n'
              '\n'
              '<h3>Inara tilgang for</h3>\n'
              '<p>"Inara Access for:" følger det samme multi-CMDR-prinsippet. Aktivering, '
              'Inara-kommandørnavn og API-Key lagres separat for hver FID.</p>\n'
              '<p>Også her viser utvalget «oppsett» eller «ikke satt opp». En nøkkel fra en sjef '
              'brukes ikke automatisk for en annen sjef.</p>\n'
              '\n'
              '<h3>Bruk og test Inara</h3>\n'
              '<p>Med Inara satt opp og aktivert for den aktive journalen FID, kan CMDRHelper '
              'overføre støttede reise-, plasserings-, oppdrags- og skipsbegivenheter. Ikke alle '
              'journalhendelser sendes til Inara.</p>\n'
              '<p>"Test Inara-tilkobling" sjekker gjeldende synlige tilgangsdata uten å endre '
              'live-kommandøren.</p>\n'
              '\n'
              '<h3>Inara utboks</h3>\n'
              '<p>Støttede Inara-hendelser flagges konstant i en utboks før '
              'nettverksoverføring.</p>\n'
              '<p>Midlertidige feil gjør at disse oppføringene kan bevares for senere forsøk. '
              'Arbeideren behandler bare utboksen til den unikt aktive journalen FID; Påmeldinger '
              'fra andre befal er ikke inkludert.</p>\n'
              '\n'
              '<h3>Online status i overskriften</h3>\n'
              '<p>EDSM viser for øyeblikket:</p>\n'
              '<ul>\n'
              '<li><b>EDSM</b>– kan ikke brukes eller deaktiveres for den aktive FID</li>\n'
              '<li><b>EDSM venter</b>– oppsett og uten pågående overføring</li>\n'
              '<li><b>EDSM girkasse</b>– siste EDSM-behandlingskjøring ble avsluttet uten feil; '
              'Verktøytipset angir om hendelser ble sendt, journaldata ble behandlet eller ingen '
              'nye data ble funnet</li>\n'
              '<li><b>EDSM feil</b>– siste overføringsstatus er feil</li>\n'
              '</ul>\n'
              '<p>Det er for øyeblikket ingen ekstra, separat merket tilstand "EDSM aktiv" for '
              'EDSM.</p>\n'
              '<p>Inara skiller mer presist:</p>\n'
              '<ul>\n'
              '<li><b>INARA ut</b>– deaktivert for den aktive journalen FID</li>\n'
              '<li><b>INARA klar</b>– satt opp, men fortsatt uten bekreftet overføring i denne '
              'økten</li>\n'
              '<li><b>INARA overføring</b>– arbeideren sender for øyeblikket</li>\n'
              '<li><b>INARA aktiv</b>– den siste faktiske overføringen ble bekreftet</li>\n'
              '<li><b>INARA feil</b>– siste overføringsforsøk mislyktes</li>\n'
              '</ul>\n'
              '\n'
              '<h3>API-Key sikkerhet</h3>\n'
              '<p>API-Key er personlig legitimasjon. Inndatafeltene er skjult; De lagres '
              'kommandorelatert i applikasjonsinnstillingene og ikke i CMDRHelper-databasen.</p>\n'
              '<p>Nøkler skal ikke publiseres, deles i skjermbilder eller legges til offentlige '
              'depoter.</p>\n'
              '\n'
              '<h3>Bilder/skjermbilder</h3>\n'
              '<p>Kildemappe, Destinasjonsmappe, PNG/JPG, Autobehandling, BMP-sletting og '
              'Brightening fra 0 til 50 prosent er utelukkende plassert i hovedmenyen for bilder, '
              'ikke på Innstillinger-siden.</p>\n'
              '<p>Den kontekstsensitive hjelpen «Bilder» beskriver disse alternativene i '
              'detalj.</p>\n'
              '\n'
              '<h3>flate</h3>\n'
              '<p>Grensesnittgruppen inkluderer utseende, språk, font, skriftstørrelse og '
              'verditerskel for verdifulle utforskerkropper.</p>\n'
              '\n'
              '<h3>Mørk og lys modus</h3>\n'
              '<p>Du kan bytte direkte mellom mørkt og lyst utseende. Temaet brukes umiddelbart på '
              'grensesnittet og eksisterende system- og historiekort og lagres.</p>\n'
              '\n'
              '<h3>Språk</h3>\n'
              '<p>Grensesnittet tilbyr tolv språk å velge mellom. "Lagre språk" lagrer valget; En '
              'omstart av CMDRHelper er da nødvendig for en fullstendig enhetlig konvertering av '
              'eksisterende widgets.</p>\n'
              '\n'
              '<h3>Skrift og skriftstørrelse</h3>\n'
              '<p>Skriftfamilie og skriftstørrelse fra 7 til 24 pt kan velges og lagres.</p>\n'
              '<p>Begge endringene vil først tre i full effekt etter en omstart. Grensesnittet '
              'indikerer dette eksplisitt.</p>\n'
              '\n'
              '<h3>Verditerskel</h3>\n'
              '<p>Explorer-verditerskelen bestemmer den estimerte kredittverdien som organer '
              'fremheves som spesielt verdifulle. Endringen lagres umiddelbart og oppdaterer den '
              'tilsvarende Explorer-skjermen.</p>\n'
              '\n'
              '<h3>Skjul automatisk</h3>\n'
              '<p>"Precious Bodies" og "BIO Funs" er godt plassert i venstre sidefelt, ikke på '
              'Innstillinger-siden.</p>\n'
              '<p>Bryterne lagres og kontrollerer de støttede små live hintvinduene under '
              'utforskning. Verditerskelen for verdifulle kropper er satt i '
              'grensesnittinnstillingene.</p>\n'
              '\n'
              '<p>Cargo-vinduet bruker utelukkende Cargo-snapshotet som er bekreftet for den aktive Journal-FID-en. Commanderen som vises i CMDR View, og viewed_commander_id, påvirker ikke dette live-vinduet. For et Ship vises opptatt / maksimum · ledig; hvis CargoCapacity er ukjent, estimeres ingen verdi.</p>\n'
              '<p>«EDSM-status-HUD» under «vis automatisk» er AV som standard. Etter ankomst til et system vises en kort melding over Elite i omtrent 2,5 sekunder. Flere Location-hendelser under samme opphold gir ikke doble meldinger; en faktisk retur kan kontrolleres på nytt.</p>\n<p>«EDSM: KJENT» betyr et gyldig EDSM-treff for systemet. «EDSM: UKJENT» betyr et gyldig EDSM-svar uten systemtreff. «EDSM: INGEN SVAR» betyr nettverksfeil, HTTP-feil, tidsavbrudd eller ugyldig svar, aldri et bekreftet manglende treff. Kjennskap i EDSM er ikke det samme som offisiell oppdagelse i Elite; navn på første oppdager eller innmelder loves ikke.</p>\n<p>Meldingen virker uavhengig av navigasjons- og laste-HUD. Permanente HUD-visninger og hurtigfavorittmeldinger beholdes. Forespørselen blokkerer ikke grensesnittet; forsinkede svar for systemer du har forlatt, forkastes.</p>\n\n'
              '<p>Bryterne under «vis automatisk» i sidefeltet virker uavhengig: «Verdifulle legemer», «BIO-funn», «GEO» og «Lasterom» styrer sine respektive sanntidsvinduer. «Lasteroms-HUD» viser last i overlegget, «Navigasjons-HUD» aktiv planetnavigasjon. Disse visningsbryterne starter ikke selv nettforespørsler; HUD krever Elite i forgrunnen og passende data.</p>\n<p>«EDSM-status-HUD» krever derimot en egen offentlig EDSM-nettforespørsel, uavhengig av «Bruk EDSM», legemehurtigbufferen og en API-nøkkel. Inara-opplasting og Spansh-stasjonsinformasjon har egne tjenestebrytere; HUD-bryterne aktiverer dem ikke.</p>\n\n<h3>Oppdateringer</h3>\n'
              '<p>Oppdateringsgruppen viser installert versjon og GitHub-status. Sjekk nå ser '
              'manuelt etter en ny planlagt CMDRHelper-versjon; I tillegg skjer det en forsinket '
              'automatisk kontroll etter start.</p>\n'
              '<p>Hvis en ny versjon er tilgjengelig, vil CMDRHelper spørre før du laster ned og '
              'installerer. En annonsert databaseoppdatering vises separat i denne '
              'dialogboksen.</p>\n'
              '<p>For eksisterende installasjoner holder det normalt å installere oppdateringen → starte CMDRHelper. Nødvendige historiske rettelser av BIO-data, besøk og DSS-metadata utføres automatisk; databasen sikkerhetskopieres før reparasjoner som skriver data. Reparasjonene er versjonerte og idempotente: vellykkede revisjoner kjøres ikke fullstendig på nytt ved hver start. Rekonstruksjon krever Elite-journaler som fortsatt finnes, kan leses og entydig kan knyttes til en commander. Manglende kilder blir ikke oppdiktet eller regnet som suksess; uferdige reparasjoner forsøkes igjen ved neste start. Sletting av databasen, manuelle skript og ny import er normalt unødvendig.</p>\n\n'
              '<h3>Last ned fremdrift</h3>\n'
              '<p>Nedlastingen kjører i bakgrunnen. Hvis den totale størrelsen er kjent, viser '
              'CMDRHelper filnavn, mottatt og total MiB, prosent, overføringshastighet og estimert '
              'gjenværende tid.</p>\n'
              '<p>Uten en kjent totalstørrelse fungerer fremdriftslinjen i opptatt-modus og '
              'fortsetter å vise mengden data som mottas og - hvis det kan bestemmes - '
              'hastigheten. Før installasjonen sjekkes nedlastet ZIP.</p>\n'
              '\n'
              '<h3>Avbryt oppdatering</h3>\n'
              '<p>"Avbryt nedlasting" avslutter en pågående nedlasting på en kontrollert måte. En '
              'avbrutt, ufullstendig eller ugyldig nedlasting vil ikke bli installert.</p>\n'
              '\n'
              '<h3>Oppdater på Windows</h3>\n'
              '<p>På Windows fortsetter selve oppdateringsprosessen uavhengig av den opprinnelige '
              'startkonsollen. En konsollavstenging bør derfor ikke utilsiktet avslutte den.</p>\n'
              '<p>Hvis det oppstår en feil etter at filendringer har begynt, forsøker den '
              'eksisterende sikkerhetskopieringen å gjenopprette den forrige versjonen.</p>\n'
              '\n'
              '<h3>Start på nytt etter oppdatering</h3>\n'
              '<p>Etter vellykket installasjon starter oppdateringsprogrammet CMDRHelper på nytt '
              'via den tiltenkte startbanen og sjekker kort om den nye prosessen kjører '
              'stabilt.</p>\n'
              '<p>Hvis en utgivelse krever en engangsoppdatering av databasen, vil journalarkivet '
              'også bli revurdert etter omstart.</p>\n'
              '\n'
              '<h3>Flere befal</h3>\n'
              '<p><b>Valg av innstillinger = Hvem sin nettilgang redigerer jeg?</b></p>\n'
              '<p><b>Active Journal-FID = Hvem har lov til å sende direkte?</b></p>\n'
              '<p>Verken nettkontovalget eller CMDR-visningen har tillatelse til å bytte en '
              'direkteopplastingsmaskin til en visningskommandør.</p>\n'
              '\n'
              '<h3>Hjelp</h3>\n'
              '<p>"? Hjelp" er plassert i venstre sidefelt over "auto show" og åpner hjelpen til '
              'hovedmenyområdet som er synlig for øyeblikket.</p>\n'
              '<p>I "Innstillinger"-området åpner knappen denne innstillingshjelpen direkte.</p>\n'
              '\n'
              '<h3>Tips</h3>\n'
              '<p>Hvis du installerer på nytt eller har problemer, sjekk først:</p>\n'
              '<ul>\n'
              '<li>riktig journalmappe og anerkjent befalsidentitet</li>\n'
              '<li>ønsket språk, tema, font og utforskerverditerskel</li>\n'
              '<li>Online tilgang til riktig FID</li>\n'
              '<li>I tilfelle bildeproblemer, kilde- og målmapper i hovedmenyen "Bilder".</li>\n'
              '</ul>\n'
              '<p>Hvis det er flere sjefer, vær alltid oppmerksom på hvilken FID de synlige '
              'nettilgangsdataene gjelder for.</p>'),
    "planet_navigation": (
        'Planetnavigasjon',
        """<h2>Planetnavigasjon</h2>
<p>Planetnavigatoren hjelper deg utelukkende med å fly til en bestemt breddegrad/lengdegrad på en planet eller måne. Du angir et koordinatmål og får avstand og retning dit.</p>
<p>Den er ikke en interstellar ruteplanlegger og håndterer verken system- eller hoppnavigasjon. Du styrer skipet selv.</p>

<h3>Åpne navigatoren og angi et mål</h3>
<p>Åpne «Planetnavigasjon» i Explorer og velg «Manuell inntasting …». Vinduet kan åpnes og et mål angis før en aktuell overflateposisjon er tilgjengelig.</p>
<ul>
<li><b>Himmellegeme:</b> Velg målplaneten eller målmånen fra listen, eller bruk himmellegemet som allerede er registrert. Du kan også skrive inn navnet selv hvis det ikke finnes i listen ennå. Er du i tvil, bruk hele navnet, inkludert systemnavnet.</li>
<li><b>Breddegrad:</b> Angi målets breddegrad mellom −90° og +90°.</li>
<li><b>Lengdegrad:</b> Angi målets lengdegrad mellom −180° og +180°. Pass på fortegnet til begge koordinatene.</li>
<li><b>Målnavn:</b> Du kan valgfritt angi en betegnelse for å kjenne igjen målet lettere.</li>
</ul>
<p>Med «Sett mål» bekrefter du opplysningene. Du trenger ikke å angi tekniske ID-er som BodyID og SystemAddress; de er ikke vanlige brukeropplysninger.</p>

<h3>Når starter kompasset?</h3>
<p>Så snart et mål er satt og Elite leverer gyldige planetære posisjonsdata for det tilsvarende himmellegemet, blir navigasjonen automatisk aktiv. Du trenger ikke å trykke på en egen startknapp.</p>
<p>Hvis disse dataene fortsatt mangler eller gjelder et annet himmellegeme, venter navigatoren med «Venter på planetkoordinater …». Du kan angi et mål allerede før disse dataene kommer.</p>

<p>Aktiv navigasjon krever gyldige koordinater, legemenavn, retning og planetradius fra Elite for mållegemet. Landing kreves ikke: data kan komme under innflyging. Uten gyldig posisjon eller på et annet legeme venter navigatøren uten å finne på en posisjon.</p>

<h3>Lagre nåværende sted</h3>
<p>«★ Lagre nåværende posisjon» lagrer din bekreftede nåværende posisjon, ikke navigasjonsmålet du skrev inn. Gyldig Elite-posisjon, identifisert kommandør og kjent system kreves. Ellers er handlingen deaktivert eller en melding vises.</p>
<p>System, legeme og koordinater fryses når handlingen åpnes. I favorittdialogen kan du endre navn, kategori og notat og legge til et bilde. Først «Lagre» lagrer lokalt for kommandøren; avbryt lagrer ingenting. Senere bevegelser endrer ikke den fryste posisjonen.</p>

<h3>Bruke lagrede posisjoner</h3>
<p>Åpne «★ Favoritter» i Explorer. Velg et lagret overflatested og «◎ Til koordinatene» for å bruke legeme, koordinater og navn som mål. Det erstatter forrige mål; på et annet legeme venter navigatøren på passende posisjonsdata.</p>
<p>«Rediger» endrer navn, kategori og notat. «Slett» fjerner favoritten etter bekreftelse, ikke Elite-data. Favoritter bevares ved omstart og er skilt etter kommandør; selve navigasjonsmålet gjelder bare denne økten.</p>

<h3>Planetkule: mer enn 380 km</h3>
<p>Når målavstanden er større enn 380 km, viser navigatoren planetkulen.</p>
<ul>
<li>Den <b>hvite sirkelen</b> markerer din egen posisjon.</li>
<li>Det <b>lille målpunktet</b> er oransje når målet ligger på den synlige siden av planeten.</li>
<li>Hvis målet ligger på den skjulte baksiden, vises målpunktet i rødt.</li>
<li>Posisjonen din står fast i visningen. Planeten og målet vises i forhold til posisjonen og orienteringen din.</li>
</ul>
<p>Den hvite pilen peker fremover; den gule pilen viser den relative retningen til målet. Kulen er en skjematisk orienteringshjelp, ikke en geografisk nøyaktig terrengvisning. Et rødt punkt betyr baksiden av kulen, ikke automatisk «bak skipet ditt».</p>

<h3>Perspektivrutenett: til og med 380 km</h3>
<p>Ved en målavstand på opptil og med 380 km bytter visningen automatisk til et skråstilt perspektivrutenett. Hvis avstanden igjen øker til over 380 km, kommer kulen tilbake.</p>
<p>Tverrlinjene danner et <b>avstandsrutenett med 50 km mellom linjene</b>. Målpunktet tegnes i rutenettet ut fra avstand og relativ retning. Perspektivet hjelper deg videre i innflygingen; helningen får avstandene til å se tettere ut bakover. For den faktiske kursen du skal styre, følg også med på målkurs og relativ retning.</p>

<h3>Lese navigasjonsverdiene riktig</h3>
<ul>
<li><b>Målavstand:</b> Den store visningen viser gjenværende avstand til målet langs den tenkte planetoverflaten.</li>
<li><b>Målkoordinater:</b> Koordinatparet som er angitt for målet, først breddegrad, deretter lengdegrad. Det forblir uendret mens du beveger deg.</li>
<li><b>Nåværende koordinater:</b> Ditt sist bekreftede koordinatpar fra Elite, også breddegrad / lengdegrad.</li>
<li><b>Avstand langs overflaten:</b> Samme overflateavstand som målavstanden, eventuelt mer nøyaktig avrundet i detaljvisningen. Dette er ikke en annen rute eller en direkte romlig avstand gjennom luften.</li>
<li><b>Peiling:</b> Den absolutte retningen til målet fra din nåværende posisjon, som kompassvinkel: 000° er nord, 090° øst, 180° sør og 270° vest.</li>
<li><b>Styrekurs:</b> Din nåværende orientering slik Elite oppgir den. Den viser hvilken vei du peker nå, og trenger ennå ikke å samsvare med peilingen.</li>
<li><b>Relativ retning:</b> Forskjellen mellom orienteringen din og peilingen, for eksempel «23° høyre», «10° venstre» eller «Rett frem». Ved 180° er målet bak deg.</li>
<li><b>Målkurs:</b> Den fremhevede peilingen som en absolutt kurs du kan dreie til i Elite-HUD-en. Den er ikke en ekstra dreievinkel.</li>
</ul>
<p>Eksempel: Med styrekurs 051° og målkurs 074° dreier du 23° til høyre til Elite-kompasset viser omtrent 074°. Mens du flyr videre, kan peiling og målkurs endre seg; følg de oppdaterte verdiene.</p>
<p>På samme posisjon som målet, ved en pol eller på det nøyaktig motsatte punktet på planeten kan retningen være ubestemt. Da viser navigatoren den tilsvarende meldingen i stedet for en oppdiktet kurs.</p>

<h3>Vindusstørrelse</h3>
<p>Navigatorvinduet kan fritt endres i størrelse. Kulen eller perspektivrutenettet tilpasser seg proporsjonalt til den tilgjengelige plassen. Minimumsstørrelsen holder detaljverdiene lesbare; kulen forblir rund. Vinduets posisjon og størrelse lagres.</p>

<h3>Slå på navigasjons-HUD</h3>
<p>Til venstre i hovedvinduet krysser du av under <b>vis automatisk → Navigasjons-HUD</b>. Ved gyldig planetnavigasjon vises HUD-en direkte over det synlige Elite-vinduet i forgrunnen.</p>
<p>Den viser tre linjer:</p>
<ul>
<li>relativ retning</li>
<li>målkurs</li>
<li>avstand</li>
</ul>
<p>HUD-en er gjennomsiktig, slipper klikk gjennom og tar ikke fokus: den dekker ikke spillet med en ugjennomsiktig flate, fanger ikke opp museklikk og tar ikke inndatafokus fra Elite når den vises automatisk.</p>
<p>Uten gyldig navigasjon eller en entydig retning blir den automatisk usynlig. Den skjules også hvis Elite er minimert eller ikke er i forgrunnen. Avkryssingen i sidefeltet kan likevel være på; den angir ønsket ditt om automatisk visning, ikke den aktuelle synligheten.</p>
<p>HUD-en er bare en ekstra visning. Den vanlige navigatoren fungerer uavhengig av den, også når HUD-en er avslått eller utilgjengelig.</p>

<h3>Sette et nytt mål</h3>
<p>På samme himmellegeme kan du når som helst åpne «Manuell inntasting …» på nytt og sette andre koordinater. Det nye målet erstatter det forrige navigasjonsmålet. Med tilsvarende posisjonsdata oppdateres kompasset umiddelbart.</p>
<p>Med «Avslutt navigasjon» fjerner du det nåværende målet. For en ny innflyging setter du ganske enkelt et nytt mål.</p>

<p>Å lukke vinduet fjerner ikke målet. En aktivert navigasjons-HUD kan fortsette; «Avslutt navigasjon» fjerner målet. Når du forlater riktig legeme eller mangler posisjonsdata, venter navigasjonen og navigasjons-HUD-en skjules.</p>

<h3>Dataenes alder og begrensninger</h3>
<p>Navigasjonen bygger på statusdataene fra Elite. Oppdateringer kan komme forsinket avhengig av spilltilstanden. Aldersvisningen i navigatoren viser hvor lenge det er siden den siste bekreftede statusmeldingen.</p>
<p>Overflateavstanden beskriver den korteste buen på en tenkt kule. Den er ikke en terreng- eller veirute. Navigatoren kjenner verken hindringer eller terrenghøyder langs strekningen; flyhøyde, trygg hastighet og å unngå hindringer er fortsatt ditt ansvar.</p>

<p>Posisjonen kommer fra Status.json; journalen supplerer koblinger til legeme og system. Vinduet og aktivert navigasjons-HUD holder oppdateringer aktive ved behov. Visningen avhenger av tilgjengelige Elite-data, uten garantert nøyaktighet i meter.</p>

<h3>Tips</h3>
<p>Før innflygingen kontrollerer du navnet på himmellegemet og fortegnene til målkoordinatene. Still deg deretter inn på målkursen i Elite-kompasset og følg med på relativ retning og avstand. Hvis navigatoren venter, sjekk om Elite allerede leverer planetkoordinater for himmellegemet du skal til.</p>""",
    ),
}

DIALOG_TITLE = 'Hjelp – {area}'
CLOSE_LABEL = 'Lukk'


# Database update guidance; help itself remains version independent.
HELP_TOPICS["overview"] = (HELP_TOPICS["overview"][0], HELP_TOPICS["overview"][1] + '<h3>Databaseoppdatering kreves</h3><p>Databaseoppdateringen retter eldre lagrede forhold mellom stjerner, planeter og måner. Journalene blir bare lest. Avslutt Elite Dangerous først og gjør historiske journaler tilgjengelige hvis mulig. Hele CMDRHelper-databasen sikkerhetskopieres på forhånd; ved feil rulles endringene tilbake, og sikkerhetskopien gjenopprettes om nødvendig. Kopien beholdes for sikkerhets skyld. Avbryt lar deg utsette oppdateringen.</p>')

HELP_TOPICS["settings"] = (HELP_TOPICS["settings"][0], HELP_TOPICS["settings"][1] + '<h3>Diagnostikk og logger</h3><p>Under Innstillinger → Diagnostikk og logger kan du åpne loggfilen eller opprette en diagnosepakke. Loggene ligger i logs/ i installasjonsmappen (cmdrhelper.log og opptil fire eldre filer). ZIP-filen inneholder rensede tekniske logger, system_info.json og diagnose_summary.txt; ingen journaler, database, FID-/kommandørdata, påloggingsopplysninger, favoritter eller bilder. Personlige stier erstattes med plassholdere. Innholdet i gamle logger fra før personvernfiltreringen utelates. Velg hvor ZIP-filen skal lagres, og del den med brukerstøtte ved behov; den sendes aldri automatisk.</p>')

HELP_TOPICS["trade"] = (
    'Handel',
    """<h2>Handel</h2>
<h3>Handel i korte trekk</h3>
<p>«Selg» finner markeder som kjøper varen din. «Kjøp» finner en bestemt vare å kjøpe. «Anbefalinger» viser hva du kan kjøpe på den nåværende stasjonen og selge videre med fortjeneste innenfor dine krav.</p>

<h3>Markedsdata og alder</h3>
<p>Salg og kjøp kombinerer automatisk gyldige lagrede egne markedsobservasjoner med fellesskapets markedsdata gjennom Spansh. Anbefalinger kjøper utelukkende på ditt nåværende observerte Elite-marked; mål kommer normalt fra egne observasjoner og Spansh. Fellesskapets resultater lagres bare midlertidig i minnet.</p>
<p>Alle markedsdata er øyeblikksbilder, også egne observasjoner. Pris, tilbud og etterspørsel kan endre seg før ankomst. Sjekk alderen: verken tilgjengelighet eller fortjeneste er garantert.</p>
<p>Hvis det samme markedet er kjent fra din egen observasjon og fra fellesskapet, bruker CMDRHelper det nyeste gyldige øyeblikksbildet.</p>

<h3>Velge en vare</h3>
<p>Klikk på «Handelsvare», søk etter vist navn, engelsk navn eller symbol, og velg varen. Tyske navn kommer fra den vedlikeholdte tyske varekatalogen. Mangler en tilgjengelig oversettelse, vises det engelske katalognavnet eller en lesbar betegnelse.</p>

<h3>Selg</h3>
<p>Søket bruker både gyldige egne markedsobservasjoner og fellesskapets markedsdata. Velg vare, «Mengde (t)» og filtre, deretter «Finn beste salg». Søket finner kjøpstilbud med nok etterspørsel til den angitte mengden. «Pris / t» er prisen du får ved salg. «Mulig inntekt» = pris × angitt mengde. Utgangspunktet er kommandørens nåværende system. Høyeste salgspris vises først som standard.</p>

<h3>Kjøp</h3>
<p>Søket bruker både gyldige egne markedsobservasjoner og fellesskapets markedsdata. Velg vare, ønsket mengde og filtre, deretter «Finn billigste kjøp». Rapportert «Tilbud» må dekke hele mengden. «Pris / t» er din kjøpspris; «Totalkostnad» = pris × ønsket mengde. Utgangspunktet er systemet du er i. Laveste kjøpspris vises først som standard. Dette er et søk etter en bestemt vare, ikke en anbefaling om fortjeneste.</p>

<h3>Filtre og resultattabeller</h3>
<ul>
<li><b>Radius (ly):</b> maksimal avstand fra utgangssystemet til målsystemet.</li>
<li><b>Maksimal alder på markedsdata / Alder på måldata:</b> høyeste tillatte alder på markedsdata; for anbefalinger gjelder dette målet.</li>
<li><b>Landingsplattform:</b> minste nødvendige landingsplass, ikke en nøyaktig stasjonsstørrelse. «Middels» tillater også store plasser; «Alle» begrenser ikke størrelsen.</li>
<li><b>Inkluder Fleet Carriers:</b> tillat eller utelukk hangarskip.</li>
<li><b>Maks. innflygingsavstand (Ls):</b> maksimal avstand fra ankomststjernen til stasjonen. Tomt felt betyr ingen begrensning. Et mål med ukjent ankomstavstand oppfyller ikke dette filteret.</li>
</ul>
<p>Egne resultater og fellesskapets resultater bruker de samme filtrene for dataalder, radius, landingsplattform, carriers og ankomstavstand. Manglende opplysninger blir ikke anslått. Mål uten kjent systemavstand eller dokumentasjon på at en aktiv begrensning er oppfylt, utelukkes. For egne markeder gjelder dette særlig manglende landingsplass- og ankomstdata; når hangarskip utelukkes, må det være kjent at målet ikke er et hangarskip.</p>
<p>Klikk på kolonneoverskrifter for å sortere: tall etter tallverdi, dataalder etter faktisk alder og landingsplasser etter størrelsesklasse. Salg og kjøp viser maksimalt 100 treff. «Det finnes flere treff. Begrens filtrene.» varsler om et begrenset søk. Tilgjengelige egne resultater og fellesskapets resultater sorteres sammen etter pris før listen begrenses. På grunn av søkegrensene til fellesskapstjenesten er dette ikke garantert de beste tilbudene totalt sett.</p>
<p>Hvis fellesskapssøket mislykkes ved salg eller kjøp, er passende egne resultater fortsatt brukbare. CMDRHelper markerer da søket som ufullstendig: bedre tilbud fra fellesskapet kan mangle.</p>

<h3>Egne markedsdata</h3>
<p>Åpne varemarkedet i Elite mens du er dokket. Når CMDRHelper kjører, registrerer det markedet automatisk dersom tilknytningen til den nåværende stasjonen er sikker. Ingen manuell import er nødvendig. Åpning på nytt oppdaterer øyeblikksbildet.</p>
<p>Ett aktuelt øyeblikksbilde beholdes per marked og kommandør, yngre enn 24 timer. Eldre bilder fjernes automatisk; ingen varig prishistorikk lagres. Gyldige egne observasjoner overlever omstart av Helper. «Egne markedsdata: X stasjoner» teller den aktive kommandørens gyldige observerte stasjonsmarkeder. Den valgte maksimale alderen på markedsdata gjelder også for egne resultater.</p>
<ul>
<li><b>✓ Lest inn:</b> Under anbefalinger finnes et gyldig eget øyeblikksbilde for den nåværende stasjonen.</li>
<li><b>Åpne varemarkedet:</b> Stasjonen mangler et brukbart eget øyeblikksbilde.</li>
<li><b>Markedsdata utdaterte:</b> Et tidligere vist øyeblikksbilde er ikke lenger gyldig. Åpne markedet på nytt.</li>
</ul>
<p>Hvis et gammelt øyeblikksbilde ble fjernet før visningen ble åpnet, vises også «Åpne varemarkedet». Under flyging vises ingen positiv status for forrige stasjon.</p>

<h3>Anbefalinger</h3>
<p>Du trenger en nåværende stasjon, dens gyldige egne øyeblikksbilde og et kjent nåværende skip med sikkert kjent ledig lasteplass. Opptatt plass trekkes fra. Med ukjent eller full lasteplass kan et nytt søk ikke starte; mengder blir ikke funnet på. Etter avgang gjøres ingen ny beregning ut fra det gamle oppholdsstedet.</p>
<p>Still inn «Minste fortjeneste»: 10 % tar bare med muligheter med minst 10 % margin. Det søkes etter varer som tilbys lokalt. Kjøpsstasjonen er ikke selv et mål. For samme målstasjon (samme MarketID) brukes det nyeste gyldige øyeblikksbildet. Hver vare viser det kontrollerte målet med høyest «Mulig fortjeneste» innenfor filtrene, ikke nødvendigvis galaksens beste. Tabellen starter med høyeste mulige fortjeneste; «Kilde» viser «Elite lokalt» eller «Spansh», og «Alder på måldata» viser alderen på målets markedsdata.</p>

<h3>Bare egne markedsdata</h3>
<p>Denne avkrysningsboksen finnes bare under Anbefalinger. Salg og kjøp bruker automatisk begge kilder. Avkryssingen begrenser anbefalingene til gyldige målmarkeder du selv har observert. Ingen fellesskapsdata hentes; Spansh er ikke nødvendig. Radius, ekstra aldersgrense for måldata, minste fortjeneste samt landingsplass-, hangarskip- og ankomstfiltre gjelder fortsatt og må kunne oppfylles ut fra tilgjengelige opplysninger. Å utelate fellesskapssøket med vilje er ingen feil og gjør ikke søket ufullstendig. Slik kan du søke raskt mellom allerede besøkte stasjoner.</p>

<h3>Mulig fortjeneste og mengde</h3>
<ul>
<li><b>Fortjeneste / t:</b> salgspris ved målet − kjøpspris her. «Fortjeneste %» = fortjeneste per tonn ÷ kjøpspris × 100.</li>
<li><b>Mengde (t):</b> den minste av ledig lasteplass, tilbudet på kjøpsmarkedet og etterspørselen ved målet.</li>
<li><b>Mulig fortjeneste:</b> fortjeneste per tonn × mulig mengde; et anslag basert på kjente øyeblikksbilder.</li>
</ul>
<p>Eksempel: 280 t ledig, 150 t tilbud, 20 000 t etterspørsel → 150 t mulig mengde. Ikke alle varer kan automatisk fylle hele den ledige lasteplassen.</p>

<h3>Husket handelsflyvning</h3>
<p>Kryss av for å huske nøyaktig én anbefaling. Et annet valg erstatter den. Det separate notatet viser vare, målstasjon, målsystem og «Mulig fortjeneste» på valgtidspunktet. Det er en huskelapp, ikke en anbefaling som beregnes på nytt fortløpende.</p>
<p>Notatet beholdes ved kjøp, lastendring, avgang, systembytte, dokking og markedsåpning. Det forsvinner med «Fjern» eller ved å fjerne krysset, når et nytt anbefalingssøk faktisk starter, ved kommandørbytte og når Helper avsluttes. Det lagres ikke over en omstart.</p>
<p>«Kopier system» kopierer bare navnet på målsystemet til utklippstavlen. Målstasjonen forblir synlig i notatet; ingen rute opprettes.</p>

<h3>Søk, fremdrift og avbrudd</h3>
<p>Start søk manuelt. Anbefalinger kontrollerer flere varer og kan ta lengre tid. Når omfanget er kjent, viser fremdriftslinjen og «Kontrollerer varer: x av y …» faktisk kontrollerte varer. «Avbryt» er bare tilgjengelig under et søk som kan avbrytes; et pågående nettverkssvar kan forsinke avbruddet. Fanebytte avbryter søket; felles filtre for salg/kjøp beholdes.</p>
<p>Hvis enkelte fellesskapsforespørsler mislykkes eller søkegrenser nås, kan gyldige kontrollerte anbefalinger bli stående. Et ufullstendig søk betyr at treffene gjelder kontrollerte data, men ikke alle varer eller mål er fullstendig undersøkt. Les meldingen, snevr inn filtrene ved søkegrenser eller prøv igjen senere. Et manuelt avbrudd forkaster den aktuelle resultatlisten.</p>

<h3>Diagnostikk ved problemer</h3>
<p>«Kopier diagnostikk» kopierer tekniske opplysninger fra siste avsluttede anbefalingssøk til feilsøking. Teksten inneholder ingen kommandør-/FID-data eller markedspriser. Diagnostikken forblir i minnet; ingen varig diagnostikkfil opprettes og ingenting sendes automatisk. Del selv den kopierte teksten med brukerstøtte ved behov.</p>

<h3>Slik gjennomfører du en handelsrunde</h3>
<ol>
<li>Dokk på en stasjon og åpne varemarkedet i Elite.</li>
<li>Åpne «Handel» → «Anbefalinger» og se etter «Lest inn».</li>
<li>Still inn minste fortjeneste og filtre, og velg «Søk etter anbefalinger».</li>
<li>Kryss av anbefalingen du vil huske, og kjøp varen i Elite.</li>
<li>Bruk «Kopier system» ved behov og fly til målet; stasjonen forblir synlig i notatet.</li>
<li>Selg i Elite. Åpne markedet der for også å oppdatere dine egne data om det nye markedet.</li>
</ol>""",
)


HELP_TOPICS["explorer"] = (
    HELP_TOPICS["explorer"][0],
    HELP_TOPICS["explorer"][1] + '<h3>FØRSTE FOTAVTRYKK</h3><p>FØRSTE FOTAVTRYKK vises i gult i himmellegemets statuskolonne, sammen med kartleggingsstatusen. CMDRHelper utleder det fra tilgjengelige Elite-journaler, uavhengig av biologiske funn. Ingen innlevering til Universal Cartographics eller Vista Genomics er nødvendig; salg endrer ikke gult til grønt.</p>',
)


HELP_TOPICS["explorer"] = (
    HELP_TOPICS["explorer"][0],
    HELP_TOPICS["explorer"][1] + '<p>«Tilpass til vindusbredden» fordeler verdilistens kolonner automatisk over den tilgjengelige bredden. Valget er på som standard og lagres. Svært smale vinduer eller stor skrift kan fortsatt kreve vannrett rulling. Når valget er av, kan breddene justeres manuelt. Dette er uavhengig av automatisk tilpasning av den grafiske oversikten.</p>',
)
