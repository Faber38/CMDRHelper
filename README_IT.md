# CMDRHelper V3 (3.0)

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Il tuo co-pilota per Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_it.png)

**Compagno personale per Elite Dangerous – esplorazione, navigazione e dati del comandante a colpo d’occhio**

CMDRHelper è un’applicazione desktop autonoma che analizza i journal locali di Elite Dangerous e utilizza i dati di posizione planetaria di `Status.json`. Ti aiuta a individuare corpi interessanti, ritrovare luoghi salvati e consultare viaggi e scoperte. I dati personali persistono dopo il riavvio e sono separati per comandante.

## Explorer

L’Explorer presenta il sistema attuale in tre viste:

- **Mappa del sistema:** rappresentazione grafica di stelle, pianeti e lune conosciuti. Un clic su un corpo apre i dettagli. «Mostra tutto» apre la panoramica del sistema.
- **Elenco dei valori:** valori di scansione e cartografia dei corpi conosciuti, valore già ottenuto e potenziale totale. Gli indicatori aiutano a riconoscere candidati alla terraformazione, possibili prime scoperte e prime mappature.
- **BIO / GEO / ESTRAZIONE:** segnali biologici e geologici, siti di estrazione planetari e ritrovamenti personali comprovati.

Le analisi distinguono i segnali segnalati dai ritrovamenti personali effettivi. **BIO ×N** è il numero di segnali segnalati, non la conferma di specie completamente analizzate. **ESTRAZIONE ×N** conta i siti di estrazione planetari senza rivelarne le singole risorse. Le merci estratte personalmente, i materiali secondari raccolti durante l’estrazione e la composizione generale dei materiali di un corpo restano distinti.

L’Explorer mostra anche stime dei valori BIO, progresso delle analisi personali e dati cartografici e BIO non ancora venduti. I valori si basano sulle informazioni disponibili dei journal e dei corpi; i dati mancanti non vengono presentati come scoperte personali. I dati EDSM aggiuntivi sono informazioni esterne da distinguere dai ritrovamenti personali.

I dettagli dei corpi includono proprietà fisiche disponibili, atmosfera, anelli, materiali e informazioni sulle scoperte. Le rappresentazioni utilizzano texture adeguate e animazioni per alcuni oggetti astronomici particolari. L’area Cargo mostra carico e capacità conosciuti della nave o dell’SRV attualmente utilizzati; per il Rhino, carico e ritrovamenti minerari personali restano dati diversi.

In alto nell’Explorer si trovano **★ Preferiti | Navigazione planetaria | Mostra tutto**. Preferiti e navigazione planetaria aprono finestre proprie; le tre viste dell’Explorer restano disponibili.

## Navigazione planetaria

Il navigatore planetario serve esclusivamente a raggiungere una precisa **latitudine/longitudine su un pianeta o una luna**. Per viaggiare tra sistemi stellari è disponibile il pianificatore di rotte separato.

### Inserire una destinazione e partire

Seleziona il corpo di destinazione oppure usa quello attuale, riconosciuto automaticamente quando possibile. Inserisci latitudine e longitudine e, facoltativamente, un nome. Non devi inserire dati tecnici come BodyID o SystemAddress. Anche **0,0** è una coordinata valida.

Non appena Elite fornisce dati di posizione planetaria validi per il corpo corrispondente, la bussola si attiva automaticamente. Senza dati corrispondenti il navigatore mostra uno stato di attesa. Puoi impostare in qualsiasi momento nuove coordinate di destinazione sullo stesso corpo; sostituiscono la destinazione precedente.

### Visualizzazione durante l’avvicinamento

| Distanza dalla destinazione | Visualizzazione |
| --- | --- |
| **Oltre 380 km** | Globo planetario con la propria posizione come cerchio bianco e la destinazione come piccolo punto. La destinazione è arancione sul lato visibile e rossa sul lato nascosto. La posizione del giocatore resta fissa nella rappresentazione; pianeta e destinazione sono mostrati rispetto a essa. |
| **Fino a 380 km inclusi** | Passaggio automatico a una griglia prospettica inclinata con **intervalli di distanza di 50 km** e la destinazione tracciata al suo interno per proseguire l’avvicinamento. |

La finestra del navigatore è liberamente ridimensionabile. Globo o griglia prospettica si adattano proporzionalmente allo spazio disponibile; i valori dettagliati restano leggibili.

