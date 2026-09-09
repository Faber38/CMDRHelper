"""Norwegian content for contextual help."""


HELP_TOPICS = {
    "materials": (
        'Materialer',
        """<h2>Materialer</h2>
<h3>CMDRHelper v3.2</h3>
<p>Materialoversikt for engineering: alle 146 materialer i Raw, Manufactured og Encoded, med grader, kapasitet og unntak. Oppdatert beholdning per commander, søk, filtre, fem diskrete radbakgrunner og lagrede kolonnebredder og rekkefølge gir oversikt. Ukjent beholdning skilles fra null.</p>
<p>Odyssey-beholdning: den fjerde materialfanen inneholder 223 katalogidentiteter for varer, komponenter, data og forbruksvarer. Skipslager, ryggsekk og pålitelig total holdes atskilt; oppdragsstabler, oppdragsstatus og engineering-bruk vises. Positive antall er gullfargede. Navn uten oversettelse vises på engelsk.</p>
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
<p>Den fjerde fanen under Materialer inneholder Varer, Komponenter, Data og Forbruksvarer. Skipslager og Ryggsekk viser beholdningene hver for seg. Totalt viser summen bare når begge tilstandene passer pålitelig sammen. En utdatert ryggsekkbeholdning blir bevisst ikke vist som aktuell eller lagt til totalen; ? betyr ukjent beholdning eller beholdning som for øyeblikket ikke kan rekonstrueres pålitelig. Grensen på 1000 gjelder hver skipslagerkategori, ikke enkeltgjenstander. Eksemplet for ingeniørmaterialer ovenfor definerer ikke et individuelt maksimum for Odyssey-gjenstander. Forbruksvarer har fortsatt ingen fullstendig validert kapasitetsregel, så ingen ubekreftet kapasitet vises.</p>
<p>Bruk viser gjenstandens bruksmerking. Oppdrag betyr at den konkrete beholdningsstabelen er knyttet til et oppdrag, ikke at gjenstandstypen generelt er en oppdragsgjenstand. Vanlige og oppdragsbundne stabler holdes atskilt. Også etter at oppdraget er fullført, forblir gjenstanden merket så lenge journalen fører den i beholdningen; fullføring fjerner den ikke automatisk. Verktøytipset viser oppdragsnummeret og kjent status. Ingeniørarbeid betyr at den statiske Odyssey-katalogen kjenner minst én bekreftet bruk: draktoppgradering, våpenoppgradering, draktmodifikasjon, våpenmodifikasjon eller opplåsing av en ingeniør. De enkelte bruksområdene vises i verktøytipset. Manglende merking betyr ikke at gjenstanden er ubrukelig eller bare kan handles. Powerplay-gjenstander og andre spesialgjenstander kan også vises.</p>
<p>Søket finner de viste lokale og engelske material-/gjenstandsnavnene. De seks Odyssey-filtrene er Alle (alle gjenstander), Oppdrag (stabler knyttet til et oppdrag), Ingeniørarbeid (gjenstander med bekreftet ingeniørbruk), Ryggsekk (ryggsekkbeholdning større enn null), Skipslager (lagerbeholdning større enn null) og Beholdning 0 (pålitelig kjent totalbeholdning på 0). Ukjent beholdning ? er ikke 0 og tas ikke med i Beholdning 0. Manglende navneoversettelser erstattes med det engelske navnet, så enkelte navn kan fortsatt vises på engelsk i det valgte språket. Dette er tilsiktet og er ingen oversettelsesfeil i beholdningslogikken.</p>
<p>Beholdningen oppdateres automatisk i bakgrunnen. Bekreftede nye innsamlinger kan markeres kort. Ved bytte av commander fjernes gamle beholdninger umiddelbart. Underfaner, filtre, kolonnebredder og kolonnerekkefølge lagres separat for Odyssey.</p>""",
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
              '<h3>tidsskrift</h3>\n'
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
              '<p>"Oppdrag"-knappen eller menyelementet tar deg til hele oppdragsvisningen med '
              'kjente oppdragsmål og statusinformasjon.</p>\n'
              '\n'
              '<h3>Siste stand</h3>\n'
              '<p>"Siste tilstand" oppsummerer den siste kjente vedvarende sjefstilstanden. Dette '
              'gjør at viktig informasjon kan gjenopprettes selv etter omstart av Elite Dangerous '
              'eller CMDRHelper.</p>\n'
              '\n'
              '<h3>Endelige systemer</h3>\n'
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
              '<h3>Tupp</h3>\n'
              '<p>Hvis fartøysjefen, skipet eller plasseringen ikke samsvarer med gjeldende status '
              'i spillet, sjekk først journalvisningen øverst og sjekk deretter journalmappen satt '
              'under "Innstillinger".</p>'),
 'missions': ('Oppdrag',
              '<h2>Oppdrag</h2>\n'
              '<p>Oppdragsvisningen viser oppdragene til den nåværende sjefen som er kjent fra '
              'Elite Dangerous Journal. CMDRHelper lagrer oppdragsdata på '
              'kommando-for-kommando-basis, slik at åpne oppdrag beholdes selv etter en omstart av '
              'Elite Dangerous eller CMDRHelper.</p>\n'
              '\n'
              '<h3>Åpne oppdrag</h3>\n'
              '<p>Nye oppdrag kommer ut<code>MissionAccepted</code>overtatt og lagret '
              'permanent.</p>\n'
              '<p>Så lenge det ikke er noen endelig oppdragshendelse, forblir oppdraget åpent. En '
              'ny spilløkt uten oppdragsliste vil kanskje ikke automatisk fjerne kjente åpne '
              'oppdrag.</p>\n'
              '\n'
              '<h3>Oppdragsstatus</h3>\n'
              '<p>CMDRHelper behandler blant annet følgende statusendringer:</p>\n'
              '<ul>\n'
              '<li>Oppdrag akseptert</li>\n'
              '<li>Oppdraget fullført</li>\n'
              '<li>Oppdraget mislyktes</li>\n'
              '<li>Oppdraget ble avbrutt</li>\n'
              '<li>Oppdragsmålet omdirigert</li>\n'
              '<li>Fremgang på støttede last-/depotoppdrag</li>\n'
              '</ul>\n'
              '<p>En siste hendelse endrer bare det tilknyttede oppdraget.</p>\n'
              '\n'
              '<h3>Oppdrag fra tidsskriftet</h3>\n'
              '<p>Elite Dangerous gir oppdragsinformasjon om ulike journalbegivenheter. CMDRHelper '
              'slår sammen disse hendelsene til en vedvarende oppdragstilstand.</p>\n'
              '<p>En ekte oppdragsbegivenhet kan tjene som et autoritativt øyeblikksbilde. Hvis et '
              'slikt arrangement mangler, vil ikke eldre åpne oppdrag bli stengt bare av denne '
              'grunn.</p>\n'
              '\n'
              '<h3>Destinasjoner og steder</h3>\n'
              '<p>I den grad Elite gir informasjonen i journalen, viser CMDRHelper:</p>\n'
              '<ul>\n'
              '<li>Målsystem</li>\n'
              '<li>Destinasjonsstasjon eller destinasjon</li>\n'
              '<li>Målplanet eller kropp</li>\n'
              '<li>Oppdragsbetegnelse</li>\n'
              '<li>kjent fremgang</li>\n'
              '<li>nåværende status</li>\n'
              '</ul>\n'
              '<p>Ikke alle oppdrag gir all informasjon. Manglende data er ikke oppfunnet av '
              'CMDRHelper.</p>\n'
              '\n'
              '<h3>Utholdenhet og start på nytt</h3>\n'
              '<p>Åpne oppdrag lagres i den sjefsrelaterte databasen.</p>\n'
              '<p>Dette betyr at de beholdes selv om:</p>\n'
              '<ul>\n'
              '<li>Elite Dangerous avsluttes og startes på nytt senere</li>\n'
              '<li>CMDRHelper er stengt i mellom</li>\n'
              '<li>Den nye journaløkten inneholder i utgangspunktet ingen misjonshendelser</li>\n'
              '</ul>\n'
              '<p>Bare en dokumentert oppdragshendelse endrer den lagrede tilstanden.</p>\n'
              '\n'
              '<h3>Flere befal</h3>\n'
              '<p>Oppdragene er strengt adskilt av sjefen.</p>\n'
              '<p>En oppdragshendelse er kun tildelt sjefen hvis journaløkt er unikt identifisert. '
              'Oppdrag fra en annen sjef kan ikke vises eller endres.</p>\n'
              '\n'
              '<h3>Foreldreløse eller ikke lenger gyldige oppdrag</h3>\n'
              '<p>Hvis eldre journaldata eller en tidligere import holder et oppdrag åpent selv om '
              'det ikke lenger eksisterer i spillet, kan den eksisterende funksjonen for '
              'tilbakestilling/opprydding av foreldreløse oppdrag brukes.</p>\n'
              '<p>Denne funksjonen skal bare brukes hvis det er tydelig at det viste oppdraget '
              'ikke lenger er aktivt.</p>\n'
              '\n'
              '<h3>Online tjenester</h3>\n'
              '<p>Støttede oppdragshendelser kan i tillegg overføres til Inara hvis en gyldig og '
              'aktivert Inara-tilgang er satt opp for den aktive journalen FID.</p>\n'
              '<p>En manglende eller utilgjengelig Inara-tilkobling påvirker ikke lokal '
              'oppdragslagring.</p>\n'
              '\n'
              '<h3>Tupp</h3>\n'
              '<p>Hvis et oppdrag ikke vises eller viser en feil status, sjekk først om Elite '
              'Dangerous allerede har skrevet den tilsvarende oppdragshendelsen til '
              'journalen.</p>\n'
              '<p>CMDRHelper kan bare vise informasjon som journalen faktisk gir eller som '
              'allerede er lagret fra tidligere unike oppdragsbegivenheter.</p>'),
 'explorer': ('Utforsker',
              '<h2>Utforsker</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Systemoversikt: den nye Elite-inspirerte visningen erstatter miniatyroversikten i Explorer og Krønike. Stjerner og planeter danner hovedstrukturen med måner som grener under; flerstjernesystemer forblir oversiktlige. Zoom, rulling, tilpass til vinduet og klikk på himmellegemer gir tilgang til detaljer.</p>\n<p>Kompakte asteroidebelter: klynger samles til belter i oversikten og vanlige systemkart i Explorer og Krønike. Alle data om de enkelte klyngene beholdes.</p>\n<p>Korrigert kartografi: en skanning etter DSS-kartlegging nullstiller ikke lenger usolgte utforskningsverdier, kartleggingstid eller effektivitet. Feil registreringer repareres ved oppstart fra tilgjengelige journaler med entydig commander-tilordning. Manglende kilder lar reparasjonen stå åpen; databasen trenger ikke slettes.</p>\n'
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
              '<h3>ØKOLOGISK ×N</h3>\n'
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
              '<p><b>ABBAU ×24</b></p>\n'
              '<p>betyr at 24 planetariske gruveplasser er rapportert for denne kroppen.</p>\n'
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
              '<p><b>Kobber – 56 t</b></p>\n'
              '<p>Denne informasjonen betyr at denne fartøysjefen faktisk hentet ut 56 tonn kobber '
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
              '<h3>Country bar</h3>\n'
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
              '<h3>ØKOLOGISK / GEO / DEGRADERING</h3>\n'
              '<p>Dette synet grupperer kropper med biologiske, geologiske eller planetariske '
              'nedbrytningssignaler.</p>\n'
              '<p>Dette betyr at interessante kropper ikke trenger å søkes opp individuelt i det '
              'komplette systemkartet.</p>\n'
              '<p>Hvis du har dine egne gruvedata på overflaten, kan dine personlige gruvefunn '
              'også være synlige.</p>\n'
              '<p>Manuelt justerte kolonnebredder i den felles Explorer-tabellen BIO / GEO / ABBAU beholdes ved gjenåpning og omstart. Lagrede kolonnebredder i sprettoppvinduer gjenopprettes mer robust; ugyldige verdier erstattes med trygge standardbredder.</p>\n\n'
              '<h3>Kroppsdetalj</h3>\n'
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
              '<h3>Vis bil</h3>\n'
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
              '<h3>Tupp</h3>\n'
              '<p>Hvis du har en interessant kropp, er det verdt å klikke på den detaljerte '
              'visningen. Dette er det beste stedet å skille mellom generelle kroppsdata, mulige '
              'leteresultater og faktiske funn dokumentert av din egen sjef.</p>'
              """

<h3>★ Favoritter</h3>
<p>Knappen «★ Favoritter» øverst i Explorer åpner et eget favorittvindu som kan brukes på nytt. Her lagrer du systemer, planeter/måner og steder på overflaten for den aktive kommandøren.</p>
<p>Den rullbare listen, alfabetisk sortert etter navn, viser navn, type, system, himmellegeme og breddegrad/lengdegrad der det er relevant, kategori og en liten bildeforhåndsvisning. Fritekstsøk, typefilter og kategorifilter kan brukes sammen. Søket omfatter navn, system, himmellegeme og notat.</p>
<p>«Åpne / Vis» viser de lagrede opplysningene, notatet og en større bildeforhåndsvisning. «Vis i Explorer» åpner den eksisterende systemoversikten eller detaljvisningen for himmellegemet hvis favoritten tilhører det gjeldende Explorer-systemet og passende data er tilgjengelige. For andre systemer forblir de lagrede favorittdataene synlige; ingen systemrute beregnes.</p>

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

<h3>Favorittmål og kommandør</h3>
<p>«▶ Til ruten» setter favorittens kjente system som mål i ruteplanleggeren. Starten følger eksisterende oppførsel med gjeldende AppState; en manuelt angitt start beholdes. Ingen rute beregnes automatisk. «◎ Til koordinatene» starter eksisterende planetnavigasjon til overflatestedet med eksisterende HUD når system, himmellegeme og gyldige koordinater er lagret. Reisen til systemet og overflatenavigasjonen er to separate trinn, uten automatisk reiseforløp. Uten overflatekoordinater er bare ruten tilgjengelig; handlinger som mangler nødvendige data skjules.</p>
<p>For steder på overflaten sender «◎ Til koordinatene» det lagrede himmellegemet, breddegrad, lengdegrad og favorittnavnet til den eksisterende planetnavigatoren. Det nye målet erstatter det forrige. Favoritter har ingen egen navigasjonslogikk. Navigatoren avgjør fortsatt selv: samsvarende, gyldige planetære data aktiverer navigasjonen; ellers venter den på disse dataene.</p>
<p>Favoritter tilhører bare den aktive kommandøren. Ved kommandørbytte oppdateres listen, og en åpen redigeringsdialog forkastes. Et mål som fortsatt håndteres som den forrige kommandørens favorittmål, avsluttes. Kommandørvalget i kronikken utvider ikke denne favorittlisten.</p>
<p>«Slett» krever bekreftelse og fjerner bare favorittoppføringen og dens interne bildekopi. Det opprinnelige skjermbildet eller det valgte originalbildet og alle Explorer-, journal- og himmellegemedata beholdes.</p>"""),
 'chronicle': (
        'Krønike',
        """<h2>Krønike</h2>
<h3>CMDRHelper v3.2</h3>
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
<p>For FABER38 kan listen for eksempel inneholde:</p>
<ul>
<li>Alle</li>
<li>kopper</li>
</ul>
<p>Hvis ytterligere råvarer faktisk utvinnes senere, vil de automatisk vises i ditt personlige valg.</p>

<h3>Målrettet søk etter råvarer</h3>
<p>For eksempel, hvis "Kobber" er valgt og deretter "Bruk" trykkes, vil historikken kun vise kropper som den aktuelle fartøysjefen beviselig har utvunnet kobber på.</p>
<p>Eksempel:</p>
<p><b>Prua Hypai NV-E c28-66 / 2 — ABBAU ×24 — kobber 56 t</b></p>
<p>Dette betyr at kronikken kan brukes som en personlig lokasjonsdatabase: et råmateriale som allerede er utvunnet kan bli funnet igjen senere.</p>

<h3>Alle råvarer</h3>
<p>Med "Råmateriale: Alle" blir alle matchende personlige gruvefunn på overflaten tatt i betraktning.</p>
<p>Hvis flere varer er kjent på en kropp, kan de vises sammen med mengdene de har fått til nå.</p>
<p>Eksempel:</p>
<p><b>ABBAU ×24 — Helium-3 18 t, kobber 56 t</b></p>
<p>Mengdene er de personlige gruveverdiene til den respektive sjefen, som faktisk er dokumentert fra journalhendelser.</p>
<p>Også med en aktiv periode forblir personlige utvunne mengder lagrede totalmengder. <b>Kobber 56 t</b> betyr ikke automatisk <b>56 t i den valgte perioden</b>. Perioden krever et passende systembesøk, men begrenser ikke den viste utvunne mengden til denne perioden.</p>

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
 'jump_tip': ('Hopptips',
              '<h2>Hopptips</h2>\n'
              '<p>Hopptipset støtter utforskning ved å evaluere allerede kjente systemdata og '
              'fremheve interessante målsystemer.</p>\n'
              '<p>Funksjonen er ment som et beslutningshjelpemiddel. Det garanterer ikke at et '
              'anbefalt system faktisk inneholder sjeldne eller spesielt verdifulle funn.</p>\n'
              '\n'
              '<h3>Grunnlag for evalueringen</h3>\n'
              '<p>CMDRHelper bruker eksisterende journal- og databaseinformasjon for å evaluere '
              'kjente mønstre i systemnavn og systemklasser.</p>\n'
              '<p>Det kan blant annet tas hensyn til systemforkortelser, allerede kjente '
              'kroppstyper og tidligere funn.</p>\n'
              '\n'
              '<h3>Systemforkortelse</h3>\n'
              '<p>Mange prosedyregenererte systemer i Elite Dangerous inneholder bokstav- og '
              'tallkombinasjoner som identifiserer spesifikke systemgrupper.</p>\n'
              '<p>CMDRHelper kan statistisk evaluere disse forkortelsene og vise i hvilke grupper '
              'interessante funn forekom hyppigere i dataene som er kjent til dags dato.</p>\n'
              '\n'
              '<h3>Revurdere</h3>\n'
              '<p>Med "Re-evaluate" analyseres den eksisterende databasen på nytt.</p>\n'
              '<p>Fartøysjefens lagrede data brukes. Funksjonen oppretter ikke nye elitedata eller '
              'endrer journalfiler.</p>\n'
              '\n'
              '<h3>Resultatliste</h3>\n'
              '<p>Resultatlisten viser de mest interessante systemforkortelsene eller kandidatene '
              'i henhold til den aktuelle evalueringen.</p>\n'
              '<p>Avhengig av eksisterende database kan det være informasjon om:</p>\n'
              '<ul>\n'
              '<li>interessante planetariske klasser</li>\n'
              '<li>biologiske funn</li>\n'
              '<li>Vannverdener</li>\n'
              '<li>terraformerbare kropper</li>\n'
              '<li>andre bemerkelsesverdige leteresultater</li>\n'
              '</ul>\n'
              '<p>vises.</p>\n'
              '\n'
              '<h3>Sannsynlighet i stedet for garanti</h3>\n'
              '<p>En høy verdi eller en god rangering betyr bare at et bestemt mønster oftere ble '
              'assosiert med interessante funn i dataene som er evaluert så langt.</p>\n'
              '<p>Det er ingen garanti.</p>\n'
              '<p>Et anbefalt system kan fortsatt være helt uinteressant, mens et lavt vurdert '
              'system kan inneholde verdifulle funn.</p>\n'
              '\n'
              '<h3>Egen database</h3>\n'
              '<p>Hopptipset fungerer med fartøysjefens allerede kjente data.</p>\n'
              '<p>Jo flere systemer og organer som registreres over tid, desto større blir den '
              'personlige databasen for evaluering.</p>\n'
              '<p>Dette betyr at rangeringen kan endres senere.</p>\n'
              '\n'
              '<h3>Flere befal</h3>\n'
              '<p>Personlige evalueringer håndteres på kommando-for-kommando basis.</p>\n'
              '<p>Data fra en annen fartøysjef må ikke forfalske den personlige vurderingen '
              'ubemerket.</p>\n'
              '<p>Globale astronomiske masterdata kan derimot deles så lenge de ikke representerer '
              'befalsrelaterte personlige funn.</p>\n'
              '\n'
              '<h3>Bruk i praksis</h3>\n'
              '<p>Hopptipset egner seg spesielt hvis det er flere mulige destinasjoner å velge '
              'mellom og det ønskes ytterligere beslutningshjelp.</p>\n'
              '<p>Den erstatter ikke en komplett ruteplanlegger og beregner ikke en sikker, '
              'optimal rute.</p>\n'
              '<p>Menypunktet "Ruteplanlegger" er tilgjengelig for spesifikk ruteplanlegging.</p>\n'
              '\n'
              '<h3>Tupp</h3>\n'
              '<p>Bruk hopptipset som en ekstra letehjelp:</p>\n'
              '<p>"I følge mine tidligere data, hvilket system virker mer interessant?"</p>\n'
              '<p>Ikke som en spådom:</p>\n'
              '<p>"Det er garantert et spesifikt funn i dette systemet."</p>'),
 'route_planner': ('Ruteplanlegger',
                   '<h2>Ruteplanlegger</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Bedre ruteplanlegger: starten følger automatisk gjeldende system til du angir en manuelt; tømming av feltet gjenoppretter automatikken. Skip og carriers bruker nøyaktig validerte ID64-adresser uten å velge lignende navn. «Unable to find route» forklares som at ingen rute ble funnet; kontroller mål, rekkevidde og ruteinnstillinger.</p>\n'
                   '<p>Ruteplanleggeren støtter planlegging av lengre turer med skip eller Fleet '
                   'Carrier. CMDRHelper kan bruke eksterne rutedata fra Spansh og forberede den '
                   'planlagte ruten for videre bruk.</p>\n'
                   '\n'
                   '<h3>Start og slutt</h3>\n'
                   '<p>Et start- og målsystem kreves for ruteberegning.</p>\n'
                   '<p>I den grad det er mulig kan CMDRHelper bruke fartøysjefens gjeldende kjente '
                   'system som utgangspunkt. Start og mål bør kontrolleres før beregning.</p>\n'
                   '\n'
                   '<h3>Send eller Fleet Carrier</h3>\n'
                   '<p>Ruteplanleggeren skiller mellom turer med et vanlig skip og med en Fleet '
                   'Carrier.</p>\n'
                   '<p>Begge bruker ulike krav og beregningsmetoder. Derfor må riktig rutetype '
                   'velges før planlegging.</p>\n'
                   '\n'
                   '<h3>Skipsrute</h3>\n'
                   '<p>For en skipsrute er det tatt hensyn til hoppegenskapene som er kjent eller '
                   'lagt inn for det aktive skipet.</p>\n'
                   '<p>Avhengig av tilgjengelige data kan FSD-data, skipsdata, masse, drivstoff og '
                   'andre hoppparametere inkluderes i planleggingen.</p>\n'
                   '<p>En beregnet rute er et planleggingshjelpemiddel. Endringer i skipet eller '
                   'dets masse kan endre den faktiske hoppedistansen som er oppnåelig i '
                   'spillet.</p>\n'
                   '\n'
                   '<h3>Flåtetransportrute</h3>\n'
                   '<p>Fleet Carrier har andre hoppregler enn vanlige skip.</p>\n'
                   '<p>CMDRHelper bruker den utpekte Spansh transportørplanleggingen for '
                   'tilsvarende ruter.</p>\n'
                   '<p>Ruten brukes til å planlegge hoppsekvensen. Faktisk tritiumforbruk og '
                   'tilgjengelig rekkevidde kan også avhenge av masse og gjeldende '
                   'transportørstatus.</p>\n'
                   '\n'
                   '<h3>Spansh</h3>\n'
                   '<p>For selve ruteberegningen kan CMDRHelper bruke den eksterne tjenesten '
                   'Spansh.</p>\n'
                   '<p>Forespørselen behandles i bakgrunnen slik at grensesnittet forblir '
                   'operativt under en lengre beregning.</p>\n'
                   '<p>CMDRHelper har ingen innflytelse på tilgjengeligheten eller responstiden '
                   'til den eksterne tjenesten.</p>\n'
                   '\n'
                   '<h3>beregning</h3>\n'
                   '<p>Etter å ha startet en beregning, sendes forespørselen videre til den valgte '
                   'ruteplanleggeren.</p>\n'
                   '<p>Avhengig av ruten og tjenesten, kan beregningen ta litt tid. I løpet av '
                   'denne tiden skal ingen andre identiske beregninger startes unødvendig.</p>\n'
                   '\n'
                   '<h3>Resultat</h3>\n'
                   '<p>En vellykket beregnet rute viser de tiltenkte systemene eller hopppunktene '
                   'i deres rekkefølge.</p>\n'
                   '<p>Avhengig av rutetypen vises tilleggsinformasjon om distanse, hopp, '
                   'drivstoff eller tritium og andre tilgjengelige rutedata.</p>\n'
                   '\n'
                   '<h3>Rute og nåværende sjef</h3>\n'
                   '<p>Det nåværende systemet og skipet kan – så lenge de er klart kjent i den '
                   'aktive AppState – brukes til forhåndstildeling eller for å støtte '
                   'planlegging.</p>\n'
                   '<p>Den faktiske ruten forblir imidlertid en plan og endrer ingen journal- '
                   'eller fartøydata.</p>\n'
                   '\n'
                   '<h3>CTSVision eksport</h3>\n'
                   '<p>Beregnede flåtetransportruter kan eksporteres som CSV for CTSVision.</p>\n'
                   '<p>Dette betyr at en transportørrute planlagt i CMDRHelper så kan brukes i '
                   'CTSVision for hoppkontroll eller rutebehandling der.</p>\n'
                   '<p>Eksporten endrer ikke ruten i CMDRHelper.</p>\n'
                   '\n'
                   '<h3>CSV-fil</h3>\n'
                   '<p>Den eksporterte filen inneholder rutedataene som kreves for CTSVision i den '
                   'tiltenkte rekkefølgen.</p>\n'
                   '<p>Filen bør ikke endres strukturelt på en ukontrollert måte etter eksport '
                   'hvis den da skal leses inn av CTSVision.</p>\n'
                   '\n'
                   '<h3>Feil og eksterne tjenester</h3>\n'
                   '<p>Hvis Spansh ikke kan nås eller tjenesten returnerer en feil, viser '
                   'CMDRHelper en tilsvarende feilmelding.</p>\n'
                   '<p>En feil i online ruteberegning endrer ikke lokale fartøysjef eller '
                   'journaldata.</p>\n'
                   '\n'
                   '<h3>Ruteplanlegger og hopptips</h3>\n'
                   '<p>Hopptips og ruteplanlegger utfører forskjellige oppgaver:</p>\n'
                   '<ul>\n'
                   '<li>Jump tips evaluerer mulige interessante letemål basert på eksisterende '
                   'data.</li>\n'
                   '<li>Ruteplanlegger beregner en bestemt rute mellom start og destinasjon.</li>\n'
                   '</ul>\n'
                   '<p>Et godt hopptips er derfor ikke automatisk en del av en optimal rute.</p>\n'
                   '\n'
                   '<h3>Flere befal</h3>\n'
                   '<p>Hvis fartøysjefrelaterte data som nåværende system eller skip brukes, '
                   'kommer disse fra den aktive live AppState og må tydelig tilordnes der.</p>\n'
                   '<p>Bare å se på en annen fartøysjef i CMDR-visningen bytter ikke '
                   'ruteplanleggeren til deres system eller skip.</p>\n'
                   '<p>En ruteberegning i seg selv endrer ikke personopplysningene til en annen '
                   'fartøysjef.</p>\n'
                   '\n'
                   '<h3>Tupp</h3>\n'
                   '<p>Før en lang tur, sjekk alltid igjen:</p>\n'
                   '<ul>\n'
                   '<li>Startsystem</li>\n'
                   '<li>Målsystem</li>\n'
                   '<li>Rutetype skip/transportør</li>\n'
                   '<li>for skipsruter, det underliggende skipet, FSD og hoppparametere</li>\n'
                   '<li>for transportørruter, den tilgjengelige tritiumreserven</li>\n'
                   '</ul>\n'
                   '<p>For flåtetransportører er det tilrådelig å også planlegge tilstrekkelige '
                   'reserver for hjemreise eller uplanlagte omveier.</p>'),
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
            '<h3>Automatisk behandling</h3>\n'
            '<p>Hvis "Konverter automatisk" er aktivert og gyldige kilde- og målmapper er angitt, '
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
            '<p>Som standard beholdes den originale BMP-filen. Hvis "Slett BMP etter konvertering" '
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
            '<p><b>FABER38_F12520967/</b></p>\n'
            '<p>FID holder oppdraget klart selv med flere sjefer. Dette gjør at to sjefer med '
            'samme navn kan skilles fra hverandre.</p>\n'
            '\n'
            '<h3>filnavn</h3>\n'
            '<p>Nye behandlede bilder får et navn med fangsttidspunkt, sjefsnavn og - hvis '
            'tilgjengelig - stjernesystemet kjent ved kø.</p>\n'
            '<p>Eksempel:</p>\n'
            '<p><b>2026-09-04_13-18-22_FABER38_Prua-Hypai-RB-D-c29-71.png</b></p>\n'
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
            'kontinuerlig<code>_2</code>,<code>_3</code>,<code>_4</code>og så videre.</p>\n'
            '<p>Dette betyr at et annet skjermbilde med samme tidsstempel ikke vil overskrive et '
            'eksisterende målbilde.</p>\n'
            '\n'
            '<h3>Fartøyskifte under behandling</h3>\n'
            '<p>Commander, FID og systemet fanges sammen når du setter et skjermbilde i kø.</p>\n'
            '<p>Et senere skifte av befal endrer ikke tildelingen av dette allerede ventende '
            'bildet. Dette betyr at et skjermbilde av FABER38 ikke senere blir skrevet til mappen '
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
            '<p>Det vil være i undermappen<b>UNKNOWN_UNKNOWN/</b>behandlet; filnavnet brukes også '
            'for Commander<b>UKJENT</b>. Denne mappen kan vises gjennom Alle kommandoer, ikke '
            'gjennom Uallokert rotmappefilter.</p>\n'
            '\n'
            '<h3>Flere befal</h3>\n'
            '<p>To separate regler gjelder for bildebehandling:</p>\n'
            '<ul>\n'
            '<li><b>Lagre nye bilder:</b>Den aktive journalidentiteten med Commander og FID når de '
            'står i kø, bestemmer målmappen.</li>\n'
            '<li><b>Se bilder:</b>Kommandoen som vises eller det valgte gallerifilteret bestemmer '
            'de synlige bildene.</li>\n'
            '</ul>\n'
            '<p>Dette betyr at galleriet til en annen sjef kan ses mens FABER38 spilles uten at '
            'nye skjermbilder havner i mappen til den aktuelle sjefen.</p>\n'
            '\n'
            '<h3>Tupp</h3>\n'
            '<p>En delt rotmappe for skjermbilder er tilstrekkelig. CMDRHelper separerer '
            'automatisk nylig behandlede bilder i Commander og FID.</p>\n'
            '<p>Med "Current Commander", "All Commanders" og "Unassigned" kan du bytte mellom '
            'personlig galleri, undermappene til alle kommandoer og eldre bilder i rotmappen.</p>\n'
            '<p>Høyere lysstyrke kan hjelpe med mørke bilder; det påvirker det nyopprettede '
            'målbildet under konverteringen.</p>'),
 'commander_view': ('CMDR-visning',
                    '<h2>CMDR-visning</h2>\n'
                    '<p>CMDR-visningen oppsummerer en fartøysjefs permanent lagrede personlige '
                    'opplysninger.</p>\n'
                    '<p>Den lar deg også bytte mellom de kjente sjefene for CMDRHelper og se deres '
                    'egne data. Personlig informasjon skilles ved hjelp av Frontier ID (FID).</p>\n'
                    '\n'
                    '<h3>Velg Commander</h3>\n'
                    '<p>Hvis flere sjefer er kjent, kan du bruke valget ovenfor for å finne ut '
                    'hvem som har lagret informasjon som vises. Denne sjefen er den betraktede '
                    'sjefen.</p>\n'
                    '<p>Displayet markerer det som enten "Live Active" eller "View Only".</p>\n'
                    '\n'
                    '<h3>Regnes som kommandør og livekommandør</h3>\n'
                    '<p>Å velge en annen sjef i CMDR-visningen gjør den ikke til den aktive '
                    'journalkommandøren.</p>\n'
                    '<p>Live-sjefen bestemmes utelukkende fra den for øyeblikket unikt '
                    'identifiserte Elite Dangerous-journaløkten. På denne måten kan historien til '
                    'en annen sjef ses mens Elite Dangerous fortsetter å kjøre med FABER38.</p>\n'
                    '\n'
                    '<h3>Frontier ID (FID)</h3>\n'
                    '<p>FID er den stabile Frontier-identifikatoren til en sjef.</p>\n'
                    '<p>CMDRHelper bruker den og den interne kommando-ID-en som er løst fra den '
                    'for å skille personopplysninger på en sikker måte. Kommandører med lignende '
                    'eller identiske navn forblir også adskilt.</p>\n'
                    '\n'
                    '<h3>Oversikt</h3>\n'
                    '<p>Fanen "Oversikt" viser kun permanent lagret informasjon for den aktuelle '
                    'fartøysjefen:</p>\n'
                    '<ul>\n'
                    '<li>Kommandørnavn, FID og status «Live active» eller «View only»</li>\n'
                    '<li>første og siste kjente tidspunkt</li>\n'
                    '<li>Antall besøkte systemer, bio- og geofunn, kodex-oppføringer og '
                    'kartografisalg</li>\n'
                    '<li>Siste kjente plassering og antall åpne oppdrag</li>\n'
                    '<li>nåværende eller siste skip</li>\n'
                    '<li>Fleet Carrier og operatørens plassering</li>\n'
                    '<li>Eiendeler</li>\n'
                    '<li>åpne biodata og åpne kartografiske data inkludert eksisterende '
                    'estimater</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Eiendeler/kreditter</h3>\n'
                    '<p>«Eiendeler»-feltet viser den sist lagrede kredittsaldoen til den aktuelle '
                    'fartøysjefen fra en passende journalhendelse, formatert som f.eks.<b>1 234 '
                    '567 kr</b>.</p>\n'
                    '<p>CMDRHelper legger ikke til fiktive inntekter eller utgifter dersom det '
                    'ikke er ny, sikker journalstatus.</p>\n'
                    '\n'
                    '<h3>Leiesoldatmynter</h3>\n'
                    '<p>Leiesoldatmyntene kommer fra MercCoins-feltene levert av Elite '
                    'Dangerous<code>Statistics → Bank_Account</code>og lagres kommandorelatert som '
                    'et Frontier øyeblikksbilde.</p>\n'
                    '<p>Synlige er:</p>\n'
                    '<ul>\n'
                    '<li>Nåværende</li>\n'
                    '<li>Totalt brukt</li>\n'
                    '<li>Engineering</li>\n'
                    '<li>utstyr</li>\n'
                    '<li>Rapportert av Frontier: tjent totalt</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Aktuelle og utgaver</h3>\n'
                    '<p>"Gjeldende" viser<code>MercCoins_Current</code>. «Total Spent» tar '
                    'over<code>MercCoins_Total_Spent</code>.</p>\n'
                    '<p>"Engineering" og "Equipment" viser andelene rapportert separat av '
                    'Frontier<code>MercCoins_Spent_On_Engineering</code>og<code>MercCoins_Spent_On_MercGear</code>.</p>\n'
                    '<p>For FABER38, for eksempel, en løpende beholdning av<b>1275</b>, '
                    'totalt<b>220</b>brukt og borte<b>220</b>rapportert til ingeniørarbeid.</p>\n'
                    '\n'
                    '<h3>Alt i alt fortjent</h3>\n'
                    '<p>"Rapportert av Frontier: tjent totalt" '
                    'viser<code>MercCoins_Total_Earned</code>. CMDRHelper beregner ikke egen '
                    'balanse fra dette.</p>\n'
                    '<p>Frontiers kumulative verdi trenger ikke matematisk å samsvare med '
                    'gjeldende beholdning og rapporterte utgifter. For eksempel kan 1275 '
                    'nåværende, 25 totalt opptjente og 220 totalt brukt rapporteres samtidig.</p>\n'
                    '<p>CMDRHelper korrigerer ikke disse verdiene, men viser de individuelle '
                    'Frontier-tellerne uendret.</p>\n'
                    '\n'
                    '<h3>Hvorfor ikke ha din egen MercCoins balanse?</h3>\n'
                    '<p>Elite Dangerous gir ikke en unik journalpost for hver individuelle mottak '
                    'eller utgift av leiesoldatmynter. MercCoins vises som totaler i '
                    'Statistics.</p>\n'
                    '<p>En egenberegnet bookinghistorikk vil derfor ikke være pålitelig. '
                    'CMDRHelper lagrer det siste kjente Frontier øyeblikksbildet i stedet.</p>\n'
                    '\n'
                    '<h3>Oppdrag</h3>\n'
                    '<p>"Oppdrag"-fanen viser de lagrede oppdragene til den aktuelle sjefen som en '
                    'tabell med status, oppdragsnavn, mål, utløpstid og belønning.</p>\n'
                    '\n'
                    '<h3>utforskning</h3>\n'
                    '<p>Utforskning-fanen viser åpne biodata, åpne kartografidata, biofunn, første '
                    'fotfall, selvkarterte og effektivt kartlagte kropper, og antall besøkte '
                    'systemer.</p>\n'
                    '<p>Den dedikerte "Chronicle"-fanen i CMDR-visningen er for øyeblikket '
                    'fortsatt en plassholder. Hele kronikken finner du i hovedmenypunktet med '
                    'samme navn.</p>\n'
                    '\n'
                    '<h3>Skip/flåte</h3>\n'
                    '<p>"Skips"-fanen viser først det aktive eller sist brukte skipet med '
                    'skipsnavn, skipstype, plassering og ShipID.</p>\n'
                    '<p>De lagrede skipene til den aktuelle sjefen vises under dem som utvidbare '
                    'kort. De kan sorteres stigende eller synkende etter:</p>\n'
                    '<ul>\n'
                    '<li>sist eller for øyeblikket brukt</li>\n'
                    '<li>Skipsnavn eller skipstype</li>\n'
                    '<li>maksimal hopprekkevidde</li>\n'
                    '<li>Lastekapasitet eller tom masse</li>\n'
                    '<li>sist kjente sted eller tidspunkt</li>\n'
                    '</ul>\n'
                    '<p>Du kan også filtrere for alle skip, skip med kjøretøyhangar eller skip med '
                    'jagerhangar.</p>\n'
                    '\n'
                    '<h3>Skipsdetaljer</h3>\n'
                    '<p>Et åpnet skipskart viser - hvis lagret - skips-ID, ShipID, plassering, '
                    'siste tid, maksimal hopprekkevidde, FSD og Guardian booster, masse, last og '
                    'tankkapasiteter samt utlastingstid og status.</p>\n'
                    '<p>Hvis moduldata er tilgjengelig, oppsummeres også kjøretøy- og '
                    'jagerflyhangar, skjoldgenerator og skjoldforsterker, '
                    'Guardian-skjoldforsterkninger, våpen, skrog- og modulforsterkninger og '
                    'passasjerkabiner.</p>\n'
                    '<p>Lastestatusen kan være fullstendig, ufullstendig eller foreldet. Manglende '
                    'informasjon vises som "–" og er ikke løst.</p>\n'
                    '\n'
                    '<h3>Fleet Carrier</h3>\n'
                    '<p>For en lagret tilpasset Fleet Carrier viser visningen operatørens navn, '
                    'kallesignal, operatør-ID, siste plassering og tidspunktet for siste '
                    'oppdatering.</p>\n'
                    '\n'
                    '<h3>Vedvarende sjefsstat</h3>\n'
                    '<p>Viktig fartøysjefinformasjon forblir permanent lagret. Dette gjør at '
                    'kjente verdier kan vises igjen etter en omstart av CMDRHelper eller Elite '
                    'Dangerous uten å fullstendig evaluere hver journal på nytt.</p>\n'
                    '<p>Nye unike journalhendelser oppdaterer den lagrede tilstanden.</p>\n'
                    '\n'
                    '<h3>Historisk rekonstruksjon</h3>\n'
                    '<p>For funksjoner som legges til senere, kan CMDRHelper søke i eksisterende '
                    'journalområder som tydelig er tildelt en fartøysjef én gang for informasjon '
                    'som allerede er kjent.</p>\n'
                    '<p>For eksempel kan eldre MercCoins-øyeblikksbilder tas i bruk. Gjentatte '
                    'kontroller er ikke ment å produsere dupliserte data og endrer ikke vanlige '
                    'journalleseposisjoner.</p>\n'
                    '\n'
                    '<h3>Flere befal</h3>\n'
                    '<p>Spesielt forblir følgende atskilt når det gjelder befal:</p>\n'
                    '<ul>\n'
                    '<li>Eiendeler og oppdrag</li>\n'
                    '<li>egen kartografi og organiske funn</li>\n'
                    '<li>Overflategruvehistorie og leiesoldatmynter</li>\n'
                    '<li>Online legitimasjon</li>\n'
                    '<li>sjefsrelaterte skjermbilder</li>\n'
                    '</ul>\n'
                    '<p>Globale astronomiske egenskaper til et system eller en kropp kan '
                    'imidlertid brukes sammen.</p>\n'
                    '\n'
                    '<h3>Innvirkning på andre synspunkter</h3>\n'
                    '<p>Hvis du endrer den aktuelle sjefen, oppdateres selve CMDR-visningen, det '
                    'personlige utvalget av råmateriale for gruvedrift i kronikken og, med '
                    'passende filter, skjermbildegalleriet.</p>\n'
                    '<p>Den erstatter ikke den faktiske live-kommandøren for journalbehandling '
                    'eller online opplastinger.</p>\n'
                    '\n'
                    '<h3>Inara og EDSM</h3>\n'
                    '<p>Inara- og EDSM-tilganger administreres separat per henholdsvis sjef og '
                    'FID.</p>\n'
                    '<p>Bare å se på en fartøysjef starter ikke en overføring med deres API-Key. '
                    'Bare det aktive tidsskriftet FID er relevant for live-opplastinger.</p>\n'
                    '<p>Tilgangsdataene administreres under "Innstillinger" i området for '
                    'elektroniske tjenester.</p>\n'
                    '\n'
                    '<h3>Tupp</h3>\n'
                    '<p>Bruk CMDR-visningen hvis du vil se lagret personlig informasjon for en '
                    'bestemt sjef.</p>\n'
                    '<p><b>CMDR-visning = Hvem vil jeg se?</b></p>\n'
                    '<p><b>Active Journal-FID = Hvem spiller egentlig akkurat nå?</b></p>\n'
                    '<p>Denne separasjonen forhindrer at personlige data eller online opplastinger '
                    'fra forskjellige sjefer blandes sammen.</p>'),
 'settings': ('Innstillinger',
              '<h2>Innstillinger</h2>\n<h3>CMDRHelper v3.2</h3>\n<p>Bedre oppdateringsinformasjon: Ja/Nei-vinduet viser installert og tilgjengelig versjon samt opptil seks nyheter når et sammendrag finnes. Lange lister kan rulles og handlingene forblir tilgjengelige. Visningen følger med v3.2; en uendret v3.1-klient viser den ikke ennå.</p>\n'
              '<p>"Innstillinger"-området bestemmer hvordan CMDRHelper fungerer med Elite '
              'Dangerous, journalfiler, database, nettjenester, grensesnitt og oppdateringer.</p>\n'
              '<p>Endringer i legitimasjon og baner bør gjøres nøye. Kommandørrelaterte '
              'innstillinger administreres separat av Frontier ID om nødvendig.</p>\n'
              '\n'
              '<h3>tidsskrift</h3>\n'
              '<p>Journalmappen er en av de viktigste innstillingene. Den må peke til mappen der '
              'Elite Dangerous<code>Journal*.log</code>filer av Windows- eller Proton-profilen som '
              'brukes.</p>\n'
              '<p>Tidsskriftene gir blant annet:</p>\n'
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
              'tydelig tilordnede tidsskrifter.</p>\n'
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
              '<h3>Oppdateringer</h3>\n'
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
              '<h3>Tupp</h3>\n'
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
<p>Åpne «Planetnavigasjon» i oversikten og velg «Manuell inntasting …».</p>
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

<h3>Dataenes alder og begrensninger</h3>
<p>Navigasjonen bygger på statusdataene fra Elite. Oppdateringer kan komme forsinket avhengig av spilltilstanden. Aldersvisningen i navigatoren viser hvor lenge det er siden den siste bekreftede statusmeldingen.</p>
<p>Overflateavstanden beskriver den korteste buen på en tenkt kule. Den er ikke en terreng- eller veirute. Navigatoren kjenner verken hindringer eller terrenghøyder langs strekningen; flyhøyde, trygg hastighet og å unngå hindringer er fortsatt ditt ansvar.</p>

<h3>Tips</h3>
<p>Før innflygingen kontrollerer du navnet på himmellegemet og fortegnene til målkoordinatene. Still deg deretter inn på målkursen i Elite-kompasset og følg med på relativ retning og avstand. Hvis navigatoren venter, sjekk om Elite allerede leverer planetkoordinater for himmellegemet du skal til.</p>""",
    ),
}

DIALOG_TITLE = 'Hjelp – {area}'
CLOSE_LABEL = 'Lukk'
