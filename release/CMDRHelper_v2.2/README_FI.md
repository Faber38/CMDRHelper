# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Co-pilottisi Elite Dangerousiin](cmdrhelper/assets/readme/cmdrhelper_readme_fi.png)

**Henkilökohtainen kumppani Elite Dangerousiin -- tutkimusmatkailu,
järjestelmäanalyysi ja Commanderin tiedot yhdellä silmäyksellä**

CMDRHelper on itsenäinen työpöytäsovellus **Elite Dangerous** -peliin.
Se analysoi pelin paikallisten Journal-tiedostojen tietoja ja esittää ne
selkeästi. Tavoitteena on henkilökohtainen apuri, joka järjestelmää
tutkittaessa näyttää nopeasti, mitä jo tiedetään, mitkä taivaankappaleet
ovat kiinnostavia sekä mitä omia löytöjä ja kartoituksia on tehty.

Projekti on edelleen aktiivisessa kehityksessä.

## Toimintojen yleiskatsaus

### Elite Dangerous -Journalit

CMDRHelper lukee paikallisia Journal-tiedostoja ja käsittelee muun
muassa tähtijärjestelmiä, tähtiä, planeettoja, kuita, Belt Clustereita,
skannauksia, kartoituksia sekä biologisia ja geologisia signaaleja.
Commanderin omat tiedot voidaan erottaa täydentävistä ulkoisista
tiedoista.

### Tehtävät

CMDRHelper analysoi Elite Dangerous -Journalien tehtävätapahtumia ja
esittää aktiiviset tehtävät selkeästi. Tehtävien tilaa ja niihin
liittyviä Journal-tapahtumia seurataan.

Myös pelin aikana NPC-viesteinä (`ReceiveText`) saapuvat
tehtävätarjoukset voidaan tunnistaa ja ottaa huomioon tehtävien
myöhemmässä yhdistämisessä. Koska Elite Dangerous ei tarjoa kaikille
tehtävätyypeille kaikkia tietoja samassa Journal-tapahtumassa,
yhdistäminen rakennetaan vaiheittain käytettävissä olevien
Journal-tietojen perusteella.

### Järjestelmä- ja Explorer-näkymä

Järjestelmän tunnetut kappaleet esitetään graafisesti ja ne voidaan
valita suoraan. CMDRHelper voi näyttää muun muassa:

-   kappaleen nimen ja tyypin
-   etäisyyden järjestelmässä
-   itse skannattu tai vain ulkoisesta lähteestä tunnettu
-   jo löydetty ja kartoitettu
-   mahdollinen ensilöytö ja mahdollinen First Mapping
-   Commanderin kartoittama
-   tehokas kartoitus
-   biologiset ja geologiset signaalit
-   skannaus- ja kartoitusarvot

BIO-signaalit korostetaan selvästi kyseisen kappaleen kohdalla.
Kohdistus tehdään järjestelmäkohtaisesti, jotta eri tähtijärjestelmien
BodyID-tunnuksia ei sekoiteta keskenään.

### Kappaleen yksityiskohtainen näkymä

Kappaletta napsautettaessa avautuu yksityiskohtainen näkymä.
Käytettävissä olevista tiedoista riippuen siinä näytetään kappaleen
tyyppi, massa, etäisyys, painovoima, ilmakehä, vulkanismi,
laskeutumiskelpoisuus, terraforming-tila, materiaalit,
BIO-/GEO-signaalit, skannausarvo, kartoitusarvo ja löytötila.

Puuttuvat tiedot näytetään tuntemattomina eikä niitä esitetä varmoina
tietoina.

## Kappaleiden graafinen esitys

CMDRHelper sisältää omat grafiikat lukuisille kappaletyypeille, kuten
High Metal Content Worlds, Metal Rich Bodies, Rocky Bodies, Icy Bodies,
Rocky Ice Worlds, Earth-like Worlds, Water Worlds, Ammonia Worlds,
useille kaasujättiläisluokille, vesi- tai ammoniakkipohjaista elämää
sisältäville kaasujättiläisille, heliumrikkaille kaasujättiläisille, eri
tähtiluokille ja Belt Clustereille.

Tavallisia PNG-kuvia käytetään yleisnäkymissä. Monille kappaleille on
lisäksi saatavilla **2:1-equirectangular `_texture.png`** animoitua
yksityiskohtaista näkymää varten.

### Pyörivät 3D-planeetat

Sopivat 2:1-tekstuurit projisoidaan pyörivälle pallolle. CPU-renderöijä
toimii **PySide6:n ja NumPyn** avulla ilman ylimääräisiä
OpenGL-/PyOpenGL-riippuvuuksia. Se sisältää palloprojektion, hitaan
pyörimisen, valaistuksen, reunan tummennuksen ja ilmakehän reunan.

### Animoidut elämänmuodot

Elämää sisältäville kaasujättiläisille on erilaisia animaatioita:

**Water Life:** syaanin-/turkoosinvärisiä leijuvia organismeja, joilla
on halo ja liikkuvat pyrstöt.

**Ammonia Life:** omia violetin-/meripihkanvärisiä, puoliläpinäkyviä
organismeja, joilla on sykkivä ydin, lyhyitä säikeitä ja hitaampi liike.

### Animoidut Belt Clusterit

Belt Clustereita ei esitetä palloina. Yksityiskohtainen näkymä luo
proseduraalisen asteroidikentän, jossa on yksittäisiä asteroideja, eri
kokoja ja syvyyksiä, omaa pyörimistä, yksilöllistä ajautumista,
parallaksiefekti, kraattereita sekä hillittyjä pöly- ja hiukkasefektejä.

