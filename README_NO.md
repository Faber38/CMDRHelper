# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Din co-pilot for Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_no.png)

**Personlig følgesvenn for Elite Dangerous – utforskning, navigasjon og kommandørdata på et øyeblikk**

CMDRHelper er et selvstendig skrivebordsprogram som analyserer de lokale Elite Dangerous-journalene og bruker planetære posisjonsdata fra `Status.json`. Det hjelper deg å oppdage interessante himmellegemer, finne tilbake til lagrede steder og gjennomgå reiser og funn. Personlige data beholdes etter omstart og holdes atskilt for hver kommandør.

## Nytt i v3.2 sammenlignet med v3.1

- Materialoversikt for engineering: alle 146 materialer i Raw, Manufactured og Encoded, med grader, kapasitet og unntak. Oppdatert beholdning per commander, søk, filtre, fem diskrete radbakgrunner og lagrede kolonnebredder og rekkefølge gir oversikt. Ukjent beholdning skilles fra null.

- Odyssey-beholdning: den fjerde materialfanen inneholder 223 katalogidentiteter for varer, komponenter, data og forbruksvarer. Skipslager, ryggsekk og pålitelig total holdes atskilt; oppdragsstabler, oppdragsstatus og engineering-bruk vises. Positive antall er gullfargede. Navn uten oversettelse vises på engelsk.

- Søk etter materialhandlere (Finn materialhandler → Åpne ruteplanlegger): på forespørsel søker Spansh separat etter Raw, Manufactured og Encoded fra commanderens nåværende system. Carriers utelates og stasjonsdetaljer kontrolleres. Avstanden i ly er direkte mellom systemene; fellesskapsdata garanterer ikke tilgang. Overføring til ruteplanleggeren setter bare målsystemet og starter ingen rute. Ingen søk etter Odyssey-handlere.

- Systemoversikt: den nye Elite-inspirerte visningen erstatter miniatyroversikten i Explorer og Krønike. Stjerner og planeter danner hovedstrukturen med måner som grener under; flerstjernesystemer forblir oversiktlige. Zoom, rulling, tilpass til vinduet og klikk på himmellegemer gir tilgang til detaljer.

- Kompakte asteroidebelter: klynger samles til belter i oversikten og vanlige systemkart i Explorer og Krønike. Alle data om de enkelte klyngene beholdes.

- Korrigert kartografi: en skanning etter DSS-kartlegging nullstiller ikke lenger usolgte utforskningsverdier, kartleggingstid eller effektivitet. Feil registreringer repareres ved oppstart fra tilgjengelige journaler med entydig commander-tilordning. Manglende kilder lar reparasjonen stå åpen; databasen trenger ikke slettes.

- Bedre ruteplanlegger: starten følger automatisk gjeldende system til du angir en manuelt; tømming av feltet gjenoppretter automatikken. Skip og carriers bruker nøyaktig validerte ID64-adresser uten å velge lignende navn. «Unable to find route» forklares som at ingen rute ble funnet; kontroller mål, rekkevidde og ruteinnstillinger.

- Bedre oppdateringsinformasjon: Ja/Nei-vinduet viser installert og tilgjengelig versjon samt opptil seks nyheter når et sammendrag finnes. Lange lister kan rulles og handlingene forblir tilgjengelige. Visningen følger med v3.2; en uendret v3.1-klient viser den ikke ennå.

## v3.1 (v3.0.3 → v3.1)

- BIO-fremdriften er kompakt: 1/3 gul, 2/3 blå og 3/3 grønn; fullført tilstand «Ferdig» er også grønn. Under «vis automatisk» har GEO en egen lagret bryter: bare BIO, bare GEO eller begge sammen. Manuelt justerte kolonnebredder i den felles Explorer-tabellen BIO / GEO / ABBAU beholdes ved gjenåpning og omstart. Lagrede kolonnebredder i sprettoppvinduer gjenopprettes mer robust; ugyldige verdier erstattes med trygge standardbredder.

- Oppdagelse og kartlegging skilles og knyttes til skannetidspunktet ditt: «Allerede oppdaget ved skanningen din» og «Allerede kartlagt ved skanningen din». Manglende opplysninger forblir Ukjente. First Discovery- og First Mapping-kandidater gjelder bare ved skanningen; et historisk Nei beviser ikke at himmellegemet fortsatt er uoppdaget eller ukartlagt i dag. Egen kartlegging bekrefter ikke et offisielt førstekrav. EDSM-kjennskap holdes separat.

