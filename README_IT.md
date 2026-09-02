# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Il tuo co-pilota per Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_it.png)

**Compagno personale per Elite Dangerous -- esplorazione, analisi dei
sistemi e dati del Commander a colpo d'occhio**

CMDRHelper è un programma desktop indipendente per **Elite Dangerous**
che analizza le informazioni contenute nei file Journal locali del gioco
e le presenta in modo chiaro. L'obiettivo è offrire un helper personale
che, durante l'esplorazione di un sistema, mostri rapidamente ciò che è
già noto, quali corpi celesti sono interessanti e quali scoperte e
mappature sono state effettuate personalmente.

Il progetto è ancora in fase di sviluppo attivo.

## Panoramica delle funzioni

### Journal di Elite Dangerous

CMDRHelper legge i file Journal locali ed elabora, tra le altre cose,
sistemi stellari, stelle, pianeti, lune, Belt Cluster, scansioni,
mappature e segnali biologici e geologici. I dati personali del
Commander rimangono distinguibili dalle informazioni supplementari
provenienti da fonti esterne.

### Missioni

CMDRHelper analizza gli eventi delle missioni presenti nei Journal di
Elite Dangerous e mostra in modo chiaro le missioni attive. Lo stato
delle missioni e i relativi eventi Journal vengono monitorati.

Anche le offerte di missione che arrivano durante il gioco tramite
messaggi NPC (`ReceiveText`) possono essere riconosciute e considerate
per la successiva assegnazione delle missioni. Poiché Elite Dangerous
non fornisce, per ogni tipo di missione, tutte le informazioni nello
stesso evento Journal, l'assegnazione viene costruita progressivamente a
partire dai dati Journal disponibili.

### Vista sistema ed Explorer

I corpi conosciuti di un sistema vengono rappresentati graficamente e
possono essere selezionati direttamente. CMDRHelper può mostrare, tra le
altre cose:

-   nome e tipo del corpo
-   distanza all'interno del sistema
-   scansionato personalmente oppure noto solo tramite fonti esterne
-   già scoperto e mappato
-   possibile prima scoperta e possibile First Mapping
-   mappato dal Commander
-   mappatura efficiente
-   segnali biologici e geologici
-   valori di scansione e mappatura

I segnali BIO vengono evidenziati chiaramente sul corpo interessato.
L'assegnazione avviene in base al sistema, in modo da non confondere i
BodyID appartenenti a sistemi stellari differenti.

### Vista dettagli del corpo

Facendo clic su un corpo si apre una vista dettagliata. A seconda dei
dati disponibili vengono mostrati tipo del corpo, massa, distanza,
gravità, atmosfera, vulcanismo, possibilità di atterraggio, stato di
terraformazione, materiali, segnali BIO/GEO, valore di scansione, valore
di mappatura e stato della scoperta.

Le informazioni mancanti vengono indicate come sconosciute e non
presentate come dati certi.

## Rappresentazione grafica dei corpi

CMDRHelper dispone di grafica dedicata per numerosi tipi di corpi, tra
cui High Metal Content Worlds, Metal Rich Bodies, Rocky Bodies, Icy
Bodies, Rocky Ice Worlds, Earth-like Worlds, Water Worlds, Ammonia
Worlds, diverse classi di giganti gassosi, giganti gassosi con vita
basata sull'acqua o sull'ammoniaca, giganti gassosi ricchi di elio,
diverse classi stellari e Belt Cluster.

Le normali immagini PNG vengono utilizzate nelle panoramiche. Per molti
corpi è inoltre disponibile una **texture equirettangolare 2:1
`_texture.png`** per la vista dettagliata animata.

### Pianeti 3D rotanti

Le texture 2:1 adatte vengono proiettate su una sfera rotante. Il
renderer CPU utilizza **PySide6 e NumPy** senza dipendenze aggiuntive da
OpenGL/PyOpenGL. Comprende proiezione sferica, rotazione lenta,
illuminazione, oscuramento del bordo e bordo atmosferico.