### Comprendere i valori di navigazione

- **Coordinate della destinazione:** latitudine e longitudine salvate della destinazione.
- **Coordinate attuali:** l’ultima propria posizione planetaria valida.
- **Distanza dalla destinazione / Distanza sulla superficie:** distanza calcolata verso la destinazione sulla superficie sferica; il valore grande e quello dettagliato indicano la stessa distanza con arrotondamenti diversi.
- **Rilevamento:** direzione assoluta dalla posizione attuale alla destinazione.
- **Heading:** l’orientamento attuale segnalato da Elite.
- **Direzione relativa:** differenza tra heading e rilevamento, ad esempio «23° a destra», «a sinistra» o «dritto».
- **Rotta obiettivo:** rotta assoluta verso cui puoi virare nell’HUD di Elite. Corrisponde al rilevamento e non è un ulteriore angolo di rotazione relativo.

Esempio: **Heading 051° → Rotta obiettivo 074° = 23° a destra**.

La navigazione dipende dai dati di stato del gioco; gli aggiornamenti possono arrivare in ritardo secondo lo stato del gioco. La distanza sulla superficie non è un percorso stradale o adattato al terreno. Ostacoli e quote del terreno lungo il tragitto non vengono considerati.

## HUD di navigazione

A sinistra, sotto **mostra automaticamente → HUD di navigazione**, puoi attivare una visualizzazione aggiuntiva facoltativa direttamente sopra Elite. Quando la navigazione planetaria è valida, mostra:

- direzione relativa,
- rotta obiettivo assoluta,
- distanza.

L’HUD è trasparente, lascia passare i clic e non prende il focus: non sottrae al gioco né clic del mouse né focus di input. Senza navigazione valida diventa automaticamente invisibile; la casella laterale può restare selezionata. Il navigatore normale funziona indipendentemente dall’HUD.

L’HUD è stato provato in gioco su **Linux/X11** e su **Windows 11 con Elite**. Su Windows, l’associazione fra più monitor usa la loro geometria e la posizione della finestra Elite, non la corrispondenza dei nomi dei monitor.

## Preferiti

**Explorer → ★ Preferiti** apre una finestra separata e riutilizzabile. I preferiti appartengono al **comandante attivo**. Cambiare comandante aggiorna la vista; la selezione dei comandanti nella cronaca non estende l’elenco dei preferiti.

### Salvare tre tipi

La barra delle azioni superiore offre:

| Azione | Preferito salvato |
| --- | --- |
| **★ Salva il sistema attuale** | Il sistema attuale, senza coordinate di superficie. |
| **★ Salva pianeta / luna** | Un pianeta o una luna conosciuti selezionati nel sistema attuale, senza coordinate di superficie. |
| **★ Salva la posizione attuale** | Un luogo in superficie con sistema, corpo, latitudine e longitudine attuali. |

Il pulsante della posizione resta sempre visibile ed è disponibile solo con dati di posizione planetaria attuali validi e un comandante attivo. **Il clic fissa comandante, sistema, corpo e coordinate prima dell’apertura del dialogo di modifica.** I successivi movimenti nel gioco non cambiano questa posizione. Lo stesso percorso di salvataggio è disponibile nel navigatore planetario. Gli ID interni conosciuti vengono acquisiti automaticamente; nessuna coordinata viene inventata.

Scegli un nome ed esattamente una categoria: **Bio, Geo, Estrazione, Panorama, Sito di atterraggio, Interessante o Altro**. Nota e immagine sono facoltative.

### Trovare, visualizzare e modificare

L’elenco scorrevole, ordinato alfabeticamente per nome, mostra nome, tipo, sistema, corpo e coordinate se pertinenti, categoria e piccola anteprima dell’immagine. **Ricerca a testo libero e filtri per tipo e categoria** sono combinabili. La ricerca considera nome, sistema, corpo e nota.

**Apri / Mostra** mostra dati salvati, nota e anteprima più grande. **Mostra nell’Explorer** usa la panoramica del sistema o i dettagli del corpo esistenti se il preferito appartiene al sistema attuale dell’Explorer e sono disponibili dati corrispondenti. Per gli altri sistemi restano disponibili le informazioni salvate del preferito.

