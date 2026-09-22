"""Italian content for contextual help."""


HELP_TOPICS = {
    "materials": (
        'Materiali',
        """<h2>Materiali</h2>
<h3>CMDRHelper</h3>
<p>Gestione dei materiali di ingegneria: tutti i 146 materiali Raw, Manufactured ed Encoded, con gradi, capacità e casi speciali. Scorte aggiornate per comandante, ricerca, filtri, cinque sfondi discreti e larghezza/ordine delle colonne salvati facilitano la consultazione. Una quantità sconosciuta resta distinta da zero.</p>
<p>Inventario Odyssey: la quarta scheda contiene 223 identità di catalogo per merci, materiali, dati e consumabili. Armadietto, zaino e totale attendibile restano separati; sono visibili pile di missione, stato e usi ingegneristici. Le quantità positive sono dorate. I nomi non tradotti usano l’inglese.</p>
<p>Ricerca commercianti di materiali (Cerca commerciante → Apri pianificatore rotte): su richiesta, Spansh cerca separatamente Raw, Manufactured ed Encoded dal sistema attuale del comandante. I carrier sono esclusi e i dettagli delle stazioni verificati. La distanza in ly è diretta tra sistemi; i dati della comunità non garantiscono l’accesso. L’invio al pianificatore imposta solo il sistema di destinazione, senza avviare una rotta. Nessuna ricerca di commercianti Odyssey.</p>
<p>Questa sezione principale mostra i materiali di ingegneria del comandante attualmente visualizzato. La selezione nella vista CMDR vale anche qui; i dati degli altri comandanti rimangono separati.</p>
<h3>Tre categorie</h3>
<p>Le schede Materiali grezzi, Materiali prodotti e Dati codificati contengono tutti i 146 materiali del catalogo, compresi quelli Guardian e Thargoid. L’elenco è ordinato per grado e alfabeticamente all’interno di ciascun grado.</p>
<h3>Scorte e barre</h3>
<p>I numeri indicano scorta / massimo, ad esempio Vanadio 244 / 250. La barra corrispondente indica 97,6 %. Anche i materiali mai posseduti vengono mostrati con 0 quando la scorta è nota in modo affidabile.</p>
<p>Le scorte vuote sono evidenziate in rosso tenue, quelle scarse in giallo/arancione e quelle quasi piene o piene in verde. I numeri rimangono visibili indipendentemente dai colori.</p>
<h3>Ricerca e filtri</h3>
<p>La ricerca considera il nome visualizzato e quello inglese del materiale. Può essere combinata con tutti i filtri: Tutti, Vuoto (0), Scarso (oltre 0 fino al 20 %), Quasi pieno (dall’80 % a meno del 100 %) e Pieno (100 %). I valori tra il 20 % e l’80 % appaiono solo in Tutti. Schede e filtri vengono ripristinati al successivo avvio.</p>
<h3>Valori sconosciuti</h3>
<p>Senza un inventario completo affidabile viene mostrato, ad esempio, ? / 250. Se il massimo è sconosciuto, può apparire 12 / ?. In entrambi i casi non vengono mostrati percentuale o barra; questi materiali appaiono soltanto in Tutti. Un grado sconosciuto compare in un gruppo separato alla fine dell’elenco.</p>
<h3>Aggiornamento in tempo reale</h3>
<p>I nuovi eventi del diario aggiornano automaticamente le scorte, anche dopo scambi di materiali, interventi di ingegneria, sintesi o ricompense in materiali. Durante la lettura iniziale viene mostrato un messaggio di caricamento. Un materiale appena raccolto viene evidenziato brevemente con un’indicazione come Vanadio +1; il consumo non genera una notifica di raccolta.</p>
<h3>Nomi dei materiali</h3>
<p>Se il nome di un materiale non è ancora disponibile nella lingua scelta, viene usato il suo nome inglese. I simboli interni del diario non sostituiscono i nomi visualizzati esistenti.</p>
<h3>Odyssey</h3>
<p>La quarta scheda di Materiali contiene Merci, Materiali, Dati e Consumabili. Armadietto e zaino mostrano le scorte personali. Portaflotta ✎ mostra le scorte private confermate manualmente sulla propria portaflotta per merci, materiali e dati. Doppio clic per confermare, correggere o impostare come sconosciuto. — significa sconosciuto; 0 richiede una conferma esplicita. La colonna « Totale » include armadietto, zaino e portaflotta solo con valori noti e coerenti. Con più pile, le scorte della portaflotta compaiono una volta nel riepilogo; le pile restano separate. I consumabili mantengono il totale personale senza portaflotta. FCMaterials non è un inventario completo della portaflotta e non viene usato come tale. Il limite di 1000 dell’armadietto vale per categoria, non per oggetto. Le scorte della portaflotta sono calcolate dall’ultima conferma. Le variazioni dell’armadietto vengono compensate solo sulla propria portaflotta, sottraendo le transazioni personali esplicite. Acquisti e vendite dal barista, soprattutto da altri giocatori, possono modificare le scorte reali senza essere rilevati automaticamente. Fare doppio clic per confermare nuovamente se necessario. Il totale usa una proiezione delle ultime scorte confermate, senza garanzia di dati in tempo reale. Il deposito privato Odyssey condivide 1.000 posti tra merci, materiali e dati. La somma delle scorte è completa solo quando tutte le posizioni e i materiali aggiuntivi sono confermati, inclusi gli zeri. Altrimenti si mostra un minimo. Se il limite è superato, i valori restano e Totale diventa sconosciuto. Armadietto, zaino e prenotazioni del mercato non sono scorte private della portaflotta.<br><b>! – Configurare le scorte della portaflotta</b><br>Fai doppio clic nella colonna Portaflotta e inserisci la quantità attuale per OGNI posizione. Conferma esplicitamente anche TUTTE le posizioni vuote con 0.<br>— = non ancora confermato / sconosciuto<br>0 = scorte vuote confermate esplicitamente</p>
<p>Gli ordini di acquisto aperti del barista riservano spazio. L’occupazione nel gioco può superare le scorte di materiali. Le prenotazioni non sono materiali e non entrano nei totali. Senza dati di mercato sufficientemente aggiornati, l’occupazione resta sconosciuta. Gli scambi di altri giocatori possono modificare questa istantanea.</p>
<p>Utilizzo mostra le indicazioni d’uso dell’oggetto. Missione indica l’assegnazione a una missione della specifica pila d’inventario, non una proprietà generale del tipo di oggetto. Le pile normali e quelle legate a missioni rimangono separate. Anche dopo il completamento della missione, l’oggetto resta contrassegnato finché il diario lo riporta nell’inventario; il completamento non lo rimuove automaticamente. Il suggerimento mostra il numero della missione e lo stato noto. Ingegneria significa che il catalogo statico Odyssey conosce almeno un utilizzo confermato: potenziamento della tuta, potenziamento dell’arma, modifica della tuta, modifica dell’arma o sblocco di un ingegnere. I singoli utilizzi sono riportati nel suggerimento. L’assenza dell’indicazione non significa che l’oggetto sia inutile o soltanto commerciabile. Possono apparire anche oggetti Powerplay e altri oggetti speciali.</p>
<p>La ricerca trova i nomi visualizzati locali e quelli inglesi dei materiali/oggetti. I sei filtri Odyssey sono Tutti (tutti gli oggetti), Missione (pile assegnate a una missione), Ingegneria (oggetti con un utilizzo di ingegneria confermato), Zaino (scorta nello zaino maggiore di zero), Armadietto (scorta nell’armadietto maggiore di zero) e Scorta 0 (scorta totale di 0 nota in modo affidabile). Una scorta sconosciuta — non è 0 ed è esclusa da Scorta 0. In assenza di traduzione del nome viene usato quello inglese; alcuni nomi possono quindi rimanere in inglese nella lingua scelta. È un comportamento intenzionale, non un errore di traduzione della logica d’inventario.</p>
<p>L’inventario personale viene aggiornato automaticamente in background. Le nuove raccolte confermate possono essere evidenziate brevemente. Quando si cambia comandante, le vecchie scorte vengono rimosse immediatamente. Sottoschede, filtri, larghezze e ordine delle colonne vengono salvati separatamente per Odyssey.</p>
<h3>Mining</h3>
<p>Materiali → Mining è la panoramica centrale delle 57 merci minerarie commerciabili attualmente note, distinte dai materiali per gli ingegneri. Un’unica tabella comprende l’estrazione sulla superficie dei pianeti e negli asteroidi/anelli. I prezzi di riferimento fissi sono indicativi, non prezzi di mercato in tempo reale.</p>
<p><b>Colonne</b><br><b>Merce:</b> nome della merce o risorsa.<br><b>SRV:</b> scorte verificate nel SRV.<br><b>Nave:</b> scorte verificate nella nave.<br><b>Carrier:</b> scorta sul proprio carrier; Elite non fornisce un inventario personale completo, quindi la scorta iniziale va confermata manualmente.<br><b>Totale:</b> SRV + Nave + Carrier, solo se tutte e tre le quantità sono note. Altrimenti —; sconosciuto non significa zero.<br><b>Prezzo medio Cr/t:</b> riferimento fisso, senza garanzia del prezzo di vendita attuale. I prezzi mancanti restano sconosciuti.<br><b>Classe di valore:</b> ALTA da 100.000 Cr/t; MEDIA tra 25.000–99.999 Cr/t; BASSA sotto 25.000 Cr/t. Un prezzo sconosciuto non ha classe di valore.</p>
<p><b>Confermare la scorta del carrier</b><br>Elite Dangerous non fornisce a CMDRHelper un inventario personale completo del carrier. Per definire una base nota per una merce: 1. Fai doppio clic sulla sua cella Carrier. 2. Inserisci la scorta attuale come numero intero maggiore o uguale a 0. 3. Applica il valore per confermarlo manualmente. 4. CMDRHelper segue poi automaticamente gli eventi CargoTransfer inequivocabili tra la nave e il proprio carrier. Il tooltip mostra la conferma manuale e l’eventuale aggiornamento successivo.</p>
<p><b>— = scorta sconosciuta</b><br>Senza una scorta iniziale confermata, i singoli trasferimenti non consentono di calcolare una scorta assoluta affidabile. Con un doppio clic puoi modificare, correggere o reimpostare il valore come sconosciuto in qualsiasi momento. Se un trasferimento produrrebbe un risultato contraddittorio o negativo, la scorta torna sconosciuta e deve essere confermata nuovamente a mano.</p>
<p><b>Nave e SRV</b><br>Le scorte di SRV e nave vengono ricostruite separatamente dai dati di carico verificati. Le quantità sconosciute restano —. Le istantanee complete hanno priorità sulle variazioni calcolate.</p>
<p><b>↻ Aggiorna</b><br>Le scorte di SRV e nave vengono aggiornate separatamente usando dati verificati. Le scorte confermate del carrier restano conservate indipendentemente. Gli aggiornamenti automatici continuano normalmente. Verde significa pronto o riuscito, l’animazione colorata indica un aggiornamento in corso e rosso un tentativo fallito. Dati mancanti o non verificabili non vengono mostrati come scorta vuota.</p>
<p><b>Combinare i filtri</b><br>La ricerca filtra le risorse per nome. La classe offre Tutti, ALTA, MEDIA e BASSA; l’origine offre Tutti, Estrazione planetaria e Asteroidi/Anelli. «Solo disponibili» mostra una merce se almeno una scorta nota in SRV, nave o carrier è positiva. Le scorte sconosciute non valgono 0 e non nascondono una scorta positiva nota in un’altra posizione. Ricerca, classe, origine e filtro scorte sono combinabili.</p>
<p><b>ABBAU ×N nell’esploratore</b><br>Un clic apre Materiali → Mining e imposta automaticamente il filtro di origine su Estrazione planetaria. Nell’esploratore non esiste una seconda tabella Mining.</p>
<p><b>Ordinamento e larghezze</b><br>Fai clic sulle intestazioni per ordinare in senso crescente o decrescente. Scorte e prezzi sono ordinati numericamente, con i valori sconosciuti in fondo. Trascina i bordi delle colonne per regolarne la larghezza. Ordinamento, larghezze e filtri di classe, origine e Solo disponibili vengono salvati.</p>
<p><b>Origine</b><br>Surface indica l’estrazione sulla superficie dei pianeti; Asteroid indica asteroidi/anelli. Alcune risorse provengono da entrambi gli ambienti (Both) e compaiono in entrambi i filtri di origine corrispondenti.</p>""",
    ),'overview': ('Panoramica',
              '<h2>Panoramica</h2>\n'
              '<p>La panoramica è la home page di CMDRHelper. Riepiloga le informazioni più '
              "importanti sul comandante attualmente attivo e mostra a colpo d'occhio se il "
              'diario, la posizione e i servizi online sono riconosciuti correttamente.</p>\n'
              '\n'
              '<h3>Comandante e nave</h3>\n'
              "<p>Qui vengono visualizzati il \u200b\u200bcomandante riconosciuto dall'Elite "
              'Dangerous Journal e la nave attualmente in uso.</p>\n'
              "<p>CMDRHelper assegna i dati personali al rispettivo comandante in base all'ID "
              'Frontier (FID). Ciò mantiene i dati di diversi comandanti separati gli uni dagli '
              'altri.</p>\n'
              '<p>Quando si cambia il comandante, vengono caricate le informazioni salvate '
              'associate al nuovo comandante.</p>\n'
              '\n'
              '<p>CMDRHelper mostra l’ultima modalità di gioco comunicata da Elite. Open, Solo e Gruppo privato vengono riconosciuti da LoadGame. Per i gruppi privati, il nome del gruppo comunicato da Elite viene mostrato senza modifiche. Questo non significa che Elite sia attualmente in esecuzione.</p>\n'
              '<h3>diario</h3>\n'
              '<p>CMDRHelper utilizza i file journal di Elite Dangerous come fonte dati '
              'principale.</p>\n'
              '<p>La visualizzazione del diario informa se i file del diario sono stati trovati e '
              'assegnati al comandante attivo. Le nuove voci del diario complete vengono elaborate '
              'automaticamente durante il gioco.</p>\n'
              '<p>Le aree del giornale che sono già state elaborate vengono salvate in modo che '
              'CMDRHelper non debba valutare nuovamente completamente ciascun giornale al '
              'successivo avvio.</p>\n'
              '\n'
              '<h3>Posizione attuale</h3>\n'
              '<p>Mostra il sistema stellare attualmente conosciuto e, per quanto noto dal diario, '
              'la posizione esatta del comandante.</p>\n'
              '<p>La posizione viene aggiornata da eventi come salti, attracco e altri rapporti di '
              'posizione e memorizzata comandante per comando.</p>\n'
              '\n'
              '<h3>Missioni</h3>\n'
              "<p>Quest'area mostra il numero di missioni aperte attualmente conosciute.</p>\n"
              '<p>Il pulsante o la voce di menu "Missioni" ti porta alla visualizzazione completa '
              'della missione con gli obiettivi noti della missione e le informazioni sullo '
              'stato.</p>\n'
              '\n'
              '<h3>Ultimo atto</h3>\n'
              '<p>“Ultimo stato” riassume l’ultimo stato di comandante persistente conosciuto. Ciò '
              'consente di ripristinare informazioni importanti anche dopo aver riavviato Elite '
              'Dangerous o CMDRHelper.</p>\n'
              '\n'
              '<h3>Sistemi finali</h3>\n'
              '<p>I sistemi recentemente visitati o riconosciuti dalla rivista vengono '
              'visualizzati qui.</p>\n'
              "<p>L'elenco serve come una rapida panoramica del recente viaggio del "
              'Comandante.</p>\n'
              '<p>La cronologia delle visite considera Location, FSDJump e CarrierJump anche durante la lettura del journal in tempo reale. Più eventi di posizione nello stesso soggiorno ininterrotto contano come una visita: A → A → A conta una volta. Un vero ritorno viene conservato: A → B → C → A conta quattro visite.</p>\n\n'
              '<h3>Stato in linea</h3>\n'
              '<p>Sono presenti ulteriori indicatori di stato nella parte superiore della finestra '
              'principale:</p>\n'
              '<ul>\n'
              '<li><b>Riconosciuto il giornale</b>– CMDRHelper ha rilevato una fonte di giornale e '
              "un'identità del comandante valide.</li>\n"
              '<li><b>EDSM</b>– mostra lo stato corrente della trasmissione EDSM per il giornale '
              'attivo FID.</li>\n'
              '<li><b>INARA</b>– mostra lo stato corrente della trasmissione Inara per il giornale '
              'attivo FID.</li>\n'
              '</ul>\n'
              '<p>I dati di accesso online sono gestiti separatamente per ciascun comandante. Un '
              'comandante non usa mai automaticamente lo API-Key di un altro comandante.</p>\n'
              '\n'
              '<h3>Importante per più comandanti</h3>\n'
              '<p>I dati in tempo reale dipendono sempre dal comandante che è stato chiaramente '
              "identificato dall'attuale sessione del diario di Elite Dangerous.</p>\n"
              '<p>La semplice visualizzazione di un comandante diverso in una vista non modifica '
              'il comandante live attivo né influisce su alcuna trasmissione EDSM o Inara.</p>\n'
              '\n'
              '<h3>Mancia</h3>\n'
              '<p>Se il comandante, la nave o la posizione non corrispondono allo stato attuale '
              'del gioco, controlla prima la visualizzazione del diario in alto e poi controlla la '
              'cartella del diario impostata in "Impostazioni".</p>'
              '<p>Open appare in rosso, Solo in oro e Gruppo privato in verde, con il nome del gruppo comunicato. La modalità viene ricostruita dai journal disponibili e aggiornata con le nuove voci LoadGame.</p>\n<p>Un singolo clic su una voce dei sistemi recenti copia il nome del sistema negli appunti. Appare brevemente «✓ Copiato: &lt;Sistema&gt;».</p>\n'),
 'missions': (
        'Missioni e ricompense',
        """<h2>Missioni e ricompense</h2>
<p>Questa pagina principale mostra le missioni e le ricompense osservate del comandante attualmente attivo nel diario. Selezionare un altro comandante nella vista CMDR separata non modifica questa pagina. I dati rimangono separati per comandante.</p>

<h3>Come usare la pagina</h3>
<ol>
<li>Apri «Missioni e ricompense» e seleziona una missione nell'elenco.</li>
<li>Controlla «Stato» e «DETTAGLI MISSIONE». «Passo successivo» ti aiuta a orientarti.</li>
<li>Se necessario, usa «Aggiorna journal» per rileggere i dati disponibili del diario.</li>
<li>Considera separatamente le ricompense delle missioni, «Taglie» e «Obbligazioni di combattimento».</li>
</ol>

<h3>Elenco e dettagli</h3>
<p>L'elenco contiene le missioni aperte confermate e le offerte provvisorie rilevate durante gli incontri. Mostra missione, sistema, pianeta / luogo, stato, prossimo passo, ricompensa e scadenza. Selezionando una voce compaiono i dettagli disponibili su destinazione e avanzamento. Le informazioni mancanti nel diario restano sconosciute; la scadenza delle offerte provvisorie è sconosciuta.</p>

<h3>Stato delle missioni</h3>
<p>Lo stato segue i dati disponibili su missione, posizione e avanzamento. Non tutti i tipi di missione forniscono tutte le fasi intermedie.</p>
<ul>
<li><b>Missione accettata / In viaggio:</b> La missione è nota; l'arrivo a destinazione non è ancora stato rilevato.</li>
<li><b>Nel sistema di destinazione:</b> Sei nel sistema obiettivo, ma non ancora alla destinazione identificata della missione.</li>
<li><b>Alla destinazione della missione:</b> È stata raggiunta la stazione o il corpo celeste corrispondente alla destinazione.</li>
<li><b>Destinazione modificata:</b> È stata segnalata una nuova destinazione della missione.</li>
<li><b>Merce raccolta:</b> È stato rilevato il ritiro del carico della missione.</li>
<li><b>Consegna in corso:</b> È stata registrata una consegna; viene mostrato l'avanzamento noto delle quantità.</li>
<li><b>Obiettivo completato / Dati ricevuti:</b> Il compito o la raccolta dati è terminato. La missione può essere ancora aperta, ad esempio con «Torna al terminale missioni». Questo non conferma ancora il pagamento.</li>
</ul>
<p>Completamenti, fallimenti e abbandoni rilevati rimuovono la missione interessata dall'elenco delle missioni aperte. Un nuovo quadro completo delle missioni può identificare le voci precedenti come non più attive.</p>

<h3>Ricompensa totale</h3>
<p>«Ricompensa totale» somma le ricompense note in crediti delle missioni aperte confermate. Non è un saldo già pagato. Le offerte provvisorie degli incontri, le taglie e le obbligazioni di combattimento sono escluse.</p>

<h3>Missioni da incontri</h3>
<p>Gli incontri spaziali supportati possono comparire come offerte provvisorie «Incarico da incontro», anche prima che sia disponibile una MissionID definitiva. «Ricompensa offerta» non è quindi ancora una ricompensa confermata di una missione aperta e non rientra nella ricompensa totale.</p>
<p>Se dati successivi del diario associano inequivocabilmente un'offerta a una missione, le due voci vengono unite. In caso di ambiguità l'offerta rimane provvisoria. Le offerte non confermate vengono nascoste localmente dopo 24 ore; ciò non indica una scadenza della missione nel gioco.</p>

<h3>Taglie</h3>
<p>Quest'area mostra le taglie osservate localmente, con totale e importi per fazione. Conosce solo i dati registrati, non un saldo di gioco di cui sia garantita la completezza. «Registrazione da questo momento.» indica l'inizio della registrazione; le lacune vengono segnalate da «Sincronizzazione incompleta: potrebbero mancare alcuni eventi.».</p>
<p>Un riscatto di taglie o una morte rilevati azzerano l'intero saldo locale delle taglie, indipendentemente dallo stato delle missioni.</p>

<h3>Obbligazioni di combattimento</h3>
<p>Qui sono mostrate per fazione le obbligazioni di combattimento osservate il cui riscatto non è stato rilevato. Un eventuale saldo precedente all'inizio della registrazione non è incluso. In caso di incertezza compare «Importo osservato» insieme a «Saldo non completamente verificato.».</p>
<p>Un riscatto attribuito senza ambiguità elimina l'importo osservato della fazione indicata; le altre fazioni restano invariate. Se l'attribuzione non è chiara, gli importi rimangono e compare «Riscossione rilevata – controlla il saldo.». Una morte rilevata elimina le obbligazioni di combattimento osservate.</p>

<h3>Azzeramento locale</h3>
<p>«Reimposta…» nella rispettiva area ricompense azzera, dopo conferma, solo il saldo locale di quell'area per il comandante attivo. <b>Non modifica alcun valore in Elite Dangerous.</b> Taglie e obbligazioni di combattimento vengono azzerate separatamente; le missioni non vengono né ripulite né completate.</p>

<h3>Aggiornamento e riavvio</h3>
<p>Le missioni aperte note e i saldi locali delle ricompense rimangono dopo il riavvio di Helper. Una nuova sessione del diario senza elenco missioni non rimuove automaticamente le missioni aperte. Le lacune nella registrazione possono lasciare incompleti soprattutto i saldi delle ricompense. «Aggiorna journal» può soltanto leggere le informazioni esistenti, non creare i dati di gioco mancanti.</p>
<p>La visualizzazione locale delle missioni non richiede una connessione a Inara. Con una connessione abilitata e configurata per il comandante attivo, gli eventi di missione supportati possono anche essere trasmessi.</p>""",
    ),
 'explorer': ('Esploratore',
              '<h2>Esploratore</h2>\n<h3>CMDRHelper</h3>\n<p>Panoramica del sistema: la nuova vista in stile Elite sostituisce la vecchia miniatura in Explorer e Cronaca. Stelle e pianeti formano la struttura principale, con lune ramificate sotto; i sistemi multipli restano leggibili. Zoom, scorrimento, adattamento alla finestra e clic sui corpi consentono di consultare i dettagli.</p>\n<p>Fasce di asteroidi compatte: i gruppi vengono riuniti in fasce nella panoramica e nelle normali mappe di Explorer e Cronaca. Tutti i dati dei singoli gruppi vengono conservati.</p>\n<p>Cartografia corretta: una scansione successiva alla mappatura DSS non azzera più valori esplorativi invenduti, ora della mappatura o efficienza. Le registrazioni errate vengono riparate all’avvio dai journal disponibili e attribuiti con certezza. Senza le fonti, la riparazione resta in sospeso; non occorre cancellare il database.</p>\n'
              "<p>L'Explorer valuta i sistemi e i corpi celesti scoperti e scansionati dal "
              'comandante attivo. Combina i dati del tuo diario Elite Dangerous con informazioni '
              "aggiuntive già disponibili e visualizza insieme l'esplorazione, la cartografia, i "
              "segnali biologici/geologici e i dati sull'estrazione mineraria di superficie.</p>\n"
              '\n'
              '<h3>Sistema attuale</h3>\n'
              "<p>L'attuale livello di conoscenza del sistema è riepilogato nell'area "
              'superiore.</p>\n'
              '<p>Questi includono, tra gli altri:</p>\n'
              '<ul>\n'
              '<li>corpi ben noti e persino registrati nel giornale</li>\n'
              '<li>segnali esistenti</li>\n'
              '<li>Scansiona i valori</li>\n'
              '<li>valore cartografico già raggiunto</li>\n'
              '<li>possibile valore totale se completamente mappato</li>\n'
              '<li>Stato BIO e valori BIO stimati</li>\n'
              '<li>Cartografia e dati BIO che non sono stati ancora inviati</li>\n'
              '</ul>\n'
              '<p>I valori indicati si basano sui dati effettivamente disponibili. Le informazioni '
              'mancanti non vengono presentate come una scoperta separata.</p>\n'
              '\n'
              '<h3>Mappa del sistema</h3>\n'
              '<p>La mappa del sistema rappresenta graficamente stelle, pianeti, lune e altri '
              'corpi conosciuti nel sistema attuale.</p>\n'
              '<p>È possibile fare clic su un corpo per aprirne la vista dettagliata.</p>\n'
              '<p>Il display mostra, tra le altre cose, il tipo di corporatura, la distanza e, se '
              'disponibili, i valori di scansione e cartografia, nonché proprietà speciali di '
              'esplorazione.</p>\n'
              '\n'
              '<p>«Adatta automaticamente alla finestra» è attivo per impostazione predefinita e conserva la scelta dopo il riavvio. Adatta ogni nuova vista generale alla finestra una sola volta; attivarlo in una finestra aperta esegue un singolo adattamento. Poi puoi continuare a ingrandire e spostare la vista manualmente. «Adatta alla finestra» resta disponibile per adattarla di nuovo manualmente.</p>\n'
              '\n'
              '<h3>Stazioni e strutture</h3>\n'
              '<p>La scheda «STAZIONI (N)» mostra le stazioni e le strutture note del sistema attuale dell’Explorer come schede espandibili. Il numero nel titolo conta tutte le voci note, anche quelle nascoste dai filtri. Non è un elenco completo delle stazioni della galassia.</p>\n'
              '<p>La base sono le osservazioni del diario di Elite note localmente. Se l’integrazione Spansh è attiva, si aggiungono informazioni dalla cache separata delle stazioni. La fonte può essere «Journal», «Spansh» o «Journal + Spansh»; in caso di conflitto prevale il diario. Spansh non aggiunge Fleet Carrier qui. Il tuo carrier può apparire se è noto localmente.</p>\n'
              '\n'
              '<h3>Ricerca, filtri e ordinamento delle stazioni</h3>\n'
              '<p>«Cerca nome della stazione…» cerca subito nomi di stazioni o parti di nomi, senza distinguere maiuscole e minuscole. Una ricerca vuota non limita i nomi. Ricerca ed entrambi i filtri devono essere soddisfatti insieme.</p>\n'
              '<ul>\n'
              '<li><b>Tipo:</b> Limita l’elenco a stazioni orbitali, avamposti, stazioni di superficie, insediamenti, meganavi, Fleet Carrier o altre strutture. «Tutti i tipi» rimuove il limite di tipo.</li>\n'
              '<li><b>Corpo associato:</b> Seleziona un corpo associato noto. «Tutti i corpi» ammette tutte le posizioni; «Sconosciuto» appare quando alcune voci non sono associabili con certezza a un corpo noto.</li>\n'
              '<li><b>Ordina per:</b> Inizialmente in ordine alfabetico per «Nome». In alternativa, ordine crescente per «Tipo», «Corpo associato» o «Distanza dal punto di arrivo». La distanza è ordinata numericamente; distanze o corpi sconosciuti vengono per ultimi nel rispettivo ordinamento.</li>\n'
              '</ul>\n'
              '<p>Non ci sono intestazioni di colonne delle stazioni da cliccare: i selettori ordinano le schede. Ricerca, filtri e ordinamento non inviano richieste di rete. Cambiare sistema azzera ricerca e filtri di tipo/corpo. Una vista vuota distingue l’assenza di voci note dalle voci che non soddisfano i filtri.</p>\n'
              '\n'
              '<h3>Dettagli delle stazioni e servizi</h3>\n'
              '<p>Clicca l’intestazione di una scheda per aprire o chiudere i dettagli. Se noti, vengono mostrati nome, tipo, sistema, corpo associato, MarketID, ultimo aggiornamento e fonte. Un doppio clic sull’anteprima apre il visualizzatore immagini.</p>\n'
              '<p>Spansh può aggiungere distanza di arrivo in secondi luce, affiliazione, governo, fazione dominante, dati economici e numero di piattaforme grandi, medie e piccole. Le date dei dati della stazione, del sistema e del recupero sono mostrate separatamente, se disponibili; un nuovo recupero non garantisce dati della stazione più recenti.</p>\n'
              '<p>I «Servizi» noti appaiono come campi etichettati, ad esempio «Mercato», «Cantiere navale», «Equipaggiamento», «Riparazione», «Rifornimento» o «Commerciante di materiali». L’intestazione mostra al massimo tre servizi e, se necessario, il numero di quelli aggiuntivi; espandendo la scheda si vedono tutti i servizi riconosciuti da CMDRHelper. I dati mancanti non vengono inventati e non dimostrano che un servizio sia assente.</p>\n'
              '\n'
              '<h3>Stazioni sulla mappa e aggiornamento</h3>\n'
              '<p>La mappa del sistema e «Vista completa» usano le stesse informazioni note sulle stazioni. Le strutture associate con certezza a un corpo compaiono accanto ad esso; le altre sotto «Altre strutture». Un clic apre i dettagli o, per gruppi, prima un elenco di selezione.</p>\n'
              '<p>In «Vista completa», «Aggiorna dati Spansh» aggiorna le informazioni Spansh sulle stazioni del sistema visualizzato nella finestra. L’opzione Spansh deve essere attiva e l’identità del sistema nota. La riga di stato indica richieste in corso, successo, errore o un aggiornamento già effettuato oggi. In caso di errore restano disponibili i dati locali e quelli utilizzabili in cache. La guida delle impostazioni spiega richieste automatiche, cache e aggiornamento manuale.</p>\n'
              '\n'
              '<h3>BIO ×N</h3>\n'
              '<p>BIO ×N denota il numero di segnali biologici di un corpo riportati dal '
              'gioco.</p>\n'
              '<p>Il numero inizialmente indica solo quanti segnali o generi biologici sono stati '
              'segnalati. Ciò non significa automaticamente che tutte le specie biologiche siano '
              'già state trovate o analizzate.</p>\n'
              '<p>Le effettive scoperte organiche proprie sono conservate separatamente.</p>\n'
              '\n'
              '<h3>GEO×N</h3>\n'
              '<p>GEO×N mostra il numero di segnali geologici di un corpo segnalati dal '
              'gioco.</p>\n'
              '<p>Questi possono includere, ad esempio, caratteristiche geologiche come fumarole o '
              'geyser. CMDRHelper visualizza solo le informazioni che appaiono dai dati del '
              'giornale/corpo esistenti.</p>\n'
              '\n'
              '<h3>ABBAU ×N</h3>\n'
              '<p>ABBAU ×N mostra il numero di siti minerari planetari di un corpo segnalati da '
              'Elite Dangerous.</p>\n'
              '<p>Esempio:</p>\n'
              '<p><b>ABBAU ×12</b></p>\n'
              '<p>significa che per questo corpo sono stati segnalati 12 siti minerari '
              'planetari.</p>\n'
              '<p>Il numero non dice quale materia prima può essere estratta in un unico '
              'luogo.</p>\n'
              '\n'
              '<h3>Reperti minerari propri</h3>\n'
              '<p>Se il comandante ha effettivamente effettuato operazioni di superficie con lo '
              'Rhino, lo CMDRHelper memorizza i risultati personali documentati '
              'separatamente.</p>\n'
              '<p>Viene fatta una distinzione tra:</p>\n'
              '<ul>\n'
              '<li>merci effettivamente ottenute, ad es. B. Rame in tonnellate</li>\n'
              "<li>materiali secondari raccolti durante l'estrazione</li>\n"
              '<li>materiali generali della superficie del corpo</li>\n'
              '</ul>\n'
              '<p>Un esempio di ritrovamento personale potrebbe essere:</p>\n'
              '<p><b>Rame – 40 t</b></p>\n'
              '<p>Queste informazioni significano che questo comandante ha effettivamente estratto '
              'lì 40 t di rame.</p>\n'
              '<p>I reperti minerari personali vengono salvati per ciascun comandante e non '
              'vengono mescolati con i reperti di altri comandanti.</p>\n'
              '\n'
              '<h3>Materiali della superficie corporea</h3>\n'
              '<p><code>Scan.Materials</code>descrive la composizione generale del materiale '
              'superficiale di un corpo.</p>\n'
              '<p>Ad esempio, ferro, nichel, zolfo o altri materiali possono essere visualizzati '
              'con valori percentuali.</p>\n'
              '<p>Questi valori non vanno confusi con le materie prime di un deposito minerario '
              'planetario. Frontier non fornisce alcuna associazione diretta documentata tra '
              'questi materiali generali del corpo e i contenuti di un singolo sito minerario nel '
              'Diario.</p>\n'
              '\n'
              '<h3>Terraformazione</h3>\n'
              "<p>Il simbolo o l'etichetta per la terraformazione mostra che un corpo è "
              'considerato un candidato alla terraformazione in base ai dati disponibili.</p>\n'
              '\n'
              '<h3>Prima scoperta</h3>\n'
              '<p>«Già scoperto al momento della tua scansione» descrive lo stato precedente a quella scansione. Sì significa già scoperto, No significa non ancora scoperto allora; le informazioni mancanti restano Sconosciute. ★ indica un candidato First Discovery al momento della scansione, non un primato ufficiale ancora garantito oggi.</p>\n<p>Un valore storico WasDiscovered=false o WasMapped=false non significa che il corpo sia ancora non scoperto o non mappato oggi. Queste osservazioni restano storiche dopo la vendita dei dati o una nuova visita. La presenza in EDSM è un’informazione separata e non prova una scoperta ufficiale in Elite. Non se ne deduce alcun primo scopritore ufficiale.</p>\n'
              '\n'
              '<h3>Prima mappatura</h3>\n'
              '<p>CMDRHelper distingue tra:</p>\n'
              '<ul>\n'
              '<li>◉ Candidato First Mapping al momento della scansione: non ancora mappato quando lo hai scansionato</li>\n<li>◎ Mappato da te: è registrato il completamento della tua mappatura DSS</li>\n<li>◉✓ Candidato alla scansione e tua mappatura documentati; primato ufficiale non confermato</li>\n'
              '</ul>\n'
              '<p>«Già mappato al momento della tua scansione» viene valutato indipendentemente dalla scoperta. Le informazioni mancanti restano Sconosciute. Un corpo già scoperto poteva non essere ancora mappato alla scansione. La tua mappatura non conferma un riconoscimento ufficiale First Mapping; dopo più visite, neppure l’ordine rispetto alla scansione salvata è sempre documentato.</p>\n<p>Il completamento della tua mappatura DSS salva ora in modo affidabile l’ora della mappatura, le sonde usate e l’obiettivo di efficienza. Le scansioni successive non fanno più perdere i dati esistenti.</p>\n'
              '\n'
              '<h3>Atterraggio possibile</h3>\n'
              "<p>L'indicatore di atterrabilità identifica i corpi sui quali, secondo i dati "
              "conosciuti, è possibile l'atterraggio.</p>\n"
              '\n'
              '<h3>Cornici dorate/corpi pregiati</h3>\n'
              '<p>I corpi particolarmente preziosi possono essere evidenziati nella '
              "visualizzazione dell'esploratore.</p>\n"
              '<p>Il bordo dorato indica una stima di cartografia sopra la soglia impostata. Non è un indicatore First Discovery e non conferma dati invenduti o bonus di primato ancora disponibili oggi.</p>\n'
              '<p>Non sostituisce la visualizzazione dettagliata del valore del corpo.</p>\n'
              '\n'
              '<h3>Elenco dei valori</h3>\n'
              '<p>La lista dei valori mostra stime basate sulla scansione salvata, non pagamenti ancora dovuti garantiti. I bonus di primato restano non confermati. I suggerimenti di mappa e lista e i dettagli del corpo usano gli stessi stati riferiti al momento della scansione.</p>\n'
              '<p>È particolarmente adatto per confrontare rapidamente corpi interessanti o '
              'preziosi in un sistema.</p>\n'
              '\n'
              '<h3>BIO / GEO / ABBAU</h3>\n'
              '<p>Questa vista raggruppa corpi con segnali biologici, geologici o di estrazione mineraria '
              'planetaria.</p>\n'
              '<p>Ciò significa che non è necessario cercare singolarmente i corpi interessanti '
              'nella mappa completa del sistema.</p>\n'
              '<p>Se disponi di dati di estrazione di superficie, possono essere visibili anche i '
              'tuoi ritrovamenti minerari personali.</p>\n'
              '<p>Le larghezze modificate manualmente nella tabella comune BIO / GEO / ABBAU dell’Explorer restano salvate dopo la riapertura e il riavvio. Il ripristino delle colonne dei popup è più robusto; valori non validi vengono sostituiti da larghezze predefinite sicure.</p>\n\n'
              '<h3>Uso delle tabelle</h3>\n<p>Nella lista dei valori e in BIO / GEO / ABBAU, fai clic su '
              'un’intestazione per ordinare e di nuovo per invertire la direzione. Trascina i bordi delle '
              'colonne con il mouse per ridimensionarle. Ordinamento e larghezze sono salvati separatamente '
              'per ogni tabella. I nomi dei corpi seguono un ordine naturale, ad esempio A 2 prima di A 10. '
              'Distanze, crediti e quantità sono ordinati numericamente. Stato, analisi e visita sono ordinati '
              'secondo il loro significato, non alfabeticamente.</p>\n\n<h3>Particolare del corpo</h3>\n'
              '<p>Cliccando su un corpo si apre la vista dettagliata.</p>\n'
              '<p>Per quanto è noto, lì può apparire quanto segue:</p>\n'
              '<ul>\n'
              '<li>Tipo di corporatura</li>\n'
              '<li>massa</li>\n'
              '<li>distanza</li>\n'
              '<li>Gravità</li>\n'
              '<li>atmosfera</li>\n'
              '<li>Atterrabilità</li>\n'
              '<li>Stato di terraformazione</li>\n'
              '<li>Segnali BIO/GEO</li>\n'
              '<li>siti minerari planetari</li>\n'
              '<li>Materiali di superficie</li>\n'
              '<li>propri reperti minerari</li>\n'
              '<li>Valore di scansione</li>\n'
              '<li>valore cartografico</li>\n'
              '<li>valore corrente</li>\n'
              '</ul>\n'
              '<p>Non tutti gli enti dispongono di tutte le informazioni.</p>\n'
              '\n'
              '<h3>Previsioni BIO</h3>\n'
              '<p>CMDRHelper può stimare possibili scoperte biologiche sulla base dei dati '
              'esistenti su corpi idonei.</p>\n'
              '<p>Le previsioni non sono una garanzia che una particolare specie sarà '
              "effettivamente presente. Servono come aiuto decisionale per l'esplorazione.</p>\n"
              '<p>Anche i valori BIO stimati sono previsioni e vengono trattati separatamente dai '
              'risultati effettivi confermati.</p>\n'
              '\n'
              '<h3>Non ancora inviato</h3>\n'
              '<p>CMDRHelper mantiene la cartografia nota relativa al comandante e i dati BIO che '
              'non sono stati ancora inviati.</p>\n'
              '<p>Le vendite di cartografia e le royalties biologiche vengono contabilizzate '
              'utilizzando gli eventi del giornale corrispondenti.</p>\n'
              '<p>I dati cartografici già venduti non dovrebbero apparire nuovamente aperti dopo '
              'la ricostruzione.</p>\n'
              '\n'
              '<h3>Visualizzazione automatica</h3>\n'
              '<p>I suggerimenti Explorer supportati, come Corpi di valore o Ritrovamenti BIO, '
              'possono essere visualizzati automaticamente utilizzando gli interruttori nella '
              'barra laterale sinistra.</p>\n'
              '<p>Queste piccole finestre live servono come suggerimenti aggiuntivi durante il '
              'gioco e non sostituiscono la visualizzazione completa di Explorer.</p>\n'
              '<p>“Cargo” mostra le scorte confermate dello Ship o SRV determinato dalla FID attiva del Journal. Il Cargo dello SRV non viene mai acquisito come Cargo dello Ship; i Limpets contano nell’occupazione totale e vengono mostrati separatamente nella tabella Nome | Quantità.</p>\n'
              '<p>Il progresso BIO è compatto: 1/3 giallo, 2/3 blu e 3/3 verde; anche lo stato completato «Completato» è verde. In «mostra automaticamente», GEO ha un proprio interruttore salvato: solo BIO, solo GEO o entrambi insieme.</p>\n<p>La finestra di carico adatta automaticamente l’altezza al contenuto. Con molte voci l’altezza è limitata e la tabella scorre; larghezza scelta e posizione restano invariate. L’interruttore esistente «HUD del carico» è ora in «mostra automaticamente», senza un secondo interruttore nella finestra di carico.</p>\n\n'
              '<h3>Diversi comandanti</h3>\n'
              "<p>I risultati dell'esplorazione personale, la cartografia, i reperti BIO e i "
              'propri reperti minerari di superficie vengono assegnati al rispettivo '
              'comandante.</p>\n'
              '<p>Le proprietà astronomiche globali di un corpo - ad esempio il numero di siti '
              'minerari planetari conosciuti - rimangono proprietà del corpo stesso.</p>\n'
              '\n'
              '<h3>Mancia</h3>\n'
              '<p>Se hai un corpo interessante, vale la pena fare clic sulla vista dettagliata. '
              'Questo è il posto migliore per distinguere tra dati generali del corpo, possibili '
              "risultati dell'esplorazione e ritrovamenti effettivi documentati dal tuo "
              'comandante.</p>'
              """

<h3>★ Preferiti</h3>
<p>Il pulsante «★ Preferiti» in alto nell’Explorer apre una finestra dei preferiti separata e riutilizzabile. Qui puoi salvare sistemi, pianeti/lune e luoghi in superficie per il comandante attivo.</p>
<p>L’elenco scorrevole, ordinato alfabeticamente per nome, mostra nome, tipo, sistema, corpo e latitudine/longitudine se pertinenti, categoria e una piccola anteprima dell’immagine. Ricerca a testo libero, filtro per tipo e filtro per categoria possono essere combinati. La ricerca considera nome, sistema, corpo e nota.</p>
<p>«Apri / Mostra» mostra i dati salvati, la nota e un’anteprima più grande. «Mostra nell’Explorer» apre la panoramica del sistema o la vista dettagliata del corpo già esistenti, se il preferito appartiene al sistema attuale dell’Explorer e sono disponibili dati corrispondenti. Per gli altri sistemi restano visibili i dati salvati del preferito; non viene calcolata alcuna rotta tra sistemi.</p>

<h3>Filtro distanza</h3>
<p>«Filtro distanza» è disattivato inizialmente. «Distanza max.:» ha un valore predefinito di 500 ly, regolabile da 1 a 100.000 ly. La distanza si riferisce al sistema attualmente noto e usa le coordinate dei sistemi disponibili localmente. Non viene effettuata alcuna richiesta in tempo reale solo per questo filtro.</p>
<p>I preferiti con distanza nota oltre il limite vengono nascosti. Quelli con distanza sconosciuta restano visibili. Se mancano le coordinate del sistema attuale, il filtro distanza non nasconde alcuna voce. Ricerca e filtri di tipo e categoria restano attivi. Il filtraggio si aggiorna automaticamente dopo un cambio di sistema. Attivazione e distanza massima vengono salvate.</p>

<h3>Esportare i preferiti</h3>
<p>«Esporta» crea uno ZIP portabile con tutti i preferiti del comandante attivo, non solo le voci visibili tramite ricerca o filtri di tipo, categoria e distanza. favorites.json contiene i dati strutturati dei preferiti; le immagini disponibili sono incluse in images/. Il pacchetto è trasferibile tra Linux e Windows.</p>
<p>I preferiti esistenti e le immagini originali non vengono modificati. Immagini con contenuto identico sono salvate una sola volta nel pacchetto. Immagini mancanti o danneggiate non impediscono l’esportazione dei dati. Importazione ed esportazione consentono al massimo 32 MiB per file e 256 MiB totali di contenuti non compressi.</p>

<h3>Importare i preferiti</h3>
<p>«Importa» verifica prima lo ZIP e mostra un riepilogo dei preferiti nuovi ed esistenti prima delle modifiche. I preferiti importati sono assegnati al comandante attualmente attivo. I duplicati sono riconosciuti per tipo, categoria, nome e posizione: ID noti di sistema/corpo e coordinate, altrimenti nomi di sistema/corpo. Sono considerati anche i duplicati interni al pacchetto.</p>
<p>La stessa scelta vale per tutti i duplicati rilevati: «Salta» è l’opzione predefinita e lascia inalterate le voci esistenti; «Sostituisci il preferito esistente» applica i dati importati al preferito esistente; «Importa come nuova voce» crea una voce aggiuntiva. Annullando non viene importato nulla.</p>
<p>Dati dei preferiti non validi bloccano l’intera importazione. In caso di errore, le modifiche al database vengono annullate per evitare un’importazione parziale. Immagini mancanti o danneggiate non impediscono di importare dati validi; quei preferiti vengono importati senza immagine. CMDRHelper gestisce localmente le immagini importate.</p>

<h3>Salvare un sistema, un pianeta o la posizione attuale</h3>
<ul>
<li>«★ Salva il sistema attuale» salva il sistema attuale senza coordinate di superficie.</li>
<li>«★ Salva pianeta / luna» permette di scegliere un pianeta o una luna conosciuti del sistema attuale. Anche questo preferito non riceve coordinate di superficie.</li>
<li>«★ Salva la posizione attuale» si trova in alto nella finestra dei preferiti, accanto alle altre due opzioni di salvataggio, ed è disponibile anche nel navigatore planetario. Nella finestra dei preferiti il pulsante resta sempre visibile ed è disattivato in assenza di dati di posizione planetaria attuali validi e di un comandante attivo. Il clic fissa comandante, sistema, corpo, latitudine e longitudine. I successivi movimenti nel gioco non modificano questi valori nella finestra di dialogo aperta.</li>
</ul>
<p>Inserisci un nome a scelta e seleziona esattamente una categoria: Bio, Geo, Estrazione, Panorama, Sito di atterraggio, Interessante o Altro. Nota e immagine sono facoltative. Gli ID tecnici conosciuti vengono acquisiti internamente; non devi inserirli. Anche latitudine o longitudine 0,0 sono coordinate valide.</p>
<p>«Modifica» modifica nome, categoria, nota e immagine. Sistema, corpo e coordinate salvate vengono conservati. Per salvare un altro luogo in superficie, crea un nuovo preferito in quella posizione.</p>

<h3>Preferito rapido senza mouse</h3>
<p>In «Impostazioni → Preferito rapido» puoi impostare liberamente, modificare o rimuovere una scorciatoia da tastiera globale. Dopo l’installazione, per impostazione predefinita è «Non assegnata»: CMDRHelper non registra alcun tasto senza che venga richiesto. L’assegnazione viene salvata. Se una combinazione è già in uso o non è disponibile sul tuo sistema, compare un messaggio di errore; un’eventuale assegnazione precedentemente funzionante viene mantenuta.</p>
<p>Su Linux/X11 e Windows, la scorciatoia funziona anche mentre Elite ha il focus – a piedi, nell’SRV e nella nave. Una pressione salva immediatamente la posizione attuale sulla superficie per il comandante attivo, senza finestre di dialogo e senza usare il mouse. Il comandante, il sistema, il corpo e i valori attuali di Latitude/Longitude vengono fissati in quel momento. Senza coordinate planetarie attuali valide non viene salvato nulla; le coordinate precedenti non vengono riutilizzate.</p>
<p>Il preferito riceve un nome provvisorio univoco, come «Marcatore 07.09.2026 06:32:15», e la categoria «Altro». Nella normale finestra dei preferiti puoi in seguito rinominarlo, assegnarlo a un’altra categoria, aggiungere una nota o un’immagine. Nessuno screenshot viene acquisito o importato automaticamente.</p>
<p>Per circa due secondi, «★ PREFERITO SALVATO» compare direttamente sopra la finestra attiva di Elite con il corpo e le coordinate; se la posizione non è disponibile, compare brevemente «⚠ NESSUNA COORDINATA PLANETARIA». La visualizzazione non prende il focus e non intercetta gli input. Funziona anche con l’HUD di navigazione disattivato e poi scompare completamente. Con l’HUD attivato, in seguito rimane la normale visualizzazione di navigazione. L’impostazione salvata dell’interruttore dell’HUD non viene modificata. La visualizzazione utilizza la stessa infrastruttura di sovrimpressione e gli stessi requisiti di piattaforma dell’HUD di navigazione.</p>

<h3>Immagini dei preferiti</h3>
<p>Le immagini dei preferiti sono separate dalla sezione Immagini. «Scegli immagine …» accetta PNG, JPEG e WebP. Solo al salvataggio CMDRHelper copia l’immagine selezionata nella propria cartella delle immagini dei preferiti. Il file originale non viene né spostato né modificato.</p>
<p>«Usa l’ultimo screenshot» rilegge a ogni clic la cartella sorgente degli screenshot configurata e cerca screenshot leggibili con nomi di file tipici di Elite. Senza configurazione vengono considerate le consuete cartelle degli screenshot Elite su Windows o Steam/Proton. Viene cercato anche nella cartella del comandante attivo all’interno della destinazione di conversione configurata, per trovare gli screenshot Elite convertiti corrispondenti. Uno screenshot convertito resta così reperibile anche se il suo BMP originale è stato eliminato. Per stabilire lo scatto più recente conta una data e ora univoca nel nome del file, altrimenti la data del file; per le immagini convertite conta l’ora dello scatto salvata nel nome, non quella della conversione. CMDRHelper non scatta screenshot autonomamente e non cerca in cartelle di immagini generiche.</p>
<p>Prima dell’utilizzo vengono mostrati nome del file, data e ora dello scatto e un’anteprima appena caricata. Conferma con «Usa questa immagine». Se non viene trovato uno screenshot adatto, puoi comunque usare «Scegli immagine …». Gli screenshot BMP di Elite vengono salvati come copia PNG interna.</p>
<p>Un’immagine può essere sostituita nella finestra di modifica o deselezionata con «Rimuovi immagine». Al salvataggio viene eliminata la copia interna non più utilizzata. Se manca un file immagine, il preferito resta utilizzabile senza anteprima.</p>
<p>Le immagini dei preferiti possono essere esportate e vengono copiate localmente all’importazione. Le copie interne condivise restano finché un altro preferito ne ha bisogno. Quando l’importazione sostituisce preferiti, i vecchi file immagine vengono attualmente conservati per precauzione.</p>

<h3>Destinazione del preferito e comandante</h3>
<p>«▶ Al percorso» imposta il sistema noto del preferito come destinazione nel pianificatore. La partenza segue il comportamento esistente usando l’AppState corrente; una partenza inserita manualmente viene mantenuta. Nessun percorso viene calcolato automaticamente. «◎ Alle coordinate» avvia la navigazione planetaria esistente verso il luogo in superficie con l’HUD esistente se sono salvati sistema, corpo e coordinate valide. Il viaggio al sistema e la navigazione in superficie sono due passaggi separati, senza sequenza automatica. Senza coordinate di superficie è disponibile solo il percorso; le azioni prive dei dati necessari sono nascoste.</p>
<p>Per i luoghi in superficie, «◎ Alle coordinate» passa corpo, latitudine, longitudine e nome del preferito salvati al navigatore planetario esistente. La nuova destinazione sostituisce la precedente. I preferiti non hanno una logica di navigazione propria. Il navigatore continua a decidere autonomamente: dati planetari validi e corrispondenti attivano la navigazione; altrimenti attende tali dati.</p>
<p>I preferiti appartengono esclusivamente al comandante attivo. Cambiando comandante, l’elenco viene aggiornato e un’eventuale finestra di modifica aperta viene annullata. Una destinazione ancora gestita come destinazione preferita del comandante precedente viene terminata. La selezione dei comandanti nella cronaca non estende questo elenco di preferiti.</p>
<p>«Elimina» richiede conferma ed elimina soltanto il record del preferito e la sua copia interna dell’immagine. Lo screenshot originale o l’immagine originale selezionata e tutti i dati di Explorer, journal e corpi vengono conservati.</p>"""),
 'chronicle': (
        'Cronaca',
        """<h2>Cronaca</h2>
<h3>CMDRHelper</h3>
<p>Panoramica del sistema: la nuova vista in stile Elite sostituisce la vecchia miniatura in Explorer e Cronaca. Stelle e pianeti formano la struttura principale, con lune ramificate sotto; i sistemi multipli restano leggibili. Zoom, scorrimento, adattamento alla finestra e clic sui corpi consentono di consultare i dettagli.</p>
<p>Fasce di asteroidi compatte: i gruppi vengono riuniti in fasce nella panoramica e nelle normali mappe di Explorer e Cronaca. Tutti i dati dei singoli gruppi vengono conservati.</p>
<p>La cronaca è la storia personale dei viaggi e delle scoperte del comandante. Utilizza le informazioni del diario memorizzate in modo permanente per trovare sistemi che sono già stati visitati, per rappresentarli spazialmente e per cercare scoperte note.</p>

<h3>Sistemi visitati</h3>
<p>La Cronaca mostra i sistemi visitati e le loro posizioni nella galassia nota al Comandante.</p>
<p>Se disponibili, vengono prese in considerazione la prima e l'ultima visita nonché le informazioni note sul corpo.</p>
<p>Con un periodo attivo, il numero di visite, la prima visita e l’ultima visita nella mappa si riferiscono alle visite effettive ai sistemi selezionate dal filtro.</p>
<p>La cronaca quindi non è solo una mappa, ma anche uno strumento per ritrovare mete e scoperte di viaggi precedenti.</p>

<h3>Mappa 3D</h3>
<p>I sistemi visitati sono rappresentati spazialmente utilizzando le loro coordinate galattiche X/Y/Z.</p>
<p>Le istruzioni per l'uso si trovano direttamente sopra la mappa:</p>
<ul>
<li>Tieni premuto il pulsante sinistro del mouse → ruota la vista</li>
<li>tenere premuto il pulsante centrale del mouse e trascinare → disegnare una finestra di zoom</li>
<li>Tieni premuto il pulsante destro del mouse → sposta la vista</li>
</ul>
<p>Il display ad asse piccolo aiuta nell'orientamento nello spazio.</p>

<p>La rotellina del mouse ingrandisce o riduce la vista senza tasti aggiuntivi.</p>
<p>Un doppio clic in uno spazio vuoto della mappa ripristina la vista inclinata iniziale, azzera lo spostamento e adatta alla finestra tutti i sistemi visualizzati. I filtri e il sistema selezionato vengono mantenuti.</p>
<p>Quando inizi una rotazione con il pulsante sinistro, il sistema cliccato diventa il centro di rotazione. In uno spazio vuoto si usa il punto sotto il cursore sul piano galattico; con una vista quasi orizzontale si usa invece il centro della mappa su quel piano. Anche l’allineamento ruota attorno al centro di rotazione attuale.</p>
<p>Fai clic su un sistema per aprire la finestra dei dettagli. Qui, un clic sinistro sul nome in alto o sull’icona ⧉ accanto copia negli appunti solo il nome del sistema. Un breve ✓ conferma la copia.</p>

<h3>Posizione attuale</h3>
<p>Con "Posizione attuale" la visualizzazione della mappa può essere allineata o riportata alla posizione attualmente nota del comandante attivo.</p>
<p>Vengono prima applicati i filtri attuali. La vista viene centrata sul sistema attuale solo se è presente nella mappa risultante.</p>
<p>Altrimenti compare «Il sistema attuale non è incluso in questa selezione di filtri.» I filtri non vengono rimossi.</p>

<h3>Allinea</h3>
<p>«Allinea» ripristina l’orientamento con una vista dall’alto del piano galattico. Spostamento e zoom vengono mantenuti.</p>
<p>È utile quando molte rotazioni hanno reso la mappa poco chiara.</p>

<h3>Aggiorna Cronaca</h3>
<p>«Aggiorna Cronaca» ricarica i dati della cronaca in base ai filtri combinati attuali e aggiorna la visualizzazione. Testo libero, limiti di data attivati e filtri minerari vengono nuovamente valutati insieme; i filtri attivi non vengono ignorati.</p>
<p>La funzione non modifica i file journal né crea nuovi dati di esplorazione. Aggiorna semplicemente la visualizzazione della cronologia in base ai dati CMDRHelper esistenti.</p>

<h3>Ricerca testuale libera</h3>
<p>È possibile cercare contenuti già noti utilizzando il campo "Cronologia ricerche...".</p>
<p>La ricerca prende in considerazione – se disponibili nel database – tra l’altro:</p>
<ul>
<li>Nomi di sistema</li>
<li>Caratteristiche del corpo</li>
<li>dati biologici</li>
<li>Materiali</li>
<li>Dati del Codice</li>
</ul>
<p>Testo libero, periodo ed estrazione condividono un’unica area di filtri. «Applica» valuta insieme i filtri impostati. Invio nel campo di testo libero avvia lo stesso filtraggio combinato di «Applica».</p>

<h3>Periodo Dal/Al (UTC)</h3>
<p>Attiva «Dal» e «Al» con le rispettive caselle e scegli la data desiderata. È possibile usare anche un solo limite. Senza la casella attivata non vi è alcuna restrizione temporale su quel lato; senza entrambe le caselle non viene limitato alcun periodo.</p>
<ul>
<li><b>Dal:</b> Dall’inizio del giorno di calendario UTC selezionato, incluso.</li>
<li><b>Al:</b> Viene incluso l’intero giorno di calendario UTC selezionato, fino all’istante immediatamente precedente l’inizio del giorno successivo.</li>
</ul>
<p>UTC è il tempo coordinato universale. I limiti di data si riferiscono ai giorni di calendario UTC, non a quelli del tuo fuso orario locale.</p>
<p>Il filtro usa le visite effettive ai sistemi registrate in <code>system_visits</code>. È necessaria una visita effettiva del comandante interessato nel periodo. I valori memorizzati <code>first_seen</code> e <code>last_seen</code> non sostituiscono una visita reale: non basta che il periodo si trovi tra una prima visita precedente e un’ultima visita successiva.</p>
<p>Il periodo filtra le visite, non i singoli eventi di scoperta, BIO, GEO o estrazione. Le informazioni sui ritrovamenti noti e le quantità estratte rimangono totali memorizzati. Dal/Al si possono usare da soli o insieme al testo libero e ai filtri minerari.</p>
<p>Se Dal è successivo ad Al, compare «La data Dal non deve essere successiva alla data Al.» Non viene avviata alcuna query al database. Correggi i limiti di data e applica nuovamente i filtri.</p>

<h3>Risultati della ricerca</h3>
<p>I successi vengono visualizzati nell'elenco dei risultati esistenti sotto la scheda della cronaca.</p>
<p>A seconda del tipo di colpo, possono apparire sistema, corpo e informazioni aggiuntive.</p>
<p>Un risultato può essere utilizzato per trovare il sistema o l'organismo corrispondente già noto e per aprire le informazioni dettagliate esistenti.</p>

<h3>Nessun risultato</h3>
<p>Se un filtraggio valido non trova corrispondenze, la mappa e le rotte vengono svuotate. L’elenco dei risultati viene svuotato e nascosto, la visualizzazione dei dettagli viene reimpostata e un’eventuale finestra aperta dei dettagli di un sistema della cronaca viene chiusa.</p>
<p>I vecchi risultati non rimangono visibili. In questo caso, controlla la combinazione di testo di ricerca, periodo e filtri minerari, nonché il comandante usato per la vista interessata.</p>

<h3>Siti minerari planetari</h3>
<p>Il filtro "Siti minerari planetari" può essere utilizzato per cercare specificamente corpi noti per i quali Elite Dangerous ha segnalato siti minerari planetari.</p>
<p>La visualizzazione sottostante corrisponde a quella nota da Explorer:</p>
<p><b>ABBAU ×N</b></p>
<p>Il numero appartiene al corpo stesso e non è correlato al comandante.</p>

<h3>Almeno</h3>
<p>Usando "Almeno" puoi specificare il numero minimo di posizioni minerarie planetarie che un corpo dovrebbe avere.</p>
<p>Esempio:</p>
<p><b>Almeno 20</b></p>
<p>mostra solo corpi conosciuti con almeno:</p>
<p><b>ABBAU ×20</b></p>
<p>Ciò consente di localizzare in modo mirato aree minerarie particolarmente estese.</p>

<h3>Le mie scoperte minerarie</h3>
<p>Con i «Reperti minerari propri» la ricerca si limita ai corpi sui quali il comandante in questione ha effettuato lui stesso, in modo dimostrabile, attività minerarie di superficie.</p>
<p>Queste informazioni provengono dalla storia personale dell'attività mineraria di superficie e sono rigorosamente separate dal comandante.</p>
<p>Un corpo può quindi avere segnali ABBAU ×N globali senza che il proprio comandante vi abbia già rimosso qualcosa.</p>

<h3>Merce</h3>
<p>Se è attivata l'opzione “Reperti minerari propri”, è disponibile anche la selezione “Materia prima”.</p>
<p>L'elenco contiene solo le materie prime che il comandante in questione ha effettivamente già ottenuto dall'estrazione di superficie.</p>
<p>Questo non è un elenco teorico di tutte le possibili materie prime minerarie.</p>
<p>Per EXAMPLE, ad esempio, la selezione può contenere:</p>
<ul>
<li>Tutto</li>
<li>rame</li>
</ul>
<p>Se in seguito verranno effettivamente estratte ulteriori materie prime, queste appariranno automaticamente nella tua selezione personale.</p>

<h3>Ricerca mirata delle materie prime</h3>
<p>Ad esempio, se si seleziona "Rame" e poi si preme "Applica", la cronologia mostrerà solo i corpi sui quali il comandante in questione ha estratto rame in modo dimostrabile.</p>
<p>Esempio:</p>
<p><b>Example System / 2 — ABBAU ×12 — rame 40 t</b></p>
<p>Ciò significa che la cronaca può essere utilizzata come database di localizzazione personale: una materia prima già estratta può essere ritrovata in seguito.</p>

<h3>Tutte le materie prime</h3>
<p>Con “Materia prima: tutte” vengono prese in considerazione tutte le scoperte personali di estrazione mineraria di superficie corrispondenti.</p>
<p>Se su un corpo sono note più merci, queste possono essere visualizzate insieme alle quantità ottenute fino a quel momento.</p>
<p>Esempio:</p>
<p><b>ABBAU ×12 — Elio-3 10 t, rame 40 t</b></p>
<p>Le quantità sono i valori minerari personali del rispettivo comandante, che sono effettivamente documentati dagli eventi del diario.</p>
<p>Anche con un periodo attivo, le quantità minerarie personali rimangono quantità totali memorizzate. <b>Rame 40 t</b> non significa automaticamente <b>40 t nel periodo selezionato</b>. Il periodo richiede una visita corrispondente al sistema, ma non limita a quel periodo la quantità estratta visualizzata.</p>

<h3>Combina filtri</h3>
<p>Testo libero, limiti Dal/Al attivati e filtri minerari possono essere combinati. Un risultato deve soddisfare contemporaneamente le condizioni impostate.</p>
<p>Per esempio:</p>
<ul>
<li>Siti minerari planetari attivi</li>
<li>Almeno 20</li>
<li>I propri ritrovamenti minerari sono attivi</li>
<li>Rame materia prima</li>
</ul>
<p>cerca corpi conosciuti con almeno 20 siti minerari planetari dove il comandante in questione ha già estratto lui stesso il rame.</p>
<p>Viene considerato anche l’eventuale testo di ricerca aggiuntivo. Se viene aggiunto un periodo, il comandante visualizzato deve aver effettivamente visitato il sistema interessato in quel periodo; l’estrazione del rame non deve necessariamente essere avvenuta nello stesso periodo.</p>

<h3>Applica</h3>
<p>«Applica» esegue un filtraggio combinato con tutti i filtri di ricerca, periodo ed estrazione attualmente impostati:</p>
<ul>
<li>Testo libero</li>
<li>Dal, se attivato</li>
<li>Al, se attivato</li>
<li>Siti minerari planetari</li>
<li>Numero minimo</li>
<li>Le mie scoperte minerarie</li>
<li>Merce, se «Le mie scoperte minerarie» è attivato</li>
</ul>
<p>Invio nel campo di testo libero esegue esattamente lo stesso filtraggio. Senza testo libero e filtri minerari viene caricata la mappa normale per i comandanti selezionati sulla mappa, eventualmente limitata da Dal/Al.</p>

<h3>Reimposta</h3>
<p>«Reimposta» riporta l’area comune dei filtri allo stato iniziale:</p>
<ul>
<li>Il testo libero viene cancellato.</li>
<li>Dal e Al vengono disattivati; i campi data mostrano di nuovo la data odierna e sono disattivati.</li>
<li>Siti minerari planetari viene disattivato.</li>
<li>Il numero minimo viene impostato a 0.</li>
<li>Le mie scoperte minerarie viene disattivato.</li>
<li>Merce viene riportato su «Tutti».</li>
</ul>
<p>La selezione dei comandanti viene mantenuta. La cronaca normale viene quindi ricaricata per questa selezione della mappa; i risultati di ricerca precedenti e le visualizzazioni dei dettagli vengono reimpostati.</p>

<h3>Selezione del comandante</h3>
<p>La cronaca può visualizzare dati di vari comandanti famosi.</p>
<p>Esistono due concetti distinti di selezione:</p>
<ul>
<li><b>Selezione dei comandanti della mappa:</b> Le caselle dei comandanti determinano quali rotte dei comandanti vengono mostrate nella mappa normale senza ricerca testuale o mineraria. Un periodo attivato viene considerato.</li>
<li><b>Comandante visualizzato:</b> Le ricerche personali testuali o minerarie usano il comandante visualizzato (<code>viewed_commander_id</code>), in alternativa il comandante attivo. Anche gli elenchi personali delle merci dipendono da questo comandante.</li>
</ul>
<p>Tuttavia, le informazioni personali come i ritrovamenti minerari e gli elenchi delle materie prime vengono sempre valutate separatamente per il comandante effettivamente visualizzato.</p>
<p>Un comandante non vede nella sua selezione di materie prime scoperte minerarie che appartengono esclusivamente ad un altro comandante.</p>

<h3>Tutti i comandanti</h3>
<p>La visualizzazione della mappa/cronaca può prendere in considerazione più comandanti.</p>
<p>«Tutti i comandanti» riguarda la selezione dei comandanti della mappa. Le caselle dei comandanti non estendono automaticamente le ricerche personali testuali o minerarie a più comandanti.</p>
<p>Ciò non modifica l'assegnazione personale dei dati relativi al comandante. Le proprietà astronomiche globali di un sistema o di un corpo rimangono condivise, le scoperte personali rimangono separate.</p>

<h3>Aiuto per la ricerca/legenda</h3>
<p>Ulteriori informazioni sulla ricerca della cronaca e sul significato della visualizzazione sono accessibili tramite "Aiuto alla ricerca/legenda".</p>
<p>Un termine di ricerca selezionato con un clic viene inserito nel campo di ricerca ed eseguito insieme ai filtri di periodo ed estrazione già impostati.</p>
<p>Questa guida principale contestuale integra le brevi istruzioni per l'uso disponibili lì.</p>

<h3>Suggerimento</h3>
<p>La cronaca è particolarmente adatta per ritrovare luoghi interessanti scoperti durante un viaggio più lungo.</p>
<p>Per l’estrazione mineraria di superficie, ad esempio, può rispondere:</p>
<p>"Su quale pianeta ho mai estratto il rame?"</p>
<p>O:</p>
<p>"Quale dei pianeti che conosco ha un numero particolarmente elevato di siti minerari?"</p>""",
    ),
 'jump_tip': (
        'Analisi',
        """
<h2>Analisi</h2>
<p>L’analisi usa la tua cronologia personale di esplorazione. Analisi del sistema valuta un nome procedurale inserito; Dati storici conserva la precedente analisi dei codici con i riscontri passati e la rivalutazione. Sono strumenti decisionali, non garanzie di scoperte.</p>
<h3>Base di confronto</h3>
<p>Il codice di massa fornisce la stima di base. Regione e famiglia la affinano con cautela. I piccoli campioni locali vengono attenuati verso la base più ampia. Pochi dati significano incertezza, non una valutazione negativa. I sistemi studiati insufficientemente non contano come riscontri negativi.</p>
<h3>Indice di potenziale</h3>
<p>L’indice di potenziale 100 rappresenta la media storica personale del potenziale esplorativo attenuato. Non è una probabilità percentuale. Uno scenario di mappatura uniforme e valori estremi attenuati consentono il confronto; mediana e potenziale attenuato sono crediti stimati, non guadagni garantiti.</p>
<h3>Scoperte notevoli</h3>
<p>Il numero finale del sistema non viene valutato: Plio Aip KN-B d13-201 appartiene alla famiglia Plio Aip KN-B d13. BIO è informativo e non contribuisce alla valutazione principale. Le analisi mancanti non dimostrano valori nulli.</p>
<h3>Analisi del sistema</h3>
<p>Inserisci un sistema e scegli Analizza oppure premi Invio. Usa il sistema attuale prende il nome dallo stato di gioco esistente. Il ricalcolo avviene solo su azione dell’utente. Base di confronto e risultati indicano il livello; senza confronti locali si usa l’esperienza superiore. La qualità dei dati è separata dalla raccomandazione.</p>
<p>Il campo «Sistema» accetta un nome digitato liberamente. «Usa il sistema attuale» compila soltanto il campo; poi premi «Analizza» o Invio. Il nome viene verificato localmente rispetto al modello di denominazione procedurale supportato. Non sono presenti una ricerca del sistema online o un elenco per nomi ambigui.</p>
<p>Un campo vuoto, un nome non supportato, dati comparativi qualificati mancanti o un errore sostituiscono il risultato precedente con un messaggio. Un’analisi riuscita mostra raccomandazione, indice di potenziale e base dati locale. La tabella confronta codice di massa, regione e famiglia con numero di sistemi e base dati; seguono valori storici e ritrovamenti particolari noti.</p>
<h3>Dati storici</h3>
<p>Risultati storici per codice di sistema. Questi valori descrivono la tua esperienza di esplorazione passata e non sono una previsione diretta per un singolo sistema di destinazione. La base dati e l’attendibilità descrivono l’affidabilità dei confronti in base al campione disponibile e alla sua distribuzione tra i settori.</p>
<p>In «Dati storici», scegli in «Obiettivo» un tipo di ritrovamento, non una destinazione: per esempio un obiettivo esplorativo, un genere o una specie BIO. La prima valutazione avviene alla creazione della vista. Dopo aver cambiato obiettivo o minimo, la classifica precedente rimane fino a quando premi «Rivaluta».</p>
<p>Il campo numerico accanto alla selezione dell’obiettivo imposta il campione minimo per codice: da 1 a 50 sistemi esaminati, inizialmente 3. I codici con meno sistemi o senza ritrovamenti storici del tipo scelto sono esclusi dalla classifica.</p>
<p>La tabella «Schemi storici» mostra fino a 50 codici con posizione, successi passati (sistemi con ritrovamenti / sistemi esaminati), frequenza di successo e solidità dei dati. L’ordine segue la valutazione storica smussata, non soltanto la frequenza di successo. Entrambe le tabelle hanno un ordine fisso, senza ordinamento per colonna o azioni di dettaglio. In assenza di schemi adatti compare un messaggio; un errore di valutazione svuota la classifica e mostra un messaggio di errore. L’analisi non calcola un itinerario.</p>
""",
    ),
 'route_planner': ('Pianificatore di percorso',
                   """<h2>Pianificatore di percorso</h2>
<h3>Panoramica</h3>
<p>Il pianificatore calcola percorsi tra sistemi tramite Spansh. Scegli «Rotta della nave» o «Fleet Carrier / CTSVision». Serve una connessione di rete; CMDRHelper non pilota nave o carrier.</p>

<h3>Partenza e destinazione</h3>
<p>«Sistema di partenza» segue il sistema attuale noto del comandante attivo finché non inserisci una partenza diversa. Svuotando il campo ripristini questo comportamento. Inserisci il nome completo in «Sistema di destinazione»; una destinazione dai preferiti prepara la rotta della nave senza calcolarla.</p>
<p>Partenza e destinazione devono essere identificate senza ambiguità. Non vengono sostituite con nomi simili. Nomi sconosciuti o ambigui producono un messaggio: correggi la voce.</p>

<h3>Rotta della nave</h3>
<p>Non c’è un selettore di nave: i dati noti della nave attiva precompilano i campi tecnici. Le modifiche restano impostazioni manuali. «Applica dati della nave» riapplica i dati disponibili. Controlla l’indicazione di dati completi, incompleti, vecchi o FSD sconosciuto.</p>
<p>Controlla «Capacità serbatoio principale», «Carico attuale», «Massa base», «Capacità serbatoio di riserva», «Carburante di riserva», «Massa ottimale FSD», «Carburante FSD massimo per salto», «Potenza carburante», «Moltiplicatore carburante» e «Bonus portata». La capacità di salto deriva da questi valori; non c’è un singolo campo per la portata normale della nave. Carico ed equipaggiamento possono cambiare la portata effettiva.</p>

<h3>Opzioni della nave e calcolo</h3>
<p>«Algoritmo di rotta» offre optimistic, pessimistic, fuel, fuel_jumps e guided. La scelta viene inviata a Spansh.</p>
<p>Le opzioni sono «Usa supercarica/stelle di neutroni», «La nave parte già supercaricata», «Usa iniezioni FSD», «Escludi stelle secondarie» e «Rifornisci a ogni stella raccoglibile»: supporto neutronico, partenza già potenziata, iniezioni FSD, stelle secondarie e rifornimenti. Avvia con «Calcola rotta nave con Spansh».</p>

<h3>Rotta del carrier</h3>
<p>«Fleet Carrier / CTSVision» pianifica senza scegliere o controllare un carrier specifico. Inserisci «Tritio nel serbatoio» e «Tritio nel deposito della carrier», al massimo 25.000 t complessive. «Massa calcolata della carrier» mostra 25.000 t più entrambe le quantità.</p>
<p>«Portata massima di salto» va da 1 a 500 ly, con 500 ly predefiniti. «Calcola rotta con Spansh» avvia il calcolo. Il pulsante è disabilitato durante questa richiesta.</p>

<h3>Spansh e attesa</h3>
<p>Spansh calcola la rotta in background. Lo stato mostra la richiesta e poi esito positivo o errore. Si calcolano rotte, non prezzi commerciali o informazioni sulle stazioni. Questa vista non offre un pulsante per annullare un calcolo in corso.</p>

<h3>Risultato della rotta</h3>
<p>La lista mantiene l’ordine della rotta: numero, sistema, distanza del salto e distanza restante. Non è ordinabile liberamente. Le rotte nave aggiungono consumo, carburante residuo, neutroni e rifornimento; quelle carrier il consumo di trizio.</p>
<p>I totali mostrano distanza, numero di salti e consumo o trizio stimato. I dati mancanti restano «–». Confronta il piano con la situazione reale nel gioco.</p>

<h3>Avanzamento e prossima destinazione</h3>
<p>Una rotta nave calcolata correttamente viene adottata automaticamente. «Sistema attuale», «Prossima destinazione» e «Stato della rotta» mostrano posizione, prossimo passo e stato. La lista rimane, senza spunte aggiuntive per i passi completati.</p>
<p>Un salto nave riconosciuto al prossimo sistema o a uno successivo della rotta avanza il progresso e copia automaticamente il nome del sistema seguente negli appunti. Messaggi di posizione ripetuti e salti carrier non contano come questi avanzamenti.</p>
<p>Caricare la rotta non copia automaticamente un nome. Usa «Copia prossima destinazione» all’inizio o in seguito finché esiste una prossima destinazione. Viene copiato solo il nome del sistema: nessun incollaggio automatico o controllo di Elite.</p>

<h3>Deviazione e completamento</h3>
<p>Un salto fuori dalla rotta restante mostra «Il sistema attuale è fuori rotta». Rotta e precedente prossima destinazione restano disponibili, senza ricalcolo automatico. Un successivo salto corrispondente può riprendere il progresso. Puoi anche calcolare volontariamente una nuova rotta.</p>
<p>All’ultimo sistema appare «Rotta completata». «Prossima destinazione» diventa «–», il pulsante di copia è disabilitato e non viene copiato un altro nome. Gli appunti non vengono svuotati. La lista resta visibile.</p>

<h3>Esportazione CTSVision</h3>
<p>Solo la rotta carrier offre «Esporta per CTSVision». Dopo il calcolo scegli un nuovo file CSV. Contiene la sequenza e i dati disponibili di distanza, carburante, trizio e rifornimento per l’uso successivo in CTSVision.</p>
<p>È un’esportazione di file, non un collegamento diretto o controllo automatico del carrier. I file esistenti non vengono sovrascritti. Annullare il dialogo non crea file; gli errori di scrittura vengono segnalati.</p>

<h3>Errori e consigli</h3>
<p>Sistemi mancanti, parametri incompleti o non validi e trizio eccessivo vengono segnalati. I valori richiesti di serbatoio, massa e FSD devono essere positivi; la riserva non può superare la capacità del serbatoio di riserva.</p>
<p>Nessuna rotta trovata, problemi di rete, attesa eccessiva o risposta Spansh inutilizzabile producono un messaggio, mai un risultato inventato. Verifica nomi, dati nave e opzioni prima di ricalcolare.</p>

<h3>Analisi e comandante</h3>
<p>«Analisi», con «Analisi del sistema» e «Dati storici», valuta sistemi ed esperienze disponibili. Il pianificatore calcola il percorso concreto tra partenza e destinazione.</p>
<p>Le impostazioni iniziali usano il comandante attivo e la sua nave. Visualizzare un altro comandante nella vista CMDR non cambia questa base.</p>"""),
 'images': ('Immagini',
            '<h2>Immagini</h2>\n'
            '<p>La sezione “Immagini” gestisce gli screenshot realizzati con Elite Dangerous. '
            'CMDRHelper può riconoscere automaticamente le nuove registrazioni, elaborarle e '
            'memorizzarle in una galleria basata sul comandante.</p>\n'
            '\n'
            '<h3>Cartella di origine</h3>\n'
            '<p>La cartella di origine è la cartella in cui Elite Dangerous salva i suoi '
            'screenshot in formato BMP.</p>\n'
            '<p>CMDRHelper può monitorare questa cartella per nuovi file BMP. Affinché '
            "l'elaborazione automatica funzioni, è necessario impostare la cartella degli "
            'screenshot corretta.</p>\n'
            '\n'
            '<h3>Cartella di destinazione</h3>\n'
            '<p>La cartella di destinazione è la cartella principale comune per le immagini '
            'elaborate da CMDRHelper.</p>\n'
            "<p>L'utente imposta questa cartella principale. CMDRHelper crea automaticamente le "
            "sottocartelle relative al comandante richieste durante l'elaborazione.</p>\n"
            '\n'
            '<h3>Elaborazione automatica</h3>\n'
            '<p>Se "Converti automaticamente" è attivato e sono impostate cartelle di origine e '
            'destinazione valide, CMDRHelper controlla regolarmente la cartella di origine per '
            'nuovi screenshot BMP.</p>\n'
            '<p>Una volta attivati, i file BMP esistenti vengono inizialmente contrassegnati come '
            'conosciuti e non vengono convertiti automaticamente senza che venga richiesto. A '
            'questo scopo è disponibile la funzione separata per la conversione dei BMP '
            'esistenti.</p>\n'
            '<p>Un nuovo file non viene accodato finché non raggiunge la stessa dimensione diversa '
            "da zero in due controlli consecutivi. Di conseguenza, un'operazione di scrittura "
            'ancora in corso non viene elaborata immediatamente.</p>\n'
            '\n'
            '<h3>Conversione di immagini</h3>\n'
            '<p>Come origine, CMDRHelper elabora i file BMP. È possibile selezionare “PNG” o “JPG” '
            'come formato di destinazione.</p>\n'
            '<p>I file JPG vengono salvati al livello di qualità 95. I file PNG vengono salvati in '
            'modo ottimizzato.</p>\n'
            '<p>Per impostazione predefinita, viene mantenuto il file BMP originale. Se è attivato '
            '"Elimina BMP dopo la conversione", il BMP di origine verrà eliminato solo dopo che '
            "l'immagine di destinazione sarà stata salvata con successo.</p>\n"
            '\n'
            "<h3>Illumina l'immagine</h3>\n"
            '<p>La luminosità viene regolata dallo 0 al 50% utilizzando un cursore e un campo '
            "numerico collegato. L'impostazione viene salvata.</p>\n"
            '<p>Viene applicato automaticamente durante ogni conversione avviata successivamente, '
            'sia per i file BMP esistenti appena monitorati che per quelli avviati manualmente. Lo '
            '0% riprende la luminosità originale; valori più alti aumentano di conseguenza la '
            "luminosità dell'immagine PNG o JPG generata.</p>\n"
            '<p>La funzione non è una pura anteprima e non viene successivamente applicata ad '
            "un'immagine selezionata nella gallery. La luminosità modificata viene salvata nel "
            'nuovo file di destinazione.</p>\n'
            '<p>Il BMP sorgente rimane invariato a meno che non venga attivata anche la '
            'cancellazione del file BMP. Diario, comandante e dati di esplorazione non vengono '
            'modificati.</p>\n'
            '\n'
            '<h3>Spazio di archiviazione relativo al comandante</h3>\n'
            "<p>I nuovi screenshot vengono assegnati al comandante in gioco in base all'identità "
            "del diario presente nell'AppState live attivo.</p>\n"
            "<p>La struttura delle cartelle contiene il nome del comandante e l'ID Frontier, ad "
            'esempio:</p>\n'
            '<p><b>EXAMPLE_F12345678/</b></p>\n'
            '<p>Lo FID mantiene chiari i compiti anche con più comandanti. Ciò consente di '
            'distinguere due comandanti con lo stesso nome.</p>\n'
            '\n'
            '<h3>nomi di file</h3>\n'
            "<p>Le nuove immagini elaborate ricevono un nome con l'ora di acquisizione, il nome "
            'del comandante e, se disponibile, il sistema stellare noto durante la coda.</p>\n'
            '<p>Esempio:</p>\n'
            '<p><b>2026-09-04_13-18-22_EXAMPLE_Sol.png</b></p>\n'
            '<p>Lo FID si trova nel nome della cartella relativa al comandante, non ancora nel '
            'nome del file immagine.</p>\n'
            '\n'
            '<h3>Nomi di file sicuri</h3>\n'
            '<p>CMDRHelper disinfetta i nomi del comandante e del sistema da utilizzare come '
            'componenti di file e cartelle.</p>\n'
            '<p>Il controllo illegale e i caratteri Windows vengono sostituiti, gli spazi bianchi '
            'vengono unificati, i punti problematici o gli spazi finali vengono rimossi e i nomi '
            'Windows riservati come CON o NUL vengono protetti.</p>\n'
            '\n'
            '<h3>Tempo di registrazione</h3>\n'
            "<p>Per la denominazione, CMDRHelper utilizza l'ora di modifica del file BMP "
            "riconosciuto stabile. Solo se questo non può essere letto verrà utilizzata l'ora "
            'corrente.</p>\n'
            '<p>Ciò significa che il nome dipende solitamente dal file sorgente e non dal '
            'successivo momento della conversione.</p>\n'
            '\n'
            '<h3>Più immagini nello stesso secondo</h3>\n'
            '<p>Se il nome del file desiderato esiste già o è riservato per una conversione in '
            'corso, CMDRHelper lo aggiunge '
            'continuamente<code>_2</code>,<code>_3</code>,<code>_4</code>e così via.</p>\n'
            '<p>Ciò significa che un altro screenshot con lo stesso timestamp non sovrascriverà '
            "un'immagine di destinazione esistente.</p>\n"
            '\n'
            "<h3>Cambio del comandante durante l'elaborazione</h3>\n"
            '<p>Commander, FID e il sistema vengono catturati insieme quando si mette in coda uno '
            'screenshot.</p>\n'
            "<p>Un successivo cambio di comandante non modifica l'assegnazione di questa immagine "
            'già in attesa. Ciò significa che uno screenshot di EXAMPLE non verrà successivamente '
            'scritto nella cartella di un altro comandante.</p>\n'
            '\n'
            '<h3>galleria</h3>\n'
            '<p>La galleria mostra i file PNG, JPG e JPEG dalle directory associate al filtro '
            'selezionato. Le immagini nuove, cancellate o spostate vengono rilevate '
            'regolarmente.</p>\n'
            '<p>Il filtro della raccolta non modifica la posizione di archiviazione o '
            "l'assegnazione del comandante dei file.</p>\n"
            '\n'
            '<h3>Attuale comandante</h3>\n'
            '<p>Il filtro Comandante corrente mostra le immagini dalla cartella del comandante '
            'attualmente visualizzato nella vista CMDR.</p>\n'
            '<p>Il comandante in questione determina solo la visualizzazione della galleria. '
            "D'altra parte, l'assegnazione di un nuovo screenshot live utilizza l'identità del "
            "journal attiva durante l'accodamento.</p>\n"
            '\n'
            '<h3>Tutti i comandanti</h3>\n'
            '<p>Il filtro "Tutti i comandanti" mostra insieme le immagini delle sottocartelle '
            'valide di tutti i comandanti conosciuti. Viene presa in considerazione anche la '
            'cartella speciale per le registrazioni senza identità riconosciuta.</p>\n'
            '<p>I file non vengono spostati o uniti.</p>\n'
            '\n'
            '<h3>Non assegnato</h3>\n'
            '<p>Il filtro Non assegnati mostra i file di immagine supportati che si trovano '
            'direttamente nella cartella principale di destinazione condivisa.</p>\n'
            '<p>In particolare, le immagini più vecchie senza sottocartelle relative al comandante '
            'rimangono visibili. CMDRHelper non cerca di indovinare la loro affiliazione a '
            'posteriori.</p>\n'
            '\n'
            '<h3>Immagini esistenti</h3>\n'
            '<p>Le immagini già esistenti nella cartella principale non vengono spostate o '
            'rinominate automaticamente.</p>\n'
            '<p>Rimangono accessibili tramite "Non assegnato" purché siano disponibili come PNG, '
            'JPG o JPEG.</p>\n'
            '\n'
            "<h3>Seleziona e visualizza l'immagine</h3>\n"
            "<p>Un semplice clic su un'immagine di anteprima mostra l'immagine ridimensionata "
            "nell'area di anteprima e visualizza il nome del file.</p>\n"
            "<p>Un doppio clic apre il file con l'applicazione del sistema operativo impostata per "
            'le immagini.</p>\n'
            '<p>È possibile contrassegnare più immagini contemporaneamente. Quando si modifica la '
            "dimensione della finestra, l'anteprima dell'immagine corrente viene ridimensionata "
            'per adattarsi.</p>\n'
            '\n'
            '<h3>Elimina immagine</h3>\n'
            '<p>Le immagini contrassegnate possono essere eliminate utilizzando “Elimina '
            "selezionati” o il tasto Elimina. Prima dell'eliminazione viene visualizzata una "
            'domanda di sicurezza; Senza una selezione, viene prima evidenziata la selezione '
            'necessaria.</p>\n'
            '<p>Solo i file di destinazione PNG/JPG/JPEG selezionati vengono eliminati dalle '
            'directory del filtro galleria corrente. Il file sorgente BMP originale non è '
            'interessato.</p>\n'
            '\n'
            '<h3>Apri la cartella di destinazione</h3>\n'
            '<p>"Apri cartella di destinazione" apre la posizione di archiviazione nel file '
            'manager e, se necessario, crea la cartella principale condivisa.</p>\n'
            '<p>Il filtro "Comandante corrente" apre la sottocartella Commander esistente. Se non '
            'esiste ancora o è attivo un altro filtro, verrà aperta la cartella radice '
            'condivisa.</p>\n'
            '\n'
            '<h3>Sicurezza dei percorsi delle immagini</h3>\n'
            "<p>Prima dell'eliminazione, CMDRHelper controlla il percorso canonico di ciascun "
            "file. Deve trovarsi all'interno della cartella di destinazione configurata e "
            'direttamente in una directory consentita dal filtro della galleria corrente.</p>\n'
            '<p>I collegamenti simbolici non vengono utilizzati come cartelle Commander o immagini '
            'della galleria e non vengono eliminati tramite la galleria. I percorsi esterni '
            "all'area di destinazione e i percorsi trasversali vengono rifiutati.</p>\n"
            '\n'
            '<h3>Se non è stato rilevato alcun comandante</h3>\n'
            '<p>Se Commander e FID mancano quando si mette in coda una nuova registrazione, il '
            'file non verrà messo in attesa e non verrà assegnato a un Commander noto.</p>\n'
            '<p>Sarà nella sottocartella<b>SCONOSCIUTO_SCONOSCIUTO/</b>elaborato; il nome del file '
            'utilizzato anche per il Commander<b>SCONOSCIUTO</b>. Questa cartella può essere '
            'visualizzata tramite Tutti i Commander, non tramite il filtro Cartella radice non '
            'allocata.</p>\n'
            '\n'
            '<h3>Diversi comandanti</h3>\n'
            '<p>Alla gestione delle immagini si applicano due regole separate:</p>\n'
            '<ul>\n'
            "<li><b>Salva nuove immagini:</b>L'identità del journal attivo con Commander e FID "
            'quando accodati determina la cartella di destinazione.</li>\n'
            '<li><b>Visualizza le immagini:</b>Il comandante visualizzato o il filtro della '
            'galleria selezionato determina le immagini visibili.</li>\n'
            '</ul>\n'
            '<p>Ciò significa che mentre si gioca a EXAMPLE è possibile visualizzare la gallery di '
            'un altro comandante senza che nuovi screenshot finiscano nella cartella del '
            'comandante in questione.</p>\n'
            '\n'
            '<h3>Mancia</h3>\n'
            '<p>È sufficiente una cartella principale degli screenshot condivisa. CMDRHelper '
            'separa automaticamente le immagini appena elaborate in Commander e FID.</p>\n'
            '<p>Con "Comandante corrente", "Tutti i comandanti" e "Non assegnato" puoi passare '
            'dalla galleria personale, alle sottocartelle di tutti i comandanti e alle immagini '
            'più vecchie nella cartella principale.</p>\n'
            "<p>Una luminosità più elevata può aiutare con le foto scure; influisce sull'immagine "
            'di destinazione appena creata durante la conversione.</p>'),
 'commander_view': (
        'Vista CMDR',
        """<h2>Vista CMDR</h2>
<h3>Scegliere il comandante</h3>
<p>Il selettore in alto stabilisce di chi visualizzi i dati salvati. ● Live attivo indica il comandante attivo del diario; Solo visualizzazione un altro profilo salvato. La scelta non cambia il comandante attivo del diario: la pagina principale «Missioni e ricompense» usa sempre quello che sta realmente giocando. I dati personali restano separati tramite FID, anche con nomi identici. La consultazione non avvia invii online.</p>

<h3>Panoramica, patrimonio e MercCoins</h3>
<p>«Panoramica» mostra nome, FID, stato, prima e ultima registrazione, sistemi visitati, scoperte biologiche/geologiche, voci Codex e vendite cartografiche, posizione, missioni aperte, nave, carrier e dati biologici/cartografici invenduti con stime note. «Patrimonio» è l’ultimo saldo crediti salvato. «Mercenary credits» riporta i valori di Frontier: «Current», «Total spent», «Engineering», «Gear» e «Reported by Frontier: total earned». I contatori non devono necessariamente coincidere aritmeticamente; CMDRHelper non li corregge e non inventa una cronologia delle transazioni. I valori sconosciuti restano «–».</p>

<h3>Missioni ed esplorazione</h3>
<p>«Missioni» mostra le missioni aperte salvate del comandante visualizzato, con stato, nome, destinazione, scadenza e ricompensa. La tabella serve alla consultazione, senza dettagli o azioni di missione come nella pagina principale. «Esplorazione» mostra dati biologici/cartografici invenduti, scoperte biologiche, primi passi, corpi mappati personalmente o con efficienza e sistemi visitati. «Cronaca» è qui un segnaposto; la cronaca completa si apre dal menu principale.</p>

<h3>Flotta e dettagli delle navi</h3>
<p>«Navi» mostra in alto la nave attuale o usata per ultima, seguita dalla flotta salvata del comandante. Fai clic sull’intestazione di una scheda per espandere i dettagli. Ordina in senso crescente o decrescente per utilizzo, nome, tipo, portata di salto, capacità di carico, massa a vuoto, posizione o data; filtra tutte le navi o quelle con hangar per veicoli/caccia. Il verde indica la nave attiva in tempo reale; gli altri colori raggruppano posizioni note. I dettagli includono identificativo, ShipID, posizione, date, FSD/booster Guardian, portata, massa, capacità di carico/carburante e stato dell’equipaggiamento (completo, incompleto o datato). I moduli noti aggiungono hangar, scudi e rinforzi, armi e cabine passeggeri. I dati mancanti restano «–».</p>

<h3>Il proprio fleet carrier</h3>
<p>«Fleet Carrier personale» mostra nome, nominativo, CarrierID, ultima posizione e ultimo aggiornamento del proprio carrier salvato. Non sono offerte commerciali né scorte minerarie.</p>

<h3>Immagini personali di navi e carrier</h3>
<p>Usa «Scegli immagine della nave…» nei dettagli espansi o «Seleziona immagine della Fleet Carrier…» per il carrier. Sono supportati PNG, JPG/JPEG e WEBP. CMDRHelper conserva una propria copia locale, separata per comandante e nave o carrier, anche dopo il riavvio. Una nuova scelta sostituisce questa copia. «Rimuovi immagine personale» rimuove copia e associazione; il file originale resta intatto. Senza immagine personale appare un’anteprima standard disponibile o un segnaposto. La scelta dell’immagine è disabilitata se il carrier non è identificato in modo univoco. Le schermate non vengono associate automaticamente.</p>

<h3>Visualizzatore immagini</h3>
<p>Un doppio clic su un’immagine disponibile di nave o carrier apre il visualizzatore separato usando il file immagine, non solo la miniatura. L’immagine si adatta proporzionalmente alla finestra. Puoi ingrandire o massimizzare la finestra e chiuderla con Esc o il pulsante di chiusura. Non ci sono navigazione tra immagini o comandi di zoom. La sezione principale «Immagini» gestisce invece le schermate.</p>

<h3>Eliminare una nave</h3>
<p>«Elimina nave…» richiede conferma esplicita; Annulla è preselezionato. Rimuove la registrazione locale, i dati di equipaggiamento salvati e la copia dell’immagine personale. La nave attuale o usata per ultima e quella identificata come attiva in tempo reale sono protette; l’eliminazione è bloccata durante la rilettura. Un contrassegno locale impedisce la ricomparsa immediata dai vecchi diari. Una nuova segnalazione inequivocabile della nave come attiva nel diario in tempo reale, successiva all’eliminazione, può ripristinarla. Anche la rilettura confermata può rimuovere il contrassegno. La copia dell’immagine eliminata non viene ripristinata.</p>

<h3>Rileggere tutte le navi</h3>
<p>«Rileggi tutte le navi…» serve a recuperare informazioni sulla flotta dai diari esistenti o ritrovare navi eliminate localmente. Dopo conferma, i file noti e quelli nella cartella diari configurata vengono riletti per il comandante visualizzato, solo per la flotta. Elite non deve essere in esecuzione. I dati salvati più recenti e le navi assenti dai diari disponibili vengono conservati; le vendite riconosciute sono considerate. Se l’operazione riesce, vengono rimossi i contrassegni di eliminazione manuale di quel comandante. Le immagini personali esistenti restano, quelle eliminate non tornano. Gli altri comandanti non sono interessati. Se lettura o applicazione falliscono, i contrassegni restano: controlla l’accesso ai diari e riprova.</p>

<h3>Dati locali e sicurezza</h3>
<p>I dati salvati sono consultabili offline e dopo un riavvio; rappresentano l’ultimo stato noto. Immagini, eliminazione e rilettura riguardano soltanto CMDRHelper. Non modificano navi, carrier o crediti in Elite Dangerous e non riscrivono i diari.</p>""",
    ),
 'settings': ('Impostazioni',
              '<h2>Impostazioni</h2>\n<h3>CMDRHelper</h3>\n<p>Informazioni di aggiornamento migliori: la finestra Sì/No mostra versione installata e disponibile e fino a sei novità, se esiste un riepilogo. Gli elenchi lunghi scorrono e le azioni restano accessibili.</p>\n'
              '<p>L\'area "Impostazioni" determina il modo in cui CMDRHelper funziona con Elite '
              'Dangerous, file journal, database, servizi online, interfaccia e '
              'aggiornamenti.</p>\n'
              '<p>Le modifiche alle credenziali e ai percorsi devono essere apportate con '
              'attenzione. Se necessario, le impostazioni relative al comandante vengono gestite '
              "separatamente dall'ID Frontier.</p>\n"
              '\n'
              '<h3>diario</h3>\n'
              '<p>La cartella del diario è una delle impostazioni più importanti. Deve puntare '
              'alla cartella in cui si trova Elite Dangerous<code>Diario*.log</code>file del '
              'profilo Windows o Proton utilizzato.</p>\n'
              '<p>Le riviste forniscono, tra le altre cose:</p>\n'
              '<ul>\n'
              '<li>Identità, posizione e viaggio del comandante</li>\n'
              '<li>Missioni, navi e risorse</li>\n'
              '<li>Esplorazione, cartografia e dati BIO</li>\n'
              '<li>Estrazione di superficie, monete mercenarie e altri stati supportati</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Visualizzazione e funzionamento del giornale</h3>\n'
              '<p>Il gruppo di diari mostra il set di cartelle, il numero di diari trovati, i '
              "diari più vecchi e quelli più nuovi, il nome del file più recente e l'ora "
              "dell'ultima voce letta.</p>\n"
              '<p>"Seleziona cartella diario" cambia la cartella. "Leggi ora" attiva '
              'immediatamente il normale aggiornamento.</p>\n'
              '<p>Le sessioni chiaramente identificabili vengono assegnate utilizzando FID. Le '
              'nuove voci complete vengono elaborate in modo incrementale; Posizioni di lettura '
              'sicure impediscono che ogni diario venga riletto inutilmente nella sua interezza al '
              'successivo avvio.</p>\n'
              '\n'
              '<h3>banca dati</h3>\n'
              '<p>CMDRHelper memorizza in modo permanente i dati richiesti in un database SQLite '
              'locale. Ciò include i dati globali del sistema e del corpo, nonché le informazioni '
              'esplicitamente assegnate a un comandante.</p>\n'
              '<p>La pagina delle impostazioni mostra le statistiche sui dati salvati. Il database '
              'non deve essere modificato manualmente mentre CMDRHelper è in esecuzione.</p>\n'
              '\n'
              "<h3>Importa l'archivio del diario</h3>\n"
              '<p>“Importa archivio diario” confronta completamente i file di diario della '
              'cartella di diario impostata con il database. Le aree del giornale già note vengono '
              'prese in considerazione in base alle informazioni di importazione salvate e non '
              'vengono duplicate ciecamente come nuovi dati.</p>\n'
              "<p>Durante un'importazione visibile manualmente vengono visualizzati lo stato di "
              'avanzamento, il numero e il file attualmente elaborato. Al termine, CMDRHelper '
              'segnala dati importati o già noti oppure un errore.</p>\n'
              "<p>L'importazione dell'archivio serve anche a riapprendere le informazioni storiche "
              'supportate da riviste chiaramente assegnate.</p>\n'
              '\n'
              '<h3>Dati relativi al comandante</h3>\n'
              "<p>CMDRHelper separa le informazioni personali in base allo FID e all'ID comandante "
              'interno associato. Questi includono, ma non sono limitati a, missioni, risorse, '
              'MercCoins, esplorazione personale e accesso online.</p>\n'
              '<p>Una sessione del diario sconosciuta o ambigua non può essere assegnata '
              'arbitrariamente a un comandante.</p>\n'
              '\n'
              '<h3>Servizi in linea</h3>\n'
              '<p>CMDRHelper supporta EDSM e Inara. Entrambi gli accessi vengono elaborati e '
              'salvati separatamente per ciascun comandante conosciuto o ciascun FID.</p>\n'
              '<p>La selezione nelle impostazioni determina solo quale accesso è attualmente in '
              'fase di modifica o test. Solo il comandante chiaramente identificato dalla sessione '
              'del diario attiva è autorizzato a inviare in diretta.</p>\n'
              '\n'
              '<h3>Informazioni sulle stazioni Spansh</h3>\n'
              '<p>In «SERVIZI ONLINE», «Aggiungi informazioni sulle stazioni da Spansh» attiva l’integrazione facoltativa di stazioni e strutture nell’Explorer e nelle viste sistema. Inizialmente è disattivata. Viene inviato solo l’identificativo pubblico del sistema, non informazioni sul comandante; non serve una chiave API personale. L’opzione non controlla le ricerche dei mercati commerciali.</p>\n'
              '<p>Se disattivata, sono mostrate solo informazioni locali del diario e non partono nuove richieste di stazioni Spansh; anche l’aggiornamento manuale è disabilitato. La cache esistente non viene eliminata, ma non integra la vista. Riattivare l’opzione rende nuovamente disponibili i dati in cache senza avviare da sola una richiesta di rete.</p>\n'
              '\n'
              '<h3>Richieste automatiche e cache delle stazioni</h3>\n'
              '<p>Il controllo automatico avviene solo a un nuovo ingresso dal vivo del comandante attivo del diario in un altro sistema, ad esempio dopo un salto della nave, del carrier o una nuova posizione confermata. Avvio, cambio di comandante, importazione di archivi e semplice apertura dell’Explorer o di una vista sistema non avviano richieste automatiche.</p>\n'
              '<p>La cache separata delle stazioni sopravvive ai riavvii di Helper. Un recupero di meno di 7 giorni fa è considerato recente ed evita una nuova richiesta automatica. Dati mancanti o più vecchi possono essere aggiornati al successivo ingresso dal vivo idoneo. È previsto al massimo un tentativo automatico per sistema e giorno del calendario locale; contano anche gli errori, persino dopo un riavvio. Non esiste un aggiornamento continuo in background di tutti i sistemi salvati. I vecchi dati utilizzabili in cache possono restare visibili anche senza connessione.</p>\n'
              '<p>Questa cache contiene informazioni aggiuntive sulle stazioni, non prezzi dei mercati commerciali. I dati comunitari Spansh per vendita, acquisto e raccomandazioni hanno una propria cache di ricerca temporanea in RAM. Le istantanee commerciali osservate personalmente in Elite sono salvate separatamente: sopravvivono al riavvio, ma sono valide solo se più recenti di 24 ore.</p>\n'
              '\n'
              '<h3>Aggiornare manualmente le stazioni</h3>\n'
              '<p>Apri «Vista completa» e scegli «Aggiorna dati Spansh». Vengono aggiornate solo le informazioni sulle stazioni Spansh del sistema mostrato nella finestra, non tutti i sistemi salvati né i prezzi dei mercati. L’opzione deve essere attiva; durante una richiesta per quel sistema l’azione è disabilitata.</p>\n'
              '<p>L’azione manuale può ignorare il periodo di 7 giorni e un tentativo automatico fallito quel giorno. Se il sistema è già stato recuperato con successo oggi secondo il calendario locale, non viene inviata un’altra richiesta: «I dati Spansh sono già stati aggiornati oggi.» Un recupero riuscito rinnova la cache. In caso di errore restano i dati locali e quelli utilizzabili in cache; la riga di stato segnala l’errore. Un tentativo manuale fallito può essere ripetuto.</p>\n'
              '\n'
              '<h3>EDSM accesso per</h3>\n'
              '<p>“EDSM accesso per:” seleziona il comandante da modificare. La selezione mostrerà '
              '"impostato" o "non impostato" a seconda che sia memorizzato uno API-Key.</p>\n'
              '<p>Sono visibili il nome del comandante, il campo API-Key nascosto, "Usa EDSM", un '
              'test di connessione e il suo ultimo stato di test.</p>\n'
              '<p>Ogni comandante necessita del proprio accesso EDSM appropriato. La selezione non '
              "sposta l'uploader live su questo comandante.</p>\n"
              '\n'
              '<h3>Utilizzare e testare EDSM</h3>\n'
              '<p>"Utilizza EDSM" abilita o disabilita il servizio per lo FID selezionato. Le '
              "credenziali mancanti o disattivate non influiscono sull'elaborazione del journal "
              'locale.</p>\n'
              '<p>“Test connessione EDSM” verifica i dati di accesso attualmente visibili nel '
              'form. Un test riuscito conferma la connessione, ma non modifica il giornale attivo '
              'FID o il Live Commander.</p>\n'
              '\n'
              '<h3>Inara accesso per</h3>\n'
              '<p>"Inara Accesso per:" segue lo stesso principio multi-CMDR. L\'attivazione, il '
              'nome del comandante Inara e API-Key vengono salvati separatamente per ogni '
              'FID.</p>\n'
              '<p>Anche in questo caso la selezione indica “impostato” o “non impostato”. Una '
              'chiave di un comandante non viene utilizzata automaticamente per un altro '
              'comandante.</p>\n'
              '\n'
              '<h3>Utilizzare e testare Inara</h3>\n'
              '<p>Con Inara configurato e abilitato per il diario attivo FID, CMDRHelper può '
              'trasmettere gli eventi di viaggio, posizione, missione e nave supportati. Non tutti '
              'gli eventi del diario vengono inviati a Inara.</p>\n'
              '<p>"Test connessione Inara" controlla i dati di accesso attualmente visibili senza '
              'modificare il Live Commander.</p>\n'
              '\n'
              '<h3>Posta in uscita Inara</h3>\n'
              '<p>Gli eventi Inara supportati vengono contrassegnati in modo persistente in una '
              'casella di posta in uscita prima della trasmissione in rete.</p>\n'
              '<p>Gli errori temporanei consentono di conservare queste voci per tentativi '
              'successivi. Il lavoratore elabora solo la posta in uscita del giornale attivo in '
              'modo univoco FID; Le voci di altri comandanti non sono incluse.</p>\n'
              '\n'
              "<h3>Stato online nell'intestazione</h3>\n"
              '<p>EDSM attualmente mostra:</p>\n'
              '<ul>\n'
              '<li><b>EDSM</b>– non può essere utilizzato o disattivato per lo FID attivo</li>\n'
              '<li><b>EDSM sta aspettando</b>– impostato e senza trasmissione in corso</li>\n'
              "<li><b>Trasmissione EDSM</b>– l'ultimo ciclo di lavorazione EDSM si è concluso "
              'senza errori; La descrizione comando indica se gli eventi sono stati inviati, i '
              'dati del journal sono stati elaborati o se non sono stati trovati nuovi dati</li>\n'
              "<li><b>Errore EDSM</b>– l'ultimo stato di trasmissione non è corretto</li>\n"
              '</ul>\n'
              '<p>Al momento non esiste uno stato aggiuntivo etichettato separatamente "EDSM '
              'attivo" per EDSM.</p>\n'
              '<p>Inara distingue più precisamente:</p>\n'
              '<ul>\n'
              '<li><b>INARA fuori</b>– disabilitato per il giornale attivo FID</li>\n'
              '<li><b>INARA pronta</b>– impostato, ma ancora senza trasmissione confermata in '
              'questa sessione</li>\n'
              '<li><b>Trasmissione INARA</b>– il lavoratore sta attualmente inviando</li>\n'
              "<li><b>INARA attiva</b>– l'ultimo trasferimento effettivo è stato confermato con "
              'successo</li>\n'
              "<li><b>Errore INARA</b>– l'ultimo tentativo di trasferimento non è riuscito</li>\n"
              '</ul>\n'
              '\n'
              '<h3>Sicurezza API-Key</h3>\n'
              '<p>Le API-Key sono credenziali personali. I campi di input sono nascosti; Sono '
              "memorizzati in relazione al comandante nelle impostazioni dell'applicazione e non "
              'nel database CMDRHelper.</p>\n'
              '<p>Le chiavi non devono essere pubblicate, condivise in screenshot o aggiunte a '
              'repository pubblici.</p>\n'
              '\n'
              '<h3>Immagini/Screenshot</h3>\n'
              '<p>Cartella di origine, Cartella di destinazione, PNG/JPG, Elaborazione automatica, '
              'Eliminazione BMP e Schiarimento da 0 a 50% si trovano esclusivamente nel menu '
              'Immagini principale, non nella pagina Impostazioni.</p>\n'
              '<p>La guida sensibile al contesto "Immagini" descrive queste opzioni in '
              'dettaglio.</p>\n'
              '\n'
              '<h3>superficie</h3>\n'
              "<p>Il gruppo di interfacce include l'aspetto, la lingua, il carattere, la "
              'dimensione del carattere e la soglia del valore per i preziosi corpi degli '
              'esploratori.</p>\n'
              '\n'
              '<h3>Modalità buio e luce</h3>\n'
              "<p>Puoi passare direttamente dall'aspetto scuro a quello chiaro. Il tema viene "
              "immediatamente applicato all'interfaccia, al sistema esistente e alle schede della "
              'cronologia e salvato.</p>\n'
              '\n'
              '<h3>Lingua</h3>\n'
              "<p>L'interfaccia offre dodici lingue tra cui scegliere. “Salva lingua” salva la "
              'selezione; Per una conversione completamente uniforme dei widget esistenti è quindi '
              'necessario un riavvio di CMDRHelper.</p>\n'
              '\n'
              '<h3>Carattere e dimensione del carattere</h3>\n'
              '<p>È possibile selezionare e salvare la famiglia di caratteri e la dimensione del '
              'carattere da 7 a 24 pt.</p>\n'
              "<p>Entrambe le modifiche avranno pieno effetto solo dopo un riavvio. L'interfaccia "
              'lo indica esplicitamente.</p>\n'
              '\n'
              '<h3>Soglia di valore</h3>\n'
              '<p>La soglia del valore Explorer determina la stima del valore del credito da cui '
              'gli enti vengono evidenziati come particolarmente pregiati. La modifica viene '
              'salvata immediatamente e aggiorna la visualizzazione Explorer corrispondente.</p>\n'
              '\n'
              '<h3>Nascondi automaticamente</h3>\n'
              '<p>"Corpi preziosi" e "Reperti BIO" si trovano saldamente nella barra laterale '
              'sinistra, non nella pagina Impostazioni.</p>\n'
              '<p>Gli interruttori vengono salvati e controllano le piccole finestre di '
              "suggerimento live supportate durante l'esplorazione. La soglia del valore per gli "
              "Enti di valore è impostata nelle impostazioni dell'interfaccia.</p>\n"
              '\n'
              '<p>La finestra Cargo utilizza esclusivamente lo snapshot Cargo confermato per la FID attiva del Journal. Il commander visualizzato in CMDR View e viewed_commander_id non influiscono su questa finestra live. Per uno Ship mostra occupato / massimo · libero; se CargoCapacity è sconosciuta, non viene stimato alcun valore.</p>\n'
              '<p>«HUD stato EDSM» in «mostra automaticamente» è DISATTIVATO per impostazione predefinita. All’ingresso in un sistema compare un messaggio sopra Elite per circa 2,5 secondi. Più eventi Location nello stesso soggiorno non producono duplicati; un vero ritorno può essere verificato nuovamente.</p>\n<p>«EDSM: CONOSCIUTO» indica una corrispondenza EDSM valida per il sistema. «EDSM: SCONOSCIUTO» indica una risposta EDSM valida senza corrispondenza. «EDSM: NESSUNA RISPOSTA» indica un errore di rete, HTTP, timeout o una risposta non valida, mai un’assenza confermata di corrispondenza. La presenza in EDSM non equivale a una scoperta ufficiale in Elite; non vengono promessi nomi di primi scopritori o segnalatori.</p>\n<p>Il messaggio funziona indipendentemente dagli HUD di navigazione e carico. Le indicazioni permanenti e i messaggi del preferito rapido restano disponibili. La richiesta non blocca l’interfaccia; le risposte tardive per sistemi già lasciati vengono scartate.</p>\n\n'
              '<h3>Aggiornamenti</h3>\n'
              '<p>Il gruppo di aggiornamento mostra la versione installata e lo stato di GitHub. '
              'Controlla ora controlla manualmente la presenza di una nuova versione CMDRHelper '
              'pianificata; Inoltre dopo la partenza viene effettuato un controllo automatico '
              'ritardato.</p>\n'
              '<p>Se è disponibile una nuova versione, CMDRHelper chiederà prima di scaricarla e '
              'installarla. Un aggiornamento del database annunciato viene mostrato separatamente '
              'in questa finestra di dialogo.</p>\n'
              '<p>Per le installazioni esistenti normalmente basta: installare l’aggiornamento → avviare CMDRHelper. Le correzioni storiche necessarie per dati BIO, visite e metadati DSS sono automatiche; prima delle riparazioni che scrivono dati viene creata una copia di sicurezza del database. Le riparazioni sono versionate e idempotenti: le revisioni riuscite non vengono rieseguite integralmente a ogni avvio. La ricostruzione richiede journal Elite ancora presenti, leggibili e attribuibili senza ambiguità a un commander. Le fonti mancanti non vengono inventate né considerate un successo; le riparazioni pendenti vengono ritentate all’avvio successivo. Normalmente non servono eliminazione del database, script manuali o reimportazione.</p>\n\n'
              '<h3>Scarica i progressi</h3>\n'
              '<p>Il download viene eseguito in background. Se la dimensione totale è nota, '
              'CMDRHelper mostra il nome del file, i MiB ricevuti e totali, la percentuale, la '
              'velocità di trasferimento e il tempo rimanente stimato.</p>\n'
              '<p>Senza una dimensione totale nota, la barra di avanzamento funziona in modalità '
              'occupato e continua a mostrare la quantità di dati ricevuti e, se determinabile, la '
              "velocità. Prima dell'installazione, viene controllato lo ZIP scaricato.</p>\n"
              '\n'
              '<h3>Annulla aggiornamento</h3>\n'
              '<p>"Annulla download" termina un download in corso in modo controllato. Un download '
              'interrotto, incompleto o non valido non verrà installato.</p>\n'
              '\n'
              '<h3>Aggiornamento su Windows</h3>\n'
              '<p>Su Windows, il processo di aggiornamento vero e proprio continua '
              'indipendentemente dalla console di avvio originale. Uno spegnimento della console '
              'non dovrebbe quindi interromperla involontariamente.</p>\n'
              "<p>Se si verifica un errore dopo l'inizio delle modifiche ai file, il backup di "
              'rollback esistente tenta di ripristinare la versione precedente.</p>\n'
              '\n'
              "<h3>Riavvia dopo l'aggiornamento</h3>\n"
              "<p>Al termine dell'installazione, l'aggiornamento CMDRHelper si riavvia tramite il "
              'percorso di avvio previsto e controlla brevemente se il nuovo processo funziona in '
              'modo stabile.</p>\n'
              '<p>Se una versione richiede un aggiornamento una tantum del database, anche '
              "l'archivio del journal verrà rivalutato dopo il riavvio.</p>\n"
              '\n'
              '<h3>Diversi comandanti</h3>\n'
              "<p><b>Selezione delle impostazioni = Di chi è l'accesso online che sto "
              'modificando?</b></p>\n'
              '<p><b>Active Journal-FID = Chi è autorizzato a trasmettere in diretta?</b></p>\n'
              "<p>Né la selezione dell'account online né la visualizzazione CMDR sono consentite "
              'per trasformare un uploader dal vivo in un comandante di sola visualizzazione.</p>\n'
              '\n'
              '<h3>Aiuto</h3>\n'
              '<p>"? Aiuto" si trova nella barra laterale sinistra sopra "mostra automatica" e '
              "apre la guida dell'area del menu principale attualmente visibile.</p>\n"
              '<p>Nell\'area "Impostazioni", il pulsante apre direttamente la guida alle '
              'impostazioni.</p>\n'
              '\n'
              '<h3>Mancia</h3>\n'
              '<p>Se stai reinstallando o riscontri problemi, controlla prima:</p>\n'
              '<ul>\n'
              '<li>cartella del diario corretta e identità del comandante riconosciuta</li>\n'
              '<li>lingua, tema, carattere e soglia del valore di Explorer desiderati</li>\n'
              '<li>Accesso online allo FID corretto</li>\n'
              '<li>In caso di problemi con le immagini, cartelle di origine e di destinazione nel '
              'menu principale "Immagini".</li>\n'
              '</ul>\n'
              '<p>Se sono presenti più comandanti, prestare sempre attenzione a quale FID si '
              'riferiscono ai dati di accesso online visibili.</p>'),
    "planet_navigation": (
        'Navigazione planetaria',
        """<h2>Navigazione planetaria</h2>
<p>Il navigatore planetario serve esclusivamente a raggiungere una determinata latitudine/longitudine su un pianeta o una luna. Imposti un obiettivo tramite coordinate e ottieni la distanza e la direzione per raggiungerlo.</p>
<p>Non è un pianificatore di rotte interstellari e non gestisce la navigazione tra sistemi o i salti. Sei tu a pilotare la nave.</p>

<h3>Aprire il navigatore e inserire un obiettivo</h3>
<p>Apri «Navigazione planetaria» nell’Explorer e scegli «Inserimento manuale …». Puoi aprire la finestra e inserire una destinazione prima che sia disponibile una posizione attuale sulla superficie.</p>
<ul>
<li><b>Corpo celeste:</b> Seleziona il pianeta o la luna di destinazione dall’elenco oppure usa il corpo già rilevato. Puoi anche inserire il nome del corpo manualmente se non è ancora nell’elenco. In caso di dubbio, usa il nome completo, incluso il nome del sistema.</li>
<li><b>Latitudine:</b> Inserisci la latitudine dell’obiettivo tra −90° e +90°.</li>
<li><b>Longitudine:</b> Inserisci la longitudine dell’obiettivo tra −180° e +180°. Fai attenzione al segno di entrambe le coordinate.</li>
<li><b>Nome obiettivo:</b> Puoi inserire una descrizione facoltativa per riconoscere più facilmente l’obiettivo.</li>
</ul>
<p>Con «Imposta obiettivo» confermi i dati inseriti. Non devi inserire ID tecnici come BodyID e SystemAddress: non sono normali dati richiesti all’utente.</p>

<h3>Quando si attiva la bussola?</h3>
<p>Non appena è impostato un obiettivo ed Elite fornisce dati di posizione planetaria validi per il corpo corrispondente, la navigazione si attiva automaticamente. Non devi premere un pulsante di avvio separato.</p>
<p>Se questi dati mancano ancora o appartengono a un altro corpo, il navigatore attende mostrando «In attesa delle coordinate planetarie …». Puoi inserire un obiettivo anche prima di ricevere questi dati.</p>

<p>La navigazione attiva richiede coordinate, nome del corpo, orientamento e raggio planetario validi forniti da Elite per il corpo di destinazione. Non serve atterrare: i dati possono arrivare durante l’avvicinamento. Senza posizione valida o su un altro corpo, il navigatore attende senza inventare una posizione.</p>

<h3>Salvare la posizione attuale</h3>
<p>«★ Salva la posizione attuale» salva la posizione attuale confermata, non la destinazione inserita. Servono una posizione Elite valida, un comandante identificato e un sistema noto. Altrimenti l’azione è disabilitata o appare un avviso.</p>
<p>All’apertura vengono fissati sistema, corpo e coordinate. Nel dialogo dei preferiti puoi modificare nome, categoria e nota e associare un’immagine. Solo «Salva» salva localmente per quel comandante; annullare non salva nulla. Gli spostamenti successivi non cambiano la posizione fissata.</p>

<h3>Usare le posizioni salvate</h3>
<p>Apri «★ Preferiti» nell’Explorer. Seleziona un luogo di superficie e «◎ Alle coordinate» per usare corpo, coordinate e nome come destinazione. Sostituisce la destinazione precedente; su un altro corpo il navigatore attende dati di posizione corrispondenti.</p>
<p>«Modifica» modifica nome, categoria e nota. «Elimina» elimina il preferito dopo conferma, senza cancellare dati Elite. I preferiti sopravvivono ai riavvii e sono separati per comandante; la destinazione di navigazione attuale dura solo per la sessione.</p>

<h3>Globo planetario: oltre 380 km</h3>
<p>Quando la distanza dall’obiettivo è superiore a 380 km, il navigatore mostra il globo planetario.</p>
<ul>
<li>Il <b>cerchio bianco</b> indica la tua posizione.</li>
<li>Il <b>piccolo punto dell’obiettivo</b> è arancione quando l’obiettivo si trova sul lato visibile del pianeta.</li>
<li>Se l’obiettivo si trova sul lato posteriore nascosto, il punto viene mostrato in rosso.</li>
<li>La tua posizione rimane fissa nella rappresentazione. Il pianeta e l’obiettivo vengono rappresentati rispetto alla tua posizione e al tuo orientamento.</li>
</ul>
<p>La freccia bianca punta in avanti; quella gialla indica la direzione relativa dell’obiettivo. Il globo è un aiuto schematico all’orientamento, non una vista del terreno geograficamente precisa. Un punto rosso indica il lato posteriore del globo, non automaticamente «dietro la tua nave».</p>

<h3>Griglia prospettica: fino a 380 km inclusi</h3>
<p>A una distanza dall’obiettivo fino a 380 km inclusi, la visualizzazione passa automaticamente a una griglia prospettica inclinata. Se la distanza torna a superare 380 km, ricompare il globo.</p>
<p>Le linee trasversali formano una <b>griglia delle distanze a intervalli di 50 km</b>. Il punto dell’obiettivo viene disegnato nella griglia in base alla distanza e alla direzione relativa. La prospettiva ti aiuta a proseguire l’avvicinamento; l’inclinazione fa apparire gli intervalli più ravvicinati verso il fondo. Per la rotta effettiva da seguire, osserva anche la rotta obiettivo e la direzione relativa.</p>

<h3>Leggere correttamente i valori di navigazione</h3>
<ul>
<li><b>Distanza dall’obiettivo:</b> L’indicazione grande mostra la distanza residua dall’obiettivo lungo la superficie planetaria ideale.</li>
<li><b>Coordinate obiettivo:</b> La coppia di coordinate inserita per l’obiettivo, prima la latitudine e poi la longitudine. Rimane invariata mentre ti muovi.</li>
<li><b>Coordinate attuali:</b> La tua ultima coppia di coordinate confermata da Elite, sempre latitudine / longitudine.</li>
<li><b>Distanza sulla superficie:</b> La stessa distanza sulla superficie indicata come distanza dall’obiettivo, eventualmente arrotondata con maggiore precisione nella visualizzazione dettagliata. Non è un secondo percorso né una distanza spaziale diretta attraverso l’aria.</li>
<li><b>Rilevamento:</b> La direzione assoluta verso l’obiettivo dalla tua posizione attuale, espressa come angolo della bussola: 000° è nord, 090° est, 180° sud e 270° ovest.</li>
<li><b>Prua:</b> Il tuo orientamento attuale, come fornito da Elite. Indica dove sei rivolto e non deve necessariamente coincidere già con il rilevamento.</li>
<li><b>Direzione relativa:</b> La differenza tra il tuo orientamento e il rilevamento, ad esempio «23° a destra», «10° a sinistra» o «Dritto». A 180°, l’obiettivo è dietro di te.</li>
<li><b>Rotta obiettivo:</b> Il rilevamento evidenziato come rotta assoluta sulla quale puoi allinearti nell’HUD di Elite. Non è un ulteriore angolo di virata.</li>
</ul>
<p>Esempio: con prua 051° e rotta obiettivo 074°, vira di 23° a destra finché la bussola di Elite indica circa 074°. Proseguendo il volo, il rilevamento e la rotta obiettivo possono cambiare: segui i valori aggiornati.</p>
<p>Nella stessa posizione dell’obiettivo, a un polo o nel punto esattamente opposto sul pianeta, la direzione può essere indefinita. Il navigatore mostra allora l’avviso corrispondente anziché una rotta inventata.</p>

<h3>Dimensioni della finestra</h3>
<p>La finestra del navigatore è liberamente ridimensionabile. Il globo o la griglia prospettica si adattano proporzionalmente allo spazio disponibile. Le dimensioni minime mantengono leggibili i valori dettagliati; il globo rimane rotondo. La posizione e le dimensioni della finestra vengono salvate.</p>

<h3>Attivare l’HUD di navigazione</h3>
<p>A sinistra nella finestra principale, seleziona la casella sotto <b>visualizzazione automatica → HUD di navigazione</b>. Con una navigazione planetaria valida, l’HUD appare direttamente sopra la finestra visibile di Elite in primo piano.</p>
<p>Mostra tre righe:</p>
<ul>
<li>direzione relativa</li>
<li>rotta obiettivo</li>
<li>distanza</li>
</ul>
<p>L’HUD è trasparente, lascia passare i clic e non prende il focus: non copre il gioco con un’area opaca, non intercetta i clic del mouse e non sottrae a Elite il focus di input quando appare automaticamente.</p>
<p>Senza navigazione valida o una direzione univoca, diventa automaticamente invisibile. Viene nascosto anche quando Elite è ridotto a icona o non è in primo piano. La casella nella barra laterale può comunque restare selezionata: rappresenta la tua preferenza per la visualizzazione automatica, non la visibilità attuale.</p>
<p>L’HUD è solo una visualizzazione aggiuntiva. Il navigatore normale funziona indipendentemente da esso, anche quando l’HUD è disattivato o non disponibile.</p>

<h3>Impostare un nuovo obiettivo</h3>
<p>Sullo stesso corpo puoi riaprire «Inserimento manuale …» in qualsiasi momento e impostare altre coordinate. Il nuovo obiettivo sostituisce quello di navigazione precedente. Con dati di posizione corrispondenti, la bussola si aggiorna immediatamente.</p>
<p>Con «Termina navigazione» rimuovi l’obiettivo attuale. Per un altro avvicinamento, imposta semplicemente un nuovo obiettivo.</p>

<p>Chiudere la finestra non elimina la destinazione. Il HUD di navigazione attivo può continuare; «Termina navigazione» rimuove la destinazione. Lasciare il corpo corrispondente o perdere i dati di posizione mette la navigazione in attesa e nasconde il suo HUD.</p>

<h3>Aggiornamento dei dati e limiti</h3>
<p>La navigazione si basa sui dati di stato forniti da Elite. Gli aggiornamenti possono arrivare in ritardo a seconda dello stato del gioco. L’indicazione dell’età nel navigatore mostra quanto tempo è trascorso dall’ultimo messaggio di stato confermato.</p>
<p>La distanza sulla superficie descrive l’arco più breve su una sfera ideale. Non è un percorso sul terreno o stradale. Il navigatore non conosce gli ostacoli né le quote del terreno lungo il tragitto: altitudine di volo, velocità sicura ed evitamento degli ostacoli restano responsabilità tua.</p>

<p>La posizione attuale proviene da Status.json; il diario completa le associazioni di corpo e sistema. La finestra e il HUD attivo mantengono gli aggiornamenti quando servono. La visualizzazione dipende dai dati Elite disponibili, senza precisione garantita in metri.</p>

<h3>Suggerimento</h3>
<p>Prima dell’avvicinamento, controlla il nome del corpo e i segni delle coordinate dell’obiettivo. Allineati quindi alla rotta obiettivo sulla bussola di Elite e osserva direzione relativa e distanza. Se il navigatore è in attesa, verifica se Elite sta già fornendo coordinate planetarie per il corpo obiettivo.</p>""",
    ),
}