## EDSM täydentävänä tietolähteenä

CMDRHelper pystyy erottamaan omat Journal-tiedot EDSM-tiedoista. Lähde
merkitään vastaavasti omaksi Journaliksi, EDSM:ksi tai omaksi
Journaliksi + EDSM:ksi. Omat Journal-tiedot ovat erityisen tärkeitä,
koska ne osoittavat, mitä kyseinen Commander on todella itse skannannut
tai kartoittanut.

CMDRHelper voi lähettää uudet Journal-tiedot automaattisesti EDSM:ään.
Tällöin huomioidaan EDSM:n ajantasainen dynaaminen Discard-luettelo,
jotta vain EDSM:n haluamat tapahtumat lähetetään. Siirron eteneminen
tallennetaan turvallisesti Journal-tiedostokohtaisesti. Ensimmäisellä
aktivointikerralla jo olemassa olevia vanhoja Journaleita ei lähetetä
uudelleen kokonaisuudessaan.

EDSM-tila näytetään suoraan yleisnäkymän yläosassa. Vihreä ilmaisin
merkitsee toimivaa tiedonsiirtoa; virheet näytetään punaisina ja
kirjataan lisäksi CMDRHelperin lokiin.

## Paikallinen tietokanta

CMDRHelper käyttää SQLitea. Seuraavat säännöt ovat voimassa:

-   `cmdrhelper/database.py` on ohjelmakoodia ja kuuluu julkaisuun.
-   `data/cmdrhelper.db` sisältää henkilökohtaisia Commander-tietoja
    eikä sitä **jaeta**.
-   Uudessa asennuksessa paikallinen tietokanta rakennetaan uudelleen
    kyseiselle käyttäjälle.

Näin henkilökohtaisia Commander-tietoja ei toimiteta julkaisun mukana.

## Diagnostiikka ja lokitiedosto

CMDRHelper ylläpitää omaa kiertävää lokitiedostoa diagnostiikkaa ja
vianetsintää varten. Tärkeät ohjelma-, Journal-, tietokanta- ja
EDSM-tapahtumat kirjataan lokiin. EDSM-lokitusta on vähennetty niin,
etteivät pelkästään EDSM:n hylkäämät Journal-tapahtumat täytä normaalia
lokia tarpeettomasti, kun taas onnistuneet siirrot, varoitukset ja
virheet pysyvät näkyvissä.

## Alustat

CMDRHelper kehitetään Pythonilla ja PySide6:lla, ja se on tarkoitettu
**Linuxille ja Windowsille**. Kehitys tapahtuu pääasiassa Linuxissa;
Windows voidaan asentaa mukana toimitettujen batch-tiedostojen avulla.

## Vaatimukset

Python **3.10–3.13** sekä `requirements.txt`-tiedostossa määritellyt paketit:

``` text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

## Asennus Linuxissa

``` bash
./install.sh
./start.sh
```

Vaihtoehtoisesti voidaan käyttää olemassa olevia
Linux-käynnistysskriptejä.

## Asennus Windowsissa

Windowsia varten on `install.bat` ja `start.bat`.

`install.bat` tarkistaa Python 3.10–3.13:n, luo tai korjaa paikallisen `venv`-ympäristön, päivittää
pipin ja asentaa `requirements.txt`-tiedoston paketit. Tämän jälkeen
CMDRHelper käynnistetään `start.bat`-tiedostolla.

## Julkaisun luominen

``` bash
./create_release.sh
```

Julkaisuversion numero määritetään suoraan skriptissä. Luotu ZIP
sisältää ohjelmakoodin ja assetit, mutta ei henkilökohtaista
tietokantaa, virtuaalista Python-ympäristöä eikä Git-, välimuisti- tai
editoritiedostoja.

## Versio 2.2

**Versio 2.2** erottaa verkkopalvelut, omat löydöt, kuvakaappaukset ja
palkkasoturikrediitit komentajittain sekä vahvistaa Journal- ja päivitysprosessia.

### Multi-CMDR-verkkopalvelut

-   Inara ja EDSM tallentavat tunnukset komentaja/FID-kohtaisesti omalla API-
    avaimella ja näyttävät **määritetty/ei määritetty**. Valinta vain muokkaa
    tunnuksia; live-lähetys käyttää aina aktiivista Journal-FID:tä, ei katsottua
    komentajaa tai asetusvalintaa. Lähetyspaikat ja runtime-tilat ovat erilliset,
    ja vanhat workerit mitätöityvät FID-vaihdossa.
-   Automaattinen Inara-siirto käyttää pysyvää, deduplikoitua SQLite-outboxia,
    eriä ja retrytä. Häiriö ei estä sovellusta; kuittaamattomat eventit pysyvät
    komentajallaan ja niitä yritetään vain aktiiviselle FID:lle. Vierasta outboxia
    ei lähetetä. Tuki: FSD-hypyt, telakointi, laskeutumiset, Carrier-matkat,
    sijainti, tehtävät ja alusten osto/myynti. Ei luvata: credits/assets, cargo,
    materiaalit, ShipLocker, loadoutit, eksobiologia, oma Surface-Mining-historia
    tai dokumentoimattomat Frontier-eventit.

### Journal, Surface Mining ja kartografia

-   Reader löytää ensin viimeisen täydellisen Journal-tilan. Offset etenee vasta
    transaktiotallennuksen jälkeen; Inara-outbox on valinnainen. Puuttuva/virheellinen
    asetus tai Inara-/EDSM-verkkovirhe ei vaikuta paikallisiin tietoihin tai
    offseteihin. Erikoistapaukset korjataan hallitusti ja idempotentisti ilman
    historiallista Inara-massalähetystä.
-   `MiningRefined` tallentaa oikeasti louhitut commodities kumulatiivisesti
    komentaja/järjestelmä/body-kohtaisesti. Varman Rhino-kontekstin materiaalit
    pysyvät erillään `Scan.Materials`-tiedoista. Body-näkymä näyttää **Omat
    louhintalöydöt** ja tarvittaessa sivumateriaalit; **LOUHINTA ×N** tarkoittaa
    yhä planeettakohteita ja löydöt näkyvät vasta louhinnan jälkeen. Kertaluonteinen
    backfill lukee vanhat Rhino-Journalit. Depotin sisältöä ei ennusteta etukäteen.
-   `SellExplorationData` ja `MultiSellExplorationData` ovat myyntiraja.
    Historiallista `NavBeaconDetail`-tietoa ei pidetä avoimena, eivätkä myydyt
    vanhat tiedot palaa rekonstruktion jälkeen.

### Palkkasoturikrediitit

-   Saldo tulee vain `Statistics.Bank_Account`-arvoista, Frontier-nimellä
    `MercCoins`: nykyinen, yhteensä käytetty, Engineering, varusteet ja
    `total_earned`. Arvot ovat riippumattomia; osittainen snapshot ei poista
    tunnettuja kenttiä. Vain yksiselitteiset sessiot hyväksytään, multi-CMDR on
    tiukasti erotettu ja kertaluonteinen backfill idempotentti. `total_earned` voi
    poiketa saldosta; CMDRHelper säilyttää arvot ilman omaa saldo- tai deltalaskua.

### Kuvat, käyttöliittymä ja päivitys

-   Uudet kuvat menevät komentaja+FID-kansioihin; nimi sisältää ajan, komentajan
    ja varman järjestelmän. Identiteetti jäädytetään jonotushetkellä. Suodattimet:
    **Nykyinen komentaja**, **Kaikki**, **Kohdistamaton**. Legacy-kuvat säilyvät,
    FID erottaa samat nimet. Ikkuna skaalautuu taas vaakasuunnassa, Explorer-selite
    rivittyy ja online-valikoiden leveys/popup-sijainti rajataan ilman suurempaa
    minimileveyttä.
-   Windowsissa worker ja uudelleenkäynnistetty sovellus irrotetaan `start.bat`/
    `cmd.exe`-konsolista uudella prosessiryhmällä, itsenäisellä konsolilla ja ilman
    perittyjä standardikahvoja. Control-C/Break/interrupt ja rollback, myös
    `KeyboardInterrupt`, ovat turvallisempia; epävarmat dependencies saavat
    korjausmerkin. Kahden sekunnin handshake säilyy.
-   ZIP ladataan asynkronisesti. Todelliset tavut ohjaavat nimeä, MiB:tä,
    kokonaismäärää, prosenttia, nopeutta, ETAa ja palkkia; tuntematon koko käyttää
    busy-tilaa näyttäen MiB:t. Säieturvallinen peruutus poistaa keskeneräiset/
    virheelliset tiedostot, ja asennus alkaa vain kelvollisesta ZIPistä. Vaiheet:
    lataus, ZIP-tarkistus, updaterin käynnistys. Backupin, purun, kopioinnin,
    requirements-asennuksen ja uudelleenkäynnistyksen eteneminen ei vielä näy.

## Versio 2.1

**Versio 2.1** parantaa biologiaennusteita, laivastonäkymää ja suurten
Journal-arkistojen suorituskykyä sekä vahvistaa Windows- ja Linux-asennusta,
käynnistystä, päivitystä ja palautusta.

### Bioennusteet ja elinympäristö

-   uusi ennuste näyttää riittävillä tiedoilla konkreettisia mahdollisia
    lajeja pelkän suvun sijasta. Useita lajeja voidaan näyttää luottamuksella
    **KORKEA**, **KESKITASO** tai **MATALA**; pieniä otoksia käsitellään
    varovaisesti.
-   löydetty tai tunnistettu laji korvaa ennusteen. Kun kaikki BIO-signaalit
    tunnetaan, jäljellä olevat ennusteet poistuvat.
-   tiivis BIO-ikkuna näyttää ehdokkaiden arvioidut arvot ja kappaleen
    mahdollisen kokonaisarvon. Oranssi/kulta on arvio, vihreä vahvistettu arvo;
    spekulatiivisia First Footfall -bonuksia ei lasketa mukaan.
-   lämpötila, paine, ilmakehän koostumus, säde sekä tähti-/parent-konteksti
    tallennetaan elinympäristötiedoiksi. Yleistä variantti- tai väriennustetta
    ei ole toteutettu.

### CMDR-laivasto

-   laivasto voidaan lajitella nousevasti tai laskevasti viime käytön, nimen,
    tyypin, hyppymatkan, rahtitilan, tyhjämassan, sijainnin tai ajan mukaan.
-   suodattimet näyttävät kaikki alukset tai ajoneuvo- tai fighter-hangaarilla
    varustetut alukset. Hangaarit tunnistetaan todellisista Loadout-moduuleista;
    SRV:t ja fighterit pysyvät emoaluksen varusteina.

-   hallisuodatin tunnistaa `int_buggybay_*`- ja uuden suuren
    `int_mkiilargebuggybay_*`-hallin keksimättä sisältöä. `mev_rhino` käsitellään
    SRV:nä/maa-ajoneuvona, ei omana aluksena, väittämättä hallia aina tunnetuksi.

### Pysyvä Commander-tila ja uudelleenkäynnistys

-   tehtävät, avoimet bio-/kartografiatiedot, viime sijainti, alukset ja loadoutit,
    oma Fleet Carrier ja varallisuus säilyvät SQLitessa CMDRHelper/Elite-käynnistyksissä.
-   tila säilyy, kunnes oikea Journal-tapahtuma muuttaa sitä; uudesta istunnosta
    puuttuva tieto ei poista tunnettua tietoa.
-   keskeytyksen jälkeen jatketaan viimeisestä turvallisesta kohdasta;
    keskeneräistä viimeistä riviä ei katsota käsitellyksi.
-   v2.1 voi hallitusti rakentaa kerran tarvittavat tilat vanhoista Journaleista
    ja jatkaa sitten inkrementaalisesti.

### Planeettojen kaivoskohteet ja pintamateriaalit

-   `FSSBodySignals`/`SAASignalsFound` ilmoittavat **planeettojen kaivoskohteet**,
    jotka näkyvät BIO/GEO:n rinnalla lokalisoituna **LOUHINTA ×N**. N on
    Frontierin määrä, ei laskettu indeksi.
-   `Scan.Materials` tallennetaan kappaleelle; nimet ja prosentit näytetään
    **kappaleen pintamateriaaleina**, myös työkaluvihjeessä.
-   kohteiden määrä ja yleinen materiaalikoostumus pidetään erillään;
    materiaaleja ei väitetä tietyn kaivoskohteen sisällöksi.

### Journalit, arkistotuonti ja suorituskyky

-   sekä `Journal.YYMMDDHHMMSS.PART.log` että
    `Journal.YYYY-MM-DDTHHMMSS.PART.log` käsitellään oikeassa järjestyksessä,
    joten vanha tiedosto ei enää korvaa nykyistä CMDR:ää tai tilaa.
-   epätäydellisten arkistojen Signal-/Mapping-tapahtumat voidaan tuoda ilman
    aiempaa täydellistä Body Scania; myöhemmät skannaukset täydentävät tiedot
    ja multi-CMDR-erottelu säilyy.
-   pysyvä Journal-indeksi ohittaa tunnetut muuttumattomat tiedostot. Aktiivista
    tiedostoa luetaan vain viimeisestä turvallisesta tavupaikasta; metadata ja
    SHA-256 varmistavat identiteetin, ja FID-kohdistus säilyy.
-   ensimmäinen suuri indeksin rakennus näyttää aidot luvut, prosentit ja
    pienet animoidut avaruusalukset responsiivisessa näkymässä. Myöhemmillä
    nopeilla käynnistyksillä näkymää ei yleensä näytetä.

-   indeksin jälkeen käsitellään vain uudet täydet rivit. Muutokset ja turvallinen
    sijainti tallennetaan yhdessä; virheessä se ei etene ja osittainen rivi odottaa.
-   pikakäynnistys löytää live-CMDR:n uusimmasta yksiselitteisestä indeksoidusta
    istunnosta, lataa tilan heti ja saa Journal-määrän indeksistä.

### Asennus ja päivitys

-   vahvistetut Windows- ja Linux-skriptit tukevat Python-versioita 3.10–3.13,
    käyttävät vain paikallista `venv`-ympäristöä ja korjaavat turvallisesti
    paikalliseksi todetun ympäristön. Linux-symlinkit käsitellään varovasti;
    vieraita ympäristöjä ei käytetä.
-   päivitys ja palautus ilmoittavat virheistä selkeästi ja suojaavat
    henkilötiedot ja Elite-Journalit.
-   normaali päivitys v2.0:sta v2.1:een on tuettu. Selvästi v2.0:aa vanhemmissa
    asennuksissa asetukset kannattaa varmuuskopioida; ongelmissa puhdas asennus
    voi auttaa. Älä koskaan poista Elite-Journaleja tai vanhoja Helper-tietoja
    yleisenä korjauksena.
-   erittäin suuren arkiston ensimmäinen v2.1-käynnistys voi kestää indeksin
    vuoksi hetken; myöhemmät käynnistykset ovat huomattavasti nopeampia.

## Versio 2.0

**Versio 2.0** lisää aidon Multi-CMDR-tuen ja säilyttää version 1.5
reittisuunnittelijan sekä kaikki aiemmat ominaisuudet.

### Multi-CMDR ja CMDR-näkymä

-   komentajat tunnistetaan automaattisesti Frontier-FID:n avulla. Vain
    Journal määrittää live-komentajan; toisen profiilin katselu ei muuta
    kohdistusta eikä live-kirjoituksia.
-   käynnit, tutkimus, tehtävät, sijainnit, alukset, Fleet Carrier, varallisuus
    sekä myymättömät biologiset ja kartografiset tiedot tallennetaan erikseen.
-   **CMDR-näkymä** näyttää tunnetut komentajat offline-tilassa: tehtävät,
    viimeisen sijainnin ja aluksen, Fleet Carrierin sijainteineen, varallisuuden
    sekä arviot myymättömistä tiedoista.

### Multi-CMDR-kronikka

-   jokaisella komentajalla on vakaa väri ja omat tai yhteiset suodattimet.
-   aikajärjestyksessä olevat reitit pysyvät erillään eivätkä yhdistä eri
    komentajien hyppyjä.
-   usean komentajan vierailemat järjestelmät näkyvät moninkertaisina käynteinä.

### Komentajien laivastot

-   jokaisella komentajalla on pysyvä laivasto, jossa tunnetut alukset ja
    avattavat tiedot varustuksesta, kantamasta, tankeista, rahdista ja sijainnista.
-   live-alus on vihreä; muut saavat vakaat sijaintivärit ja luetteloa voi
    vierittää pystysuunnassa.
-   puvut, Scarab-, Scorpion- ja Nomad-SRV:t, hävittäjät, taksit ja
    laskeutumisalukset eivät ole tavallisia komentajan aluksia.

### Olemassa olevat tietokannat

Sisäiset skeemamigraatiot jatkavat olemassa olevien tietokantojen käyttöä.
Multi-CMDR-tiedot erotetaan Frontier-FID:llä. Jos vanhat tiedot voivat kuulua
usealle profiilille, CMDRHelper ei arvaa eikä poista kaikkea; epäselvä kohdistus
jää ratkaisematta.

CMDRHelper tukee edelleen **Linuxia ja Windowsia** ja sisältää version 1.5
alus- ja Fleet Carrier -reittisuunnittelijan.

## Versio 1.5

**Versio 1.5** on merkittävä toiminnallinen päivitys. Se lisää uuden
reittisuunnittelijan aluksille ja Fleet Carriereille, yhdistää reitin
etenemisen tiiviimmin Elite Dangerous -Journaliin sekä parantaa
luotettavuutta ja suorituskykyä erityisesti Windowsissa.

### Reittisuunnittelija ja alusreitit

-   uusi **Reittisuunnittelija** laskee alusreitit Spansh Galaxy Plotterilla
    ja näyttää kaikki välijärjestelmät CMDRHelperissa.
-   CMDRHelper tunnistaa Journalista aluksen, FSD:n, FSD-engineeringin ja
    aktiivisen Guardian FSD Boosterin. Käytettävissä olevat tankki-, lasti-,
    massa- ja FSD-arvot siirretään automaattisesti.
-   automaattisesti tunnistettuja arvoja voi edelleen muokata. Manuaaliset
    ohitukset säilyvät myöhemmissä Loadout-, lasti- ja polttoainepäivityksissä,
    kunnes tunnistetut alustiedot otetaan erikseen uudelleen käyttöön.
-   Loadout-, lasti- ja polttoainemuutokset päivittävät vain kyseiset
    reittiarvot. Tuntemattomat arvot pysyvät näkyvästi tyhjinä eikä niitä
    arvioida.
-   lähtö- ja kohdejärjestelmälle tarkistetaan tarkka Spansh-osuma ennen
    laskentaa. Tuntematon järjestelmä ilmoitetaan ymmärrettävästi käynnistämättä
    epäonnistuvaa reittityötä.
-   eteneminen seuraa olemassa olevan Journal-virran todellisia
    `FSDJump`-tapahtumia. Onnistuneen hypyn jälkeen seuraava järjestelmä
    kopioidaan automaattisesti Qt-leikepöydälle ja voidaan kopioida uudelleen
    myös käsin.

### Fleet Carrier ja CTSVision

-   erillinen **Fleet Carrier / CTSVision** -tila käyttää Spansh Fleet Carrier
    Routeria.
-   lasketut Fleet Carrier -reitit sisältävät hyppy- ja Tritium-tiedot, ja ne
    voidaan viedä CTSVision-yhteensopivaksi CSV-tiedostoksi.

### Journalin luotettavuus ja suorituskyky

-   aktiivisen Journal-tiedoston tilapäinen lukuvirhe ei enää kuittaa muutosta
    liian aikaisin. Normaali kyselyjakso yrittää uudelleen ilman aggressiivista
    busy-wait-silmukkaa.
-   BIO- ja kartografiaoppiminen ei enää käy koko Journal-arkistoa läpi
    tavallisten asiaan liittymättömien tapahtumien yhteydessä. Täysi analyysi
    rajataan olennaisiin BIO- tai myyntitapahtumiin ja tarkoitettuun
    arkistotuontiin.
-   tämä vähentää tarpeetonta työtä jokaisella Journal-lisäyksellä ja parantaa
    luotettavuutta ja reagointia erityisesti Windowsissa.

## Versio 1.0.8

**Versio 1.0.8** lisää henkilökohtaisen hyppysuosituksen tutkimusmatkoille,
täydentää kansainvälistämistä ja parantaa Tutkimuksen live-ikkunoita sekä
Kronikan karttanäkymää.

### Hyppyvinkki ja hyppysuositus

-   uusi **”Hyppyvinkki”**-osio analysoi omaa paikallista
    tutkimustietokantaasi ja näyttää, mitkä proseduraaliset järjestelmäkoodit
    voivat olla erityisen kiinnostavia valitulle tutkimuskohteelle.
-   kohteiksi voi valita muun muassa BIO-löydöt yleisesti, tunnetut BIO-suvut
    ja -lajit, arvokkaat tutkimuskappaleet, terraformauskandidaatit,
    Vesimaailmat, Maan kaltaiset maailmat ja Ammoniakkimaailmat.
-   sijoituksessa huomioidaan koodilla aiemmin tutkitut järjestelmät,
    osumat, osumaprosentti, tallennetut löydöt ja käytettävissä oleva
    otoskoko. Säädettävä tutkittujen järjestelmien vähimmäismäärä estää
    liian pienten aineistojen yliarvioinnin.
-   CMDRHelper korostaa galaksikartalta etsittäviä ensisijaisia koodeja,
    kuten yhdistelmiä `ZL-Z b` tai `NR-C d`.
-   suositus perustuu yksinomaan **omaan aiempaan tutkimushistoriaasi** ja
    siihen tallennettuihin löytöihin. Se on tilastollinen ohje eikä
    **takaa löytöä**.

### Kansainvälistäminen

-   kansainvälistämistä on täydennetty edelleen ja verrattu uudelleen
    saksankieliseen viitteeseen.
-   kaikilla **12 tuetulla käyttöliittymäkielellä** on nyt sama täydellinen
    **560 käännösavaimen** kokonaisuus.
-   **hyppyvinkin ja hyppysuosituksen** uudet ja aiemmin puuttuneet
    käännökset on lisätty kaikkiin tuettuihin kieliin.
-   avainjoukko, avainten järjestys ja muotoilun paikkamerkit on yhtenäistetty
    kaikissa kielitiedostoissa.

### Tutkimuksen live-ikkunat ja asetukset

-   Tutkimuksen asetuksiin on lisätty selittävät tooltipit **”Arvokkaat
    kappaleet”**- ja **”BIO-löydöt”**-ikkunoiden automaattiselle näyttämiselle.
-   tooltipit kertovat, milloin kukin ikkuna avautuu automaattisesti asetetun
    arvorajan tai havaittujen BIO- tai GEO-signaalien perusteella.
-   Commanderin jo kartoittamia arvokkaita kappaleita ei enää näytetä
    avoimina kohteina pienessä live-ikkunassa.
-   kokonaan analysoidut BIO-kappaleet poistuvat BIO-liveikkunasta; saman
    kappaleen GEO-osuus, jota ei ole vielä kartoitettu DSS:llä, pysyy
    näkyvissä.

### Kronikka

-   Kronikan kartan suuntaus on korjattu siten, että positiivinen Z-akseli
    osoittaa ylöspäin. Tallennetut Elite-`StarPos`-koordinaatit säilyvät
    muuttumattomina.

## Versio 1.0

**Versiossa 1.0** CMDRHelper saavuttaa suunnitellun peruslaajuuden
ensimmäisen täydellisen kehitysvaiheen.

Tärkeät muutokset ja laajennukset versioon 1.0 asti:

### Kappaleiden ja tähtien esityksen viimeistely

-   tuettujen planeetta-, tähti- ja erikoiskohdetyyppien kuvamateriaalia
    on täydennetty edelleen.
-   lisätähtiluokat ja erityiset tähtityypit esitetään omilla
    grafiikoilla yleisen oletusesityksen sijaan.
-   soveltuville kappaleille on edelleen käytettävissä pyörivät
    2:1-equirectangular-tekstuurit yksityiskohtaisessa näkymässä.
-   erityisiä astronomisia kohteita voidaan lisäksi esittää
    yksityiskohtaisessa näkymässä sopivilla videoilla.
-   neutronitähdet, valkoiset kääpiöt, mustat aukot ja supermassiiviset
    mustat aukot saavat näin huomattavasti yksilöllisemmän esityksen.
-   käytetty ulkopuolinen kuva- ja videomateriaali dokumentoidaan
    lähteen ja credit-tiedon kanssa kohdassa **"Kuva- ja videomateriaali
    / Media Credits"**.

### Viimeistelty monikielisyys

-   käyttöliittymän käännökset on viimeistelty tuetuille kielille ja
    yhdenmukaistettu yhteiseen avainjoukkoon.
-   kaikki **12 käyttöliittymäkieltä** käyttävät samaa täydellistä
    käännösavainjoukkoa.
-   automaattinen käännöstarkistus tarkistaa puuttuvat, ylimääräiset ja
    päällekkäiset avaimet sekä poikkeavat muotoilun placeholderit.
-   saksa toimii täysin ylläpidettynä viitteenä käyttöliittymälle ja
    tulevalle dokumentaatiolle.

### Muutokset versiosta 0.9.9

### Monikielisyys ja käännösten tarkistus

-   käyttöliittymä on siirretty keskitettyyn monikielisyysjärjestelmään.
-   CMDRHelper tukee nyt **12 käyttöliittymäkieltä**: **saksa, englanti,
    ranska, italia, norja (Bokmål), ruotsi, suomi, puola, hollanti,
    espanja, turkki ja kreikka**.
-   kieli voidaan valita ja tallentaa asetuksissa; kielten nimet näkyvät
    valintakentässä kukin omalla kielellään.
-   puuttuvat käännökset käyttävät määriteltyä fallback-järjestystä:
    **valittu kieli → englanti → saksa → käännösavain**.
-   käännökset sijaitsevat keskitetysti kielitiedostoissa hakemistossa
    `cmdrhelper/i18n/`.
-   uusi kehittäjätyökalu `tools/check_i18n.py` tarkistaa
    automaattisesti:
    -   ohjelmassa käytetyt `tr("...")`-avaimet,
    -   puuttuvat tai ylimääräiset käännösavaimet,
    -   päällekkäiset avaimet,
    -   poikkeavat muotoilun placeholderit, kuten `{system}` tai
        `{count}`.
-   Linuxissa i18n-tarkistus suoritetaan automaattisesti käynnistyksen
    yhteydessä `start.sh`-skriptin kautta. Löydetyt käännösongelmat
    ilmoitetaan selvästi, mutta ne eivät estä ohjelman käynnistymistä.
-   tehtävien ja Journalin käsittely pidetään edelleen erillään
    valitusta CMDRHelper-käyttöliittymäkielestä, jotta Elite Dangerousin
    sisäiset tiedot eivät riipu lokalisoiduista näyttöteksteistä.

### Explorer ja järjestelmäkartta

-   järjestelmäkartan Parent-/Child-rakenne on uudistettu: tähdet,
    planeetat, kuut ja Belt Clusterit järjestetään Journal-hierarkian
    mukaisesti.
-   uusi **"Näytä kaikki"** -toiminto, joka tarjoaa koko järjestelmän
    kompaktin pienoiskuvan.
-   pienoiskuvan kappaleita voidaan napsauttaa; pääkartta siirtyy sen
    jälkeen suoraan valittuun kappaleeseen.
-   suurten järjestelmäkarttojen navigointia on parannettu:
    -   hiiren rulla siirtää karttaa vaakasuunnassa.
    -   pitämällä hiiren oikeaa painiketta painettuna ja vetämällä
        ylös/alas karttaa siirretään pystysuunnassa.
-   kappaleiden visuaalista kokoa skaalataan voimakkaammin todellisen
    säteen perusteella.
-   BIO-, GEO-, Terraforming-, ensilöytö- ja First Mapping -merkintöjen
    esitystä on parannettu edelleen.
-   uusi **arvolista** Explorerissa: planeetat ja kuut lajitellaan
    riveittäin niiden nykyisen arvioidun kartoitusarvon mukaan.
-   arvolista erottaa nyt selvästi **First Mapping mahdollinen**, **jo
    kartoitettu** ja **itse kartoitettu**.
-   tällä hetkellä saavutettu kartoitusarvo korostetaan arvolistassa
    tarkoituksellisesti, kun taas tila- ja metatiedot esitetään
    hillitymmin.
-   uusi **"Ei vielä luovutettu"** -näyttö avoimille kartoitus- ja
    BIO-arvoille kaikissa järjestelmissä viimeisimmän myynnin jälkeen;
    kartoitus ja BIO nollataan erikseen.
-   avoimet Explorer-arvot korostetaan pääikkunassa keltaisella, jotta
    vielä myymättömät tiedot tunnistetaan heti.

### Explorer-liveikkunat

-   uudet vapaasti sijoitettavat **liveikkunat arvokkaille kappaleille
    ja BIO-löydöille**, jotka ilmestyvät automaattisesti
    tutkimusmatkailun aikana.
-   liveikkunoiden sijainti ja koko tallennetaan ja niitä käytetään
    uudelleen seuraavalla näyttökerralla.
-   toiseen tähtijärjestelmään siirryttäessä liveikkunat suljetaan ja
    tyhjennetään automaattisesti; ne ilmestyvät uudelleen vasta, kun
    uudessa järjestelmässä tunnistetaan sopivia tietoja.
-   **"Arvokkaat kappaleet"** -ikkuna ottaa automaattisesti mukaan
    kaikki planeetat ja kuut, joiden tällä hetkellä saavutettavissa
    oleva kartoitusarvo saavuttaa asetuksissa valitun raja-arvon.
-   sama säädettävä raja-arvo ohjaa nyt arvolistan keltaista korostusta,
    arvokkaiden kappaleiden liveikkunaa ja **järjestelmäkartan
    kultakehystä**.
-   **BIO-liveikkuna** näyttää pelin aikana kompaktisti kappaleet,
    tunnistetut suvut tai lajit, skannauksen etenemisen ja tunnetut
    Vista Genomics -arvot.
-   BIO-löydöt käyttävät samaa värilogiikkaa kuin pääikkunassa: harmaa =
    DSS/FSS havaittu, valkoinen = ensimmäinen näyte, keltainen = toinen
    näyte, vihreä = analyysi valmis.
-   osittain tunnistetuissa BIO-signaaleissa planeetta laajenee
    automaattisesti ja näyttää yksittäiset löydöt omilla riveillään;
    vielä tuntemattomat signaalit pysyvät näkyvissä.
-   kun kaikki kappaleen BIO-lajit on analysoitu kokonaan, planeetta
    tiivistyy takaisin kompaktiksi vihreäksi yhteenvetoriviksi.
-   yleiset DSS/FSS-sukunimet korvataan automaattisesti konkreettisella
    BIO-lajilla heti, kun se tunnetaan `ScanOrganic`-tapahtuman kautta.
-   tunnetut yksittäisarvot näytetään suoraan kyseisen BIO-löydön
    yhteydessä; täysin tunnetut kappaleet näyttävät lisäksi
    kokonaisarvon.
-   liveikkunoissa on hillitty punaruskea tausta, jotta ne erottuvat
    pelatessa selvästi CMDRHelperin pääikkunasta.

### BIO-analyysi

-   biologiset tiedot analysoidaan ja näytetään erillään tavallisista
    kartoitusarvoista.
-   oma **BIO-planeettalista**, joka sisältää kaikki kappaleet, joilla
    on havaittu biologisia signaaleja.
-   `SAASignalsFound`- tai `FSSBodySignals`-tapahtumien BIO-suvut
    tuodaan jälkikäteen myös olemassa olevista Journaleista.
-   `ScanOrganic`-tapahtuman konkreettiset BIO-lajit ja variantit
    näytetään suoraan listassa.
-   kunkin BIO-löydön skannauksen eteneminen esitetään väreillä:
    -   harmaa = tunnetaan vain DSS/FSS:n kautta
    -   valkoinen = ensimmäinen näyte
    -   keltainen = toinen näyte
    -   vihreä = kolmas näyte / analyysi valmis
-   tunnettu Vista Genomics -perusarvo näytetään heti, kun BIO-laji on
    yksiselitteisesti tunnistettu.
-   täysin analysoitujen BIO-näytteiden perusarvon näyttö.
-   mahdollisen **First Logged -kokonaisarvon ×5** näyttö.
-   tunnettuja BIO-arvoja voidaan täydentää olemassa olevista
    myyntitiedoista.
-   lajit, joille ei tunneta arvoa, merkitään analyysissä.
-   BIO-tila erottaa avoimen, vieraillun ja täysin analysoidun tilan.

### Tehtävät

-   `MissionRedirected`-tapahtuman käsittelyä on parannettu.
-   uudelleenohjatut tehtävät voivat ottaa käyttöön nimen, uuden
    kohdejärjestelmän tai uuden kohdeaseman sekä tiedot aiemmasta
    kohteesta.
-   tehtäviä voidaan tietyissä tapauksissa rekonstruoida myös silloin,
    kun täydellistä `MissionAccepted`-merkintää ei aiemmin ollut.
-   tehtäväsarakkeiden leveyttä voidaan säätää vapaasti; valitut
    leveydet tallennetaan.
-   **kaikkien tällä hetkellä avoimien tehtävien kokonaispalkkion**
    näyttö.

### Kuvat ja kuvakaappaukset

-   oma kuvakaappausalue gallerialla ja esikatselulla.
-   uusien Elite Dangerous -BMP-kuvakaappausten automaattinen muunnos.
-   tallennus PNG- tai JPG-muotoon.
-   BMP-tiedoston valinnainen poistaminen onnistuneen muunnoksen
    jälkeen.
-   säädettävä kirkkauskorjaus 0--50 %.
-   Elite-kuvakaappauskansion helpompi käyttö Steam/Protonissa.
-   galleria päivittyy myös ulkoisesti poistettujen tiedostojen jälkeen.
-   automaattisen muunnoksen ja poistamisen asetusten näkyvyyttä on
    parannettu.

### Verkkopalvelut

-   automaattinen EDSM-Journal-siirto on integroitu edelleen ja näkyy
    pääikkunan tila-alueella.
-   tilat siirrolle, odotukselle, virheelle ja käytöstä poistetulle
    EDSM:lle.
-   Inara-tilan näyttö valmisteluna myöhempää automaattista siirtoa
    varten.

### Käytettävyys ja vakaus

-   käyttöliittymän fontti ja fonttikoko voidaan valita asetuksissa ja
    ottaa käyttöön koko käyttöliittymässä uudelleenkäynnistyksen
    jälkeen.
-   asetussivua voidaan vierittää, jotta kaikki vaihtoehdot ovat
    käytettävissä myös pienemmillä ikkunako'oilla.
-   näkyvä **"Lopeta"**-painike vasemmassa sivupalkissa.
-   Single Instance -lukitus estää ohjelman toisen samanaikaisen
    käynnistymisen vahingossa.
-   turvallinen järjestelmän pienoiskuvanäkymä ilman jo näkyvän
    Explorer-widgetin suoraa renderöintiä.
-   useita parannuksia käyttöliittymään, Journal-käsittelyyn,
    tietokantaan ja päivitysprosessiin.

## Projektin tila

CMDRHelper on kehitysvaiheessa. Käyttöliittymä, tietomalli ja esitystapa
voivat vielä muuttua. Lisää kappaletyyppejä, Journal-toimintoja,
Explorer-toimintoja, tietolähteitä ja laskelmia on suunnitteilla.
Linuxia ja Windowsia testataan edelleen.

CMDRHelper syntyi henkilökohtaiseksi työkaluksi ja sitä kehitetään
vaiheittain laajemmaksi Elite Dangerous -helperiksi.

## Kuva- ja videomateriaali / Media Credits

CMDRHelper käyttää joidenkin erityisten astronomisten kohteiden
visualisointiin **NASA Scientific Visualization Studion (NASA SVS)**
materiaalia. Kyseiset mediat säilyvät oikeudenhaltijoidensa omaisuutena,
ja niiden credit-tiedot ilmoitetaan NASA SVS -sivuilla annettujen
tietojen mukaisesti.

### Neutronitähti

-   CMDRHelper-tiedosto: `star_neutron.webm`
-   Lähde: NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animaattorit: Walt Feimer (KBR Wyle Services, LLC) ja Lisa Poje
    (USRA)
-   Lähde: https://svs.gsfc.nasa.gov/20267/

### Musta aukko

-   CMDRHelper-tiedosto: `black_hole.mp4` tai projektissa käytetty
    videotiedostopääte
-   Lähde: NASA Scientific Visualization Studio, **Black Hole Accretion
    Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Lähde: https://svs.gsfc.nasa.gov/13326/

### Supermassiivinen musta aukko

-   CMDRHelper-tiedosto: `black_hole_supermassive.mp4` tai projektissa
    käytetty videotiedostopääte
-   Lähde: NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Lähde: https://svs.gsfc.nasa.gov/14576/

### Valkoinen kääpiö

-   CMDRHelper-tiedosto: `star_white_dwarf.webm`
-   käytetty NASA-media: **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Lähde: NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animaattori: Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Lähde: https://svs.gsfc.nasa.gov/20344/

Näiden lähteiden ja credit-tietojen mainitseminen ei tarkoita, että NASA
tukisi, sertifioisi tai julkaisisi CMDRHelperia. NASA-median
jatkokäytössä sovelletaan alkuperäislähteiden omia ohjeita ja
jäljentämiskäytäntöjä.

## Lisenssi

CMDRHelper on vapaa ohjelmisto ja se julkaistaan **GNU General Public
License Version 3 (GPL-3.0)** -lisenssillä.

Lähdekoodia saa käyttää, muuttaa ja jakaa edelleen GPL-3.0:n ehtojen
mukaisesti. Myös johdettujen versioiden jakelussa sovelletaan GPL-3.0:n
ehtoja.

Copyright © 2026 **Holger Mangold (Faber38)**.

Täydelliset lisenssiehdot löytyvät tiedostosta `LICENSE`.

## Huomautus Elite Dangerousista

CMDRHelper on itsenäinen community-/harrasteprojekti eikä Frontier
Developmentsin virallinen tuote.

**Elite Dangerous** sekä siihen liittyvät nimet ja sisällöt kuuluvat
niiden oikeudenhaltijoille.