- «EDSM-status-HUD» under «vis automatisk» er AV som standard. Etter ankomst til et system vises en kort melding over Elite i omtrent 2,5 sekunder. «EDSM: KJENT» betyr et gyldig EDSM-treff for systemet. «EDSM: UKJENT» betyr et gyldig EDSM-svar uten systemtreff. «EDSM: INGEN SVAR» betyr nettverksfeil, HTTP-feil, tidsavbrudd eller ugyldig svar, aldri et bekreftet manglende treff. Kjennskap i EDSM er ikke det samme som offisiell oppdagelse i Elite; navn på første oppdager eller innmelder loves ikke. Meldingen virker uavhengig av navigasjons- og laste-HUD.

- Besøkshistorikken tar med Location, FSDJump og CarrierJump også under løpende journaloppdatering. Flere stedshendelser under ett sammenhengende opphold teller som ett besøk: A → A → A teller én gang. En faktisk retur beholdes: A → B → C → A teller fire besøk.

- Fullført egen DSS-kartlegging lagrer nå kartleggingstidspunkt, brukte sonder og effektivitetsmål pålitelig. Senere skanninger fører ikke lenger til tap av eksisterende opplysninger.

- Lastevinduet tilpasser høyden automatisk til innholdet. Ved mange oppføringer begrenses høyden og tabellen kan rulles; valgt bredde og vindusposisjon beholdes. Den eksisterende bryteren «Lasteroms-HUD» ligger nå under «vis automatisk», uten en ekstra bryter i lastevinduet.

- For eksisterende installasjoner holder det normalt å installere oppdateringen → starte CMDRHelper. Nødvendige historiske rettelser av BIO-data, besøk og DSS-metadata utføres automatisk; databasen sikkerhetskopieres før reparasjoner som skriver data. Reparasjonene er versjonerte og idempotente: vellykkede revisjoner kjøres ikke fullstendig på nytt ved hver start. Rekonstruksjon krever Elite-journaler som fortsatt finnes, kan leses og entydig kan knyttes til en commander. Manglende kilder blir ikke oppdiktet eller regnet som suksess; uferdige reparasjoner forsøkes igjen ved neste start. Sletting av databasen, manuelle skript og ny import er normalt unødvendig.

## Explorer

Explorer viser det gjeldende systemet i tre visninger:

- **Systemkart:** grafisk fremstilling av kjente stjerner, planeter og måner. Klikk på et himmellegeme for å åpne detaljene. «Vis alle» åpner systemoversikten.
- **Verdiliste:** Verdilisten viser estimater basert på den lagrede skanningen, ikke garanterte utestående utbetalinger. Førstebonuser forblir ubekreftet. Verktøytips i kart og liste og detaljene for himmellegemet bruker de samme tidfestede tilstandene.
- **BIO / GEO / ABBAU:** biologiske og geologiske signaler, planetære gruvesteder og dokumenterte personlige funn.

Analysene skiller mellom rapporterte signaler og faktiske personlige funn. **BIO ×N** er det rapporterte antallet signaler, ikke en bekreftelse på ferdig analyserte arter. **GRUVEDRIFT ×N** teller planetære gruvesteder uten å avsløre råstoffinnholdet på hvert enkelt sted. Personlig utvunnede handelsvarer, sekundære materialer samlet under gruvedrift og himmellegemets generelle materialsammensetning holdes atskilt.

Explorer viser også anslåtte BIO-verdier, fremdrift i egne analyser og usolgte kartografi- og BIO-data. Verdiene bygger på tilgjengelig journal- og himmellegemeinformasjon; manglende data presenteres ikke som personlige oppdagelser. Supplerende EDSM-data er ekstern informasjon som må skilles fra personlige funn.

Himmellegemedetaljene omfatter tilgjengelige fysiske egenskaper, atmosfære, ringer, materialer og oppdagelsesinformasjon. Fremstillingene bruker passende teksturer og animasjoner for enkelte spesielle astronomiske objekter. Cargo-området viser kjent last og kapasitet for skipet eller SRV-en som brukes nå; for Rhino er last og personlige gruvefunn fortsatt forskjellige opplysninger.