DIALOG_TITLE = 'Aiuto – {area}'
CLOSE_LABEL = 'Chiudi'


# Database update guidance; help itself remains version independent.
HELP_TOPICS["overview"] = (HELP_TOPICS["overview"][0], HELP_TOPICS["overview"][1] + '<h3>Aggiornamento del database necessario</h3><p>L’aggiornamento corregge vecchie relazioni salvate tra stelle, pianeti e lune. I diari vengono solo letti. Chiudi prima Elite Dangerous e rendi disponibili anche i diari storici, se possibile. Il database CMDRHelper viene copiato integralmente prima delle modifiche; in caso di errore queste vengono annullate e, se necessario, viene ripristinata la copia. La copia viene conservata per sicurezza. Annulla permette di rimandare l’aggiornamento.</p>')

HELP_TOPICS["settings"] = (HELP_TOPICS["settings"][0], HELP_TOPICS["settings"][1] + '<h3>Diagnostica e registri</h3><p>In Impostazioni → Diagnostica e registri puoi aprire il registro o creare un pacchetto diagnostico. I registri si trovano in logs/ nella cartella di installazione (cmdrhelper.log e fino a quattro archivi precedenti). Lo ZIP contiene registri tecnici ripuliti, system_info.json e diagnose_summary.txt; nessun diario, database, dato FID/del comandante, credenziale, preferito o immagine. I percorsi personali sono sostituiti da segnaposto. Il contenuto dei vecchi registri precedenti al filtro di riservatezza viene omesso. Scegli dove salvare lo ZIP e condividilo con il supporto se necessario; non viene mai inviato automaticamente.</p>')