**Modifica** cambia nome, categoria, nota e immagine. Sistema, corpo e coordinate salvate non vengono sostituiti dai valori in tempo reale. Per un’altra posizione crea un nuovo preferito di superficie.

**Elimina** richiede conferma e rimuove esclusivamente il record del preferito e la sua copia interna dell’immagine. I dati dell’Explorer, dei journal e dei corpi vengono conservati.

### Immagini dei preferiti e ultimo screenshot

Le immagini dei preferiti sono **completamente separate dalla normale sezione Immagini**. CMDRHelper gestisce una propria copia interna nella cartella delle immagini dei preferiti (`data/favorites/images/` nella disposizione standard dei dati). L’originale non viene né spostato né modificato.

- **Scegli immagine …** accetta PNG, JPEG o WebP e mostra un’anteprima. La copia interna nasce soltanto al salvataggio.
- **Usa l’ultimo screenshot** rilegge a ogni clic la cartella sorgente effettiva degli screenshot. Considera anche gli screenshot Elite convertiti corrispondenti nella cartella del comandante attivo all’interno della destinazione di conversione configurata. Così un nuovo screenshot resta disponibile se la conversione automatica ha già eliminato il suo BMP.
- Vengono proposti file leggibili con nomi Elite o di conversione corrispondenti, non immagini arbitrarie da cartelle generiche. L’ordine usa un’ora di acquisizione univoca nel nome del file, altrimenti la data del file. Per le immagini convertite si usa l’ora di acquisizione salvata nel nome, non quella della conversione.
- Prima di accettare uno screenshot trovato, vedi nome del file, data e ora di acquisizione e un’anteprima appena caricata. Conferma con **Usa questa immagine**. Se non viene trovato uno screenshot adatto, resta disponibile la scelta manuale. CMDRHelper non scatta screenshot autonomamente.

Un’immagine può essere sostituita o rimossa successivamente. Le copie interne non più necessarie vengono eliminate al salvataggio o all’eliminazione del preferito. **Le azioni sui preferiti non eliminano mai lo screenshot originale o un’immagine originale selezionata.** Se manca un file immagine interno, il preferito resta utilizzabile senza anteprima.

### Preferito di superficie come destinazione

**▶ Vai alla destinazione** passa corpo, latitudine, longitudine e nome del preferito salvati al navigatore planetario esistente e ne sostituisce la destinazione precedente. I preferiti non hanno logica di navigazione propria. Dati planetari validi e corrispondenti avviano la navigazione; altrimenti il navigatore attende come sempre.

I preferiti di altri comandanti non possono diventare destinazioni personali. Cambiare comandante termina una destinazione ancora gestita come preferito del comandante precedente. I preferiti di sistema e corpo mostrano informazioni esistenti, senza una propria pianificazione delle rotte.

## Cronaca

La cronaca conserva la tua storia di viaggi e ritrovamenti. La sua **mappa di viaggio 3D** mostra sistemi visitati e rotte dei comandanti. I dettagli di sistemi e corpi aiutano a ritrovare informazioni note su BIO, GEO, materiali, Codex ed estrazione.

### Filtri combinati

**Applica** o **Invio nel campo di testo libero** esegue insieme tutti i filtri impostati:

- testo libero,
- facoltativamente **Dal** e **Al**,
- **Siti minerari planetari** e **Almeno**,
- **Le mie scoperte minerarie** e **Merce**.

Un termine da **Guida alla ricerca / Legenda** viene inserito nel campo di ricerca ed eseguito insieme ai filtri di periodo ed estrazione già impostati.

### Periodo in UTC

Da e A si attivano ciascuno con la propria casella. È possibile una sola soglia; senza casella attiva non esiste una restrizione temporale da quel lato. **Da** include l’inizio del giorno di calendario UTC selezionato. **A** comprende l’intero giorno UTC selezionato. UTC è la base temporale comune, non la tua ora di calendario locale.

Contano le **visite effettive ai sistemi**: almeno una visita salvata deve ricadere nel periodo. Il semplice primo o ultimo momento in cui un sistema diventa noto non sostituisce una visita. Con un periodo attivo, numero di visite, prima e ultima visita nella mappa si riferiscono alle visite filtrate.

Il periodo filtra visite, non singoli eventi di scoperta, BIO, GEO o estrazione. Le informazioni note sui ritrovamenti e le quantità minerarie personali restano **totali** salvati. **«Rame 56 t» con un periodo attivo non significa automaticamente «56 t in questo periodo».** Se Da è successivo ad A, appare un errore e non parte alcuna interrogazione al database.