Øverst i Explorer finnes **★ Favoritter | Planetnavigasjon | Vis alt**. Favoritter og planetnavigasjon åpner egne vinduer; de tre Explorer-visningene er fortsatt tilgjengelige.

## Planetnavigasjon

Planetnavigatoren hjelper deg utelukkende å fly til en bestemt **breddegrad/lengdegrad på en planet eller måne**. For reiser mellom stjernesystemer finnes en egen ruteplanlegger.

### Angi et mål og fly

Velg målhimmellegemet eller bruk det gjeldende himmellegemet, som gjenkjennes automatisk når det er mulig. Angi breddegrad og lengdegrad og eventuelt et målnavn. Du trenger ikke oppgi tekniske data som BodyID eller SystemAddress. **0,0** er også en gyldig koordinat.

Så snart Elite leverer gyldige planetære posisjonsdata for riktig himmellegeme, aktiveres kompasset automatisk. Uten passende data viser navigatoren en ventetilstand. Du kan når som helst sette et nytt koordinatmål på samme himmellegeme; det erstatter det forrige målet.

### Visning under innflyging

| Avstand til målet | Visning |
| --- | --- |
| **Mer enn 380 km** | Planetkule med egen posisjon som en hvit sirkel og målet som en liten prikk. Målet er oransje på den synlige siden og rødt på den skjulte baksiden. Spillerposisjonen står fast i visningen; planet og mål fremstilles i forhold til den. |
| **Til og med 380 km** | Automatisk overgang til et skråstilt perspektivrutenett med **50-km-avstandsintervaller** og målets posisjon tegnet inn for den videre innflygingen. |

Navigatorvinduets størrelse kan endres fritt. Kulen eller perspektivrutenettet tilpasses proporsjonalt til plassen; detaljverdiene forblir lesbare.

### Forstå navigasjonsverdiene

- **Målkoordinater:** målets lagrede breddegrad og lengdegrad.
- **Gjeldende koordinater:** din siste gyldige planetære posisjon.
- **Målavstand / Avstand over overflaten:** beregnet avstand til målet over kuleoverflaten; den store målavstanden og detaljverdien viser samme avstand med ulik avrunding.
- **Peiling:** absolutt retning fra gjeldende posisjon til målet.
- **Heading:** din gjeldende orientering slik Elite rapporterer den.
- **Relativ retning:** forskjellen mellom heading og peiling, for eksempel «23° høyre», «venstre» eller «rett frem».
- **Målkurs:** den absolutte kursen du kan dreie til i Elite-HUD-en. Den tilsvarer peilingen og er ikke en ekstra relativ dreievinkel.

Eksempel: **Heading 051° → Målkurs 074° = 23° høyre**.

Navigasjonen avhenger av spillets statusdata; oppdateringer kan komme forsinket avhengig av spilltilstanden. Overflateavstanden er ingen terreng- eller veirute. Hindringer og terrenghøyder langs strekningen tas ikke med.

## Navigasjons-HUD

Til venstre under **vis automatisk → Navigasjons-HUD** kan du aktivere en valgfri tilleggsvisning direkte over Elite. Ved gyldig planetnavigasjon viser den:

- relativ retning,
- absolutt målkurs,
- avstand.

HUD-en er gjennomsiktig, slipper gjennom klikk og tar ikke fokus: den tar verken museklikk eller inndatafokus fra spillet. Uten gyldig navigasjon blir den automatisk usynlig; avkryssingen i sidefeltet kan fortsatt være aktiv. Den vanlige navigatoren fungerer uavhengig av HUD-en.

HUD-en er testet i spillet under **Linux/X11** og **Windows 11 med Elite**. Under Windows knyttes flere skjermer til visningen ved hjelp av geometrien deres og Elite-vinduets posisjon, ikke ved samsvar mellom skjermnavn.

## Favoritter

**Explorer → ★ Favoritter** åpner et eget, gjenbrukbart vindu. Favoritter tilhører den **aktive kommandøren**. Kommandørbytte oppdaterer visningen; kommandørvalget i kronikken utvider ikke favorittlisten.

### Lagre tre typer

Den øverste handlingsraden tilbyr:

| Handling | Lagret favoritt |
| --- | --- |
| **★ Lagre nåværende system** | Det gjeldende systemet, uten overflatekoordinater. |
| **★ Lagre planet / måne** | En valgt kjent planet eller måne i gjeldende system, uten overflatekoordinater. |
| **★ Lagre nåværende posisjon** | Et sted på overflaten med gjeldende system, himmellegeme, breddegrad og lengdegrad. |

Posisjonsknappen er alltid synlig og er bare tilgjengelig med gyldige, aktuelle planetære posisjonsdata og en aktiv kommandør. **Ved klikk fryses kommandør, system, himmellegeme og koordinater før redigeringsdialogen åpnes.** Senere bevegelser i spillet endrer ikke denne posisjonen. Samme lagringsflyt er tilgjengelig i planetnavigatoren. Kjente interne ID-er overføres automatisk; ingen koordinater diktes opp.

Velg et navn og nøyaktig én kategori: **Bio, Geo, Gruvedrift, Utsikt, Landingssted, Interessant eller Annet**. Notat og bilde er valgfrie.

### Finne, vise og redigere

Den rullbare listen, alfabetisk sortert etter navn, viser navn, type, system, himmellegeme og koordinater der det er relevant, kategori og en liten bildeforhåndsvisning. **Fritekstsøk, type- og kategorifilter** kan kombineres. Søket omfatter navn, system, himmellegeme og notat.

**Åpne / Vis** viser lagrede opplysninger, notatet og en større bildeforhåndsvisning. **Vis i Explorer** bruker eksisterende systemoversikt eller himmellegemedetaljer hvis favoritten tilhører gjeldende Explorer-system og passende data finnes. For andre systemer er de lagrede favorittopplysningene fortsatt tilgjengelige.

**Rediger** endrer navn, kategori, notat og bilde. System, himmellegeme og lagrede koordinater erstattes ikke av sanntidsverdier. For en annen posisjon oppretter du en ny overflatefavoritt.

**Slett** krever bekreftelse og fjerner bare favorittoppføringen og dens interne bildekopi. Explorer-, journal- og himmellegemedata beholdes.

### Favorittbilder og siste skjermbilde

Favorittbilder er **helt atskilt fra det vanlige Bilder-området**. CMDRHelper håndterer sin egen interne kopi i favorittbildemappen (`data/favorites/images/` ved vanlig datalagring). Originalen blir verken flyttet eller endret.

- **Velg bilde …** godtar PNG, JPEG eller WebP og viser en forhåndsvisning. Den interne kopien opprettes først ved lagring.
- **Bruk siste skjermbilde** skanner den faktiske kildemappen på nytt ved hvert klikk. Passende konverterte Elite-skjermbilder i den aktive kommandørens mappe under det konfigurerte konverteringsmålet tas også med. Dermed er et nytt skjermbilde fortsatt tilgjengelig hvis automatisk konvertering allerede har slettet BMP-filen.
- Lesbare filer med passende Elite- eller konverteringsnavn tilbys, ikke vilkårlige bilder fra generelle bildemapper. Rekkefølgen bestemmes av en entydig opptakstid i filnavnet, ellers filtiden. For konverterte bilder brukes opptakstiden i navnet, ikke konverteringstidspunktet.
- Før du godtar et funnet skjermbilde, vises filnavn, opptakstid og en nylastet forhåndsvisning. Bekreft med **Bruk dette bildet**. Hvis ingen passende skjermbilder finnes, er manuelt bildevalg fortsatt tilgjengelig. CMDRHelper tar ikke skjermbilder selv.

Et bilde kan senere erstattes eller fjernes. Interne kopier som ikke trengs lenger, fjernes ved lagring eller sletting av favoritten. **Favoritthandlinger sletter aldri det opprinnelige skjermbildet eller et valgt originalbilde.** Hvis en intern bildefil mangler, kan favoritten fortsatt brukes uten forhåndsvisning.

### Overflatefavoritt som mål

**▶ Til målet** sender lagret himmellegeme, breddegrad, lengdegrad og favorittnavn til den eksisterende planetnavigatoren og erstatter det forrige målet. Favoritter har ingen egen navigasjonslogikk. Passende gyldige planetære data starter navigasjonen; ellers venter navigatoren som vanlig.

Andre kommandørers favoritter kan ikke brukes som egne mål. Kommandørbytte avslutter et mål som fortsatt håndteres som den forrige kommandørens favorittmål. System- og himmellegemefavoritter viser eksisterende informasjon, uten egen ruteplanlegging.