HELP_TOPICS["trade"] = (
    'Commercio',
    """<h2>Commercio</h2>
<h3>Il commercio in breve</h3>
<p>«Vendi» trova mercati che acquistano la tua merce. «Acquistare» trova una merce specifica da comprare. «Consigli» mostra cosa puoi acquistare alla stazione attuale e rivendere con profitto secondo i tuoi criteri.</p>

<h3>Dati di mercato e aggiornamento</h3>
<p>Vendita e acquisto combinano automaticamente le tue osservazioni di mercato valide salvate con i dati comunitari ottenuti tramite Spansh. Le raccomandazioni acquistano esclusivamente dal tuo mercato Elite attuale osservato; le destinazioni provengono normalmente dalle tue osservazioni e da Spansh. I risultati comunitari restano soltanto temporaneamente in memoria.</p>
<p>Tutti i dati sono istantanee, anche le osservazioni personali. Prezzi, offerta e domanda possono cambiare prima dell'arrivo. Controlla l'età dei dati: disponibilità e profitto non sono garantiti.</p>
<p>Se lo stesso mercato è noto da una tua osservazione e dalla comunità, CMDRHelper usa l’istantanea valida più recente.</p>

<h3>Scegliere una merce</h3>
<p>Fai clic su «Merce», cerca il nome visualizzato, il nome inglese o il simbolo e scegli la merce. I nomi tedeschi provengono dal catalogo tedesco curato. Se manca una traduzione disponibile, compare il nome del catalogo inglese o una denominazione leggibile.</p>

<h3>Vendi</h3>
<p>La ricerca usa sia le tue osservazioni di mercato valide sia i dati di mercato della comunità. Scegli merce, «Quantità (t)» e filtri, poi «Cerca la vendita migliore». La ricerca trova offerte d'acquisto con domanda sufficiente per la quantità inserita. «Prezzo / t» è il prezzo che ricevi vendendo. «Ricavo possibile» = prezzo × quantità inserita. Il punto di partenza è il sistema attuale del comandante. Per impostazione predefinita compare prima il prezzo di vendita più alto.</p>

<h3>Acquistare</h3>
<p>La ricerca usa sia le tue osservazioni di mercato valide sia i dati di mercato della comunità. Scegli merce, quantità desiderata e filtri, poi «Cerca l’acquisto più economico». L'«Offerta» riportata deve coprire l'intera quantità. «Prezzo / t» è il tuo prezzo d'acquisto; «Costo totale» = prezzo × quantità desiderata. Il punto di partenza è il sistema attuale. Compare prima il prezzo d'acquisto più basso. È una ricerca mirata di merce, non una raccomandazione di profitto.</p>

<h3>Filtri e tabelle dei risultati</h3>
<ul>
<li><b>Raggio (ly):</b> distanza massima tra il sistema di partenza e quello di destinazione.</li>
<li><b>Età massima dei dati di mercato / Età dati destinazione:</b> età massima consentita dei dati; nelle raccomandazioni riguarda la destinazione.</li>
<li><b>Dimensione piattaforma:</b> dimensione minima richiesta della piattaforma, non dimensione esatta della stazione. «Media» ammette anche piattaforme grandi; «Tutte» non impone restrizioni.</li>
<li><b>Includi Fleet Carrier:</b> includere o escludere le portaerei.</li>
<li><b>Distanza massima di arrivo (Ls):</b> distanza massima dalla stella d'arrivo alla stazione. Vuoto significa nessun limite. Una destinazione senza distanza d'avvicinamento nota non soddisfa il filtro.</li>
</ul>
<p>I risultati personali e comunitari usano gli stessi filtri per età dei dati, raggio, piattaforma di atterraggio, carrier e distanza di arrivo. I dati mancanti non vengono stimati. Sono escluse destinazioni senza distanza intersistema nota o senza dati che dimostrino il rispetto di una restrizione attiva. Nei mercati personali ciò riguarda soprattutto piattaforme e distanze d'avvicinamento mancanti; escludendo le portaerei, deve essere noto che la destinazione non è una portaerei.</p>
<p>Fai clic sulle intestazioni per ordinare: numeri per valore, età dei dati per anzianità effettiva e piattaforme per classe di dimensione. Vendita e acquisto mostrano al massimo 100 risultati. «Ci sono altri risultati. Restringi i filtri.» segnala una ricerca limitata. I risultati personali e comunitari disponibili vengono ordinati insieme per prezzo prima di limitare l’elenco. A causa dei limiti di ricerca del servizio comunitario, non è garantito che siano le migliori offerte in assoluto.</p>
<p>Se la ricerca comunitaria fallisce durante la vendita o l’acquisto, i risultati personali corrispondenti restano utilizzabili. CMDRHelper segnala che la ricerca è incompleta: potrebbero mancare offerte migliori della comunità.</p>

<h3>I tuoi dati di mercato</h3>
<p>Apri il mercato delle merci in Elite quando sei attraccato. Con CMDRHelper in esecuzione, il mercato viene acquisito automaticamente se è associabile con certezza alla stazione attuale. Non serve un'importazione manuale. Aprirlo di nuovo aggiorna l'istantanea.</p>
<p>Viene conservata una sola istantanea attuale per mercato e comandante, più recente di 24 ore. Quelle vecchie vengono eliminate automaticamente; non esiste uno storico permanente dei prezzi. Le osservazioni valide sopravvivono al riavvio di Helper. «Dati di mercato personali: X stazioni» conta i mercati personali validi del comandante attivo. Il limite scelto per l’età dei dati di mercato si applica anche ai risultati personali.</p>
<ul>
<li><b>✓ Acquisito:</b> Nelle raccomandazioni è disponibile un'istantanea personale valida della stazione attuale.</li>
<li><b>Apri il mercato:</b> Manca un'istantanea personale utilizzabile per questa stazione.</li>
<li><b>Dati obsoleti:</b> Un'istantanea mostrata in precedenza non è più valida. Apri nuovamente il mercato.</li>
</ul>
<p>Se un'istantanea vecchia è stata eliminata prima di aprire la vista, compare ugualmente «Apri il mercato». In volo non viene mostrato uno stato positivo per la stazione precedente.</p>

<h3>Consigli</h3>
<p>Servono la stazione attuale, la sua istantanea personale valida e la nave attuale nota con spazio libero di carico accertato. Lo spazio occupato viene sottratto. Con stiva piena o spazio libero sconosciuto non si avvia una nuova ricerca; le quantità non vengono inventate. Dopo la partenza non si ricalcola dalla posizione precedente.</p>
<p>Imposta «Profitto minimo»: 10 % considera solo opportunità con almeno il 10 % di margine. Si cercano merci offerte localmente. La stazione d'acquisto non è una destinazione. Per la stessa stazione di destinazione (stesso MarketID) vale l'istantanea valida più recente. Ogni merce mostra la destinazione verificata con il maggiore «Profitto potenziale» secondo i filtri, non necessariamente la migliore della galassia. La tabella inizia dal profitto possibile più alto; «Fonte» mostra «Elite locale» o «Spansh», e «Età dati destinazione» l'età dei dati di destinazione.</p>

<h3>Solo i miei dati di mercato</h3>
<p>Questa casella è disponibile solo nelle Raccomandazioni. Vendita e acquisto usano automaticamente entrambe le fonti. Questa casella limita le raccomandazioni ai mercati di destinazione validi osservati personalmente. Non si interrogano dati comunitari; Spansh non è necessario. Raggio, ulteriore limite d'età dei dati di destinazione, profitto minimo, piattaforma, portaerei e avvicinamento continuano a valere e devono essere verificabili con i dati disponibili. Saltare intenzionalmente la ricerca comunitaria non è un errore e non rende la ricerca incompleta. Puoi così cercare rapidamente tra stazioni già visitate.</p>

<h3>Profitto possibile e quantità</h3>
<ul>
<li><b>Profitto / t:</b> prezzo di vendita a destinazione − prezzo d'acquisto qui. «Profitto %» = profitto per tonnellata ÷ prezzo d'acquisto × 100.</li>
<li><b>Quantità (t):</b> il minimo tra spazio libero di carico, offerta del mercato d'acquisto e domanda a destinazione.</li>
<li><b>Profitto potenziale:</b> profitto per tonnellata × quantità possibile; una stima basata sulle istantanee note.</li>
</ul>
<p>Esempio: 280 t libere, offerta di 150 t, domanda di 20.000 t → quantità possibile di 150 t. Non ogni merce riempie automaticamente tutta la stiva libera.</p>

<h3>Volo commerciale memorizzato</h3>
<p>Spunta una raccomandazione per ricordarla: ne puoi tenere una sola. Una nuova selezione la sostituisce. Il riquadro separato mostra merce, stazione e sistema di destinazione e «Profitto potenziale» al momento della scelta. È un promemoria, non una raccomandazione ricalcolata continuamente.</p>
<p>Rimane dopo acquisto, variazioni del carico, partenza, cambio di sistema, attracco e apertura del mercato. Scompare con «Rimuovi» o togliendo la spunta, all'effettivo avvio di una nuova ricerca di raccomandazioni, cambiando comandante e chiudendo Helper. Non viene conservato al riavvio.</p>
<p>«Copia sistema» copia negli appunti soltanto il nome del sistema di destinazione. La stazione resta visibile nel promemoria; non viene creata alcuna rotta.</p>

<h3>Ricerca, avanzamento e annullamento</h3>
<p>Avvia le ricerche manualmente. Le raccomandazioni controllano più merci e possono richiedere più tempo. Una volta definito l'ambito, la barra e «Verifica merci: x di y …» indicano le merci effettivamente verificate. «Annulla» è disponibile solo durante una ricerca annullabile; una risposta di rete in corso può ritardare l'annullamento. Cambiare scheda annulla la ricerca; i filtri comuni di vendita/acquisto restano.</p>
<p>Se singole richieste comunitarie falliscono o si raggiungono limiti, possono restare visibili raccomandazioni valide già verificate. Una ricerca incompleta significa che i risultati riguardano i dati controllati, ma non tutte le merci o destinazioni sono state verificate completamente. Leggi l'avviso, restringi i filtri in caso di limiti o riprova più tardi. L'annullamento manuale scarta l'elenco corrente.</p>

<h3>Diagnostica in caso di problemi</h3>
<p>«Copia diagnostica» copia informazioni tecniche sull'ultima ricerca di raccomandazioni terminata per aiutare a risolvere problemi. Il testo non contiene dati del comandante/FID né prezzi di mercato. La diagnostica resta in memoria; non viene creato un file permanente e nulla viene trasmesso automaticamente. Se necessario, invia personalmente il testo copiato all'assistenza.</p>

<h3>Come effettuare un viaggio commerciale</h3>
<ol>
<li>Attracca a una stazione e apri il mercato in Elite.</li>
<li>Apri «Commercio» → «Consigli» e verifica «Acquisito».</li>
<li>Imposta profitto minimo e filtri, poi scegli «Cerca consigli».</li>
<li>Spunta la raccomandazione da ricordare e acquista la merce in Elite.</li>
<li>Usa «Copia sistema» se necessario e vola a destinazione; la stazione resta nel promemoria.</li>
<li>Vendi in Elite. Apri il mercato sul posto per aggiornare anche i tuoi dati personali del nuovo mercato.</li>
</ol>""",
)