### Comandante e aggiornamento

La **selezione dei comandanti della mappa** determina le rotte visualizzate. Le ricerche personali di testo libero ed estrazione si riferiscono invece al comandante visualizzato o attivo. Le caselle della mappa non estendono automaticamente le ricerche personali a più comandanti.

**Aggiorna cronaca** ricarica i dati e riesegue i filtri attivi. **Posizione attuale** applica prima lo stato attuale dei filtri e centra il sistema attuale solo se è presente nella mappa risultante. Altrimenti appare un messaggio; i filtri restano attivi.

**Reimposta** svuota il testo libero, disattiva Da/A e ripristina i campi data visibili. Le caselle di estrazione vengono deselezionate, il numero minimo diventa 0 e la merce diventa Tutte. La selezione dei comandanti resta invariata; viene poi caricata la cronaca normale.

Con **nessun risultato**, mappa e rotte vengono svuotate, l’elenco dei risultati svuotato e nascosto, i dettagli ripristinati e un’eventuale finestra aperta dei dettagli di sistema della cronaca chiusa. I vecchi risultati non restano visibili.

### Controllare la mappa

- Trascinare con il pulsante sinistro: ruotare.
- Trascinare con il pulsante destro: spostare.
- Trascinare con il pulsante centrale: disegnare un riquadro di zoom.
- Rotella: zoom.
- **Allinea:** ripristina l’orientamento alla vista galattica dall’alto; spostamento e zoom vengono conservati.

## Immagini e conversione automatica degli screenshot

Nella sezione **Immagini** imposti la cartella sorgente degli screenshot Elite e la destinazione di conversione. La conversione automatica trasforma i nuovi screenshot BMP in **PNG o JPEG**. È disponibile una schiaritura regolabile. I BMP già presenti all’avvio non vengono convertiti retroattivamente solo attivando il monitoraggio; per loro è disponibile la conversione manuale.

I file convertiti includono nel nome ora di acquisizione, comandante e sistema e vengono archiviati per comandante. L’assegnazione automatica segue il comandante del journal attivo. Una diversa selezione nella galleria non cambia questo comandante attivo.

L’opzione di **eliminare il BMP originale dopo una conversione riuscita** appartiene esclusivamente a questa conversione e ha un’impostazione propria. È indipendente dalla gestione delle immagini dei preferiti.

La galleria mostra le immagini convertite corrispondenti con anteprima. Viene riletta quando viene mostrata di nuovo; anche l’aggiornamento considera i file attuali. Selezione e anteprima grande vengono aggiornate insieme. Se l’immagine selezionata scompare, ne viene selezionata una ancora presente oppure l’anteprima viene svuotata. La sezione Immagini ha inoltre una propria selezione di immagini e una funzione di eliminazione con conferma.

## Altre viste

- **Panoramica:** comandante attivo, nave, posizione, rilevamento del journal, missioni aperte e stato online.
- **Missioni:** missioni aperte salvate in modo persistente, con destinazioni note, progresso e stato di completamento. I dati mancanti non vengono integrati o inventati.
- **CMDR:** patrimonio, ranghi, statistiche, MercCoins, navi/flotta e posizione nota del Fleet Carrier. I MercCoins sono mostrati come totali segnalati da Frontier, non come saldo calcolato autonomamente.
- **Pianificatore di rotte:** pianificazione separata per nave e Fleet Carrier con Spansh. Le rotte carrier calcolate si possono esportare in CSV per CTSVision. Il calcolo richiede la connessione al servizio esterno.

## Comandante, dati locali e servizi online

CMDRHelper riconosce il comandante attivo dall’ID Frontier della sessione journal attuale. Esplorazione personale, missioni, patrimonio, preferiti e credenziali online sono memorizzati separatamente. Visualizzare un altro comandante non cambia né il comandante in tempo reale né l’assegnazione dei suoi caricamenti.

Il database SQLite locale conserva sistemi, corpi e storia personale dopo i riavvii. Le nuove voci complete del journal vengono elaborate durante il gioco; le posizioni di lettura salvate evitano riletture inutili. Se posizione o comandante non corrispondono, controlla prima il rilevamento del journal e la sua cartella nelle impostazioni.