## Kronikk

Kronikken er din lagrede reise- og funnhistorie. **3D-reisekartet** viser besøkte systemer og kommandørruter. System- og himmellegemedetaljer hjelper deg å finne igjen kjent BIO-, GEO-, material-, Codex- og gruveinformasjon.

### Kombinerte filtre

**Bruk** eller **Enter i fritekstfeltet** kjører alle angitte filtre samlet:

- fritekst,
- eventuelt **Fra** og **Til**,
- **Planetære gruveområder** og **Minst**,
- **Mine gruvefunn** og **Vare**.

Et uttrykk fra **Søkehjelp / Tegnforklaring** settes inn i søkefeltet og kjøres sammen med periode- og gruvefiltrene som allerede er angitt.

### Periode i UTC

Fra og Til aktiveres hver med sin avkryssing. Bare én grense er også mulig; uten aktiv avkryssing er det ingen tidsbegrensning på den siden. **Fra** inkluderer starten av den valgte UTC-kalenderdagen. **Til** inkluderer hele den valgte UTC-dagen. UTC er den felles tidsreferansen, ikke din lokale kalendertid.

**Faktiske systembesøk** er avgjørende: minst ett lagret besøk må ligge i perioden. At systemet bare ble kjent første eller siste gang, erstatter ikke et besøk. Med aktiv periode viser antall besøk, første og siste besøk i kartvisningen til de filtrerte besøkene.

Perioden filtrerer besøk, ikke enkelte oppdagelses-, BIO-, GEO- eller gruvehendelser. Kjent funninformasjon og personlige gruvemengder forblir lagrede **totalverdier**. **«Kobber 56 t» med aktiv periode betyr ikke automatisk «56 t i denne perioden».** Hvis Fra er etter Til, vises en feilmelding; ingen databaseforespørsel starter.

### Kommandør og oppdatering

**Kartets kommandørvalg** bestemmer hvilke kommandørruter som vises. Personlige fritekst- og gruvesøk gjelder derimot den viste eller aktive kommandøren. Kartets avkryssinger utvider ikke automatisk personlige søk til flere kommandører.

**Oppdater kronikk** laster data på nytt og kjører de aktive filtrene igjen. **Gjeldende posisjon** bruker først gjeldende filtertilstand og sentrerer bare på det nåværende systemet hvis det finnes på resultatkartet. Ellers vises en melding; filtrene beholdes.

**Tilbakestill** tømmer fritekst, deaktiverer Fra/Til og tilbakestiller de synlige datofeltene. Gruveavkryssingene fjernes, minimumsantall blir 0 og handelsvare blir Alle. Kommandørvalget beholdes; deretter lastes den normale kronikken.

Ved **ingen treff** tømmes kart og ruter, trefflisten tømmes og skjules, detaljvisningen tilbakestilles og et åpent systemdetaljvindu i kronikken lukkes. Gamle resultater blir ikke stående.

### Kartbetjening

- Dra med venstre museknapp: roter.
- Dra med høyre museknapp: flytt.
- Dra med midtre museknapp: trekk opp et zoomvindu.
- Musehjul: zoom.
- **Juster:** tilbakestill orienteringen til galaktisk visning ovenfra; forskyvning og zoom beholdes.

## Bilder og automatisk skjermbildekonvertering

I **Bilder** angir du kildemappen for Elite-skjermbilder og konverteringsmålet. Automatisk konvertering gjør nye BMP-skjermbilder om til **PNG eller JPEG**. Justerbar lysning er tilgjengelig. BMP-filer som allerede finnes ved oppstart, konverteres ikke i etterkant bare fordi overvåkingen aktiveres; manuell konvertering finnes for dem.

Konverterte filnavn inneholder opptakstid, kommandør og system, og filene lagres kommandørvis. Automatisk tilordning følger den aktive journalkommandøren. Et annet valg i galleriet endrer ikke denne aktive kommandøren.

Valget om å **slette opprinnelig BMP etter vellykket konvertering** tilhører utelukkende denne konverteringen og har en egen innstilling. Det er uavhengig av håndteringen av favorittbilder.