### Forme di vita animate

Per i giganti gassosi con forme di vita sono disponibili animazioni
differenti:

**Water Life:** organismi fluttuanti color ciano/turchese con alone e
code in movimento.

**Ammonia Life:** organismi dedicati viola/ambrati, semitrasparenti, con
nucleo pulsante, filamenti corti e movimento più lento.

### Belt Cluster animati

I Belt Cluster non vengono rappresentati come sfere. La vista
dettagliata genera un campo procedurale di asteroidi con singoli
asteroidi, dimensioni e profondità differenti, rotazione propria, deriva
individuale, effetto parallasse, crateri e discreti effetti di polvere e
particelle.

## EDSM come fonte dati supplementare

CMDRHelper può distinguere i propri dati Journal dalle informazioni
EDSM. La fonte viene contrassegnata di conseguenza come Journal
personale, EDSM oppure Journal personale + EDSM. I dati Journal
personali sono particolarmente importanti perché mostrano ciò che il
rispettivo Commander ha effettivamente scansionato o mappato in prima
persona.

CMDRHelper può trasmettere automaticamente a EDSM i nuovi dati Journal.
Viene presa in considerazione l'attuale lista dinamica EDSM Discard, in
modo che vengano inviati soltanto gli eventi richiesti da EDSM. Lo stato
di avanzamento del trasferimento viene salvato in modo sicuro per ogni
file Journal. Alla prima attivazione, i vecchi Journal già esistenti non
vengono nuovamente trasmessi per intero.

Lo stato EDSM viene visualizzato direttamente nella parte superiore
della panoramica. Un indicatore verde segnala un trasferimento
funzionante; gli errori vengono visualizzati in rosso e registrati anche
nel log di CMDRHelper.

## Database locale

CMDRHelper utilizza SQLite. Si applicano le seguenti regole:

-   `cmdrhelper/database.py` è codice del programma e fa parte della
    release.
-   `data/cmdrhelper.db` contiene dati personali del Commander e **non**
    viene distribuito.
-   In una nuova installazione, il database locale viene ricostruito per
    il rispettivo utente.

In questo modo nessun dato personale del Commander viene distribuito
insieme a una release.

## Diagnostica e file di log

CMDRHelper mantiene un proprio file di log rotante per la diagnostica e
la ricerca degli errori. Vengono registrati importanti eventi del
programma, del Journal, del database e di EDSM. Il logging EDSM è stato
ridotto in modo che i semplici eventi Journal scartati da EDSM non
riempiano inutilmente il normale log, mentre i trasferimenti riusciti,
gli avvisi e gli errori rimangono visibili.

## Piattaforme

CMDRHelper è sviluppato con Python e PySide6 ed è destinato a **Linux e
Windows**. Lo sviluppo avviene principalmente su Linux; Windows può
essere configurato tramite i file batch inclusi.

## Requisiti

Python **da 3.10 a 3.13** e i pacchetti indicati in `requirements.txt`:

``` text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

## Installazione su Linux

``` bash
./install.sh
./start.sh
```

Questi script usano esclusivamente il `venv` locale dell'installazione e
possono ripararlo con prudenza senza toccare i dati personali.

## Installazione su Windows

Per Windows sono previsti `install.bat` e `start.bat`.

`install.bat` verifica Python 3.10–3.13, crea o ripara il `venv` locale e installa
`requirements.txt`. Successivamente CMDRHelper viene avviato tramite
`start.bat`.

## Creazione di una release

``` bash
./create_release.sh
```

La versione della release viene impostata direttamente nello script. Il
file ZIP generato contiene il codice del programma e gli asset, ma non
il database personale, l'ambiente virtuale Python né file Git, cache o
file dell'editor.

## Versione 2.1

**La versione 2.1** migliora biologia, flotta e prestazioni con grandi archivi
Journal, oltre a rendere più sicuri installazione, avvio, aggiornamento e
rollback su Windows e Linux.

### Previsioni biologiche e habitat

-   quando i dati bastano, la nuova previsione mostra Species concrete e non
    solo il genere. Può proporre più Species plausibili con confidenza
    **ALTA**, **MEDIA** o **BASSA**; i campioni piccoli sono valutati con
    prudenza.
-   Species trovate o identificate sostituiscono le previsioni; quando tutti i
    segnali BIO sono noti, le previsioni residue scompaiono.
-   il popup BIO compatto mostra valori stimati dei candidati e un possibile
    totale del corpo: arancione/oro indica una stima, verde un valore noto.
    Le stime non includono bonus speculativi First Footfall.
-   temperatura, pressione, composizione atmosferica, raggio e contesto di
    stella/parent arricchiscono i dati habitat. Non è presente una previsione
    generale di varianti o colori.

### Flotta CMDR

-   la flotta si ordina, in modo crescente o decrescente, per ultimo utilizzo,
    nome, tipo, portata di salto, carico, massa a vuoto, posizione o data.
-   i filtri mostrano tutte le navi, quelle con hangar veicoli o con hangar
    fighter, riconosciuti dai moduli Loadout reali. SRV e fighter restano
    equipaggiamento della nave madre e non diventano navi separate.

### Journal, archivio e prestazioni

-   i nomi storici `Journal.YYMMDDHHMMSS.PART.log` e moderni
    `Journal.YYYY-MM-DDTHHMMSS.PART.log` sono elaborati insieme nell'ordine
    corretto, evitando che vecchi Journal sovrascrivano CMDR o stato correnti.
-   eventi Signal/Mapping incompleti possono essere importati anche senza un
    Body Scan precedente; scan successivi completano i dati e la separazione
    multi-CMDR resta invariata.
-   un indice Journal persistente salta i file noti e invariati. Il Journal
    attivo viene letto incrementalmente dall'ultima posizione byte sicura;
    metadati e SHA-256 proteggono l'identità e l'attribuzione FID resta intatta.
-   il primo indice molto grande mostra numeri reali, percentuale e piccole
    astronavi animate in una UI responsiva. Gli avvii rapidi successivi di
    norma non mostrano la schermata.

### Installazione e aggiornamento

-   gli script Windows e Linux rafforzati supportano Python 3.10–3.13, usano
    soltanto il `venv` locale e riparano con cautela un ambiente locale
    danneggiato. I symlink Linux sono gestiti in sicurezza; ambienti estranei
    non vengono usati.
-   update e rollback segnalano chiaramente i problemi e proteggono dati
    personali e Journal Elite.
-   è previsto il normale aggiornamento da v2.0 a v2.1. Per installazioni molto
    anteriori a v2.0, salvare le impostazioni; in caso di problemi può aiutare
    un'installazione pulita. Non eliminare mai i Journal Elite né, come rimedio
    generico, i vecchi dati di CMDRHelper.
-   con archivi enormi, il primo avvio v2.1 può richiedere tempo una sola volta
    per l'indice; gli avvii successivi sono molto più rapidi.

## Versione 2.0

La **versione 2.0** introduce un vero supporto Multi-CMDR, mantenendo il
route planner della versione 1.5 e tutte le funzioni già disponibili.

### Multi-CMDR e Vista CMDR

-   i Commander vengono identificati automaticamente tramite il FID Frontier.
    Solo il Journal determina il Commander live; la scelta di un altro
    profilo da visualizzare non modifica attribuzione o scritture live.
-   visite, esplorazione, missioni, posizioni, navi, Fleet Carrier, patrimonio
    e dati biologici e cartografici invenduti restano separati per Commander.
-   la **Vista CMDR** mostra offline ogni Commander noto: missioni, ultima
    posizione e nave, Fleet Carrier con posizione, patrimonio e stime dei dati
    biologici e cartografici ancora da vendere.

### Cronaca Multi-CMDR

-   ogni Commander ha un colore stabile e filtri singoli o comuni.
-   le rotte cronologiche restano separate e non collegano mai salti di
    Commander differenti.
-   i sistemi visitati da più Commander mostrano visite multiple.

### Flotte dei Commander

-   ogni Commander dispone di una flotta persistente con tutte le navi note e
    dettagli espandibili su loadout, autonomia, serbatoi, carico e posizione.
-   la nave live è verde; le altre ricevono colori stabili in base all’ultima
    posizione e l’elenco ha lo scorrimento verticale.
-   tute, SRV Scarab, Scorpion e Nomad, caccia imbarcati, taxi e dropship non
    vengono registrati come normali navi del Commander.

### Database esistenti

Le migrazioni integrate continuano a usare i database esistenti. I dati
Multi-CMDR sono separati tramite FID Frontier. Se vecchi dati possono
appartenere a più profili, CMDRHelper non indovina e non li elimina in blocco:
un’attribuzione ambigua rimane irrisolta.

CMDRHelper continua a supportare **Linux e Windows** e include il route planner
per navi e Fleet Carrier della versione 1.5.

## Versione 1.5

La **versione 1.5** è un importante aggiornamento funzionale. Introduce il
nuovo pianificatore di rotta per navi e Fleet Carrier, collega più
strettamente l’avanzamento al Journal di Elite Dangerous e migliora
affidabilità e prestazioni, soprattutto in Windows.

### Pianificatore e rotte delle navi

-   il nuovo **Pianificatore di rotta** calcola rotte navali con Spansh
    Galaxy Plotter e mostra tutti i sistemi intermedi in CMDRHelper.
-   CMDRHelper rileva dal Journal nave, FSD, engineering dell’FSD e Guardian
    FSD Booster attivo. I valori disponibili di serbatoio, carico, massa e
    FSD vengono acquisiti automaticamente.
-   i valori rilevati restano modificabili. Le sostituzioni manuali vengono
    conservate durante i successivi aggiornamenti di Loadout, carico e
    carburante, finché non si riapplicano esplicitamente i dati della nave.
-   le modifiche a Loadout, carico e carburante aggiornano solo gli input
    interessati. I valori sconosciuti restano visibilmente vuoti e non
    vengono stimati.
-   prima del calcolo, partenza e destinazione vengono verificate con una
    corrispondenza Spansh esatta; i sistemi sconosciuti producono un messaggio
    comprensibile senza avviare un job destinato a fallire.
-   l’avanzamento usa i veri eventi `FSDJump` del flusso Journal esistente.
    Dopo un salto riuscito, il sistema successivo viene copiato
    automaticamente negli appunti Qt e può essere ricopiato manualmente.

### Fleet Carrier e CTSVision

-   una modalità dedicata **Fleet Carrier / CTSVision** utilizza Spansh Fleet
    Carrier Router.
-   le rotte Fleet Carrier includono dati sui salti e sul Tritium e possono
    essere esportate in un CSV compatibile con CTSVision.

### Affidabilità del Journal e prestazioni

-   un errore temporaneo di accesso al Journal attivo non conferma più
    prematuramente l’aggiornamento: il normale polling riprova senza un ciclo
    di attesa aggressivo.
-   l’apprendimento BIO e cartografico non riesamina più l’intero archivio
    per normali eventi non pertinenti. Le analisi complete sono limitate agli
    eventi BIO o di vendita rilevanti e all’importazione prevista.
-   si riduce così il lavoro inutile a ogni aggiunta al Journal, migliorando
    affidabilità e reattività, in particolare su Windows.

## Versione 1.0.8

La **versione 1.0.8** aggiunge una raccomandazione di salto personale per
l’esplorazione, completa l’internazionalizzazione e migliora le finestre
live dell’Esploratore e la visualizzazione della mappa della Cronaca.

### Suggerimento e raccomandazione di salto

-   la nuova sezione **«Suggerimento di salto»** analizza il proprio database
    di esplorazione locale e mostra quali codici di sistemi procedurali
    possono essere particolarmente interessanti per l’obiettivo scelto.
-   gli obiettivi disponibili comprendono ritrovamenti BIO in generale,
    generi e specie BIO noti, corpi di esplorazione di valore, candidati alla
    terraformazione, mondi d’acqua, mondi simili alla Terra e mondi ad
    ammoniaca.
-   la classifica considera i sistemi già esaminati con un codice, i
    risultati, il tasso di successo, i ritrovamenti salvati e la dimensione
    del campione disponibile. Un numero minimo regolabile di sistemi
    esaminati evita di sopravvalutare campioni troppo piccoli.
-   CMDRHelper evidenzia i codici da preferire sulla mappa galattica, per
    esempio combinazioni come `ZL-Z b` o `NR-C d`.
-   la raccomandazione si basa esclusivamente sulla **propria cronologia di
    esplorazione** e sui ritrovamenti in essa salvati. È un’indicazione
    statistica e **non garantisce alcun ritrovamento**.

### Internazionalizzazione

-   l’internazionalizzazione è stata ulteriormente completata e verificata
    di nuovo rispetto al riferimento tedesco.
-   tutte le **12 lingue dell’interfaccia supportate** dispongono ora dello
    stesso insieme completo di **560 chiavi di traduzione**.
-   in tutte le lingue sono state aggiunte le traduzioni nuove e finora
    mancanti per il **suggerimento e la raccomandazione di salto**.
-   insieme e ordine delle chiavi e segnaposto di formattazione sono stati
    uniformati in tutti i file di lingua.

### Finestre live e impostazioni dell’Esploratore

-   le impostazioni dell’Esploratore includono nuovi tooltip esplicativi per
    la visualizzazione automatica delle finestre **«Corpi di valore»** e
    **«Ritrovamenti BIO»**.
-   i tooltip spiegano quando ogni finestra appare automaticamente in base
    alla soglia di valore configurata o ai segnali BIO o GEO rilevati.
-   i corpi di valore già cartografati dal Commander non vengono più
    mostrati come obiettivi aperti nella piccola finestra live.
-   i corpi BIO completamente analizzati scompaiono dalla finestra BIO; una
    componente GEO dello stesso corpo non ancora cartografata con il DSS
    rimane visibile.

### Cronaca

-   l’orientamento della mappa della Cronaca è stato corretto affinché l’asse
    Z positivo punti verso l’alto. Le coordinate Elite `StarPos` salvate
    rimangono invariate.

## Versione 1.0

Con la **Versione 1.0**, CMDRHelper raggiunge il primo stato di sviluppo
completo dell'ambito di base pianificato.

Principali modifiche ed estensioni fino alla Versione 1.0:

### Rappresentazione di corpi e stelle completata

-   il materiale grafico per i tipi supportati di pianeti, stelle e
    oggetti speciali è stato ulteriormente completato.
-   ulteriori classi stellari e tipi speciali di stelle vengono
    rappresentati con grafica dedicata invece di ricadere sulla
    rappresentazione standard generale.
-   per i corpi adatti continuano a essere disponibili texture
    equirettangolari 2:1 rotanti nella vista dettagliata.
-   gli oggetti astronomici speciali possono inoltre essere
    rappresentati nella vista dettagliata tramite video appropriati.
-   stelle di neutroni, nane bianche, buchi neri e buchi neri
    supermassicci ricevono così una rappresentazione molto più
    individuale.
-   il materiale grafico e video esterno utilizzato viene documentato
    con fonte e credit nella sezione **«Materiale grafico e video /
    Media Credits»**.

### Multilingua completato

-   le traduzioni dell'interfaccia utente sono state completate per le
    lingue supportate e allineate a un insieme comune di chiavi.
-   tutte le **12 lingue dell'interfaccia** utilizzano lo stesso insieme
    completo di chiavi di traduzione.
-   il controllo automatico delle traduzioni verifica chiavi mancanti,
    aggiuntive e duplicate, nonché placeholder di formattazione
    differenti.
-   il tedesco funge da riferimento completamente mantenuto per
    l'interfaccia utente e per la documentazione futura.

### Modifiche dalla Versione 0.9.9

### Multilingua e controllo delle traduzioni

-   l'interfaccia utente è stata convertita a un sistema multilingua
    centralizzato.
-   CMDRHelper supporta ora **12 lingue dell'interfaccia**: **tedesco,
    inglese, francese, italiano, norvegese (Bokmål), svedese,
    finlandese, polacco, olandese, spagnolo, turco e greco**.
-   la lingua può essere selezionata e salvata nelle impostazioni; i
    nomi delle lingue vengono visualizzati nel campo di selezione
    ciascuno nella propria lingua.
-   le traduzioni mancanti utilizzano una sequenza di fallback definita:
    **lingua selezionata → inglese → tedesco → chiave di traduzione**.
-   le traduzioni sono memorizzate centralmente nei file di lingua sotto
    `cmdrhelper/i18n/`.
-   il nuovo strumento per sviluppatori `tools/check_i18n.py` verifica
    automaticamente:
    -   le chiavi `tr("...")` utilizzate nel programma,
    -   le chiavi di traduzione mancanti o aggiuntive,
    -   le chiavi duplicate,
    -   placeholder di formattazione differenti come `{system}` o
        `{count}`.
-   su Linux il controllo i18n viene eseguito automaticamente all'avvio
    tramite `start.sh`. I problemi di traduzione rilevati vengono
    segnalati chiaramente, ma non impediscono l'avvio del programma.
-   l'elaborazione delle missioni e del Journal rimane separata dalla
    lingua dell'interfaccia CMDRHelper selezionata, affinché i dati
    interni di Elite Dangerous non dipendano dai testi localizzati
    visualizzati.

### Explorer e mappa del sistema

-   rielaborata la struttura Parent/Child della mappa del sistema:
    stelle, pianeti, lune e Belt Cluster vengono disposti secondo la
    loro gerarchia nel Journal.
-   nuova funzione **«Mostra tutto»** con una panoramica miniaturizzata
    e compatta dell'intero sistema.
-   i corpi possono essere selezionati nella panoramica miniaturizzata;
    la mappa principale passa quindi direttamente al corpo scelto.
-   navigazione migliorata nelle mappe di sistemi di grandi dimensioni:
    -   la rotella del mouse sposta la mappa orizzontalmente.
    -   tenendo premuto il pulsante destro del mouse e trascinando verso
        l'alto/il basso, la mappa viene spostata verticalmente.
-   le dimensioni visive dei corpi vengono scalate maggiormente in base
    al raggio reale.
-   ulteriormente migliorate la rappresentazione e la marcatura di BIO,
    GEO, Terraforming, prima scoperta e First Mapping.
-   nuova **lista dei valori** nell'Explorer: pianeti e lune vengono
    ordinati riga per riga in base al loro valore di mappatura stimato
    attuale.
-   la lista dei valori distingue ora chiaramente tra **First Mapping
    possibile**, **già mappato** e **mappato personalmente**.
-   il valore di mappatura attualmente ottenuto viene evidenziato in
    modo mirato nella lista dei valori, mentre stato e metadati vengono
    volutamente visualizzati in modo più discreto.
-   nuova indicazione **«Non ancora consegnato»** per i valori di
    cartografia e BIO ancora aperti in tutti i sistemi dall'ultima
    vendita; cartografia e BIO vengono azzerati separatamente.
-   i valori Explorer ancora aperti vengono evidenziati in giallo nella
    finestra principale, in modo che i dati non ancora venduti siano
    immediatamente riconoscibili.

### Finestre live dell'Explorer

-   nuove **finestre live liberamente posizionabili per corpi preziosi e
    ritrovamenti BIO**, che compaiono automaticamente durante
    l'esplorazione.
-   posizione e dimensioni delle finestre live vengono salvate e
    riutilizzate alla successiva comparsa.
-   passando a un altro sistema stellare, le finestre live vengono
    automaticamente chiuse e svuotate; ricompaiono solo quando nel nuovo
    sistema vengono rilevati dati appropriati.
-   la finestra **«Corpi preziosi»** include automaticamente tutti i
    pianeti e le lune il cui valore di mappatura attualmente ottenibile
    raggiunge la soglia scelta nelle impostazioni.
-   la stessa soglia configurabile controlla ora l'evidenziazione gialla
    della lista dei valori, la finestra live dei corpi preziosi e la
    **cornice dorata nella mappa del sistema**.
-   la **finestra live BIO** mostra in modo compatto durante il gioco i
    corpi, i generi o le specie riconosciuti, il progresso della
    scansione e i valori Vista Genomics noti.
-   i ritrovamenti BIO utilizzano la stessa logica cromatica della
    finestra principale: grigio = rilevato tramite DSS/FSS, bianco =
    primo campione, giallo = secondo campione, verde = analisi completa.
-   in presenza di segnali BIO parzialmente determinati, un pianeta si
    espande automaticamente mostrando i singoli ritrovamenti in righe
    separate; i segnali ancora sconosciuti rimangono visibili.
-   non appena tutte le specie BIO di un corpo sono state analizzate
    completamente, il pianeta viene nuovamente compresso in una riga
    riassuntiva verde.
-   i nomi generici dei generi DSS/FSS vengono automaticamente
    sostituiti dalla specie BIO concreta non appena questa viene
    identificata tramite `ScanOrganic`.
-   i singoli valori noti vengono mostrati direttamente accanto al
    rispettivo ritrovamento BIO; i corpi completamente conosciuti
    mostrano inoltre il valore totale.
-   le finestre live hanno uno sfondo discretamente rosso-bruno, in modo
    da distinguersi chiaramente dalla finestra principale di CMDRHelper
    durante il gioco.

### Analisi BIO

-   i dati biologici vengono analizzati e visualizzati separatamente dai
    normali valori di cartografia.
-   lista dedicata **dei pianeti BIO** con tutti i corpi sui quali sono
    stati rilevati segnali biologici.
-   i generi BIO provenienti da `SAASignalsFound` o `FSSBodySignals`
    vengono importati retroattivamente anche dai Journal esistenti.
-   le specie e le varianti BIO concrete provenienti da `ScanOrganic`
    vengono mostrate direttamente nella lista.
-   il progresso della scansione per ogni ritrovamento BIO viene
    rappresentato tramite colori:
    -   grigio = noto soltanto tramite DSS/FSS
    -   bianco = primo campione
    -   giallo = secondo campione
    -   verde = terzo campione / analisi completa
-   il valore base Vista Genomics noto viene mostrato non appena una
    specie BIO è stata identificata in modo univoco.
-   visualizzazione del valore base dei campioni BIO completamente
    analizzati.
-   visualizzazione del possibile **valore totale First Logged ×5**.
-   i valori BIO noti possono essere integrati utilizzando dati di
    vendita già disponibili.
-   le specie senza valore noto vengono contrassegnate nell'analisi.
-   lo stato BIO distingue tra aperto, visitato e completamente
    analizzato.

### Missioni

-   migliorata l'elaborazione di `MissionRedirected`.
-   le missioni reindirizzate possono acquisire nome, nuovo sistema di
    destinazione o nuova stazione di destinazione e informazioni sulla
    destinazione precedente.
-   in determinati casi le missioni possono essere ricostruite anche se
    in precedenza non era presente una voce `MissionAccepted` completa.
-   la larghezza delle colonne delle missioni può essere regolata
    liberamente; le larghezze selezionate vengono salvate.
-   visualizzazione della **ricompensa totale di tutte le missioni
    attualmente aperte**.

### Immagini e screenshot

-   area screenshot dedicata con galleria e anteprima.
-   conversione automatica dei nuovi screenshot BMP di Elite Dangerous.
-   output in formato PNG o JPG.
-   eliminazione opzionale del file BMP dopo una conversione riuscita.
-   correzione della luminosità configurabile dallo 0 al 50%.
-   utilizzo più comodo della cartella screenshot di Elite tramite
    Steam/Proton.
-   la galleria viene aggiornata anche dopo l'eliminazione esterna dei
    file.
-   migliorata la visibilità delle opzioni per la conversione automatica
    e l'eliminazione.

### Servizi online

-   il trasferimento automatico dei Journal a EDSM è ulteriormente
    integrato e visibile tramite l'area di stato nella finestra
    principale.
-   stato per trasferimento, attesa, errore ed EDSM disattivato.
-   indicatore di stato Inara come preparazione per il futuro
    trasferimento automatico.

### Utilizzo e stabilità

-   il tipo di carattere e la dimensione del carattere dell'interfaccia
    possono essere selezionati nelle impostazioni e applicati all'intera
    interfaccia dopo un riavvio.
-   la pagina delle impostazioni è scorrevole, in modo che tutte le
    opzioni rimangano accessibili anche con finestre di dimensioni
    ridotte.
-   pulsante **«Esci»** visibile nella barra laterale sinistra.
-   il blocco Single Instance impedisce l'avvio accidentale di una
    seconda istanza simultanea del programma.
-   panoramica miniaturizzata sicura del sistema senza rendering diretto
    del widget Explorer già visibile.
-   diversi miglioramenti all'interfaccia, all'elaborazione del Journal,
    al database e al processo di aggiornamento.

## Stato del progetto

CMDRHelper è in fase di sviluppo. Interfaccia utente, modello dei dati e
rappresentazione possono ancora cambiare. Sono previsti ulteriori tipi
di corpi, funzioni Journal, funzioni Explorer, fonti dati e calcoli.
Linux e Windows continueranno a essere testati.

CMDRHelper è nato come strumento personale e viene progressivamente
sviluppato in un helper più completo per Elite Dangerous.

## Materiale grafico e video / Media Credits

CMDRHelper utilizza, per alcuni oggetti astronomici speciali,
visualizzazioni del **NASA Scientific Visualization Studio (NASA SVS)**.
I rispettivi media rimangono proprietà dei loro titolari dei diritti e
vengono citati secondo i credit indicati nelle pagine NASA SVS.

### Stella di neutroni

-   File CMDRHelper: `star_neutron.webm`
-   Fonte: NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatori: Walt Feimer (KBR Wyle Services, LLC) e Lisa Poje (USRA)
-   Fonte: https://svs.gsfc.nasa.gov/20267/

### Buco nero

-   File CMDRHelper: `black_hole.mp4` oppure l'estensione video
    utilizzata nel progetto
-   Fonte: NASA Scientific Visualization Studio, **Black Hole Accretion
    Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Fonte: https://svs.gsfc.nasa.gov/13326/

### Buco nero supermassiccio

-   File CMDRHelper: `black_hole_supermassive.mp4` oppure l'estensione
    video utilizzata nel progetto
-   Fonte: NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Fonte: https://svs.gsfc.nasa.gov/14576/

### Nana bianca

-   File CMDRHelper: `star_white_dwarf.webm`
-   Media NASA utilizzato: **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Fonte: NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animatrice: Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Fonte: https://svs.gsfc.nasa.gov/20344/

La citazione di queste fonti e dei relativi credit non significa che
CMDRHelper sia supportato, certificato o pubblicato dalla NASA. Per il
riutilizzo dei media NASA si applicano le rispettive indicazioni e linee
guida di riproduzione delle fonti originali.

## Licenza

CMDRHelper è software libero ed è pubblicato sotto la **GNU General
Public License Version 3 (GPL-3.0)**.

Il codice sorgente può essere utilizzato, modificato e ridistribuito
secondo le condizioni della GPL-3.0. Anche la distribuzione di versioni
derivate è soggetta alle condizioni della GPL-3.0.

Copyright © 2026 **Holger Mangold (Faber38)**.

Le condizioni complete della licenza sono disponibili nel file
`LICENSE`.

## Nota su Elite Dangerous

CMDRHelper è un progetto community/hobby indipendente e non è un
prodotto ufficiale di Frontier Developments.

**Elite Dangerous** e i relativi nomi e contenuti sono proprietà dei
rispettivi titolari dei diritti.