**EDSM** può fornire dati di sistema aggiuntivi. I dati journal supportati possono essere inviati a **EDSM e Inara** se il servizio è configurato e attivo con credenziali proprie del comandante attivo. Un comandante non usa automaticamente la chiave API di un altro. Il salvataggio locale funziona indipendentemente dalla disponibilità di una connessione online.

## Lingue e guida contestuale

L’interfaccia supporta **12 lingue**: **DE, EN, FR, IT, NO, SV, FI, PL, NL, ES, TR, EL** – tedesco, inglese, francese, italiano, norvegese, svedese, finlandese, polacco, olandese, spagnolo, turco e greco.

Attualmente ci sono **937 chiavi UI-i18n per lingua**. **? Guida** offre **10 argomenti dettagliati di guida contestuale in tutte le 12 lingue**. I preferiti fanno parte della guida Explorer; la navigazione planetaria ha un argomento proprio, accessibile direttamente dal navigatore. La guida usa la lingua attuale dell’interfaccia e mantiene il tedesco come ripiego in caso di catalogo o voce mancanti.

## Requisiti

| Piattaforma | Python |
| --- | --- |
| **Windows** | **Python 3.10 o successivo, x64 obbligatorio.** Nessun limite superiore artificiale per le versioni esistenti. Sono determinanti le successive verifiche effettive di pacchetti e import. |
| **Linux** | Invariato: **Python da 3.10 a 3.13**, 64 bit consigliato. Deve essere disponibile il modulo venv corrispondente alla versione Python. |

I pacchetti richiesti sono in `requirements.txt`:

```text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

L’installazione scarica queste dipendenze. I file locali di Elite devono essere accessibili per analizzare i journal e per la navigazione planetaria. Su Linux Elite può funzionare tramite Steam/Proton; configura i percorsi reali di journal e screenshot in CMDRHelper. Il supporto Linux dell’HUD descritto sopra si riferisce a X11.

## Installazione su Linux

Estrai il progetto o la release completa ed esegui nella cartella del progetto:

```bash
./install.sh
./start.sh
```

Gli script usano esclusivamente il `venv` locale di questa installazione. Risolvono i collegamenti simbolici degli script, controllano Python e pip e possono riparare un ambiente locale danneggiato senza toccare dati personali o journal Elite. I pacchetti di sistema mancanti non vengono installati automaticamente; se manca il modulo venv, l’installer lo segnala. Il percorso di installazione Linux esistente resta invariato.

## Installazione su Windows

1. Estrai lo ZIP completo in una cartella dedicata.
2. Avvia **install.bat**, che richiama il file incluso **install-windows.ps1**.
3. Dopo l’installazione riuscita, avvia CMDRHelper con **start.bat**.

Un **Python esistente da 3.10 in poi, x64**, viene accettato senza limite di versione superiore artificiale. Una futura versione Python non viene rifiutata solo per il numero di versione. Un Python esistente idoneo o un venv locale utilizzabile evita un’installazione automatica di Python non necessaria.

Se non è disponibile un Python idoneo, l’installer propone, previo consenso, l’installazione automatica tramite **winget**. È stata scelta deliberatamente la serie fissa **Python 3.14 x64**; questa scelta è separata dalla regola aperta per le versioni già presenti. Se l’installazione automatica non è possibile, l’installer segnala l’errore.

L’installer crea, controlla o ripara solo il **venv locale di questa copia di CMDRHelper**, installa i requisiti ed esegue **pip check** e controlli di import per **PySide6, PySide6.QtWidgets, numpy e PIL**. Sono questi controlli effettivi a determinare l’utilizzabilità dell’ambiente. Se falliscono, l’installazione si interrompe con un errore comprensibile. Gli altri ambienti virtuali non vengono riparati o sostituiti.

## Diagnostica e pacchetti di rilascio

In caso di problemi aiutano gli indicatori del journal e dello stato online e i file nella cartella `logs`. I dati personali sono archiviati localmente; il backup dei preferiti deve includere le copie interne delle immagini oltre al database.

Per creare un proprio pacchetto di rilascio è disponibile `./create_release.sh`. La versione del programma è gestita centralmente in `cmdrhelper/version.py` e letta dallo script di rilascio. Il pacchetto contiene codice e risorse, ma nessun database personale, venv, file Git o cache.

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