Galleriet viser passende konverterte bilder med forhåndsvisning. Det leses på nytt når det vises igjen; oppdatering tar også hensyn til gjeldende filer. Valg og stor forhåndsvisning oppdateres sammen. Hvis det valgte bildet forsvinner, velges et eksisterende bilde eller forhåndsvisningen tømmes. Bilder-området har også eget bildevalg og sletting med bekreftelse.

## Andre visninger

- **Oversikt:** aktiv kommandør, skip, posisjon, journalgjenkjenning, åpne oppdrag og nettstatus.
- **Oppdrag:** varig lagrede åpne oppdrag med kjente mål, fremdrift og fullføringsstatus. Manglende opplysninger blir ikke fylt inn eller diktet opp.
- **CMDR:** formue, grader, statistikk, MercCoins, skip/flåte og kjent Fleet Carrier-posisjon. MercCoins vises som totalverdier rapportert av Frontier, ikke som en egenberegnet saldo.
- **Ruteplanlegger:** separat planlegging for skip og Fleet Carrier med Spansh. Beregnede carrierruter kan eksporteres som CSV for CTSVision. Beregningen krever forbindelse til den eksterne tjenesten.

## Kommandør, lokale data og nettjenester

CMDRHelper identifiserer den aktive kommandøren med Frontier-ID fra den gjeldende journalsesjonen. Personlig utforskning, oppdrag, formue, favoritter og nettilganger lagres separat. Bare det å vise en annen kommandør endrer verken den aktive sanntidskommandøren eller tilordningen av opplastinger.

Den lokale SQLite-databasen bevarer kjente systemer, himmellegemer og personlig historikk etter omstart. Nye fullstendige journaloppføringer behandles under spilling; lagrede leseposisjoner unngår unødvendig ny gjennomlesing. Hvis posisjon eller kommandør er feil, sjekk først journalgjenkjenningen og journalmappen i innstillingene.

**EDSM** kan levere supplerende systemdata. Støttede journaldata kan sendes til **EDSM og Inara** når tjenesten er konfigurert og aktivert med den aktive kommandørens egne tilgangsdata. En kommandør bruker ikke automatisk en annens API-nøkkel. Lokal lagring fungerer uavhengig av en tilgjengelig nettforbindelse.

## Språk og konteksthjelp

Grensesnittet støtter **12 språk**: **DE, EN, FR, IT, NO, SV, FI, PL, NL, ES, TR, EL** – tysk, engelsk, fransk, italiensk, norsk, svensk, finsk, polsk, nederlandsk, spansk, tyrkisk og gresk.

Det finnes nå **937 UI-i18n-nøkler per språk**. **? Hjelp** gir **10 utførlige kontekstuelle hjelpetemaer på alle 12 språk**. Favoritter inngår i Explorer-hjelpen; planetnavigasjon har et eget tema som kan åpnes direkte fra navigatoren. Hjelpen bruker gjeldende grensesnittspråk og beholder tysk som reserve hvis en katalog eller oppføring mangler.

## Forutsetninger

| Plattform | Python |
| --- | --- |
| **Windows** | **Python 3.10 eller nyere, x64 kreves.** Ingen kunstig øvre grense for eksisterende versjoner. Faktiske pakke- og importkontroller avgjør deretter om miljøet fungerer. |
| **Linux** | **Python 3.10 eller nyere**, 64-bit anbefales. venv-modulen for den aktuelle Python-versjonen må være tilgjengelig. |

Nødvendige pakker står i `requirements.txt`:

```text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

Installasjonen laster ned disse avhengighetene. Lokale Elite-filer må være tilgjengelige for journalanalyse og planetnavigasjon. Under Linux kan Elite kjøre gjennom Steam/Proton; de faktiske journal- og skjermbildestiene angis i CMDRHelper. Linux-HUD-støtten beskrevet ovenfor gjelder X11.

## Installasjon under Linux

Pakk ut hele prosjektet eller utgivelsen og kjør i prosjektmappen:

```bash
./install.sh
./start.sh
```

Skriptene bruker utelukkende denne installasjonens lokale `venv`. De løser symbolske skriptlenker, sjekker Python og pip og kan reparere et skadet lokalt miljø uten å berøre personlige data eller Elite-journaler. Manglende systempakker installeres ikke automatisk; installasjonsprogrammet melder fra hvis venv-modulen mangler. Den eksisterende Linux-installasjonsmåten er uendret.

## Installasjon under Windows

1. Pakk ut hele ZIP-filen i en egen mappe.
2. Start **install.bat**, som kjører den medfølgende **install-windows.ps1**.
3. Etter vellykket installasjon starter du CMDRHelper med **start.bat**.

Eksisterende **Python fra 3.10 og nyere, x64**, godtas uten kunstig versjonstak. En fremtidig Python-versjon avvises ikke bare på grunn av versjonsnummeret. En passende eksisterende Python eller et brukbart lokalt venv hindrer unødvendig automatisk Python-installasjon.

Hvis ingen passende Python finnes, tilbyr installasjonsprogrammet automatisk installasjon via **winget** etter samtykke. Den faste versjonsserien **Python 3.14 x64** er bevisst valgt til dette; valget er atskilt fra den åpne regelen for eksisterende Python-versjoner. Hvis automatisk installasjon ikke er mulig, meldes feilen.

Installasjonsprogrammet oppretter, sjekker eller reparerer bare det **lokale venv-et til denne CMDRHelper-kopien**, installerer avhengighetene og kjører **pip check** og importkontroller for **PySide6, PySide6.QtWidgets, numpy og PIL**. Bare disse faktiske kontrollene avgjør om miljøet kan brukes. Hvis de mislykkes, stopper installasjonen med en forståelig feilmelding. Andre virtuelle miljøer repareres eller erstattes ikke.

## Diagnostikk og utgivelsespakker

Ved problemer hjelper journal- og nettstatusindikatorene samt loggfilene i `logs`-mappen. Personlige data lagres lokalt; en sikkerhetskopi av favorittene må inneholde deres interne bildekopier i tillegg til databasen.

Bruk `./create_release.sh` for å lage en egen utgivelsespakke. Programversjonen styres sentralt i `cmdrhelper/version.py` og leses av utgivelsesskriptet. Pakken inneholder programkode og ressurser, men ingen personlig database, venv, Git- eller hurtigbufferfiler.

## Bilde- og videomateriale / Media Credits

CMDRHelper bruker visualiseringer fra **NASA Scientific Visualization
Studio (NASA SVS)** for enkelte spesielle astronomiske objekter. De
respektive mediene forblir rettighetshavernes eiendom og krediteres i
henhold til opplysningene på NASA SVS-sidene.

### Nøytronstjerne

-   CMDRHelper-fil: `star_neutron.webm`
-   Kilde: NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatører: Walt Feimer (KBR Wyle Services, LLC) og Lisa Poje (USRA)
-   Kilde: https://svs.gsfc.nasa.gov/20267/

### Sort hull

-   CMDRHelper-fil: `black_hole.mp4` eller videofilendelsen som brukes i
    prosjektet
-   Kilde: NASA Scientific Visualization Studio, **Black Hole Accretion
    Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Kilde: https://svs.gsfc.nasa.gov/13326/

### Supermassivt sort hull

-   CMDRHelper-fil: `black_hole_supermassive.mp4` eller videofilendelsen
    som brukes i prosjektet
-   Kilde: NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Kilde: https://svs.gsfc.nasa.gov/14576/

### Hvit dverg

-   CMDRHelper-fil: `star_white_dwarf.webm`
-   brukt NASA-medium: **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Kilde: NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatør: Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Kilde: https://svs.gsfc.nasa.gov/20344/

Oppføringen av disse kildene og creditene betyr ikke at CMDRHelper
støttes, sertifiseres eller utgis av NASA. Ved videre bruk av
NASA-mediene gjelder de respektive merknadene og retningslinjene for
reproduksjon fra originalkildene.

## Lisens

CMDRHelper er fri programvare og publiseres under **GNU General Public
License Version 3 (GPL-3.0)**.

Kildekoden kan brukes, endres og distribueres videre i henhold til
vilkårene i GPL-3.0. Ved distribusjon av avledede versjoner gjelder også
vilkårene i GPL-3.0.

Copyright © 2026 **Holger Mangold (Faber38)**.

De fullstendige lisensvilkårene finnes i filen `LICENSE`.

## Merknad om Elite Dangerous

CMDRHelper er et uavhengig community-/hobbyprosjekt og ikke et offisielt
produkt fra Frontier Developments.

**Elite Dangerous** og tilhørende navn og innhold tilhører sine
respektive rettighetshavere.
