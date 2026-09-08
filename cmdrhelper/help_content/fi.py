"""Finnish content for contextual help."""


HELP_TOPICS = {'overview': ('Yleiskatsaus',
              '<h2>Yleiskatsaus</h2>\n'
              '<p>Yleiskatsaus on CMDRHelper:n kotisivu. Se tiivistää tärkeimmät tiedot tällä '
              'hetkellä aktiivisesta komentajasta ja näyttää yhdellä silmäyksellä, tunnistetaanko '
              'päiväkirja, sijainti ja online-palvelut oikein.</p>\n'
              '\n'
              '<h3>Komentaja & laiva</h3>\n'
              '<p>Elite Dangerous Journalista tunnistettu komentaja ja tällä hetkellä käytössä '
              'oleva alus näkyvät tässä.</p>\n'
              '<p>CMDRHelper määrittää henkilötiedot vastaavalle komentajalle Frontier-tunnuksen '
              '(FID) perusteella. Tämä pitää eri komentajien tiedot erillään toisistaan.</p>\n'
              '<p>Kun vaihdat komentoa, uuteen komentajaan liittyvät tallennetut tiedot '
              'ladataan.</p>\n'
              '\n'
              '<h3>päiväkirja</h3>\n'
              '<p>CMDRHelper käyttää Elite Dangerous:n päiväkirjatiedostoja päätietolähteenä.</p>\n'
              '<p>Päiväkirjanäyttö ilmoittaa, onko päiväkirjatiedostoja löydetty ja määritetty '
              'aktiiviselle komentajalle. Uudet täydelliset päiväkirjamerkinnät käsitellään '
              'automaattisesti pelin aikana.</p>\n'
              '<p>Jo käsitellyt lokialueet tallennetaan, jotta CMDRHelper:n ei tarvitse arvioida '
              'jokaista kirjauskansiota täysin uudelleen seuraavan käynnistyksen yhteydessä.</p>\n'
              '\n'
              '<h3>Nykyinen sijainti</h3>\n'
              '<p>Näyttää tällä hetkellä tunnetun tähtijärjestelmän ja - sikäli kuin päiväkirjasta '
              'tiedetään - komentajan tarkan sijainnin.</p>\n'
              '<p>Sijainnin päivittävät tapahtumat, kuten hyppyt, telakointi ja muut '
              'sijaintiraportit, ja ne tallennetaan komentokohtaisesti.</p>\n'
              '\n'
              '<h3>Tehtävät</h3>\n'
              '<p>Tämä alue näyttää tällä hetkellä tunnettujen avoimien tehtävien määrän.</p>\n'
              '<p>"Tehtävät"-painike tai valikkokohta vie sinut koko tehtävänäkymään, jossa on '
              'tunnetut tehtävän tavoitteet ja tilatiedot.</p>\n'
              '\n'
              '<h3>Viimeinen seisoo</h3>\n'
              '<p>"Viimeinen tila" tiivistää viimeisimmän tunnetun jatkuvan komentajan tilan. Näin '
              'tärkeät tiedot voidaan palauttaa myös Elite Dangerous:n tai CMDRHelper:n '
              'uudelleenkäynnistyksen jälkeen.</p>\n'
              '\n'
              '<h3>Lopulliset järjestelmät</h3>\n'
              '<p>Tässä näkyvät äskettäin vieraillut tai päiväkirjasta tunnistetut '
              'järjestelmät.</p>\n'
              '<p>Lista toimii nopeana yleiskatsauksena komentajan viimeaikaisesta matkasta.</p>\n'
              '<p>Vierailuhistoria huomioi Location-, FSDJump- ja CarrierJump-tapahtumat myös reaaliaikaisessa päiväkirjaseurannassa. Useat sijaintitapahtumat saman keskeytymättömän oleskelun aikana ovat yksi vierailu: A → A → A lasketaan kerran. Todellinen paluu säilyy: A → B → C → A lasketaan neljäksi vierailuksi.</p>\n\n'
              '<h3>Online-tila</h3>\n'
              '<p>Pääikkunan yläosassa on muita tilailmaisimia:</p>\n'
              '<ul>\n'
              '<li><b>Lehti tunnustettu</b>– CMDRHelper havaitsi kelvollisen lokilähteen ja '
              'komentajan identiteetin.</li>\n'
              '<li><b>EDSM</b>– näyttää EDSM-lähetyksen nykyisen tilan aktiiviselle lokille '
              'FID.</li>\n'
              '<li><b>INARA</b>– näyttää aktiivisen lokin FID Inara-lähetyksen nykyisen '
              'tilan.</li>\n'
              '</ul>\n'
              '<p>Online-käyttötietoja hallitaan erikseen jokaiselle komentajalle. Päällikkö ei '
              'koskaan käytä automaattisesti toisen komentajan API-Key:tä.</p>\n'
              '\n'
              '<h3>Tärkeää useille komentajille</h3>\n'
              '<p>Reaaliaikaiset tiedot riippuvat aina komentajasta, jonka nykyinen Elite '
              'Dangerous -päiväkirjaistunto selvästi tunnistaa.</p>\n'
              '<p>Pelkästään toisen ohjaimen näyttäminen näkymässä ei muuta aktiivista '
              'live-ohjainta tai vaikuta mihinkään EDSM- tai Inara-lähetykseen.</p>\n'
              '\n'
              '<h3>Kärki</h3>\n'
              '<p>Jos komentaja, laiva tai sijainti ei vastaa pelin nykyistä tilaa, tarkista ensin '
              'yläreunassa oleva päiväkirjanäyttö ja sitten "Asetukset" -kohdassa asetettu '
              'päiväkirjakansio.</p>'),
 'missions': ('Tehtävät',
              '<h2>Tehtävät</h2>\n'
              '<p>Tehtävänäkymä näyttää Elite Dangerous Journalista tunnetun tällä hetkellä '
              'tarkasteltavan komentajan tehtävät. CMDRHelper tallentaa tehtävätiedot '
              'komentokohtaisesti, jotta avoimet tehtävät säilyvät myös Elite Dangerous:n tai '
              'CMDRHelper:n uudelleenkäynnistyksen jälkeen.</p>\n'
              '\n'
              '<h3>Avoimet tehtävät</h3>\n'
              '<p>Uusia tehtäviä on tulossa<code>MissionAccepted</code>otettu haltuun ja '
              'tallennettu pysyvästi.</p>\n'
              '<p>Niin kauan kuin viimeistä tehtävätapahtumaa ei ole, tehtävä pysyy avoinna. Uusi '
              'peliistunto ilman tehtäväluetteloa ei välttämättä poista automaattisesti tunnettuja '
              'avoimia tehtäviä.</p>\n'
              '\n'
              '<h3>Tehtävän tila</h3>\n'
              '<p>CMDRHelper käsittelee muun muassa seuraavat tilamuutokset:</p>\n'
              '<ul>\n'
              '<li>Tehtävä hyväksytty</li>\n'
              '<li>Tehtävä suoritettu</li>\n'
              '<li>Tehtävä epäonnistui</li>\n'
              '<li>Tehtävä keskeytetty</li>\n'
              '<li>Tehtävän tavoite on muutettu</li>\n'
              '<li>Edistyminen tuetuissa lasti-/varastotehtävissä</li>\n'
              '</ul>\n'
              '<p>Viimeinen tapahtuma muuttaa vain siihen liittyvää tehtävää.</p>\n'
              '\n'
              '<h3>Tehtävät lehdestä</h3>\n'
              '<p>Elite Dangerous tarjoaa tietoa erilaisista päivälehtien tapahtumista. CMDRHelper '
              'yhdistää nämä tapahtumat jatkuvaan tehtävätilaan.</p>\n'
              '<p>Todellinen täyden tehtävän tapahtuma voi toimia arvovaltaisena tilannekuvana. '
              'Jos tällainen tapahtuma puuttuu, vanhempia avoimia tehtäviä ei suljeta pelkästään '
              'tästä syystä.</p>\n'
              '\n'
              '<h3>Kohteet ja paikat</h3>\n'
              '<p>Siltä osin kuin Elite tarjoaa tiedot lehdessä, CMDRHelper näyttää:</p>\n'
              '<ul>\n'
              '<li>Kohdejärjestelmä</li>\n'
              '<li>Kohdeasema tai määränpää</li>\n'
              '<li>Kohdeplaneetta tai -keho</li>\n'
              '<li>Tehtävän nimitys</li>\n'
              '<li>tiedossa oleva edistys</li>\n'
              '<li>nykyinen tila</li>\n'
              '</ul>\n'
              '<p>Kaikki tehtävät eivät tarjoa kaikkea tietoa. Puuttuvat tiedot eivät ole '
              'CMDRHelper:n keksimiä.</p>\n'
              '\n'
              '<h3>Pysyvyys ja uudelleenkäynnistys</h3>\n'
              '<p>Avoimet tehtävät tallennetaan komentajaan liittyvään tietokantaan.</p>\n'
              '<p>Tämä tarkoittaa, että ne säilytetään, vaikka:</p>\n'
              '<ul>\n'
              '<li>Elite Dangerous lopetetaan ja käynnistetään uudelleen myöhemmin</li>\n'
              '<li>CMDRHelper on suljettu välissä</li>\n'
              '<li>Uusi päiväkirjaistunto ei aluksi sisällä yhtään lähetystapahtumaa</li>\n'
              '</ul>\n'
              '<p>Vain dokumentoitu tehtävätapahtuma muuttaa tallennettua tilaa.</p>\n'
              '\n'
              '<h3>Useita komentajia</h3>\n'
              '<p>Komentaja erottaa tehtävät tiukasti.</p>\n'
              '<p>Tehtävätapahtuma osoitetaan vain komentajalle, jonka päiväkirja-istunto on '
              'yksilöllisesti tunnistettu. Toisen komentajan tehtäviä ei saa näyttää tai '
              'muokata.</p>\n'
              '\n'
              '<h3>Orvot tai ei enää voimassa olevat tehtävät</h3>\n'
              '<p>Jos vanhemmat päiväkirjatiedot tai aiempi tuonti pitää tehtävän auki, vaikka '
              'sitä ei enää olisi pelissä, olemassa olevaa orpotehtävän '
              'nollaus-/puhdistusominaisuutta voidaan käyttää.</p>\n'
              '<p>Tätä toimintoa tulee käyttää vain, jos on selvää, että näytettävä tehtävä ei ole '
              'enää aktiivinen.</p>\n'
              '\n'
              '<h3>Online-palvelut</h3>\n'
              '<p>Tuetut tehtävätapahtumat voidaan lisäksi lähettää Inara:lle, jos aktiiviselle '
              'päiväkirjalle FID on määritetty kelvollinen ja aktivoitu Inara-käyttöoikeus.</p>\n'
              '<p>Puuttuva tai tavoittamaton Inara-yhteys ei vaikuta paikallisen tehtävän '
              'tallennustilaan.</p>\n'
              '\n'
              '<h3>Kärki</h3>\n'
              '<p>Jos tehtävä ei tule näkyviin tai sen tila on virheellinen, tarkista ensin, onko '
              'Elite Dangerous jo kirjoittanut vastaavan tehtävätapahtuman päiväkirjaan.</p>\n'
              '<p>CMDRHelper voi näyttää vain tiedot, jotka päiväkirja todella tarjoaa tai jotka '
              'on jo tallennettu aikaisemmista ainutlaatuisista tehtävätapahtumista.</p>'),
 'explorer': ('Tutkimusmatkailija',
              '<h2>Tutkimusmatkailija</h2>\n'
              '<p>Explorer arvioi aktiivisen komentajan löytämät ja skannaamat järjestelmät ja '
              'taivaankappaleet. Se yhdistää omat Elite Dangerous -päiväkirjatietosi jo saatavilla '
              'oleviin lisätietoihin ja näyttää yhdessä etsintä-, kartografia-, '
              'biologiset/geologiset signaalit ja pintakaivostiedot.</p>\n'
              '\n'
              '<h3>Nykyinen järjestelmä</h3>\n'
              '<p>Tämänhetkinen tiedon taso järjestelmästä on tiivistetty yläosassa.</p>\n'
              '<p>Näitä ovat muun muassa:</p>\n'
              '<ul>\n'
              '<li>tunnetut ja jopa kirjatut ruumiit lehdessä</li>\n'
              '<li>olemassa olevia signaaleja</li>\n'
              '<li>Skannaa arvot</li>\n'
              '<li>kartografinen arvo on jo saavutettu</li>\n'
              '<li>mahdollinen kokonaisarvo, jos se on täysin kartoitettu</li>\n'
              '<li>BIO-tila ja arvioidut BIO-arvot</li>\n'
              '<li>Kartografia ja BIO-tiedot, joita ei ole vielä toimitettu</li>\n'
              '</ul>\n'
              '<p>Näytetyt arvot perustuvat tosiasiallisesti saatavilla oleviin tietoihin. '
              'Puuttuvaa tietoa ei esitetä erillisenä löydönä.</p>\n'
              '\n'
              '<h3>Järjestelmän kartta</h3>\n'
              '<p>Järjestelmäkartta esittää graafisesti tähdet, planeetat, kuut ja muut nykyisen '
              'järjestelmän tunnetut kappaleet.</p>\n'
              '<p>Runkoa voidaan napsauttaa avataksesi sen yksityiskohtaisen näkymän.</p>\n'
              '<p>Näytöllä näkyy muun muassa kehon tyyppi, etäisyys ja – jos saatavilla – '
              'skannaus- ja kartografiaarvot sekä erityiset etsintäominaisuudet.</p>\n'
              '\n'
              '<h3>ORGAANISET ×N</h3>\n'
              '<p>BIO ×N tarkoittaa pelin ilmoittamien kehon biologisten signaalien määrää.</p>\n'
              '<p>Numero kertoo aluksi vain, kuinka monta biologista signaalia tai sukua on '
              'raportoitu. Se ei automaattisesti tarkoita, että kaikki biologiset lajit on jo '
              'löydetty tai analysoitu.</p>\n'
              '<p>Varsinaiset omat orgaaniset löydöt säilytetään erikseen.</p>\n'
              '\n'
              '<h3>GEO ×N</h3>\n'
              '<p>GEO ×N näyttää pelin ilmoittamien ruumiin geologisten signaalien määrän.</p>\n'
              '<p>Näitä voivat olla esimerkiksi geologiset piirteet, kuten fumarolit tai geysirit. '
              'CMDRHelper näyttää vain tiedot, jotka näkyvät olemassa olevista '
              'päiväkirja-/runkotiedoista.</p>\n'
              '\n'
              '<h3>ABBAU ×N</h3>\n'
              '<p>ABBAU ×N näyttää Elite Dangerous:n ilmoittaman kappaleen planeettojen '
              'louhintapaikkojen määrän.</p>\n'
              '<p>Esimerkki:</p>\n'
              '<p><b>ABBAU ×24</b></p>\n'
              '<p>tarkoittaa, että tälle ruumiille on raportoitu 24 planeetan kaivospaikkaa.</p>\n'
              '<p>Numero ei kerro, mitä raaka-ainetta voidaan louhia yhdessä paikassa.</p>\n'
              '\n'
              '<h3>Omat kaivoslöydöt</h3>\n'
              '<p>Jos päällikkö on todella tehnyt pintalouhintaa Rhino:lla, CMDRHelper tallentaa '
              'henkilökohtaiset löydökset dokumentoidusti erikseen.</p>\n'
              '<p>Tehdään ero:</p>\n'
              '<ul>\n'
              '<li>tosiasiallisesti hankittuja hyödykkeitä, esim. B. Kupari tonneina</li>\n'
              '<li>louhinnan aikana kerätyt toissijaiset materiaalit</li>\n'
              '<li>kehon yleiset pintamateriaalit</li>\n'
              '</ul>\n'
              '<p>Esimerkki henkilökohtaisesta löydöstä olisi:</p>\n'
              '<p><b>Kupari - 56 t</b></p>\n'
              '<p>Tämä tieto tarkoittaa, että tämä komentaja louhi siellä 56 tonnia kuparia.</p>\n'
              '<p>Henkilökohtaiset kaivoslöydöt tallennetaan jokaiselle komentajalle, eikä niitä '
              'sekoiteta muiden komentajien löytöihin.</p>\n'
              '\n'
              '<h3>Rungon pintamateriaalit</h3>\n'
              '<p><code>Scan.Materials</code>kuvaa kappaleen yleistä '
              'pintamateriaalikoostumusta.</p>\n'
              '<p>Esimerkiksi rauta, nikkeli, rikki tai muut materiaalit voidaan näyttää '
              'prosenttiarvoilla.</p>\n'
              '<p>Näitä arvoja ei pidä sekoittaa planeetan kaivosvaraston raaka-aineisiin. '
              'Frontier ei tarjoa mitään dokumentoitua suoraa yhteyttä näiden yleisten '
              'materiaalien ja lehdessä julkaistun yksittäisen kaivosalueen sisällön välillä.</p>\n'
              '\n'
              '<h3>Terraformointi</h3>\n'
              '<p>Maanmuokkauksen symboli tai etiketti osoittaa, että kappaletta pidetään '
              'maanmuokkausehdokkaana käytettävissä olevien tietojen perusteella.</p>\n'
              '\n'
              '<h3>Ensimmäinen löytö</h3>\n'
              '<p>”Jo löydetty skannauksesi aikaan” kuvaa tilannetta ennen silloista skannaustasi. Kyllä tarkoittaa aiemmin löydettyä, Ei tarkoittaa ettei sitä ollut vielä silloin löydetty; puuttuva tieto pysyy Tuntemattomana. ★ merkitsee First Discovery -ehdokasta skannaushetkellä, ei taattua virallista ensilöytöä, joka olisi yhä saatavilla tänään.</p>\n<p>Historiallinen WasDiscovered=false tai WasMapped=false ei tarkoita, että taivaankappale olisi edelleen löytämätön tai kartoittamaton tänään. Havainnot pysyvät historiallisina tietojen myynnin ja uusintavierailun jälkeen. Tunnettuus EDSM:ssä on erillinen tieto eikä todista virallista löytöä Elitessä. Siitä ei päätellä virallista ensilöytäjää.</p>\n'
              '\n'
              '<h3>Ensimmäinen kartoitus</h3>\n'
              '<p>CMDRHelper erottaa:</p>\n'
              '<ul>\n'
              '<li>◉ First Mapping -ehdokas skannaushetkellä: ei vielä kartoitettu, kun skannasit sen</li>\n<li>◎ Sinun kartoittamasi: oma valmis DSS-kartoituksesi on kirjattu</li>\n<li>◉✓ Ehdokkuus skannaushetkellä ja oma kartoitus todettu; virallista ensisijaisuutta ei vahvistettu</li>\n'
              '</ul>\n'
              '<p>”Jo kartoitettu skannauksesi aikaan” arvioidaan erillään löydöstä. Puuttuva tieto pysyy Tuntemattomana. Jo löydetty taivaankappale saattoi olla kartoittamaton skannaushetkellä. Oma kartoituksesi ei vahvista virallista First Mapping -merkintää; useiden vierailujen jälkeen järjestys suhteessa tallennettuun skannaukseenkaan ei ole aina todistettavissa.</p>\n<p>Oman DSS-kartoituksen valmistuminen tallentaa nyt luotettavasti kartoitusajan, käytetyt luotaimet ja tehokkuustavoitteen. Myöhemmät skannaukset eivät enää hävitä olemassa olevia tietoja.</p>\n'
              '\n'
              '<h3>Maalaisbaari</h3>\n'
              '<p>Laskeutuvuusindikaattori tunnistaa kappaleet, joille laskeutuminen on tiedossa '
              'olevien tietojen mukaan mahdollista.</p>\n'
              '\n'
              '<h3>Kultaiset kehykset / arvokkaat rungot</h3>\n'
              '<p>Erityisen arvokkaat ruumiit voidaan korostaa tutkijanäytössä.</p>\n'
              '<p>Kultainen kehys merkitsee asetetun kynnyksen ylittävää kartoitusarviota. Se ei ole First Discovery -merkintä eikä vahvista myymättömiä tietoja tai yhä saatavilla olevia ensilöytö- tai ensikartoitusbonuksia.</p>\n'
              '<p>Se ei korvaa kehon arvon yksityiskohtaista näyttöä.</p>\n'
              '\n'
              '<h3>Luettelo arvoista</h3>\n'
              '<p>Arvoluettelo näyttää tallennettuun skannaukseen perustuvia arvioita, ei taattuja maksamatta olevia palkkioita. Ensibonukset pysyvät vahvistamattomina. Kartan ja luettelon vihjetekstit sekä kappaleen tiedot käyttävät samoja ajallisesti rajattuja tiloja.</p>\n'
              '<p>Se sopii erityisen hyvin mielenkiintoisten tai arvokkaiden kappaleiden nopeaan '
              'vertailuun systeemissä.</p>\n'
              '\n'
              '<h3>ORGAANISET / GEO / HAJOAMINEN</h3>\n'
              '<p>Tämä näkymä ryhmittelee kappaleet, joilla on biologisia, geologisia tai '
              'planeettojen hajoamissignaaleja.</p>\n'
              '<p>Tämä tarkoittaa, että mielenkiintoisia kappaleita ei tarvitse etsiä yksitellen '
              'täydellisestä järjestelmäkartasta.</p>\n'
              '<p>Jos sinulla on omat pintakaivostietosi, voivat myös henkilökohtaiset '
              'kaivoslöydösi olla näkyvissä.</p>\n'
              '<p>Explorerin yhteisen BIO / GEO / ABBAU -taulukon käsin muutetut sarakeleveydet säilyvät uudelleen avattaessa ja ohjelman käynnistyessä uudelleen. Ponnahdusikkunoiden sarakeleveydet palautetaan luotettavammin; virheelliset arvot korvataan turvallisilla oletusleveyksillä.</p>\n\n'
              '<h3>Rungon yksityiskohta</h3>\n'
              '<p>Tekstin napsauttaminen avaa yksityiskohtaisen näkymän.</p>\n'
              '<p>Sikäli kuin tiedetään, siellä voi esiintyä seuraavaa:</p>\n'
              '<ul>\n'
              '<li>Vartalotyyppi</li>\n'
              '<li>massa</li>\n'
              '<li>etäisyys</li>\n'
              '<li>Painovoima</li>\n'
              '<li>tunnelmaa</li>\n'
              '<li>Maistuvuus</li>\n'
              '<li>Terraformoiva tila</li>\n'
              '<li>BIO/GEO-signaalit</li>\n'
              '<li>planetaariset kaivospaikat</li>\n'
              '<li>Pintamateriaalit</li>\n'
              '<li>omia kaivoslöytöjä</li>\n'
              '<li>Skannausarvo</li>\n'
              '<li>kartografinen arvo</li>\n'
              '<li>nykyinen arvo</li>\n'
              '</ul>\n'
              '<p>Kaikilla kehoilla ei ole kaikkea tietoa.</p>\n'
              '\n'
              '<h3>BIO ennusteet</h3>\n'
              '<p>CMDRHelper voi arvioida mahdollisia biologisia löytöjä sopivien kappaleiden '
              'olemassa olevien tietojen perusteella.</p>\n'
              '<p>Ennusteet eivät takaa, että tietty laji todella esiintyy. Ne toimivat '
              'tutkimuksen apuna päätöksenteossa.</p>\n'
              '<p>Arvioidut BIO-arvot ovat myös ennusteita ja niitä käsitellään erillään '
              'todellisista vahvistetuista löydöistä.</p>\n'
              '\n'
              '<h3>Ei vielä lähetetty</h3>\n'
              '<p>CMDRHelper ylläpitää komentajaan liittyviä tunnettuja kartografia- ja '
              'BIO-tietoja, joita ei ole vielä lähetetty.</p>\n'
              '<p>Kartografian myynti ja biologiset rojaltit on kirjattu vastaavien '
              'lehtitapahtumien avulla.</p>\n'
              '<p>Jo myyty karttatieto ei saa näkyä uudelleen avoimina jälleenrakennuksen '
              'jälkeen.</p>\n'
              '\n'
              '<h3>Näytä auto</h3>\n'
              '<p>Tuetut Explorer-vinkit, kuten arvokkaat ruumiit tai BIO-löydöt, voidaan näyttää '
              'automaattisesti käyttämällä vasemman sivupalkin kytkimiä.</p>\n'
              '<p>Nämä pienet live-ikkunat toimivat lisävinkkeinä pelatessasi eivätkä korvaa koko '
              'Explorer-näkymää.</p>\n'
              '<p>”Cargo” näyttää aktiivisen Journal-FID:n määrittämän Ship- tai SRV-ajoneuvon vahvistetun lastin. SRV Cargo -sisältöä ei koskaan oteta Ship Cargo -sisällöksi; Limpets lasketaan kokonaiskuormaan ja näytetään erikseen Nimi | Määrä -taulukossa.</p>\n'
              '<p>BIO-edistyminen näkyy tiiviisti: 1/3 keltaisena, 2/3 sinisenä ja 3/3 vihreänä; valmis tila ”Valmis” on myös vihreä. Kohdassa ”näytä automaattisesti” GEO:lla on oma tallennettava kytkin: vain BIO, vain GEO tai molemmat yhdessä.</p>\n<p>Rahti-ikkuna sovittaa korkeutensa automaattisesti sisältöön. Monilla riveillä korkeus rajataan ja taulukkoa voi vierittää; valittu leveys ja ikkunan sijainti säilyvät. Nykyinen ”Rahtitilan HUD”-kytkin on nyt kohdassa ”näytä automaattisesti”, ilman toista kytkintä rahti-ikkunassa.</p>\n\n'
              '<h3>Useita komentajia</h3>\n'
              '<p>Henkilökohtaiset etsintätulokset, kartografiat, BIO-löydöt ja omat '
              'pintakaivoslöydöt määrätään kullekin komentajalle.</p>\n'
              '<p>Kehon globaalit tähtitieteelliset ominaisuudet - esimerkiksi tunnettujen '
              'planeettojen kaivospaikkojen lukumäärä - pysyvät kehon itsensä ominaisuuksina.</p>\n'
              '\n'
              '<h3>Kärki</h3>\n'
              '<p>Jos sinulla on mielenkiintoinen runko, kannattaa klikata yksityiskohtaista '
              'näkymää. Tämä on paras paikka erottaa yleiset ruumiintiedot, mahdolliset '
              'etsintätulokset ja todelliset oman komentajasi dokumentoimat löydöt.</p>'
              """

<h3>★ Suosikit</h3>
<p>Explorerin yläosan ”★ Suosikit”-painike avaa erillisen, uudelleen käytettävän suosikki-ikkunan. Siellä voit tallentaa järjestelmiä, planeettoja/kuita ja pinnalla sijaitsevia paikkoja aktiiviselle komentajalle.</p>
<p>Nimen mukaan aakkostettu, vieritettävä luettelo näyttää nimen, tyypin, järjestelmän, tarvittaessa taivaankappaleen ja leveys-/pituusasteen, luokan sekä pienen kuvan esikatselun. Vapaatekstihakua sekä tyyppi- ja luokkasuodattimia voi käyttää yhdessä. Haku kattaa nimen, järjestelmän, taivaankappaleen ja muistiinpanon.</p>
<p>”Avaa / Näytä” näyttää tallennetut tiedot, muistiinpanon ja suuremman kuvan esikatselun. ”Näytä Explorerissa” avaa olemassa olevan järjestelmän yleiskuvan tai taivaankappaleen tietonäkymän, jos suosikki kuuluu Explorerin nykyiseen järjestelmään ja vastaavat tiedot ovat saatavilla. Muiden järjestelmien suosikkien tallennetut tiedot pysyvät näkyvissä; järjestelmien välistä reittiä ei lasketa.</p>

<h3>Järjestelmän, planeetan tai nykyisen sijainnin tallentaminen</h3>
<ul>
<li>”★ Tallenna nykyinen järjestelmä” tallentaa nykyisen järjestelmän ilman pintakoordinaatteja.</li>
<li>”★ Tallenna planeetta / kuu” antaa valita nykyisen järjestelmän tunnetun planeetan tai kuun. Tämäkään suosikki ei saa pintakoordinaatteja.</li>
<li>”★ Tallenna nykyinen sijainti” on suosikki-ikkunan yläosassa kahden muun tallennusvaihtoehdon vieressä, ja se on käytettävissä myös planeettanavigaattorissa. Suosikki-ikkunassa painike pysyy aina näkyvissä ja on poissa käytöstä, jos kelvolliset ajantasaiset planetaariset sijaintitiedot ja aktiivinen komentaja puuttuvat. Napsautus lukitsee komentajan, järjestelmän, taivaankappaleen, leveysasteen ja pituusasteen. Myöhemmät liikkeet pelissä eivät muuta näitä arvoja avoimessa valintaikkunassa.</li>
</ul>
<p>Anna haluamasi nimi ja valitse täsmälleen yksi luokka: Bio, Geo, Louhinta, Maisema, Laskeutumispaikka, Kiinnostava tai Muu. Muistiinpano ja kuva ovat valinnaisia. Tunnetut tekniset tunnisteet siirretään sisäisesti; sinun ei tarvitse syöttää niitä. Myös leveysaste tai pituusaste 0,0 on kelvollinen koordinaatti.</p>
<p>”Muokkaa” muuttaa nimeä, luokkaa, muistiinpanoa ja kuvaa. Järjestelmä, taivaankappale ja tallennetut koordinaatit säilyvät. Jos haluat tallentaa toisen paikan pinnalla, luo uusi suosikki kyseisessä sijainnissa.</p>

<h3>Pikasuosikki ilman hiirtä</h3>
<p>Kohdassa ”Asetukset → Pikasuosikki” voit vapaasti määrittää, vaihtaa tai poistaa yleisen pikanäppäimen. Asennuksen jälkeen sen oletus on ”Ei määritetty”: CMDRHelper ei rekisteröi mitään näppäintä pyytämättä. Määritys tallennetaan. Jos yhdistelmä on jo käytössä tai ei ole käytettävissä järjestelmässäsi, näyttöön tulee virheilmoitus; aiempi toimiva määritys säilytetään.</p>
<p>Linux/X11:ssä ja Windowsissa pikanäppäin toimii myös Eliten ollessa aktiivinen – jalan, SRV:ssä ja aluksessa. Näppäimen painallus tallentaa nykyisen sijainnin pinnalla heti aktiiviselle komentajalle ilman valintaikkunaa ja hiiren käyttöä. Komentaja, järjestelmä, taivaankappale ja nykyiset Latitude-/Longitude-arvot lukitaan sillä hetkellä. Ilman kelvollisia ajantasaisia planeettakoordinaatteja mitään ei tallenneta; aiempia koordinaatteja ei käytetä uudelleen.</p>
<p>Suosikki saa yksilöllisen väliaikaisen nimen, esimerkiksi ”Merkki 07.09.2026 06:32:15”, ja luokan ”Muu”. Tavallisessa suosikki-ikkunassa voit myöhemmin nimetä sen uudelleen, määrittää toisen luokan, lisätä muistiinpanon tai kuvan. Kuvakaappausta ei oteta eikä tuoda automaattisesti.</p>
<p>Noin kahden sekunnin ajan ”★ SUOSIKKI TALLENNETTU” näkyy suoraan aktiivisen Elite-ikkunan päällä yhdessä taivaankappaleen ja koordinaattien kanssa; jos sijainti puuttuu, ”⚠ EI PLANEETTAKOORDINAATTEJA” näkyy lyhyesti. Näyttö ei vie kohdistusta eikä kaappaa syötteitä. Se toimii myös navigointi-HUD:n ollessa pois päältä ja katoaa sitten kokonaan. Kun HUD on päällä, tavallinen navigointinäyttö jää näkyviin tämän jälkeen. HUD-kytkimen tallennettua asetusta ei muuteta. Näyttö käyttää samaa peittokuvan toteutusta ja samoja alustavaatimuksia kuin navigointi-HUD.</p>

<h3>Suosikkien kuvat</h3>
<p>Suosikkien kuvat ovat erillään Kuvat-osiosta. ”Valitse kuva …” hyväksyy PNG-, JPEG- ja WebP-kuvat. CMDRHelper kopioi valitun kuvan omaan suosikkikuvien kansioonsa vasta tallennettaessa. Alkuperäistä tiedostoa ei siirretä eikä muuteta.</p>
<p>”Käytä uusinta kuvakaappausta” lukee määritetyn kuvakaappausten lähdekansion uudelleen jokaisella napsautuksella ja etsii luettavia kuvakaappauksia, joilla on Elitelle tyypillinen tiedostonimi. Jos kansiota ei ole määritetty, käytetään Windowsin tai Steam/Protonin tavallisia Elite-kuvakaappauskansioita. Myös määritetyn muunnoskohteen aktiiviselle komentajalle kuuluva kansio käydään läpi vastaavien muunnettujen Elite-kuvakaappausten löytämiseksi. Muunnettu kuvakaappaus löytyy siten edelleen, vaikka sen alkuperäinen BMP olisi poistettu. Uusin kuvausaika määräytyy tiedostonimen yksiselitteisen aikaleiman mukaan tai muuten tiedostoajan mukaan; muunnetuissa kuvissa käytetään nimeen tallennettua kuvausaikaa muunnosajan sijaan. CMDRHelper ei itse ota kuvakaappauksia eikä etsi mielivaltaisista kuvakansioista.</p>
<p>Ennen käyttöä näytetään tiedostonimi, kuvausaika ja juuri ladattu esikatselu. Vahvista painamalla ”Käytä tätä kuvaa”. Jos sopivaa kuvakaappausta ei löydy, voit edelleen käyttää toimintoa ”Valitse kuva …”. Eliten BMP-kuvakaappaukset tallennetaan sisäisinä PNG-kopioina.</p>
<p>Kuvan voi korvata muokkausikkunassa tai poistaa valinnan painamalla ”Poista kuva”. Tallennettaessa poistetaan sisäinen kopio, jota ei enää käytetä. Jos kuvatiedosto puuttuu, suosikki on edelleen käytettävissä ilman esikatselua.</p>

<h3>Suosikkikohde ja komentaja</h3>
<p>Pinnalla sijaitsevien paikkojen ”▶ Kohteeseen” välittää tallennetun taivaankappaleen, leveysasteen, pituusasteen ja suosikin nimen olemassa olevalle planeettanavigaattorille. Uusi kohde korvaa aiemman. Suosikeilla ei ole omaa navigointilogiikkaa. Navigaattori päättää edelleen itse: vastaavat kelvolliset planetaariset tiedot aktivoivat navigoinnin; muuten se odottaa näitä tietoja.</p>
<p>Suosikit kuuluvat yksinomaan aktiiviselle komentajalle. Komentajan vaihtaminen päivittää luettelon ja hylkää avoimen muokkausikkunan. Kohde, jota käsitellään edelleen edellisen komentajan suosikkikohteena, lopetetaan. Kronikan komentajavalinta ei laajenna tätä suosikkiluetteloa.</p>
<p>”Poista” edellyttää vahvistusta ja poistaa vain suosikkitietueen ja sen sisäisen kuvakopion. Alkuperäinen kuvakaappaus tai valittu alkuperäinen kuva sekä kaikki Explorerin, lokin ja taivaankappaleiden tiedot säilyvät.</p>"""),
 'chronicle': (
        'Kronikka',
        """<h2>Kronikka</h2>
<p>Kronikka on komentajan henkilökohtainen matka- ja löytöhistoria. Se käyttää pysyvästi tallennettuja päiväkirjatietoja löytääkseen järjestelmiä, joissa on jo vierailtu, esittämään niitä spatiaalisesti ja etsimään tunnettuja löytöjä.</p>

<h3>Vieraillut järjestelmät</h3>
<p>Chronicle näyttää käydyt järjestelmät ja niiden sijainnit komentajan tiedossa galaksissa.</p>
<p>Jos saatavilla, ensimmäinen ja viimeinen käynti sekä tunnetut kehon tiedot otetaan huomioon.</p>
<p>Kun ajanjakso on käytössä, karttanäkymän käyntimäärä, ensimmäinen käynti ja viimeinen käynti koskevat suodatettuja todellisia järjestelmäkäyntejä.</p>
<p>Kronikka ei siis ole vain kartta, vaan myös työkalu aikaisempien matkakohteiden ja löytöjen löytämiseen.</p>

<h3>3D kartta</h3>
<p>Vieraillut järjestelmät on esitetty spatiaalisesti käyttämällä niiden galaktisia X/Y/Z-koordinaatteja.</p>
<p>Käyttöohjeet ovat suoraan kartan yläpuolella:</p>
<ul>
<li>Pidä hiiren vasenta painiketta painettuna → kierrä näkymää</li>
<li>pidä hiiren keskipainiketta painettuna ja vedä → piirrä zoomausikkuna</li>
<li>Pidä hiiren oikeaa painiketta painettuna → siirrä näkymää</li>
</ul>
<p>Pienen akselin näyttö auttaa avaruudessa suuntautumisessa.</p>

<h3>Nykyinen sijainti</h3>
<p>"Nykyinen sijainti" -toiminnolla karttanäkymä voidaan kohdistaa tai palauttaa aktiivisen komentajan tällä hetkellä tunnettuun sijaintiin.</p>
<p>Nykyiset suodattimet otetaan ensin käyttöön. Näkymä keskitetään nykyiseen järjestelmään vain, jos se sisältyy tuloksena olevaan karttaan.</p>
<p>Muussa tapauksessa näytetään ”Nykyinen järjestelmä ei sisälly tähän suodatinvalintaan.” Suodattimia ei tällöin poisteta.</p>

<h3>Kohdista</h3>
<p>”Kohdista” palauttaa suunnan galaksin tason ylhäältä katsottuun näkymään. Siirto ja zoomaus säilyvät.</p>
<p>Tästä on hyötyä, jos karttaa on kierretty paljon ja siitä on tullut vaikeaselkoinen.</p>

<h3>Päivitä Kronikka</h3>
<p>”Päivitä Kronikka” lataa kronikkatiedot uudelleen nykyisten yhdistettyjen suodattimien perusteella ja päivittää näkymän. Vapaa teksti, käyttöön otetut päivämäärärajat ja kaivossuodattimet arvioidaan jälleen yhdessä; aktiivisia suodattimia ei ohiteta.</p>
<p>Toiminto ei muuta päiväkirjatiedostoja tai luo uusia kartoitustietoja. Se yksinkertaisesti päivittää historianäytön olemassa olevien CMDRHelper-tietojen perusteella.</p>

<h3>Vapaa tekstihaku</h3>
<p>Jo tunnettua sisältöä voi hakea "Hakuhistoria..." -kentän avulla.</p>
<p>Haussa huomioidaan – mikäli tietokannassa on saatavilla – mm.</p>
<ul>
<li>Järjestelmän nimet</li>
<li>Kehon ominaisuudet</li>
<li>biologiset tiedot</li>
<li>Materiaalit</li>
<li>Codex-tiedot</li>
</ul>
<p>Vapaa teksti, ajanjakso ja kaivostoiminta ovat yhteisellä suodatinalueella. ”Käytä” arvioi asetetut suodattimet yhdessä. Enter vapaatekstikentässä käynnistää saman yhdistetyn suodatuksen kuin ”Käytä”.</p>

<h3>Ajanjakso Alkaen/Asti (UTC)</h3>
<p>Ota ”Alkaen” ja ”Asti” käyttöön omista valintaruuduistaan ja valitse haluamasi päivämäärä. Voit käyttää myös vain yhtä rajaa. Ilman valittua ruutua kyseisellä puolella ei ole aikarajoitusta; jos kumpaakaan ruutua ei ole valittu, ajanjaksoa ei rajata.</p>
<ul>
<li><b>Alkaen:</b> Valitun UTC-kalenteripäivän alusta alkaen, alkuhetki mukaan lukien.</li>
<li><b>Asti:</b> Koko valittu UTC-kalenteripäivä otetaan mukaan aina seuraavan päivän alkua edeltävään hetkeen saakka.</li>
</ul>
<p>UTC on koordinoitu yleisaika. Päivämäärärajat tarkoittavat UTC-kalenteripäiviä, eivät paikallisen aikavyöhykkeesi kalenteripäiviä.</p>
<p>Suodatus perustuu todellisiin järjestelmäkäynteihin taulussa <code>system_visits</code>. Kyseisen komentajan todellinen käynti ajanjakson sisällä on välttämätön. Tallennetut tiedot <code>first_seen</code> ja <code>last_seen</code> eivät korvaa oikeaa käyntiä: pelkkä ajanjakson sijoittuminen aiemman ensimmäisen ja myöhemmän viimeisen käynnin väliin ei riitä.</p>
<p>Ajanjakso suodattaa käyntejä, ei yksittäisiä löytö-, BIO-, GEO- tai kaivostapahtumia. Tunnettujen löytöjen tiedot ja louhitut määrät pysyvät tallennettuina kokonaisarvoina. Alkaen/Asti-rajoja voi käyttää yksinään tai yhdessä vapaan tekstin ja kaivossuodattimien kanssa.</p>
<p>Jos Alkaen on Asti-päivän jälkeen, näytetään ”Alkaen-päivämäärä ei saa olla Asti-päivämäärän jälkeen.” Tietokantakyselyä ei käynnistetä. Korjaa päivämäärärajat ja käytä suodattimia uudelleen.</p>

<h3>Hakutulokset</h3>
<p>Osumat näkyvät olemassa olevassa tulosluettelossa kronikkakortin alla.</p>
<p>Osumatyypistä riippuen näyttöön saattaa tulla järjestelmä ja runko sekä lisätietoja.</p>
<p>Osumalla voidaan etsiä vastaava jo tunnettu järjestelmä tai runko ja avata olemassa olevat yksityiskohtaiset tiedot.</p>

<h3>Ei osumia</h3>
<p>Jos kelvollinen suodatus ei löydä osumia, kartta ja reitit tyhjennetään. Tulosluettelo tyhjennetään ja piilotetaan, yksityiskohtanäyttö nollataan ja avoin kronikan järjestelmätietoikkuna suljetaan.</p>
<p>Vanhat tulokset eivät jää näkyviin. Tarkista tällöin hakutekstin, ajanjakson ja kaivossuodattimien yhdistelmä sekä kyseisessä näkymässä käytetty komentaja.</p>

<h3>Planeettojen kaivoskohteet</h3>
<p>Suodatinta "Planetary Mining sites" voidaan käyttää erityisesti sellaisten tunnettujen kappaleiden etsimiseen, joille Elite Dangerous on ilmoittanut planeettojen kaivoskohteista.</p>
<p>Taustalla oleva näyttö vastaa Explorerista tunnettua näyttöä:</p>
<p><b>ABBAU ×N</b></p>
<p>Numero kuuluu keholle itselleen, eikä se liity komentajaan.</p>

<h3>Vähintään</h3>
<p>Käyttämällä "Ainakin" voit määrittää planeetan kaivospaikkojen vähimmäismäärän ruumiilla.</p>
<p>Esimerkki:</p>
<p><b>Ainakin 20</b></p>
<p>näyttää vain tunnetut kappaleet, joissa on vähintään:</p>
<p><b>ABBAU ×20</b></p>
<p>Tämä mahdollistaa erityisen laajojen kaivosalueiden paikantamisen.</p>

<h3>Omat kaivoslöydöt</h3>
<p>”Omien kaivoslöytöjen” avulla etsintä rajoittuu kappaleisiin, joissa kyseinen komentaja on todistettavasti tehnyt pintalouhintaa itse.</p>
<p>Nämä tiedot ovat peräisin henkilökohtaisesta pintakaivoshistoriasta, ja komentaja erottaa ne tiukasti.</p>
<p>Keholla voi siis olla globaaleja ABBAU ×N-signaaleja ilman, että sen oma komentaja on jo poistanut sieltä mitään.</p>

<h3>Hyödyke</h3>
<p>Jos ”Omat kaivoslöydöt” on aktivoitu, on myös ”Raaka-aine”-valinta käytettävissä.</p>
<p>Lista sisältää vain hyödykkeet, jotka kyseinen komentaja on itse asiassa jo voittanut pintalouhinnasta.</p>
<p>Tämä ei ole teoreettinen luettelo kaikista mahdollisista kaivosraaka-aineista.</p>
<p>FABER38:n valikoimassa voi olla esimerkiksi:</p>
<ul>
<li>Kaikki</li>
<li>kupari</li>
</ul>
<p>Jos myöhemmin louhitaan lisää raaka-aineita, ne näkyvät automaattisesti henkilökohtaisessa valikoimassasi.</p>

<h3>Kohdennettu raaka-aineiden haku</h3>
<p>Jos esimerkiksi valitaan "Kupari" ja sitten painetaan "Käytä", historia näyttää vain kappaleet, joihin kyseinen komentaja on todistettavasti louhinut kuparia.</p>
<p>Esimerkki:</p>
<p><b>Prua Hypai NV-E c28-66 / 2 — ABBAU ×24 — kupari 56 t</b></p>
<p>Tämä tarkoittaa, että kronikkaa voidaan käyttää henkilökohtaisena sijaintitietokantana: jo louhittu raaka-aine löytyy myöhemmin uudelleen.</p>

<h3>Kaikki raaka-aineet</h3>
<p>"Raaka-aine: Kaikki" -asetuksella otetaan huomioon kaikki vastaavat henkilökohtaiset pintakaivoslöydöt.</p>
<p>Jos kappaleessa tunnetaan useita hyödykkeitä, ne voidaan esittää yhdessä niiden tähän mennessä saamien määrien kanssa.</p>
<p>Esimerkki:</p>
<p><b>ABBAU ×24 — Helium-3 18 t, kupari 56 t</b></p>
<p>Määrät ovat vastaavan komentajan henkilökohtaisia ​​kaivosarvoja, jotka on tosiasiallisesti dokumentoitu päiväkirjatapahtumista.</p>
<p>Myös ajanjakson ollessa käytössä henkilökohtaiset louhitut määrät pysyvät tallennettuina kokonaismäärinä. <b>Kupari 56 t</b> ei automaattisesti tarkoita <b>56 t valitulla ajanjaksolla</b>. Ajanjakso edellyttää vastaavaa järjestelmäkäyntiä, mutta ei rajaa näytettyä louhintamäärää tähän ajanjaksoon.</p>

<h3>Yhdistä suodattimet</h3>
<p>Vapaa teksti, käyttöön otetut Alkaen-/Asti-rajat ja kaivossuodattimet voidaan yhdistää. Osuman on täytettävä asetetut ehdot yhdessä.</p>
<p>Esimerkiksi:</p>
<ul>
<li>Planeettojen kaivoskohteet aktiivisia</li>
<li>Ainakin 20</li>
<li>Oma kaivostoiminta löytyy aktiivisesti</li>
<li>Raaka-aine kupari</li>
</ul>
<p>etsii tunnettuja ruumiita, joissa on vähintään 20 planeetan kaivospaikkaa, joissa kyseinen komentaja on jo louhinut itse kuparia.</p>
<p>Myös mahdollinen lisähakuteksti huomioidaan. Jos lisäksi on valittu ajanjakso, tarkasteltavan komentajan on täytynyt todella käydä kyseisessä järjestelmässä sen aikana; itse kuparin louhinnan ei tarvitse osua tähän ajanjaksoon.</p>

<h3>Käytä</h3>
<p>”Käytä” suorittaa yhdistetyn suodatuksen kaikilla tällä hetkellä asetetuilla haku-, ajanjakso- ja kaivossuodattimilla:</p>
<ul>
<li>Vapaa teksti</li>
<li>Alkaen, jos käytössä</li>
<li>Asti, jos käytössä</li>
<li>Planeettojen kaivoskohteet</li>
<li>Vähimmäismäärä</li>
<li>Omat kaivoslöydöt</li>
<li>Hyödyke, jos ”Omat kaivoslöydöt” on käytössä</li>
</ul>
<p>Enter vapaatekstikentässä suorittaa täsmälleen saman suodatuksen. Ilman vapaata tekstiä ja kaivossuodattimia ladataan tavallinen kartta kartalla valituille komentajille, tarvittaessa Alkaen/Asti-rajoilla rajattuna.</p>

<h3>Nollaa</h3>
<p>”Nollaa” palauttaa yhteisen suodatinalueen alkutilaan:</p>
<ul>
<li>Vapaa teksti tyhjennetään.</li>
<li>Alkaen ja Asti poistetaan käytöstä; päivämääräkentissä näkyy taas tämä päivä ja kentät ovat poissa käytöstä.</li>
<li>Planeettojen kaivoskohteet poistetaan käytöstä.</li>
<li>Vähimmäismääräksi asetetaan 0.</li>
<li>Omat kaivoslöydöt poistetaan käytöstä.</li>
<li>Hyödyke palautetaan arvoon ”Kaikki”.</li>
</ul>
<p>Komentajavalinta säilyy. Tavallinen kronikka ladataan sitten uudelleen tälle karttavalinnalle; aiemmat hakutulokset ja yksityiskohtanäytöt nollataan.</p>

<h3>Komentajan valinta</h3>
<p>Kronikka voi näyttää tietoja useilta tunnetuilta komentajilta.</p>
<p>Valinnassa on kaksi erillistä käsitettä:</p>
<ul>
<li><b>Kartan komentajavalinta:</b> Komentajien valintaruudut määräävät, keiden reitit näytetään tavallisella kartalla ilman vapaateksti-/kaivoshakua. Käyttöön otettu ajanjakso huomioidaan.</li>
<li><b>Tarkasteltava komentaja:</b> Henkilökohtaiset vapaateksti-/kaivoshaut käyttävät tarkasteltavaa komentajaa (<code>viewed_commander_id</code>), toissijaisesti aktiivista komentajaa. Myös henkilökohtaiset hyödykeluettelot määräytyvät tämän komentajan mukaan.</li>
</ul>
<p>Henkilötiedot, kuten omat kaivoslöydöt ja raaka-aineluettelot, arvioidaan kuitenkin aina erikseen tarkasteltavan komentajan osalta.</p>
<p>Päällikkö ei näe raaka-ainevalinnassaan mitään yksinomaan toiselle komentajalle kuuluvia kaivoslöytöjä.</p>

<h3>Kaikki komentajat</h3>
<p>Kartta/kroniikka-näyttö voi ottaa huomioon useita komentoja.</p>
<p>”Kaikki komentajat” tarkoittaa kartan komentajavalintaa. Komentajien valintaruudut eivät automaattisesti laajenna henkilökohtaisia vapaateksti-/kaivoshakuja useisiin komentajiin.</p>
<p>Tämä ei muuta komentajaan liittyvien tietojen henkilökohtaista määritystä. Järjestelmän tai kehon maailmanlaajuiset tähtitieteelliset ominaisuudet pysyvät yhteisinä, henkilökohtaiset havainnot erillisinä.</p>

<h3>Hakuapu / legenda</h3>
<p>Lisätietoa kronikkahausta ja näytön merkityksestä löytyy "Hakuohjeesta / selitteestä".</p>
<p>Napsautettu hakusana siirtyy hakukenttään, ja haku suoritetaan yhdessä jo asetettujen ajanjakso-/kaivossuodattimien kanssa.</p>
<p>Tämä asiayhteyteen liittyvä pääohje täydentää siellä olevia lyhyitä käyttöohjeita.</p>

<h3>Vinkki</h3>
<p>Kronikka sopii erityisen hyvin pitkän matkan aikana löydettyjen mielenkiintoisten paikkojen etsimiseen.</p>
<p>Esimerkiksi pintakaivostoiminnassa se voi vastata:</p>
<p>"Millä planeetalla olen koskaan louhinut kuparia?"</p>
<p>tai:</p>
<p>"Millä tunnetuista planeetoistani on erityisen paljon kaivospaikkoja?"</p>""",
    ),
 'jump_tip': ('Hyppyvinkki',
              '<h2>Hyppyvinkki</h2>\n'
              '<p>Hyppykärki tukee tutkimista arvioimalla jo tunnettua järjestelmädataa ja '
              'korostamalla mielenkiintoisia kohdejärjestelmiä.</p>\n'
              '<p>Toiminto on tarkoitettu päätöksenteon apuvälineeksi. Se ei takaa, että '
              'suositeltu järjestelmä todella sisältää harvinaisia \u200b\u200btai erityisen '
              'arvokkaita löytöjä.</p>\n'
              '\n'
              '<h3>Arvioinnin perusteet</h3>\n'
              '<p>CMDRHelper käyttää olemassa olevia loki- ja tietokantatietoja arvioidakseen '
              'tunnettuja malleja järjestelmän nimissä ja järjestelmäluokissa.</p>\n'
              '<p>Huomioon voidaan ottaa muun muassa järjestelmälyhenteet, jo tunnetut '
              'ruumistyypit ja aikaisemmat löydöt.</p>\n'
              '\n'
              '<h3>Järjestelmän lyhenne</h3>\n'
              '<p>Monet Elite Dangerous:n proseduaalisesti luodut järjestelmät sisältävät kirjain- '
              'ja numeroyhdistelmiä, jotka tunnistavat tietyt järjestelmäryhmät.</p>\n'
              '<p>CMDRHelper voi tilastollisesti arvioida nämä lyhenteet ja näyttää, missä '
              'ryhmissä mielenkiintoisia löytöjä esiintyi useammin tähän mennessä tunnetuissa '
              'tiedoissa.</p>\n'
              '\n'
              '<h3>Arvioi uudelleen</h3>\n'
              '<p>"Arvioi uudelleen" -toiminnolla olemassa oleva tietokanta analysoidaan '
              'uudelleen.</p>\n'
              '<p>Komentajan tallennettuja tietoja käytetään. Toiminto ei luo uutta huipputietoa '
              'tai muokkaa päiväkirjatiedostoja.</p>\n'
              '\n'
              '<h3>Tulosluettelo</h3>\n'
              '<p>Tuloslistassa näkyvät kiinnostavimmat järjestelmälyhenteet tai ehdokkaat '
              'nykyisen arvioinnin mukaan.</p>\n'
              '<p>Olemassa olevasta tietokannasta riippuen siellä voi olla tietoja:</p>\n'
              '<ul>\n'
              '<li>mielenkiintoisia planetaarisia luokkia</li>\n'
              '<li>biologisia löytöjä</li>\n'
              '<li>Vesimaailmat</li>\n'
              '<li>terramuotoituvat rungot</li>\n'
              '<li>muita merkittäviä tutkimustuloksia</li>\n'
              '</ul>\n'
              '<p>näkyviin.</p>\n'
              '\n'
              '<h3>Todennäköisyys takuun sijaan</h3>\n'
              '<p>Korkea arvo tai hyvä sijoitus tarkoittaa vain sitä, että tietty malli liittyi '
              'useammin mielenkiintoisiin löydöksiin tähän mennessä arvioiduissa tiedoissa.</p>\n'
              '<p>Se ei ole takuu.</p>\n'
              '<p>Suositeltu järjestelmä voi silti olla täysin epäkiinnostava, kun taas huonosti '
              'arvostettu järjestelmä voi sisältää arvokkaita löytöjä.</p>\n'
              '\n'
              '<h3>Oma tietokanta</h3>\n'
              '<p>Hyppykärki toimii komentajan jo tiedossa olevien tietojen kanssa.</p>\n'
              '<p>Mitä enemmän järjestelmiä ja elimiä tallennetaan ajan mittaan, sitä suurempi on '
              'arvioitava henkilökohtainen tietokanta.</p>\n'
              '<p>Tämä tarkoittaa, että sijoitus voi muuttua myöhemmin.</p>\n'
              '\n'
              '<h3>Useita komentajia</h3>\n'
              '<p>Henkilökohtaiset arvioinnit käsitellään komentajakohtaisesti.</p>\n'
              '<p>Toiselta päällikköltä saadut tiedot eivät saa väärentää henkilökohtaista '
              'kelpuutusta huomaamatta.</p>\n'
              '<p>Maailmanlaajuista tähtitieteellistä perustietoa voidaan toisaalta jakaa niin '
              'kauan kuin se ei edusta komentajaan liittyviä henkilökohtaisia '
              '\u200b\u200blöydöksiä.</p>\n'
              '\n'
              '<h3>Käytä käytännössä</h3>\n'
              '<p>Hyppykärki sopii erityisen hyvin, jos valittavana on useita mahdollisia kohteita '
              'ja halutaan lisäapua päätöksentekoon.</p>\n'
              '<p>Se ei korvaa täydellistä reittisuunnittelijaa eikä laske turvallista, '
              'optimaalista reittiä.</p>\n'
              '<p>Valikkokohta "Reittisuunnittelija" on käytettävissä tiettyä reittisuunnittelua '
              'varten.</p>\n'
              '\n'
              '<h3>Kärki</h3>\n'
              '<p>Käytä hyppykärkiä lisäetsintäapuna:</p>\n'
              '<p>"Kumpi järjestelmä näyttää aiempien tietojeni mukaan kiinnostavammalta?"</p>\n'
              '<p>Ei ennustuksena:</p>\n'
              '<p>"Tässä järjestelmässä on taatusti tietty löytö."</p>'),
 'route_planner': ('Reitin suunnittelija',
                   '<h2>Reitin suunnittelija</h2>\n'
                   '<p>Reittisuunnittelija tukee pidempien matkojen suunnittelua laivalla tai '
                   'Fleet Carrier:lla. CMDRHelper voi käyttää Spansh:n ulkoisia reittitietoja ja '
                   'valmistella suunnitellun reitin myöhempää käyttöä varten.</p>\n'
                   '\n'
                   '<h3>Aloita ja lopeta</h3>\n'
                   '<p>Reitin laskemiseen tarvitaan aloitus- ja kohdejärjestelmä.</p>\n'
                   '<p>Mahdollisuuksien mukaan CMDRHelper voi käyttää komentajan nykyistä '
                   'tunnettua järjestelmää lähtökohtana. Lähtö ja maali tulee tarkistaa ennen '
                   'laskemista.</p>\n'
                   '\n'
                   '<h3>Lähetys tai Fleet Carrier</h3>\n'
                   '<p>Reittisuunnittelija erottaa matkat tavallisella laivalla ja Fleet '
                   'Carrier:llä.</p>\n'
                   '<p>Molemmat käyttävät erilaisia \u200b\u200bvaatimuksia ja laskentamenetelmiä. '
                   'Siksi sopiva reittityyppi on valittava ennen suunnittelua.</p>\n'
                   '\n'
                   '<h3>Laivan reitti</h3>\n'
                   '<p>Laivareitillä huomioidaan aktiiviselle alukselle tunnetut tai syötetyt '
                   'hyppyominaisuudet.</p>\n'
                   '<p>Suunnitteluun voidaan sisällyttää käytettävissä olevista tiedoista riippuen '
                   'FSD-tiedot, laivatiedot, massa, polttoaine ja muut hyppyparametrit.</p>\n'
                   '<p>Laskettu reitti on suunnitteluapua. Muutokset laivaan tai sen massaan '
                   'voivat muuttaa pelissä saavutettavaa todellista hyppymatkaa.</p>\n'
                   '\n'
                   '<h3>Laivaston harjoittaja reitti</h3>\n'
                   '<p>Fleet Carrier:llä on erilaiset hyppysäännöt kuin normaaleissa '
                   'laivoissa.</p>\n'
                   '<p>CMDRHelper käyttää nimettyä Spansh-operaattorisuunnittelua vastaaville '
                   'reiteille.</p>\n'
                   '<p>Reittiä käytetään hyppysarjan suunnitteluun. Todellinen tritiumin kulutus '
                   'ja käytettävissä oleva toiminta-alue voivat myös riippua massasta ja sen '
                   'hetkisestä kantajan tilasta.</p>\n'
                   '\n'
                   '<h3>Spansh</h3>\n'
                   '<p>Varsinaiseen reitin laskemiseen CMDRHelper voi käyttää ulkoista palvelua '
                   'Spansh.</p>\n'
                   '<p>Pyyntö käsitellään taustalla, jotta käyttöliittymä pysyy toimintakunnossa '
                   'pidemmänkin laskennan ajan.</p>\n'
                   '<p>CMDRHelper ei vaikuta ulkoisen palvelun käytettävyyteen tai '
                   'vasteaikaan.</p>\n'
                   '\n'
                   '<h3>laskeminen</h3>\n'
                   '<p>Laskennan aloittamisen jälkeen pyyntö välitetään valitulle '
                   'reittisuunnittelijalle.</p>\n'
                   '<p>Reitistä ja palvelusta riippuen laskenta saattaa kestää jonkin aikaa. Tänä '
                   'aikana toista identtistä laskentaa ei saa aloittaa tarpeettomasti.</p>\n'
                   '\n'
                   '<h3>Tulos</h3>\n'
                   '<p>Onnistuneesti laskettu reitti näyttää aiotut järjestelmät tai hyppypisteet '
                   'järjestyksessä.</p>\n'
                   '<p>Reittityypistä riippuen näkyviin tulee lisätietoja matkasta, hyppyistä, '
                   'polttoaineesta tai tritiumista ja muista käytettävissä olevista '
                   'reittitiedoista.</p>\n'
                   '\n'
                   '<h3>Reitti ja nykyinen komentaja</h3>\n'
                   '<p>Nykyistä järjestelmää ja alusta voidaan - niin kauan kuin ne ovat selkeästi '
                   'tiedossa aktiivisessa AppStatessa - käyttää esitehtäviin tai suunnittelun '
                   'tukena.</p>\n'
                   '<p>Todellinen reitti jää kuitenkin suunnitelmaksi, eikä se muuta päiväkirjaa '
                   'tai komentajatietoja.</p>\n'
                   '\n'
                   '<h3>CTSVision vienti</h3>\n'
                   '<p>Lasketut lentoyhtiöiden reitit voidaan viedä CSV-muodossa '
                   'CTSVision:lle.</p>\n'
                   '<p>Tämä tarkoittaa, että CMDRHelper:ssä suunniteltua operaattorireittiä '
                   'voidaan sitten käyttää CTSVision:ssä hyppyohjaukseen tai reitin käsittelyyn '
                   'siellä.</p>\n'
                   '<p>Vienti ei muuta reittiä CMDRHelper:ssä.</p>\n'
                   '\n'
                   '<h3>CSV-tiedosto</h3>\n'
                   '<p>Viety tiedosto sisältää CTSVision:lle vaadittavat reittitiedot aiotussa '
                   'järjestyksessä.</p>\n'
                   '<p>Tiedostoa ei saa muuttaa rakenteellisesti hallitsemattomasti viennin '
                   'jälkeen, jos CTSVision sen jälkeen lukee sen.</p>\n'
                   '\n'
                   '<h3>Virheet ja ulkoiset palvelut</h3>\n'
                   '<p>Jos Spansh:tä ei tavoiteta tai palvelu palauttaa virheilmoituksen, '
                   'CMDRHelper näyttää vastaavan virheilmoituksen.</p>\n'
                   '<p>Virhe online-reitin laskennassa ei muuta paikallista komentoa tai '
                   'lokitietoja.</p>\n'
                   '\n'
                   '<h3>Reitin suunnittelija ja hyppyvinkki</h3>\n'
                   '<p>Hyppyvinkki ja reittisuunnittelija suorittavat erilaisia '
                   '\u200b\u200btehtäviä:</p>\n'
                   '<ul>\n'
                   '<li>Hyppyvinkki arvioi mahdolliset mielenkiintoiset etsintäkohteet olemassa '
                   'olevan datan perusteella.</li>\n'
                   '<li>Reitinsuunnittelija laskee tietyn reitin alun ja määränpään välillä.</li>\n'
                   '</ul>\n'
                   '<p>Hyvä hyppykärki ei siis automaattisesti ole osa optimaalista reittiä.</p>\n'
                   '\n'
                   '<h3>Useita komentajia</h3>\n'
                   '<p>Jos käytetään komentajaan liittyviä tietoja, kuten nykyistä järjestelmää '
                   'tai laivaa, se tulee aktiivisesta live-sovellustilasta ja se on osoitettava '
                   'selkeästi sinne.</p>\n'
                   '<p>Pelkästään toisen komentajan katsominen CMDR-näkymässä ei vaihda '
                   'reittisuunnittelijaa heidän järjestelmäänsä tai alukseensa.</p>\n'
                   '<p>Itse reitinlaskenta ei muuta toisen päällikön henkilötietoja.</p>\n'
                   '\n'
                   '<h3>Kärki</h3>\n'
                   '<p>Tarkista aina ennen pitkää matkaa uudelleen:</p>\n'
                   '<ul>\n'
                   '<li>Käynnistysjärjestelmä</li>\n'
                   '<li>Kohdejärjestelmä</li>\n'
                   '<li>Reittityyppi laiva/rahdinkuljettaja</li>\n'
                   '<li>alusreiteille alla oleva alus, FSD ja hyppyparametrit</li>\n'
                   '<li>kuljetusreiteillä käytettävissä oleva tritiumreservi</li>\n'
                   '</ul>\n'
                   '<p>Laivastonkuljettajien matkoille kannattaa varata riittävästi varauksia myös '
                   'paluumatkalle tai suunnittelemattomille kiertoteille.</p>'),
 'images': ('Kuvia',
            '<h2>Kuvia</h2>\n'
            '<p>"Kuvat"-osio hallitsee Elite Dangerous:lla otettuja kuvakaappauksia. CMDRHelper '
            'voi automaattisesti tunnistaa uudet tallenteet, käsitellä ne ja tallentaa ne '
            'galleriaan komentajan perusteella.</p>\n'
            '\n'
            '<h3>Lähdekansio</h3>\n'
            '<p>Lähdekansio on kansio, johon Elite Dangerous tallentaa kuvakaappauksensa '
            'BMP-muodossa.</p>\n'
            '<p>CMDRHelper voi tarkkailla tätä kansiota uusien BMP-tiedostojen varalta. Jotta '
            'automaattinen käsittely toimisi, oikea kuvakaappauskansio on asetettava.</p>\n'
            '\n'
            '<h3>Kohdekansio</h3>\n'
            '<p>Kohdekansio on CMDRHelper:n käsittelemien kuvien yhteinen juurikansio.</p>\n'
            '<p>Käyttäjä asettaa tämän juurikansion. CMDRHelper luo automaattisesti tarvittavat '
            'komentoriin liittyvät alikansiot käsittelyn aikana.</p>\n'
            '\n'
            '<h3>Automaattinen käsittely</h3>\n'
            '<p>Jos "Muunna automaattisesti" on aktivoitu ja kelvolliset lähde- ja kohdekansiot on '
            'asetettu, CMDRHelper tarkistaa säännöllisesti lähdekansiosta uusia '
            'BMP-kuvakaappauksia.</p>\n'
            '<p>Aktivoituna olemassa olevat BMP-tiedostot merkitään aluksi tunnetuiksi, eikä niitä '
            'muunneta automaattisesti ilman pyyntöä. Tätä varten on saatavana erillinen toiminto '
            'olemassa olevien BMP-tiedostojen muuntamiseen.</p>\n'
            '<p>Uutta tiedostoa ei lisätä jonoon, ennen kuin sen koko on sama kuin nolla kahdessa '
            'peräkkäisessä tarkistuksessa. Tämän seurauksena vielä kesken olevaa '
            'kirjoitustoimintoa ei käsitellä välittömästi.</p>\n'
            '\n'
            '<h3>Kuvan muuntaminen</h3>\n'
            '<p>Lähteenä CMDRHelper käsittelee BMP-tiedostoja. Kohdemuodoksi voidaan valita "PNG" '
            'tai "JPG".</p>\n'
            '<p>JPG-tiedostot tallennetaan laatutasolla 95. PNG-tiedostot tallennetaan '
            'optimoidulla tavalla.</p>\n'
            '<p>Oletuksena alkuperäinen BMP-tiedosto säilytetään. Jos "Poista BMP muuntamisen '
            'jälkeen" on aktivoitu, lähde-BMP poistetaan vasta, kun kohdekuva on tallennettu '
            'onnistuneesti.</p>\n'
            '\n'
            '<h3>Kirkastaa kuvaa</h3>\n'
            '<p>Kirkkautta säädetään välillä 0–50 prosenttia liukusäätimen ja linkitetyn '
            'numerokentän avulla. Asetus on tallennettu.</p>\n'
            '<p>Sitä käytetään automaattisesti jokaisen sen jälkeen aloitetun muunnoksen '
            'yhteydessä - sekä äskettäin valvotuille että manuaalisesti aloitetuille olemassa '
            'oleville BMP-tiedostoille. 0 prosenttia ottaa alkuperäisen kirkkauden; korkeammat '
            'arvot lisäävät luodun PNG- tai JPG-kuvan kirkkautta vastaavasti.</p>\n'
            '<p>Toiminto ei ole pelkkä esikatselu, eikä sitä käytetä myöhemmin galleriassa '
            'valittuun kuvaan. Muutettu kirkkaus tallennetaan uuteen kohdetiedostoon.</p>\n'
            '<p>Lähde BMP pysyy muuttumattomana, ellei myös BMP-tiedoston poistoa ole aktivoitu. '
            'Päiväkirja-, komentaja- ja etsintätiedot eivät muutu.</p>\n'
            '\n'
            '<h3>Komentajaan liittyvä tallennustila</h3>\n'
            '<p>Uudet kuvakaappaukset määritetään varsinaiselle pelaavalle Commanderille '
            'aktiivisessa live-sovelluksessa olevan päiväkirjan identiteetin perusteella.</p>\n'
            '<p>Kansiorakenne sisältää komentajan nimen ja Frontier-tunnuksen, esimerkiksi:</p>\n'
            '<p><b>FABER38_F12520967/</b></p>\n'
            '<p>FID pitää tehtävän selkeänä jopa useiden komentojen kanssa. Tämä mahdollistaa '
            'kahden samannimisen komentajan erottamisen.</p>\n'
            '\n'
            '<h3>tiedostonimiä</h3>\n'
            '<p>Uudet käsitellyt kuvat saavat nimen, jossa on kuvausaika, komentajan nimi ja -jos '
            'saatavilla - tähtijärjestelmä, joka tunnetaan jonossa.</p>\n'
            '<p>Esimerkki:</p>\n'
            '<p><b>2026-09-04_13-18-22_FABER38_Prua-Hypai-RB-D-c29-71.png</b></p>\n'
            '<p>FID on komentoriin liittyvässä kansion nimessä, ei taas kuvatiedoston '
            'nimessä.</p>\n'
            '\n'
            '<h3>Suojatut tiedostonimet</h3>\n'
            '<p>CMDRHelper puhdistaa komento- ja järjestelmänimet käytettäväksi tiedosto- ja '
            'kansiokomponentteina.</p>\n'
            '<p>Laiton ohjaus ja Windows-merkit korvataan, välilyönnit yhdistetään, ongelmalliset '
            'pisteet tai välilyönnit poistetaan ja varatut Windows-nimet, kuten CON tai NUL, '
            'suojataan.</p>\n'
            '\n'
            '<h3>Tallennusaika</h3>\n'
            '<p>Nimeämiseen CMDRHelper käyttää vakaan tunnistetun BMP-tiedoston muokkausaikaa. '
            'Vain jos tätä ei voida lukea, käytetään nykyistä aikaa.</p>\n'
            '<p>Tämä tarkoittaa, että nimi riippuu yleensä lähdetiedostosta eikä myöhemmästä '
            'muunnosajasta.</p>\n'
            '\n'
            '<h3>Useita kuvia samassa sekunnissa</h3>\n'
            '<p>Jos aiottu tiedostonimi on jo olemassa tai se on varattu meneillään olevalle '
            'muunnokselle, CMDRHelper lisää sen '
            'jatkuvasti<code>_2</code>,<code>_3</code>,<code>_4</code>ja niin edelleen.</p>\n'
            '<p>Tämä tarkoittaa, että toinen kuvakaappaus, jolla on sama aikaleima, ei korvaa '
            'olemassa olevaa kohdekuvaa.</p>\n'
            '\n'
            '<h3>Komentaja vaihtuu käsittelyn aikana</h3>\n'
            '<p>Commander, FID ja järjestelmä kaapataan yhdessä, kun kuvakaappaus on jonossa.</p>\n'
            '<p>Myöhempi komentajan vaihto ei muuta tämän jo odottavan kuvan tehtävää. Tämä '
            'tarkoittaa, että kuvakaappausta FABER38:sta ei kirjoiteta myöhemmin toisen komentajan '
            'kansioon.</p>\n'
            '\n'
            '<h3>galleria</h3>\n'
            '<p>Galleria näyttää PNG-, JPG- ja JPEG-tiedostot valittuun suodattimeen liittyvistä '
            'hakemistoista. Uusia, poistettuja tai siirrettyjä kuvia havaitaan '
            'säännöllisesti.</p>\n'
            '<p>Galleriasuodatin ei muuta tiedostojen tallennuspaikkaa tai komentajan '
            'määritystä.</p>\n'
            '\n'
            '<h3>Nykyinen komentaja</h3>\n'
            '<p>Current Commander -suodatin näyttää kuvat CMDR-näkymässä parhaillaan '
            'tarkasteltavan komentajan kansiosta.</p>\n'
            '<p>Kyseinen komentaja määrittää vain gallerian näytön. Toisaalta uuden '
            'live-kuvakaappauksen määrittäminen käyttää aktiivisena päiväkirjan identiteettiä '
            'jonossa.</p>\n'
            '\n'
            '<h3>Kaikki komentajat</h3>\n'
            '<p>"Kaikki komentajat" -suodatin näyttää kaikkien tunnettujen komentojen '
            'kelvollisista alikansioista olevat kuvat yhdessä. Myös erityinen kansio '
            'tallennuksille, joilla ei ole tunnistettua identiteettiä, otetaan huomioon.</p>\n'
            '<p>Tiedostoja ei siirretä tai yhdistetä.</p>\n'
            '\n'
            '<h3>Ei määrätty</h3>\n'
            '<p>Määrittämätön suodatin näyttää tuetut kuvatiedostot, jotka sijaitsevat suoraan '
            'jaetussa kohdejuurikansiossa.</p>\n'
            '<p>Erityisesti vanhemmat kuvat, joissa ei ole komentoriin liittyviä alikansioita, '
            'jäävät näkyviin. CMDRHelper ei yritä arvata heidän kuulumistaan '
            '\u200b\u200bjälkikäteen.</p>\n'
            '\n'
            '<h3>Olemassa olevat kuvat</h3>\n'
            '<p>Pääkansiossa jo olevia kuvia ei siirretä tai nimetä uudelleen '
            'automaattisesti.</p>\n'
            '<p>Ne ovat käytettävissä kohdassa "Unassigned" niin kauan kuin ne ovat saatavilla '
            'PNG-, JPG- tai JPEG-muodossa.</p>\n'
            '\n'
            '<h3>Valitse ja katso kuva</h3>\n'
            '<p>Yksinkertainen esikatselukuvan napsautus näyttää kuvan skaalattuna '
            'esikatselualueella ja näyttää sen tiedostonimen.</p>\n'
            '<p>Kaksoisnapsautus avaa tiedoston, jossa on kuville asetettu '
            'käyttöjärjestelmäsovellus.</p>\n'
            '<p>Useita kuvia voidaan merkitä samanaikaisesti. Kun muutat ikkunan kokoa, nykyisen '
            'kuvan esikatselu skaalataan uudelleen sopivaksi.</p>\n'
            '\n'
            '<h3>Poista kuva</h3>\n'
            '<p>Merkityt kuvat voidaan poistaa käyttämällä "Poista valitut" tai Delete-näppäintä. '
            'Ennen poistamista näyttöön tulee suojauskysely. Ilman valintaa tarvittava valinta '
            'korostetaan ensin.</p>\n'
            '<p>Vain valitut PNG/JPG/JPEG-kohdetiedostot poistetaan nykyisen galleriasuodattimen '
            'hakemistoista. Tämä ei vaikuta alkuperäiseen BMP-lähdetiedostoon.</p>\n'
            '\n'
            '<h3>Avaa kohdekansio</h3>\n'
            '<p>"Avaa kohdekansio" avaa tallennuspaikan tiedostonhallinnassa ja luo tarvittaessa '
            'jaetun juurikansion.</p>\n'
            '<p>"Current Commander" -suodatin avaa olemassa olevan Commander-alikansionsa. Jos '
            'sitä ei vielä ole tai jokin muu suodatin on aktiivinen, jaettu juurikansio '
            'avataan.</p>\n'
            '\n'
            '<h3>Kuvapolkujen turvallisuus</h3>\n'
            '<p>Ennen poistamista CMDRHelper tarkistaa kunkin tiedoston kanonisen polun. Sen on '
            'oltava määritetyssä kohdekansiossa ja suoraan nykyisen galleriasuodattimen sallimassa '
            'hakemistossa.</p>\n'
            '<p>Symbolisia linkkejä ei käytetä komentokansioina tai galleriakuvina, eikä niitä '
            'poisteta gallerian kautta. Kohdealueen ulkopuolella olevat polut ja läpikulkureitit '
            'hylätään.</p>\n'
            '\n'
            '<h3>Jos komentajaa ei havaittu</h3>\n'
            '<p>Jos Commander ja FID puuttuvat uutta tallennusta jonossa, tiedostoa ei aseteta '
            'pitoon eikä sitä osoita tunnetulle Commanderille.</p>\n'
            '<p>Se tulee olemaan alikansiossa<b>UNKNOWN_UNKNOWN/</b>jalostettu; tiedostonimi, jota '
            'käytetään myös komentajassa<b>TUNTEMATON</b>. Tätä kansiota voi tarkastella kaikkien '
            'komentojen kautta, ei Kohdistamaton juurikansio -suodattimen kautta.</p>\n'
            '\n'
            '<h3>Useita komentajia</h3>\n'
            '<p>Kuvanhallintaan sovelletaan kahta erillistä sääntöä:</p>\n'
            '<ul>\n'
            '<li><b>Tallenna uudet kuvat:</b>Aktiivinen päiväkirjaidentiteetti Commanderin ja '
            'FID:n kanssa jonossa määrittää kohdekansion.</li>\n'
            '<li><b>Katso kuvat:</b>Katsottu komento tai valittu galleriasuodatin määrittää '
            'näkyvät kuvat.</li>\n'
            '</ul>\n'
            '<p>Tämä tarkoittaa, että toisen komentajan galleriaa voidaan tarkastella FABER38:n '
            'toiston aikana ilman, että uudet kuvakaappaukset päätyvät kyseisen komentajan '
            'kansioon.</p>\n'
            '\n'
            '<h3>Kärki</h3>\n'
            '<p>Jaettu kuvakaappauksen juurikansio riittää. CMDRHelper erottaa äskettäin '
            'käsitellyt kuvat automaattisesti Commanderiksi ja FID:ksi.</p>\n'
            '<p>"Current Commander", "All Commanders" ja "Unassigned" -asetuksissa voit vaihtaa '
            'henkilökohtaisen gallerian, kaikkien komentajien alikansioiden ja juurikansion '
            'vanhempien kuvien välillä.</p>\n'
            '<p>Suurempi kirkkaus voi auttaa tummissa kuvissa; se vaikuttaa juuri luotuun '
            'kohdekuvaan muunnoksen aikana.</p>'),
 'commander_view': ('CMDR-näkymä',
                    '<h2>CMDR-näkymä</h2>\n'
                    '<p>CMDR-näkymässä on yhteenveto komentajan pysyvästi tallennetuista '
                    'henkilötiedoista.</p>\n'
                    '<p>Sen avulla voit myös vaihtaa CMDRHelper tunnettujen komentojen välillä ja '
                    'tarkastella omia tietojaan. Henkilötiedot erotetaan Frontier-tunnuksella '
                    '(FID).</p>\n'
                    '\n'
                    '<h3>Valitse Commander</h3>\n'
                    '<p>Jos tunnet useita komentoja, voit käyttää yllä olevaa valintaa '
                    'määrittääksesi, kenen tallennetut tiedot näytetään. Tämä komentaja on '
                    'katsottu komentaja.</p>\n'
                    '<p>Näyttö merkitsee sen joko "Live Active" tai "View Only".</p>\n'
                    '\n'
                    '<h3>Pidetään komentajana ja live-komentajana</h3>\n'
                    '<p>Toisen komentajan valitseminen CMDR-näkymässä ei tee siitä aktiivista '
                    'päiväkirjan komentoa.</p>\n'
                    '<p>Live-komentaja määritetään yksinomaan tällä hetkellä yksilöllisesti '
                    'tunnistetun Elite Dangerous -päiväkirjaistunnon perusteella. Tällä tavalla '
                    'toisen komentajan historiaa voidaan tarkastella, kun Elite Dangerous jatkaa '
                    'toimintaansa FABER38:n kanssa.</p>\n'
                    '\n'
                    '<h3>Frontier ID (FID)</h3>\n'
                    '<p>FID on komentajan vakaa Frontier-tunniste.</p>\n'
                    '<p>CMDRHelper käyttää sitä ja siitä määritettyä sisäistä komentajatunnusta '
                    'henkilötietojen turvalliseen erottamiseen. Myös komentajat, joilla on '
                    'samanlaiset tai identtiset nimet, pysyvät erillään.</p>\n'
                    '\n'
                    '<h3>Yleiskatsaus</h3>\n'
                    '<p>"Yleiskatsaus"-välilehti näyttää vain pysyvästi tallennetut tiedot '
                    'kyseisestä komentajasta:</p>\n'
                    '<ul>\n'
                    '<li>Komentajan nimi, FID ja tila "Live aktiivinen" tai "Vain katselu"</li>\n'
                    '<li>ensimmäinen ja viimeinen tunnettu kerta</li>\n'
                    '<li>Vierailtujen järjestelmien lukumäärä, bio- ja geolöydöt, '
                    'koodeksimerkinnät ja kartografian myynti</li>\n'
                    '<li>Viimeisin tunnettu sijainti ja avoimien tehtävien lukumäärä</li>\n'
                    '<li>nykyinen tai viimeinen laiva</li>\n'
                    '<li>Fleet Carrier ja operaattorin sijainti</li>\n'
                    '<li>Omaisuus</li>\n'
                    '<li>avoimet elämätiedot ja avoimet kartografiset tiedot, mukaan lukien '
                    'olemassa olevat arviot</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Omaisuus/luotto</h3>\n'
                    '<p>"Assets" -kentässä näkyy kyseisen päällikön viimeksi tallennettu saldo '
                    'sopivasta päiväkirjatapahtumasta muotoiltuna esim.<b>1 234 567 Kr</b>.</p>\n'
                    '<p>CMDRHelper ei lisää kuvitteellisia tuloja tai kuluja, jos uutta, suojattua '
                    'päiväkirjatilaa ei ole.</p>\n'
                    '\n'
                    '<h3>Palkkasoturikolikot</h3>\n'
                    '<p>Palkkasoturikolikot tulevat MercCoins-kentiltä, \u200b\u200bjoita tarjoaa '
                    'Elite Dangerous<code>Statistics → Bank_Account</code>ja ne on tallennettu '
                    'komentajakohtaisesti Frontier-tilannekuvana.</p>\n'
                    '<p>Näkyviä ovat:</p>\n'
                    '<ul>\n'
                    '<li>Nykyinen</li>\n'
                    '<li>Yhteensä käytetty</li>\n'
                    '<li>Tekniikka</li>\n'
                    '<li>laitteet</li>\n'
                    '<li>Raportoi Frontier: ansaittu kokonaisuudessaan</li>\n'
                    '</ul>\n'
                    '\n'
                    '<h3>Nykyiset ja versiot</h3>\n'
                    '<p>"Nykyiset" -ohjelmat<code>MercCoins_Virta</code>. "Käytettyjen '
                    'kokonaismäärä" ottaa vallan<code>MercCoins_Yhteensä_Käytetty</code>.</p>\n'
                    '<p>"Insinöörityö" ja "laitteet" näyttävät Frontier:n erikseen raportoimat '
                    'osakkeet<code>MercCoins_Spent_On_Engineering</code>ja<code>MercCoins_Spent_On_MercGear</code>.</p>\n'
                    '<p>Esimerkiksi FABER38:lle nykyinen varasto<b>1,275</b>, '
                    'yhteensä<b>220</b>käytetty ja pois<b>220</b>ilmoitettu insinööriksi.</p>\n'
                    '\n'
                    '<h3>Kokonaisuudessaan ansaittu</h3>\n'
                    '<p>"Raportoi Frontier: ansaittu kokonaisuutena" '
                    'näkyy<code>MercCoins_Total_Earned</code>. CMDRHelper ei laske tästä omaa '
                    'tasettaan.</p>\n'
                    '<p>Frontier:n kumulatiivisen arvon ei tarvitse matemaattisesti vastata '
                    'nykyistä varastoa ja raportoituja kuluja. Esimerkiksi 1 275 nykyistä, 25 '
                    'yhteensä ansaittua ja 220 kokonaiskulutusta voidaan raportoida '
                    'samanaikaisesti.</p>\n'
                    '<p>CMDRHelper ei korjaa näitä arvoja, mutta näyttää yksittäiset '
                    'Frontier-laskurit muuttumattomina.</p>\n'
                    '\n'
                    '<h3>Mikset omista MercCoins tasetta?</h3>\n'
                    '<p>Elite Dangerous ei tarjoa yksilöllistä päiväkirjatietuetta jokaiselle '
                    'yksittäiselle palkkasoturikolikoiden vastaanotolle tai kululle. MercCoins '
                    'näkyvät kokonaislukuina Statistics:ssä.</p>\n'
                    '<p>Itse laskettu varaushistoria ei siis olisi luotettava. CMDRHelper '
                    'tallentaa sen sijaan uusimman tunnetun Frontier-tilanteen.</p>\n'
                    '\n'
                    '<h3>Tehtävät</h3>\n'
                    '<p>"Tehtävät"-välilehti näyttää kyseisen komentajan tallennetut tehtävät '
                    'taulukona, jossa on tila, tehtävän nimi, tavoite, päättymisaika ja '
                    'palkinto.</p>\n'
                    '\n'
                    '<h3>etsintä</h3>\n'
                    '<p>Tutkimus-välilehti näyttää avoimet elämätiedot, avoimet kartografiset '
                    'tiedot, biologiset löydöt, ensimmäiset askeleet, itse kartoitetut ja '
                    'tehokkaasti kartoitetut kappaleet sekä vierailtujen järjestelmien '
                    'lukumäärän.</p>\n'
                    '<p>CMDR-näkymässä oleva Kroniikka-välilehti on tällä hetkellä edelleen '
                    'paikkamerkki. Koko kronikka löytyy samannimisestä päävalikon kohdasta.</p>\n'
                    '\n'
                    '<h3>Laivat/laivasto</h3>\n'
                    '<p>"Laivat"-välilehti näyttää aluksi aktiivisen tai viimeksi käytetyn aluksen '
                    'aluksen nimen, aluksen tyypin, sijainnin ja ShipID:n kanssa.</p>\n'
                    '<p>Kyseisen komentajan pelastetut alukset näkyvät niiden alla laajennettavina '
                    'korteina. Ne voidaan lajitella nousevaan tai laskevaan järjestykseen:</p>\n'
                    '<ul>\n'
                    '<li>viimeksi tai tällä hetkellä käytössä</li>\n'
                    '<li>Laivan nimi tai aluksen tyyppi</li>\n'
                    '<li>suurin hyppyalue</li>\n'
                    '<li>Lastikapasiteetti tai tyhjä massa</li>\n'
                    '<li>viimeisin tunnettu paikka tai aika</li>\n'
                    '</ul>\n'
                    '<p>Voit myös suodattaa kaikille laivoille, laivoille, joissa on ajoneuvohalli '
                    'tai laivoille, joissa on hävittäjähalli.</p>\n'
                    '\n'
                    '<h3>Lähetyksen tiedot</h3>\n'
                    '<p>Avattu laivakartta näyttää - jos se on tallennettu - aluksen ID, ShipID, '
                    'sijainti, viimeinen aika, maksimi hyppymatka, FSD- ja Guardian-tehostin, '
                    'massa, lasti ja tankkikapasiteetti sekä lastausaika ja tila.</p>\n'
                    '<p>Jos moduulitietoja on saatavilla, yhteenveto on myös ajoneuvo- ja '
                    'hävittäjähalli, kilpigeneraattori ja kilpivahvistin, Guardian-kilven '
                    'vahvistukset, aseet, rungon ja moduulivahvikkeet sekä matkustajahyt.</p>\n'
                    '<p>Lataustila voi olla täydellinen, keskeneräinen tai vanhentunut. Puuttuvat '
                    'tiedot näkyvät merkillä “–”, eikä niitä ole keksitty.</p>\n'
                    '\n'
                    '<h3>Fleet Carrier</h3>\n'
                    '<p>Tallennetun mukautetun Fleet Carrier:n kohdalla näkymässä näkyy '
                    'operaattorin nimi, kutsutunnus, operaattorin tunnus, viimeinen sijainti ja '
                    'viimeisimmän päivityksen aika.</p>\n'
                    '\n'
                    '<h3>Pysyvä komentajan tila</h3>\n'
                    '<p>Tärkeät komentajan tiedot säilyvät pysyvästi tallennettuina. Tämä '
                    'mahdollistaa tunnettujen arvojen näyttämisen uudelleen CMDRHelper:n tai Elite '
                    'Dangerous:n uudelleenkäynnistyksen jälkeen ilman, että jokainen päiväkirja on '
                    'täysin arvioitu uudelleen.</p>\n'
                    '<p>Uudet ainutlaatuiset päiväkirjatapahtumat päivittävät tallennetun '
                    'tilan.</p>\n'
                    '\n'
                    '<h3>Historiallinen jälleenrakennus</h3>\n'
                    '<p>Myöhemmin lisättävien toimintojen osalta CMDRHelper voi etsiä jo '
                    'tunnettuja tietoja olemassa olevilta päiväkirjaalueilta, jotka on selkeästi '
                    'osoitettu komentajalle.</p>\n'
                    '<p>Esimerkiksi vanhemmat MercCoins tilannekuvat voidaan ottaa käyttöön. '
                    'Toistuvien tarkistusten tarkoituksena ei ole tuottaa päällekkäisiä tietoja, '
                    'eivätkä ne muuta normaaleja päiväkirjan lukupaikkoja.</p>\n'
                    '\n'
                    '<h3>Useita komentajia</h3>\n'
                    '<p>Erityisesti seuraavat pysyvät erillisinä komentajien suhteen:</p>\n'
                    '<ul>\n'
                    '<li>Omaisuus ja tehtävät</li>\n'
                    '<li>omaa kartografiaa ja luomulöytöjä</li>\n'
                    '<li>Pintakaivoshistoriaa ja palkkasoturikolikoita</li>\n'
                    '<li>Verkkotunnukset</li>\n'
                    '<li>komentajaan liittyvät kuvakaappaukset</li>\n'
                    '</ul>\n'
                    '<p>Järjestelmän tai kappaleen globaaleja tähtitieteellisiä ominaisuuksia '
                    'voidaan kuitenkin käyttää yhdessä.</p>\n'
                    '\n'
                    '<h3>Vaikutus muihin näkemyksiin</h3>\n'
                    '<p>Kyseisen komentajan vaihtaminen päivittää itse CMDR-näkymän, kronikan '
                    'henkilökohtaisen kaivosraaka-ainevalikoiman ja sopivalla suodattimella '
                    'kuvakaappausgallerian.</p>\n'
                    '<p>Se ei korvaa todellista live-komentoa päiväkirjojen käsittelyssä tai '
                    'online-latauksissa.</p>\n'
                    '\n'
                    '<h3>Inara ja EDSM</h3>\n'
                    '<p>Inara- ja EDSM-pääsyjä hallitaan erikseen komentokohtaisesti ja '
                    'FID-käyttöoikeuksia vastaavasti.</p>\n'
                    '<p>Pelkästään komentajan katsominen ei käynnistä lähetystä niiden API-Key:n '
                    'kanssa. Vain aktiivinen päiväkirja FID on merkityksellinen '
                    'live-latauksille.</p>\n'
                    '<p>Käyttötietoja hallitaan verkkopalvelualueen "Asetukset" -kohdassa.</p>\n'
                    '\n'
                    '<h3>Kärki</h3>\n'
                    '<p>Käytä CMDR-näkymää, jos haluat tarkastella tietyn komentajan tallennettuja '
                    'henkilökohtaisia \u200b\u200btietoja.</p>\n'
                    '<p><b>CMDR-näkymä = Kenet haluan nähdä?</b></p>\n'
                    '<p><b>Active Journal-FID = Kuka pelaa juuri nyt?</b></p>\n'
                    '<p>Tämä erottelu estää henkilökohtaisten tietojen tai online-latausten '
                    'sekoittumisen eri komentajilta.</p>'),
 'settings': ('Asetukset',
              '<h2>Asetukset</h2>\n'
              '<p>"Asetukset"-alue määrittää, kuinka CMDRHelper toimii Elite Dangerous:n, '
              'päiväkirjatiedostojen, tietokannan, online-palvelujen, käyttöliittymän ja '
              'päivitysten kanssa.</p>\n'
              '<p>Tunnusten ja polkujen muutokset tulee tehdä huolellisesti. Komenteriin liittyviä '
              'asetuksia hallinnoi tarvittaessa erikseen Frontier ID.</p>\n'
              '\n'
              '<h3>päiväkirja</h3>\n'
              '<p>Päiväkirjakansio on yksi tärkeimmistä asetuksista. Sen on osoitettava kansioon, '
              'jossa Elite Dangerous<code>Päiväkirja*.loki</code>käytetyn Windows- tai '
              'Proton-profiilin tiedostot.</p>\n'
              '<p>Lehdet tarjoavat mm.</p>\n'
              '<ul>\n'
              '<li>Komentajan henkilöllisyys, sijainti ja matka</li>\n'
              '<li>Tehtävät, alukset ja omaisuus</li>\n'
              '<li>Etsintä, kartografia ja BIO-tiedot</li>\n'
              '<li>Pintakaivostoiminta, palkkasoturikolikot ja muut tuetut osavaltiot</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Päiväkirjan näyttö ja toiminta</h3>\n'
              '<p>Päiväkirjaryhmä näyttää kansiojoukon, löydettyjen lehtien lukumäärän, vanhimmat '
              'ja uusimmat päiväkirjat, uusimman tiedoston nimen ja viimeisimmän luetun merkinnän '
              'ajan.</p>\n'
              '<p>"Valitse päiväkirjakansio" muuttaa kansion. "Lue nyt" käynnistää normaalin '
              'päivityksen välittömästi.</p>\n'
              '<p>Selkeästi tunnistettavat istunnot määritetään FID:n avulla. Uudet täydelliset '
              'merkinnät käsitellään asteittain; Turvalliset lukupaikat estävät kutakin '
              'päiväkirjaa tarpeettomasti uudelleenlukemasta kokonaan uudelleen seuraavan '
              'käynnistyksen yhteydessä.</p>\n'
              '\n'
              '<h3>tietokanta</h3>\n'
              '<p>CMDRHelper tallentaa tarvittavat tiedot pysyvästi paikalliseen '
              'SQLite-tietokantaan. Tämä sisältää globaalit järjestelmä- ja kehotiedot sekä '
              'komentajalle nimenomaisesti määritetyt tiedot.</p>\n'
              '<p>Asetussivulla näkyy tilastotietoja tallennetuista tiedoista. Tietokantaa ei saa '
              'muokata manuaalisesti CMDRHelper:n ollessa käynnissä.</p>\n'
              '\n'
              '<h3>Tuo päiväkirja-arkisto</h3>\n'
              '<p>"Tuo päiväkirja-arkisto" vertaa asetetun lokikansion lokitiedostoja täysin '
              'tietokantaan. Jo tunnetut päiväkirja-alueet huomioidaan tallennettujen '
              'tuontitietojen perusteella, eikä niitä toisteta sokeasti uutena datana.</p>\n'
              '<p>Manuaalisesti näkyvän tuonnin aikana näytetään edistyminen, numero ja '
              'parhaillaan käsiteltävä tiedosto. Valmistumisen jälkeen CMDRHelper ilmoittaa '
              'tuoduista tai jo tunnetuista tiedoista tai virheestä.</p>\n'
              '<p>Arkiston tuonti palvelee myös tuetun historiallisen tiedon uudelleenoppimista '
              'selkeästi osoitetuista lehdistä.</p>\n'
              '\n'
              '<h3>Komentajaan liittyvät tiedot</h3>\n'
              '<p>CMDRHelper erottaa henkilökohtaiset tiedot FID:n ja siihen liittyvän sisäisen '
              'komentajan tunnuksen perusteella. Näitä ovat muun muassa tehtävät, omaisuus, '
              'MercCoins, henkilökohtainen tutkiminen ja online-käyttö.</p>\n'
              '<p>Tuntematonta tai epäselvää päiväkirjaistuntoa ei saa mielivaltaisesti määrätä '
              'komentajalle.</p>\n'
              '\n'
              '<h3>Online-palvelut</h3>\n'
              '<p>CMDRHelper tukee EDSM ja Inara. Molemmat pääsyt käsitellään ja tallennetaan '
              'erikseen jokaiselle tunnetulle komentajalle tai jokaiselle FID:lle.</p>\n'
              '<p>Asetuksissa oleva valinta määrittää vain, kenen käyttöoikeuksia muokataan tai '
              'testataan parhaillaan. Vain aktiivisessa päiväkirjaistunnossa selvästi tunnistettu '
              'komentaja saa lähettää suoran lähetyksen.</p>\n'
              '\n'
              '<h3>EDSM pääsy</h3>\n'
              '<p>"EDSM access for:" valitsee muokattavan ohjaimen. Valinta näyttää "asetettu" tai '
              '"ei asetettu" sen mukaan, onko API-Key tallennettu.</p>\n'
              '<p>Näkyvissä ovat komentajan nimi, piilotettu API-Key-kenttä, "Käytä EDSM", '
              'yhteystesti ja sen viimeinen testitila.</p>\n'
              '<p>Jokainen komentaja tarvitsee oman asianmukaisen EDSM-pääsyn. Valinta ei vaihda '
              'live-lataajaa tähän komentajaan.</p>\n'
              '\n'
              '<h3>Käytä ja testaa EDSM</h3>\n'
              '<p>"Käytä EDSM" ottaa palvelun käyttöön tai poistaa sen käytöstä valitulle FID:lle. '
              'Puuttuvat tai deaktivoidut tunnistetiedot eivät vaikuta paikallisen päiväkirjan '
              'käsittelyyn.</p>\n'
              '<p>"Testaa EDSM-yhteys" tarkistaa lomakkeessa tällä hetkellä näkyvät pääsytiedot. '
              'Onnistunut testi vahvistaa yhteyden, mutta ei muuta aktiivista lokia FID tai suoraa '
              'komentoa.</p>\n'
              '\n'
              '<h3>Inara pääsy</h3>\n'
              '<p>"Inara Access for:" noudattaa samaa multi-CMDR-periaatetta. Aktivointi, '
              'Inara-komentajan nimi ja API-Key tallennetaan erikseen jokaiselle FID:lle.</p>\n'
              '<p>Myös tässä valinnassa näkyy "asetettu" tai "ei asetettu". Yhden komentajan '
              'avainta ei käytetä automaattisesti toiselle komentajalle.</p>\n'
              '\n'
              '<h3>Käytä ja testaa Inara</h3>\n'
              '<p>Kun Inara on määritetty ja otettu käyttöön aktiiviselle päiväkirjalle FID, '
              'CMDRHelper voi lähettää tuetut matka-, sijainti-, tehtävä- ja laivatapahtumat. '
              'Kaikkia päiväkirjan tapahtumia ei lähetetä numeroon Inara.</p>\n'
              '<p>"Testaa Inara-yhteys" tarkistaa tällä hetkellä näkyvät pääsytiedot muuttamatta '
              'live-ohjainta.</p>\n'
              '\n'
              '<h3>Inara lähtölaatikko</h3>\n'
              '<p>Tuetut Inara-tapahtumat merkitään jatkuvasti Lähtevät-kansioon ennen '
              'verkkolähetystä.</p>\n'
              '<p>Tilapäisten virheiden ansiosta nämä merkinnät voidaan säilyttää myöhempiä '
              'yrityksiä varten. Työntekijä käsittelee vain yksilöllisesti aktiivisen lokin FID '
              'Lähtevät-kansiot; Muiden komentajien merkinnät eivät sisälly.</p>\n'
              '\n'
              '<h3>Online-tila otsikossa</h3>\n'
              '<p>EDSM näyttää tällä hetkellä:</p>\n'
              '<ul>\n'
              '<li><b>EDSM</b>– ei voida käyttää tai poistaa käytöstä aktiivisessa FID:ssa</li>\n'
              '<li><b>EDSM odottaa</b>– asetettuna ja ilman jatkuvaa lähetystä</li>\n'
              '<li><b>EDSM vaihteisto</b>– viimeinen EDSM-käsittelyajo päättyi ilman virheitä; '
              'Työkaluvihje kertoo, lähetettiinkö tapahtumia, käsiteltiinkö päiväkirjatietoja vai '
              'eikö uutta tietoa löytynyt</li>\n'
              '<li><b>EDSM virhe</b>– viimeisimmän lähetyksen tila on virheellinen</li>\n'
              '</ul>\n'
              '<p>Tällä hetkellä EDSM:lle ei ole tällä hetkellä erikseen merkittyä tilaa "EDSM '
              'aktiivinen".</p>\n'
              '<p>Inara erottaa tarkemmin:</p>\n'
              '<ul>\n'
              '<li><b>INARA ulos</b>– Ei käytössä aktiiviselle lokille FID</li>\n'
              '<li><b>INARA valmis</b>– asetettu, mutta edelleen ilman vahvistettua lähetystä '
              'tässä istunnossa</li>\n'
              '<li><b>INARA vaihteisto</b>– työntekijä lähettää parhaillaan</li>\n'
              '<li><b>INARA aktiivinen</b>– viimeinen varsinainen siirto vahvistettiin '
              'onnistuneesti</li>\n'
              '<li><b>INARA-virhe</b>– viimeinen siirtoyritys epäonnistui</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Turvallisuus API-Key</h3>\n'
              '<p>API-Key:t ovat henkilökohtaisia \u200b\u200bvaltuustietoja. Syöttökentät ovat '
              'piilossa; Ne tallennetaan komentokohtaisesti sovellusasetuksiin eivätkä '
              'CMDRHelper-tietokantaan.</p>\n'
              '<p>Avaimia ei saa julkaista, jakaa kuvakaappauksina tai lisätä julkisiin '
              'arkistoihin.</p>\n'
              '\n'
              '<h3>Kuvat/kuvakaappaukset</h3>\n'
              '<p>Lähdekansio, kohdekansio, PNG/JPG, automaattinen käsittely, BMP-poisto ja '
              'kirkkaus 0–50 prosenttia sijaitsevat yksinomaan Kuvat-päävalikossa, eivät '
              'Asetukset-sivulla.</p>\n'
              '<p>"Kuvat" -kontekstikohtaisessa ohjeessa kuvataan nämä vaihtoehdot '
              'yksityiskohtaisesti.</p>\n'
              '\n'
              '<h3>pinta</h3>\n'
              '<p>Käyttöliittymäryhmä sisältää ulkoasun, kielen, kirjasimen, kirjasinkoon ja '
              'arvokynnyksen arvokkaille tutkijakappaleille.</p>\n'
              '\n'
              '<h3>Tumma ja vaalea tila</h3>\n'
              '<p>Voit vaihtaa suoraan tumman ja vaalean ulkonäön välillä. Teema otetaan '
              'välittömästi käyttöön käyttöliittymässä ja olemassa olevissa järjestelmä- ja '
              'historiakorteissa ja tallennetaan.</p>\n'
              '\n'
              '<h3>Kieli</h3>\n'
              '<p>Käyttöliittymässä on valittavana kaksitoista kieltä. "Tallenna kieli" tallentaa '
              'valinnan; CMDRHelper on käynnistettävä uudelleen, jotta olemassa olevat widgetit '
              'muunnetaan täysin yhtenäiseksi.</p>\n'
              '\n'
              '<h3>Fontti ja fonttikoko</h3>\n'
              '<p>Fonttiperhe ja fonttikoko 7-24 pt voidaan valita ja tallentaa.</p>\n'
              '<p>Molemmat muutokset tulevat voimaan vasta uudelleenkäynnistyksen jälkeen. '
              'Käyttöliittymä osoittaa tämän selvästi.</p>\n'
              '\n'
              '<h3>Arvokynnys</h3>\n'
              '<p>Explorer-arvon kynnys määrittää arvioidun luottoarvon, josta kappaleet '
              'korostetaan erityisen arvokkaiksi. Muutos tallennetaan välittömästi ja päivittää '
              'vastaavan Explorer-näytön.</p>\n'
              '\n'
              '<h3>Piilota automaattisesti</h3>\n'
              '<p>"Precious Bodies" ja "BIO Finds" sijaitsevat tiukasti vasemmassa sivupalkissa, '
              'eivät Asetukset-sivulla.</p>\n'
              '<p>Kytkimet tallennetaan ja ohjaavat tuettuja pieniä live-vihjeikkunoita tutkimisen '
              'aikana. Arvokappaleiden arvokynnys asetetaan käyttöliittymän asetuksissa.</p>\n'
              '\n'
              '<p>Cargo-ikkuna käyttää yksinomaan aktiiviselle Journal-FID:lle vahvistettua Cargo-snapshotia. CMDR View -näkymässä tarkasteltava commander ja viewed_commander_id eivät vaikuta tähän live-ikkunaan. Shipille näytetään käytetty / enimmäismäärä · vapaa; jos CargoCapacity on tuntematon, arvoa ei arvioida.</p>\n'
              '<p>”EDSM-tila-HUD” kohdassa ”näytä automaattisesti” on oletuksena POIS. Järjestelmään saapumisen jälkeen Eliten päällä näkyy viesti noin 2,5 sekuntia. Saman oleskelun useat Location-tapahtumat eivät tuota kaksoisviestejä; todellinen paluu voidaan tarkistaa uudelleen.</p>\n<p>”EDSM: TUNNETTU” tarkoittaa kelvollista EDSM-osumaa järjestelmälle. ”EDSM: TUNTEMATON” tarkoittaa kelvollista EDSM-vastausta ilman järjestelmäosumaa. ”EDSM: EI VASTAUSTA” tarkoittaa verkko- tai HTTP-virhettä, aikakatkaisua tai virheellistä vastausta, ei koskaan vahvistettua osuman puuttumista. Tunnettuus EDSM:ssä ei ole sama kuin virallinen löytö Elitessä; ensilöytäjien tai ensimmäisten ilmoittajien nimiä ei luvata.</p>\n<p>Viesti toimii navigointi- ja rahti-HUDista riippumatta. Pysyvät HUD-näkymät ja pikasuosikkiviestit säilyvät. Pyyntö ei estä käyttöliittymän toimintaa; jo poistuttujen järjestelmien myöhäiset vastaukset hylätään.</p>\n\n'
              '<h3>Päivitykset</h3>\n'
              '<p>Päivitysryhmä näyttää asennetun version ja GitHubin tilan. Tarkista nyt '
              'tarkistaa manuaalisesti uuden ajoitetun CMDRHelper-version; Lisäksi käynnistyksen '
              'jälkeen tapahtuu viivästetty automaattitarkistus.</p>\n'
              '<p>Jos uusi versio on saatavilla, CMDRHelper kysyy ennen lataamista ja asentamista. '
              'Ilmoitettu tietokantapäivitys näytetään erikseen tässä valintaikkunassa.</p>\n'
              '<p>Olemassa oleville asennuksille riittää yleensä: asenna päivitys → käynnistä CMDRHelper. Tarvittavat historialliset BIO-tietojen, vierailujen ja DSS-metatietojen korjaukset suoritetaan automaattisesti; tietokanta varmuuskopioidaan ennen tietoja kirjoittavia korjauksia. Korjaukset ovat versioituja ja idempotentteja: onnistuneita korjausversioita ei ajeta kokonaan uudelleen joka käynnistyksessä. Palautus vaatii Elite-päiväkirjat, jotka ovat yhä olemassa, luettavissa ja yksiselitteisesti yhdistettävissä komentajaan. Puuttuvia lähteitä ei keksitä eikä tulkita onnistumiseksi; avoimia korjauksia yritetään uudelleen seuraavassa käynnistyksessä. Tietokannan poistoa, käsin ajettavia skriptejä tai uudelleentuontia ei yleensä tarvita.</p>\n\n'
              '<h3>Latauksen edistyminen</h3>\n'
              '<p>Lataus tapahtuu taustalla. Jos kokonaiskoko on tiedossa, CMDRHelper näyttää '
              'tiedoston nimen, vastaanotetun ja kokonaismibitin, prosentin, siirtonopeuden ja '
              'arvioidun jäljellä olevan ajan.</p>\n'
              '<p>Ilman tunnettua kokonaiskokoa edistymispalkki toimii varattu-tilassa ja näyttää '
              'edelleen vastaanotetun tiedon määrän ja - jos se on määritettävissä - nopeuden. '
              'Ennen asennusta ladattu ZIP tarkistetaan.</p>\n'
              '\n'
              '<h3>Peruuta päivitys</h3>\n'
              '<p>"Peruuta lataus" lopettaa käynnissä olevan latauksen hallitusti. Keskeytettyä, '
              'epätäydellistä tai virheellistä latausta ei asenneta.</p>\n'
              '\n'
              '<h3>Päivitys Windowsissa</h3>\n'
              '<p>Windowsissa varsinainen päivitysprosessi jatkuu alkuperäisestä '
              'käynnistyskonsolista riippumatta. Konsolin sammutuksen ei siksi pitäisi vahingossa '
              'lopettaa sitä.</p>\n'
              '<p>Jos virhe tapahtuu tiedostomuutosten alkamisen jälkeen, olemassa oleva '
              'palautusvarmuuskopio yrittää palauttaa edellisen version.</p>\n'
              '\n'
              '<h3>Käynnistä uudelleen päivityksen jälkeen</h3>\n'
              '<p>Onnistuneen asennuksen jälkeen päivitysohjelma CMDRHelper käynnistyy uudelleen '
              'tarkoitetun aloituspolun kautta ja tarkistaa hetken, toimiiko uusi prosessi '
              'vakaasti.</p>\n'
              '<p>Jos julkaisu vaatii kertaluonteisen tietokantapäivityksen, myös '
              'päiväkirja-arkisto arvioidaan uudelleen uudelleenkäynnistyksen jälkeen.</p>\n'
              '\n'
              '<h3>Useita komentajia</h3>\n'
              '<p><b>Asetusten valinta = Kenen online-käyttöoikeuksia muokkaan?</b></p>\n'
              '<p><b>Active Journal-FID = Kuka saa lähettää suoraa lähetystä?</b></p>\n'
              '<p>Online-tilin valinta tai CMDR-näkymä eivät saa vaihtaa live-lataajaa vain '
              'katseltavaksi.</p>\n'
              '\n'
              '<h3>Auttaa</h3>\n'
              '<p>"? Ohje" sijaitsee vasemmassa sivupalkissa "auto show" yläpuolella ja avaa tällä '
              'hetkellä näkyvän päävalikkoalueen ohjeen.</p>\n'
              '<p>Asetukset-alueella painike avaa tämän asetusohjeen suoraan.</p>\n'
              '\n'
              '<h3>Kärki</h3>\n'
              '<p>Jos asennat uudelleen tai sinulla on ongelmia, tarkista ensin:</p>\n'
              '<ul>\n'
              '<li>oikea päiväkirjakansio ja tunnistettu komentajan henkilöllisyys</li>\n'
              '<li>haluttu kieli, teema, kirjasin ja tutkimusohjelman arvokynnys</li>\n'
              '<li>Verkkoyhteys oikeaan FID:ään</li>\n'
              '<li>Jos kuvaongelmia ilmenee, lähde- ja kohdekansiot "Images"-päävalikossa</li>\n'
              '</ul>\n'
              '<p>Jos komentoja on useita, kiinnitä aina huomiota siihen, mitä FID:tä näkyvät '
              'online-käyttötiedot koskevat.</p>'),
    "planet_navigation": (
        'Planeettanavigointi',
        """<h2>Planeettanavigointi</h2>
<p>Planeettanavigaattori auttaa sinua ainoastaan lentämään tiettyyn leveys-/pituusasteeseen planeetalla tai kuussa. Määrität kohteen koordinaateilla ja saat etäisyyden ja suunnan sinne.</p>
<p>Se ei ole tähtienvälinen reittisuunnittelija eikä hoida järjestelmien välistä navigointia tai hyppyjä. Ohjaat alustasi itse.</p>

<h3>Navigaattorin avaaminen ja kohteen syöttäminen</h3>
<p>Avaa yleiskatsauksessa ”Planeettanavigointi” ja valitse ”Manuaalinen syöttö …”.</p>
<ul>
<li><b>Taivaankappale:</b> Valitse kohdeplaneetta tai -kuu luettelosta tai käytä jo tunnistettua taivaankappaletta. Voit myös kirjoittaa taivaankappaleen nimen itse, jos sitä ei vielä ole luettelossa. Käytä epäselvässä tapauksessa koko nimeä, myös järjestelmän nimeä.</li>
<li><b>Leveysaste:</b> Syötä kohteen leveysaste väliltä −90° ja +90°.</li>
<li><b>Pituusaste:</b> Syötä kohteen pituusaste väliltä −180° ja +180°. Huomioi molempien koordinaattien etumerkit.</li>
<li><b>Kohteen nimi:</b> Voit halutessasi antaa nimityksen, jonka avulla tunnistat kohteen helpommin.</li>
</ul>
<p>Vahvista syöttämäsi tiedot valinnalla ”Aseta kohde”. Sinun ei tarvitse syöttää teknisiä tunnisteita kuten BodyID ja SystemAddress; ne eivät ole tavallisia käyttäjän syöttämiä tietoja.</p>

<h3>Milloin kompassi käynnistyy?</h3>
<p>Kun kohde on asetettu ja Elite toimittaa kelvolliset planetaariset sijaintitiedot oikealle taivaankappaleelle, navigointi aktivoituu automaattisesti. Erillistä käynnistyspainiketta ei tarvitse painaa.</p>
<p>Jos nämä tiedot vielä puuttuvat tai kuuluvat toiselle taivaankappaleelle, navigaattori odottaa viestillä ”Odotetaan planetaarisia koordinaatteja …”. Voit syöttää kohteen jo ennen näiden tietojen saapumista.</p>

<h3>Planeettapallo: yli 380 km</h3>
<p>Kun kohde-etäisyys on yli 380 km, navigaattori näyttää planeettapallon.</p>
<ul>
<li><b>Valkoinen ympyrä</b> merkitsee omaa sijaintiasi.</li>
<li><b>Pieni kohdepiste</b> on oranssi, kun kohde on planeetan näkyvällä puolella.</li>
<li>Jos kohde on piilossa olevalla takapuolella, kohdepiste näytetään punaisena.</li>
<li>Sijaintisi pysyy esityksessä paikallaan. Planeetta ja kohde näytetään suhteessa sijaintiisi ja suuntaasi.</li>
</ul>
<p>Valkoinen nuoli osoittaa eteenpäin; keltainen nuoli näyttää kohteen suhteellisen suunnan. Pallo on kaavamainen suunnistusapu, ei maantieteellisesti tarkka maastonäkymä. Punainen piste tarkoittaa pallon takapuolta, ei automaattisesti ”aluksesi takana”.</p>

<h3>Perspektiiviruudukko: enintään 380 km</h3>
<p>Kun kohde-etäisyys on enintään 380 km, näyttö vaihtuu automaattisesti kallistettuun perspektiiviruudukkoon. Jos etäisyys kasvaa jälleen yli 380 km:n, pallo tulee takaisin näkyviin.</p>
<p>Poikkiviivat muodostavat <b>50 km:n etäisyysruudukon</b>. Kohdepiste piirretään ruudukkoon etäisyyden ja suhteellisen suunnan mukaan. Perspektiivi auttaa jatkamaan lähestymistä; kallistuksen vuoksi välit näyttävät tiheämmiltä takaosassa. Tarkkaa ohjaussuuntaa varten tarkkaile myös kohdesuuntaa ja suhteellista suuntaa.</p>

<h3>Navigointiarvojen oikea tulkinta</h3>
<ul>
<li><b>Kohde-etäisyys:</b> Suuri näyttö kertoo jäljellä olevan etäisyyden kohteeseen pitkin ajateltua planeetan pintaa.</li>
<li><b>Kohdekoordinaatit:</b> Kohteelle syötetty koordinaattipari, ensin leveysaste ja sitten pituusaste. Se pysyy samana liikkuessasi.</li>
<li><b>Nykyiset koordinaatit:</b> Viimeisin Elitestä vahvistettu koordinaattiparisi, myös leveysaste / pituusaste.</li>
<li><b>Etäisyys pintaa pitkin:</b> Sama pintaetäisyys kuin kohde-etäisyys, mahdollisesti tarkemmin pyöristettynä yksityiskohtanäytössä. Se ei ole toinen reitti eikä suora avaruudellinen etäisyys ilman halki.</li>
<li><b>Suuntima:</b> Absoluuttinen suunta kohteeseen nykyisestä sijainnistasi kompassikulmana: 000° on pohjoinen, 090° itä, 180° etelä ja 270° länsi.</li>
<li><b>Keulasuunta:</b> Nykyinen suuntasi Eliten ilmoittamana. Se kertoo, mihin suuntaan osoitat nyt, eikä sen tarvitse vielä vastata suuntimaa.</li>
<li><b>Suhteellinen suunta:</b> Keulasuuntasi ja suuntiman välinen ero, esimerkiksi ”23° oikealle”, ”10° vasemmalle” tai ”Suoraan”. Kun kulma on 180°, kohde on takanasi.</li>
<li><b>Kohdesuunta:</b> Korostettu suuntima absoluuttisena suuntana, johon voit kääntyä Eliten HUD:ssa. Se ei ole ylimääräinen kääntymiskulma.</li>
</ul>
<p>Esimerkki: Kun keulasuunta on 051° ja kohdesuunta 074°, käänny 23° oikealle, kunnes Elite-kompassisi näyttää noin 074°. Lennon jatkuessa suuntima ja kohdesuunta voivat muuttua; seuraa päivitettyjä arvoja.</p>
<p>Samassa sijainnissa kohteen kanssa, navalla tai täsmälleen vastakkaisessa pisteessä planeetalla suunta voi olla määrittelemätön. Navigaattori näyttää silloin vastaavan ilmoituksen keksityn suunnan sijaan.</p>

<h3>Ikkunan koko</h3>
<p>Navigaattori-ikkunan kokoa voi muuttaa vapaasti. Pallo tai perspektiiviruudukko mukautuu käytettävissä olevaan tilaan mittasuhteet säilyttäen. Vähimmäiskoko pitää yksityiskohtaiset arvot luettavina; pallo pysyy pyöreänä. Ikkunan sijainti ja koko tallennetaan.</p>

<h3>Navigointi-HUD:n käyttöönotto</h3>
<p>Valitse pääikkunan vasemmalla puolella ruutu kohdasta <b>näytä automaattisesti → Navigointi-HUD</b>. Kun planeettanavigointi on kelvollista, HUD näkyy suoraan etualalla olevan näkyvän Elite-ikkunan päällä.</p>
<p>Se näyttää kolme riviä:</p>
<ul>
<li>suhteellinen suunta</li>
<li>kohdesuunta</li>
<li>etäisyys</li>
</ul>
<p>HUD on läpinäkyvä, päästää napsautukset läpi eikä vie kohdistusta: se ei peitä peliä läpinäkymättömällä alueella, sieppaa hiiren napsautuksia eikä vie syöttökohdistusta Eliteltä ilmestyessään automaattisesti.</p>
<p>Ilman kelvollista navigointia tai yksiselitteistä suuntaa se muuttuu automaattisesti näkymättömäksi. Se piilotetaan myös silloin, kun Elite on pienennetty tai ei ole etualalla. Sivupalkin valintaruutu voi silti pysyä valittuna; se ilmaisee toiveesi automaattisesta näytöstä, ei tämänhetkistä näkyvyyttä.</p>
<p>HUD on vain lisänäyttö. Tavallinen navigaattori toimii siitä riippumatta, myös silloin, kun HUD on poistettu käytöstä tai ei ole saatavilla.</p>

<h3>Uuden kohteen asettaminen</h3>
<p>Samalla taivaankappaleella voit milloin tahansa avata ”Manuaalinen syöttö …” uudelleen ja asettaa toiset koordinaatit. Uusi kohde korvaa aiemman navigointikohteen. Vastaavilla sijaintitiedoilla kompassi päivittyy heti.</p>
<p>”Lopeta navigointi” poistaa nykyisen kohteen. Aseta vain uusi kohde seuraavaa lähestymistä varten.</p>

<h3>Tietojen ajantasaisuus ja rajoitukset</h3>
<p>Navigointi perustuu Eliten toimittamiin tilatietoihin. Päivitykset voivat saapua viiveellä pelitilanteen mukaan. Navigaattorin ikänäyttö kertoo, kuinka kauan viimeisestä vahvistetusta tilaviestistä on kulunut.</p>
<p>Pintaetäisyys kuvaa lyhintä kaarta ajatellulla pallolla. Se ei ole maasto- tai tiereitti. Navigaattori ei tunne reitin esteitä eikä maaston korkeuksia; lentokorkeus, turvallinen nopeus ja esteiden välttäminen jäävät sinun vastuullesi.</p>

<h3>Vinkki</h3>
<p>Tarkista ennen lähestymistä taivaankappaleen nimi ja kohdekoordinaattien etumerkit. Käänny sitten kohdesuuntaan Elite-kompassissa ja tarkkaile suhteellista suuntaa ja etäisyyttä. Jos navigaattori odottaa, tarkista, toimittaako Elite jo planetaarisia koordinaatteja kohdetaivaankappaleelle.</p>""",
    ),
}

DIALOG_TITLE = 'Ohje – {area}'
CLOSE_LABEL = 'Sulje'
