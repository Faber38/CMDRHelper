"""Deutsche Inhalte für die kontextbezogene Hilfe."""


HELP_TOPICS = {
    "materials": (
        "Materialien",
        """<h2>Materialien</h2>
<h3>CMDRHelper</h3>
<p>Engineering-Materialverwaltung: Alle 146 Materialien in Raw, Manufactured und Encoded, mit Graden, Maximalbeständen und Sonderfällen. Commanderbezogene Live-Bestände, Suche, Filter, fünf dezente Zeilenhintergründe und gespeicherte Spaltenbreiten/-reihenfolge erleichtern die Übersicht. Unbekannter Bestand bleibt von null unterschieden.</p>
<p>Odyssey-Inventar: Der vierte Materialreiter enthält 223 Katalogidentitäten für Waren, Materialien, Daten und Verbrauchsgegenstände. Schließfach, Rucksack und verlässlicher Gesamtbestand bleiben getrennt; Missionsstapel, Missionsstatus und Engineering-Verwendung sind sichtbar. Positive Bestandszahlen erscheinen in Gold. Fehlende Namensübersetzungen verwenden Englisch.</p>
<p>Materialhändlersuche (Händler suchen → Zum Routenplaner): Die Suche nutzt Spansh-Community-Daten und sucht auf Knopfdruck getrennt nach Raw, Manufactured und Encoded vom aktuellen Commander-System aus. Carrier werden ausgeschlossen und Stationsdetails geprüft. Die Entfernung in ly ist die direkte Systementfernung; Zugang ist nicht garantiert. Die Übergabe an den Routenplaner setzt das Zielsystem, nicht die Station, und startet keine Route. Für Odyssey gibt es keine Händlersuche.</p>
<p>Dieser Hauptbereich zeigt die Engineering-Materialien des aktuell betrachteten Commanders. Die Auswahl in der CMDR Ansicht gilt auch hier; die Daten anderer Commander bleiben getrennt.</p>
<h3>Drei Kategorien</h3>
<p>Die Reiter Rohmaterialien, Hergestellte Materialien und Verschlüsselte Daten enthalten alle 146 Katalogmaterialien, einschließlich Guardian- und Thargoid-Materialien. Die Liste ist nach Grad und innerhalb eines Grades alphabetisch sortiert.</p>
<h3>Bestand und Balken</h3>
<p>Die Zahlen zeigen Bestand / Maximum, beispielsweise Vanadium 244 / 250. Der Balken zeigt dazu 97,6 %. Auch nie besessene Materialien erscheinen bei zuverlässig bekanntem Bestand mit 0.</p>
<p>Leere Bestände sind dezent rot, knappe gelb/orange und fast volle bzw. volle grün markiert. Die Zahlen bleiben unabhängig von den Farben sichtbar.</p>
<h3>Suche und Filter</h3>
<p>Die Suche berücksichtigt den angezeigten und den englischen Materialnamen. Sie lässt sich mit allen Filtern kombinieren: Alle, Leer (0), Knapp (mehr als 0 bis 20 %), Fast voll (ab 80 % bis unter 100 %) und Voll (100 %). Werte zwischen 20 % und 80 % erscheinen nur unter Alle. Reiter und Filter werden beim nächsten Start wiederhergestellt.</p>
<h3>Unbekannte Werte</h3>
<p>Ohne verlässlichen vollständigen Bestand steht zum Beispiel ? / 250. Bei unbekanntem Maximum steht etwa 12 / ?. In beiden Fällen gibt es keinen Prozentwert oder Balken; solche Materialien erscheinen ausschließlich unter Alle. Ein unbekannter Grad steht am Listenende in einer eigenen Gruppe.</p>
<h3>Live-Aktualisierung</h3>
<p>Neue Journalereignisse aktualisieren den Bestand automatisch, auch nach Materialtausch, Engineering, Synthese oder Materialbelohnungen. Während des ersten Einlesens wird ein Ladehinweis angezeigt. Frisch gesammeltes Material wird kurz mit einer Angabe wie Vanadium +1 hervorgehoben; Verbrauch erzeugt keine Sammelmeldung.</p>
<h3>Materialnamen</h3>
<p>Ist ein Materialname noch nicht in der gewählten Sprache verfügbar, erscheint sein englischer Anzeigename. Interne Journalsymbole ersetzen keine vorhandenen Anzeigenamen.</p>
<h3>Odyssey</h3>
<p>Der vierte Reiter enthält Waren, Materialien, Daten und Verbrauchsgegenstände. Schließfach und Rucksack zeigen persönliche Bestände. Carrier ✎ zeigt für Waren, Materialien und Daten den manuell bestätigten privaten Bestand auf dem eigenen Carrier. Doppelklick zum Bestätigen, Korrigieren oder Auf-unbekannt-Setzen. — bedeutet unbekannt; 0 muss ausdrücklich bestätigt werden. Gesamt enthält Schließfach, Rucksack und Carrier nur bei bekannten, zusammenpassenden Werten. Bei mehreren Stapeln steht der Carrierbestand einmal in der Summenzeile; die Stapel bleiben getrennt. Verbrauchsgegenstände behalten die persönliche Summe ohne Carrier. FCMaterials ist kein vollständiger Carrierbestand und wird nicht als solcher verwendet. Die Schließfachgrenze von 1000 gilt je Kategorie, nicht je Gegenstand. Der Carrierbestand wird aus dem zuletzt bestätigten Stand fortgeschrieben. Nur auf dem eindeutig eigenen Carrier werden Schließfachänderungen nach Abzug expliziter persönlicher Vorgänge gegengebucht. Käufe und Verkäufe über den Carrier-Barkeeper, insbesondere durch andere Spieler, können den tatsächlichen Bestand verändern und werden möglicherweise nicht automatisch erfasst. Bei Bedarf per Doppelklick neu bestätigen. Gesamt verwendet die Projektion aus dem zuletzt bestätigten Carrierstand, keine garantierte Live-Abfrage. Das private Odyssey-Carrierlager hat gemeinsam 1.000 Plätze für Waren, Materialien und Daten. Die Bestandsumme ist nur vollständig bekannt, wenn alle Katalogpositionen und zusätzlich erfassten Materialien einschließlich 0 bestätigt sind. Sonst wird ein Mindestbestand angezeigt. Bei Überschreitung bleiben Eingaben erhalten; Gesamt wird unbekannt. Schließfach, Rucksack und Marktreservierungen zählen nicht zum privaten Materialbestand.<br><b>! – Carrierbestand einrichten</b><br>Trage im CMDRHelper per Doppelklick in der Spalte „Carrier“ für JEDE Position den aktuell auf dem Carrier vorhandenen Bestand ein. Bestätige auch ALLE leeren Positionen ausdrücklich mit 0.<br>— = noch nicht bestätigt / unbekannt<br>0 = ausdrücklich bestätigter leerer Bestand</p>
<p>Offene Kaufangebote beim Carrier-Barkeeper reservieren Lagerkapazität. Deshalb kann die Ingame-Lagerbelegung höher sein als der vorhandene Materialbestand. Reservierungen zählen nicht zum Materialbestand oder zu Material-Gesamtsummen. Ohne passend aktuelle Marktdaten bleibt die Lagerbelegung unbekannt. Angezeigte Marktstände sind Momentaufnahmen; Handel anderer Spieler kann sie verändern.</p>
<p>Die Kennzeichnung Mission gehört zum jeweiligen Bestandsstapel. Normale und missionsgebundene Gegenstände bleiben getrennt. Auch nach Missionsabschluss bleibt ein Gegenstand gekennzeichnet, solange das Journal ihn im Bestand führt. Der Tooltip zeigt Missionsnummer und bekannten Status. Engineering weist auf mindestens eine Verwendung für Anzug, Waffen oder Ingenieurfreischaltung hin; die einzelnen Verwendungen stehen im Tooltip.</p>
<p>Die Suche findet lokale und englische Namen. Die Odyssey-Filter zeigen alle Gegenstände, Missionsstapel, Engineering-Gegenstände, positiven Rucksack- oder Schließfachbestand oder sicher bekannten Gesamtbestand 0. Unbekannt ist nicht 0. Fehlende Übersetzungen fallen auf den englischen Namen zurück.</p>
<p>Der persönliche Bestand wird im Hintergrund automatisch aktualisiert. Bestätigte neue Aufnahmen können kurz hervorgehoben werden. Beim Commanderwechsel werden alte Bestände sofort entfernt. Unterreiter, Filter sowie Spaltenbreiten und Reihenfolge werden für Odyssey separat gespeichert.</p>
<h3>Mining</h3>
<p>Materialien → Mining ist die zentrale Übersicht für derzeit 57 bekannte handelbare Mining-Commodities, getrennt von Engineering-Materialien. Eine gemeinsame Tabelle umfasst planetaren Oberflächenabbau und Asteroiden-/Ring-Mining. Die festen Richtpreise dienen nur zur Orientierung und sind keine Live-Marktpreise.</p>
<p><b>Spalten</b><br><b>Rohstoff:</b> Name der Commodity bzw. des Rohstoffs.<br><b>SRV:</b> sicher bekannter Bestand im SRV.<br><b>Schiff:</b> sicher bekannter Bestand im Schiff.<br><b>Carrier:</b> Bestand auf dem eigenen Carrier; Elite liefert keine vollständige persönliche Lagerliste, daher ist eine manuelle Bestätigung des Ausgangsbestands nötig.<br><b>Gesamt:</b> SRV + Schiff + Carrier, nur wenn alle drei Teilbestände bekannt sind. Sonst —; unbekannt ist nicht 0.<br><b>Ø-Preis Cr/t:</b> fester Richtwert ohne Garantie für einen aktuellen Verkaufspreis. Fehlende Richtpreise bleiben unbekannt.<br><b>Wertklasse:</b> HOCH ab 100.000 Cr/t; MITTEL von 25.000–99.999 Cr/t; NIEDRIG unter 25.000 Cr/t. Ohne bekannten Preis gibt es keine Wertklasse.</p>
<p><b>Carrierbestand bestätigen</b><br>Elite Dangerous stellt CMDRHelper keine vollständige persönliche Carrier-Lagerliste bereit. So legst du für eine Ware einen bekannten Ausgangspunkt fest: 1. Carrier-Zelle doppelklicken. 2. Aktuellen Bestand als ganze Zahl ab 0 eingeben. 3. Den Wert übernehmen und damit manuell bestätigen. 4. Danach verfolgt CMDRHelper eindeutige CargoTransfer-Ereignisse zwischen Schiff und eigenem Carrier automatisch. Der Tooltip zeigt die manuelle Bestätigung und gegebenenfalls die spätere Fortschreibung.</p>
<p><b>— = Bestand unbekannt</b><br>Ohne bestätigten Ausgangsbestand ergeben einzelne Transfers keinen zuverlässigen absoluten Carrierbestand. Du kannst einen Wert jederzeit per Doppelklick ändern, korrigieren oder auf unbekannt zurücksetzen. Würde ein Transfer ein widersprüchliches oder negatives Ergebnis erzeugen, wird der Bestand wieder unbekannt und muss erneut manuell bestätigt werden.</p>
<p><b>Schiff und SRV</b><br>SRV und Schiff werden getrennt aus verifizierten Cargo-Daten ermittelt. Fehlende Bestände bleiben —. Vollständige Cargo-Snapshots haben Vorrang vor berechneten Änderungen.</p>
<p><b>↻ Aktualisieren</b><br>SRV-Bestand und Schiffbestand werden anhand verifizierter Daten separat aktualisiert. Bestätigter Carrierbestand bleibt davon unabhängig erhalten. Die normale Live-Aktualisierung läuft weiterhin automatisch. Grün bedeutet bereit oder erfolgreich, die Farbanimation zeigt die laufende Aktualisierung, Rot einen fehlgeschlagenen Versuch. Fehlende oder nicht verifizierbare Daten werden nicht als leerer Bestand ausgegeben.</p>
<p><b>Filter kombinieren</b><br>Die Rohstoffsuche filtert nach Namen. Die Wertklasse bietet Alle, HOCH, MITTEL und NIEDRIG; die Herkunft bietet Alle, Planetarer Abbau und Asteroiden/Ringe. „Nur Bestand“ zeigt einen Rohstoff, wenn mindestens ein bekannter Bestand in SRV, Schiff oder Carrier positiv ist. Unbekannte Bestände gelten nicht als 0 und blenden einen bekannten positiven Bestand an einem anderen Lagerort nicht aus. Suche, Wertklasse, Herkunft und Bestandsfilter lassen sich kombinieren.</p>
<p><b>ABBAU ×N im Explorer</b><br>Ein Klick öffnet Materialien → Mining und setzt den Herkunftsfilter automatisch auf Planetarer Abbau. Im Explorer gibt es keine zweite Mining-Tabelle.</p>
<p><b>Sortierung und Breiten</b><br>Klicke auf Spaltenüberschriften, um auf- oder absteigend zu sortieren. Bestände und Preise werden numerisch sortiert; unbekannte Werte stehen am Ende. Ziehe die Spaltengrenzen mit der Maus, um die Breiten anzupassen. Sortierung und Spaltenbreiten sowie die Zustände von Wertklasse, Herkunft und Nur Bestand werden gespeichert.</p>
<p><b>Herkunft</b><br>Surface bedeutet planetarer Oberflächenabbau, Asteroid steht für Asteroiden-/Ring-Mining. Manche Rohstoffe stammen aus beiden Bereichen (Both) und erscheinen in beiden passenden Herkunftsfiltern.</p>""",
    ),
    "overview": (
        "Übersicht",
        """<h2>Übersicht</h2>
<p>Die Übersicht ist die Startseite von CMDRHelper. Sie fasst die wichtigsten Informationen des aktuell aktiven Commanders zusammen und zeigt auf einen Blick, ob Journal, Standort und Online-Dienste korrekt erkannt werden.</p>

<h3>Commander &amp; Schiff</h3>
<p>Hier werden der aus dem Elite-Dangerous-Journal erkannte Commander und das aktuell verwendete Schiff angezeigt.</p>
<p>CMDRHelper ordnet persönliche Daten anhand der Frontier-ID (FID) dem jeweiligen Commander zu. Dadurch bleiben Daten verschiedener Commander voneinander getrennt.</p>
<p>Beim Wechsel des Commanders werden die zum neuen Commander gehörenden gespeicherten Informationen geladen.</p>

<p>CMDRHelper zeigt den zuletzt durch Elite gemeldeten Spielmodus. Open, Solo und Private Gruppe werden aus LoadGame erkannt. Bei privaten Gruppen wird der von Elite gemeldete Gruppenname unverändert angezeigt. Dies bedeutet nicht, dass Elite gerade läuft.</p>

<h3>Journal</h3>
<p>CMDRHelper verwendet die Journaldateien von Elite Dangerous als wichtigste Datenquelle.</p>
<p>Die Journalanzeige informiert darüber, ob Journaldateien gefunden und dem aktiven Commander zugeordnet wurden. Neue vollständige Journaleinträge werden während des Spiels automatisch verarbeitet.</p>
<p>Bereits verarbeitete Journalbereiche werden gespeichert, damit CMDRHelper beim nächsten Start nicht jedes Journal erneut vollständig auswerten muss.</p>

<h3>Aktueller Standort</h3>
<p>Zeigt das aktuell bekannte Sternensystem und – soweit aus dem Journal bekannt – den genaueren Standort des Commanders.</p>
<p>Der Standort wird durch Ereignisse wie Sprünge, Andocken und andere Positionsmeldungen aktualisiert und commanderbezogen gespeichert.</p>

<h3>Missionen</h3>
<p>Dieser Bereich zeigt die Anzahl der derzeit bekannten offenen Missionen.</p>
<p>Über die Schaltfläche beziehungsweise den Menüpunkt „Missionen“ gelangt man zur vollständigen Missionsansicht mit den bekannten Missionszielen und Statusinformationen.</p>

<h3>Letzter Stand</h3>
<p>„Letzter Stand“ fasst den zuletzt bekannten persistenten Commanderzustand zusammen. Dadurch können wichtige Informationen auch nach einem Neustart von Elite Dangerous oder CMDRHelper wiederhergestellt werden.</p>

<h3>Letzte Systeme</h3>
<p>Hier werden zuletzt besuchte beziehungsweise aus dem Journal erkannte Systeme angezeigt.</p>
<p>Die Liste dient als schneller Überblick über die jüngste Reise des Commanders.</p>
<p>Die Besuchshistorie berücksichtigt Location, FSDJump und CarrierJump auch im laufenden Journalabgleich. Mehrere Standortereignisse im selben ununterbrochenen Aufenthalt ergeben einen Besuch: A → A → A zählt einmal. Eine echte Rückkehr bleibt erhalten: A → B → C → A zählt vier Besuche.</p>

<h3>Online-Status</h3>
<p>Oben im Hauptfenster befinden sich zusätzliche Statusanzeigen:</p>
<ul>
<li><b>Journal erkannt</b> – CMDRHelper hat eine gültige Journalquelle und Commanderidentität erkannt.</li>
<li><b>EDSM</b> – zeigt den aktuellen Zustand der EDSM-Übertragung für die aktive Journal-FID.</li>
<li><b>INARA</b> – zeigt den aktuellen Zustand der Inara-Übertragung für die aktive Journal-FID.</li>
</ul>
<p>Online-Zugangsdaten werden für jeden Commander separat verwaltet. Ein Commander verwendet niemals automatisch den API-Key eines anderen Commanders.</p>

<h3>Wichtig bei mehreren Commandern</h3>
<p>Die Live-Daten richten sich immer nach dem Commander, der durch die aktuelle Elite-Dangerous-Journalsitzung eindeutig erkannt wurde.</p>
<p>Das bloße Anzeigen eines anderen Commanders in einer Ansicht verändert den aktiven Live-Commander nicht und beeinflusst keine EDSM- oder Inara-Übertragung.</p>

<h3>Tipp</h3>
<p>Wenn Commander, Schiff oder Standort nicht zum aktuellen Spielstand passen, zuerst die Journalanzeige oben und anschließend unter „Einstellungen“ den eingestellten Journalordner prüfen.</p>"""
              '<p>Open erscheint rot, Solo gold und Private Gruppe grün, bei privaten Gruppen mit dem gemeldeten Gruppennamen. Der Modus wird aus vorhandenen Journalen rekonstruiert und bei neuen LoadGame-Einträgen aktualisiert.</p>\n<p>Ein einfacher Klick auf einen Eintrag unter „Letzte Systeme“ kopiert den Systemnamen in die Zwischenablage. Kurz erscheint „✓ Kopiert: &lt;System&gt;“.</p>\n',
    ),
    "missions": (
        'Missionen & Belohnungen',
        """<h2>Missionen &amp; Belohnungen</h2>
<p>Diese Hauptseite zeigt die Missionen und beobachteten Belohnungen des aktuell aktiven Journal-Commanders. Die Auswahl eines anderen Commanders in der separaten CMDR Ansicht ändert diese Hauptseite nicht. Die Daten bleiben nach Commander getrennt.</p>

<h3>So verwendest du die Seite</h3>
<ol>
<li>Öffne „Missionen &amp; Belohnungen“ und wähle eine Mission in der Liste aus.</li>
<li>Prüfe „Status“ und die „MISSIONSDETAILS“. „Nächster Schritt“ hilft bei der Orientierung.</li>
<li>Verwende bei Bedarf „Journal aktualisieren“, um vorhandene Journaldaten erneut einzulesen.</li>
<li>Betrachte Missionsbelohnungen, „Kopfgelder“ und „Kampfbelohnungen“ getrennt.</li>
</ol>

<h3>Liste und Details</h3>
<p>Die Liste enthält bestätigte offene Missionen und erkannte vorläufige Encounter-Angebote. Sie zeigt Mission, System, Planet / Ort, Status, nächsten Schritt, Belohnung und Frist. Die Auswahl öffnet die Details mit den verfügbaren Ziel- und Fortschrittsangaben. Fehlende Journalangaben bleiben unbekannt; bei vorläufigen Angeboten ist die Frist unbekannt.</p>

<h3>Missionsstatus</h3>
<p>Der Status folgt den verfügbaren Missions-, Standort- und Fortschrittsdaten. Nicht jede Missionsart liefert alle Zwischenstände.</p>
<ul>
<li><b>Mission angenommen / Unterwegs:</b> Der Auftrag ist bekannt; das Ziel ist noch nicht als erreicht erkannt.</li>
<li><b>Im Zielsystem:</b> Du bist im Zielsystem, aber noch nicht am erkannten Missionsziel.</li>
<li><b>Am Missionsziel:</b> Die passende Zielstation oder der Zielkörper wurde erreicht.</li>
<li><b>Ziel geändert:</b> Ein neues Missionsziel wurde gemeldet.</li>
<li><b>Ware aufgenommen:</b> Die Aufnahme von Missionsfracht wurde erkannt.</li>
<li><b>Lieferung läuft:</b> Eine Lieferung wurde erfasst; bekannter Mengenfortschritt wird angezeigt.</li>
<li><b>Aufgabe erledigt / Daten erhalten:</b> Die Aufgabe beziehungsweise Datenerfassung ist erledigt. Die Mission kann noch offen sein, etwa mit „Zurück zum Missionsterminal“. Dies bestätigt noch keine Auszahlung.</li>
</ul>
<p>Erkannte Abschlüsse, Fehlschläge und Abbrüche entfernen die betroffene Mission aus der offenen Liste. Ein vollständiger neuer Missionsstand kann ältere Einträge als nicht mehr aktiv erkennen.</p>

<h3>Gesamtbelohnung</h3>
<p>„Gesamtbelohnung“ summiert die bekannten Credit-Belohnungen der bestätigten offenen Missionen. Sie ist kein bereits ausgezahltes Guthaben. Vorläufige Encounter-Angebote, Kopfgelder und Kampfbelohnungen zählen nicht dazu.</p>

<h3>Encounter-Aufträge</h3>
<p>Aus unterstützten Weltraumbegegnungen können vorläufige Angebote als „Encounter-Auftrag“ erscheinen, obwohl noch keine endgültige MissionID vorliegt. „Belohnungsangebot“ ist deshalb noch keine bestätigte offene Missionsbelohnung und fließt nicht in die Gesamtbelohnung ein.</p>
<p>Ordnen spätere Journaldaten ein Angebot eindeutig einer Mission zu, wird es mit dieser zusammengeführt. Bei Mehrdeutigkeit bleibt es vorläufig. Unbestätigte Angebote werden nach 24 Stunden lokal ausgeblendet; dies ist keine Aussage über eine Missionsfrist im Spiel.</p>

<h3>Kopfgelder</h3>
<p>Dieser Bereich zeigt lokal beobachtete Kopfgelder mit Gesamtbetrag und Fraktionsbeträgen. Er kennt nur erfasste Daten, keinen verlässlich vollständigen Spielbestand. „Erfassung ab jetzt.“ kennzeichnet den Beginn der Erfassung; bei Lücken erscheint „Nicht vollständig synchronisiert: Es können Erfassungslücken bestehen.“.</p>
<p>Eine erkannte Kopfgeldeinlösung oder ein erkannter Tod setzt den gesamten lokalen Kopfgeldstand auf null. Dies ist vom Missionsstatus unabhängig.</p>

<h3>Kampfbelohnungen</h3>
<p>Hier stehen beobachtete, noch nicht als eingelöst erkannte Kampfbelohnungen nach Fraktion. Ein möglicher Bestand vor Beginn der Erfassung fehlt. Bei Unsicherheit erscheint „Beobachteter Betrag“ mit „Bestand nicht vollständig gesichert.“.</p>
<p>Eine eindeutig zugeordnete Einlösung leert den beobachteten Betrag der genannten Fraktion; andere Fraktionen bleiben erhalten. Bei unklarer Zuordnung bleiben die Beträge stehen und „Einlösung erkannt – Bestand prüfen.“ erscheint. Ein erkannter Tod leert die beobachteten Kampfbelohnungen.</p>

<h3>Lokal zurücksetzen</h3>
<p>„Zurücksetzen…“ im jeweiligen Belohnungsbereich setzt nach Bestätigung nur dessen lokalen Stand für den aktiven Commander auf null. <b>Dies verändert keine Werte in Elite Dangerous.</b> Kopfgelder und Kampfbelohnungen werden getrennt zurückgesetzt; Missionen werden dabei weder bereinigt noch abgeschlossen.</p>

<h3>Aktualisierung und Neustart</h3>
<p>Bekannte offene Missionen und die lokalen Belohnungsstände bleiben über Helper-Neustarts erhalten. Eine neue Journalsitzung ohne Missionsliste entfernt offene Missionen nicht automatisch. Erfassungslücken können insbesondere Belohnungsstände unvollständig lassen. „Journal aktualisieren“ kann nur vorhandene Informationen einlesen, keine fehlenden Spieldaten erzeugen.</p>
<p>Die lokale Missionsanzeige benötigt keine Inara-Verbindung. Bei aktivierter, passend zum aktiven Commander eingerichteter Verbindung können unterstützte Missionsereignisse zusätzlich übertragen werden.</p>""",
    ),
    "explorer": (
        "Explorer",
        """<h2>Explorer</h2>
<h3>CMDRHelper</h3>
<p>System-Gesamtansicht: Die neue ED-artige Darstellung ersetzt die bisherige Miniübersicht und ist in Explorer und Chronik verfügbar. Sterne und Planeten bilden die Hauptstruktur, Monde verzweigen darunter; Mehrsternsysteme bleiben übersichtlich. Zoom, Scrollen, Anpassen an das Fenster und Körperklick öffnen den Zugang zu den Details.</p>
<p>Kompakte Asteroidengürtel: Belt-Cluster werden in Gesamtansicht und normalen Explorer-/Chronik-Systemkarten zu übersichtlichen Gürteln zusammengefasst. Alle einzelnen Clusterdaten bleiben erhalten.</p>
<p>Kartographie korrigiert: Ein späterer Scan nach einer DSS-Kartographierung setzt unverkaufte Explorerwerte, Mappingzeitpunkt und Effizienz nicht mehr zurück. Bestehende fehlerhafte Ansprüche werden beim Start anhand verfügbarer, eindeutig zugeordneter Journale repariert. Fehlen diese Quellen, bleibt die Reparatur offen; eine Datenbanklöschung ist nicht nötig.</p>
<p>Der Explorer wertet die vom aktiven Commander entdeckten und gescannten Systeme und Himmelskörper aus. Er verbindet die eigenen Elite-Dangerous-Journaldaten mit bereits verfügbaren Zusatzinformationen und zeigt Exploration, Kartographie, biologische/geologische Signale und Surface-Mining-Daten gemeinsam an.</p>

<h3>Aktuelles System</h3>
<p>Im oberen Bereich wird der aktuelle Kenntnisstand des Systems zusammengefasst.</p>
<p>Dazu gehören unter anderem:</p>
<ul>
<li>bekannte und selbst im Journal erfasste Körper</li>
<li>vorhandene Signale</li>
<li>Scanwerte</li>
<li>bereits erreichter Kartographiewert</li>
<li>möglicher Gesamtwert bei vollständiger Kartographierung</li>
<li>BIO-Status und geschätzte BIO-Werte</li>
<li>noch nicht abgegebene Kartographie- und BIO-Daten</li>
</ul>
<p>Die angezeigten Werte beruhen auf den tatsächlich verfügbaren Daten. Fehlende Informationen werden nicht als eigene Entdeckung ausgegeben.</p>

<h3>Systemkarte</h3>
<p>Die Systemkarte stellt Sterne, Planeten, Monde und andere bekannte Körper des aktuellen Systems grafisch dar.</p>
<p>Ein Körper kann angeklickt werden, um seine Detailansicht zu öffnen.</p>
<p>Die Darstellung zeigt unter anderem Körperart, Entfernung und – soweit vorhanden – Scan- und Kartographiewerte sowie besondere Explorationseigenschaften.</p>

<p>„Automatisch an Fenster anpassen“ ist standardmäßig eingeschaltet und merkt sich deine Auswahl auch nach einem Neustart. Eine neue Gesamtansicht wird damit einmal an die Fenstergröße angepasst; Einschalten im geöffneten Fenster passt sie ebenfalls einmal ein. Danach kannst du weiterhin manuell zoomen und verschieben. „An Fenster anpassen“ bleibt zum erneuten manuellen Einpassen verfügbar.</p>

<h3>Stationen &amp; Einrichtungen</h3>
<p>Der Reiter „STATIONEN (N)“ zeigt die bekannten Stationen und Einrichtungen des aktuellen Explorer-Systems als aufklappbare Karten. Die Zahl im Reitertitel zählt alle bekannten Einträge, auch wenn Filter einige ausblenden. Die Liste ist kein vollständiges Verzeichnis aller Stationen der Galaxis.</p>
<p>Grundlage sind lokal bekannte Journal-Beobachtungen aus Elite. Bei aktivierter Spansh-Ergänzung kommen Stationsinformationen aus dem separaten Stationscache hinzu. Die Quelle kann „Journal“, „Spansh“ oder „Journal + Spansh“ sein; bei widersprüchlichen Angaben haben Journalinformationen Vorrang. Spansh ergänzt hier keine Fleet Carrier. Ein lokal bekannter eigener Carrier kann angezeigt werden.</p>

<h3>Stationssuche, Filter und Sortierung</h3>
<p>„Stationsname suchen…“ sucht sofort nach Stationsnamen oder Namensteilen, unabhängig von Groß-/Kleinschreibung. Eine leere Suche schränkt den Namen nicht ein. Suche und beide Filter müssen gemeinsam erfüllt sein.</p>
<ul>
<li><b>Typ:</b> Beschränkt die Liste auf Orbitalstationen, Außenposten, Oberflächenstationen, Siedlungen, Megaschiffe, Fleet Carrier oder weitere Einrichtungen. „Alle Typen“ hebt die Typbeschränkung auf.</li>
<li><b>Zugehöriger Körper:</b> Wählt einen bekannten zugehörigen Körper. „Alle Körper“ lässt alle Standorte zu; „Unbekannt“ erscheint, wenn Einträge keinem bekannten Körper sicher zugeordnet sind.</li>
<li><b>Sortieren nach:</b> Standard ist alphabetisch nach „Name“. Alternativ nach „Typ“, „Zugehöriger Körper“ oder „Entfernung zum Ankunftspunkt“ aufsteigend sortieren. Entfernung wird numerisch sortiert; unbekannte Entfernungen beziehungsweise Körper stehen bei ihrer Sortierung zuletzt.</li>
</ul>
<p>Es gibt keine Stationsspalten zum Anklicken. Die Auswahlfelder sortieren die Karten. Suche, Filter und Sortierung lösen keine Netzabfrage aus. Beim Systemwechsel werden Suche und Typ-/Körperfilter zurückgesetzt. Eine leere Anzeige unterscheidet fehlende bekannte Einträge von Einträgen, die nicht zu den Filtern passen.</p>

<h3>Stationsdetails und Services</h3>
<p>Klicke auf den Kopf einer Stationskarte, um Details auf- oder zuzuklappen. Angezeigt werden, soweit bekannt, Name, Typ, System, zugehöriger Körper, MarketID, letzte Aktualisierung und Quelle. Ein Doppelklick auf das Vorschaubild öffnet den Bildbetrachter.</p>
<p>Spansh kann Entfernung zum Ankunftspunkt in Lichtsekunden, Zugehörigkeit, Regierung, kontrollierende Fraktion, Wirtschaftsdaten sowie die Anzahl großer, mittlerer und kleiner Landeplätze ergänzen. Stationsdatenstand, Systemdatenstand und Abrufzeit werden getrennt angezeigt, soweit vorhanden; ein neuer Abruf garantiert keinen neuen Stationsdatenstand.</p>
<p>Bekannte „Services“ erscheinen als beschriftete Felder, etwa „Markt“, „Werft“, „Ausstattung“, „Reparatur“, „Auftanken“ oder „Materialhändler“. Der Kartenkopf zeigt höchstens drei Services und gegebenenfalls die Zahl weiterer Einträge; aufgeklappt sind alle von CMDRHelper erkannten Services sichtbar. Fehlende Angaben werden nicht geschätzt und bedeuten nicht sicher, dass eine Einrichtung fehlt.</p>

<h3>Stationen auf der Karte und Aktualisierung</h3>
<p>Die Systemkarte und „Gesamtansicht“ verwenden dieselben bekannten Stationsinformationen. Sicher zugeordnete Einrichtungen stehen beim zugehörigen Körper, andere unter „Weitere Einrichtungen“. Ein Klick öffnet Stationsdetails oder bei Gruppen zunächst eine Auswahlliste.</p>
<p>In „Gesamtansicht“ aktualisiert „Spansh-Daten aktualisieren“ die Spansh-Stationsinformationen des dort angezeigten Systems. Voraussetzung sind aktivierte Spansh-Stationsinformationen und eine bekannte Systemidentität. Die Statuszeile meldet laufende Abfragen, Erfolg, Fehler oder eine bereits heute erfolgte Aktualisierung. Bei Fehlern bleiben lokale Informationen und vorhandene verwendbare Cachedaten erhalten. Die Regeln für automatische Abfragen, Cache und manuelles Aktualisieren stehen in der Einstellungen-Hilfe.</p>

<h3>BIO ×N</h3>
<p>BIO ×N bezeichnet die Anzahl der vom Spiel gemeldeten biologischen Signale eines Körpers.</p>
<p>Die Zahl sagt zunächst nur aus, wie viele biologische Signale beziehungsweise Gattungen gemeldet wurden. Sie bedeutet nicht automatisch, dass alle biologischen Arten bereits gefunden oder analysiert wurden.</p>
<p>Tatsächliche eigene BIO-Funde werden separat geführt.</p>

<h3>GEO ×N</h3>
<p>GEO ×N zeigt die Anzahl der vom Spiel gemeldeten geologischen Signale eines Körpers.</p>
<p>Dazu können beispielsweise geologische Erscheinungen wie Fumarolen oder Geysire gehören. CMDRHelper zeigt nur die Informationen an, die aus den vorhandenen Journal-/Körperdaten hervorgehen.</p>

<h3>ABBAU ×N</h3>
<p>ABBAU ×N zeigt die Anzahl der von Elite Dangerous gemeldeten planetaren Abbaustandorte eines Körpers.</p>
<p>Beispiel:</p>
<p><b>ABBAU ×12</b></p>
<p>bedeutet, dass für diesen Body 12 planetare Abbaustandorte gemeldet wurden.</p>
<p>Die Zahl sagt nicht, welcher Rohstoff an einem einzelnen Standort gewonnen werden kann.</p>

<h3>Eigene Abbau-Funde</h3>
<p>Wenn der Commander mit dem Rhino tatsächlich Surface Mining durchgeführt hat, speichert CMDRHelper die dabei belegten persönlichen Funde separat.</p>
<p>Dabei wird unterschieden zwischen:</p>
<ul>
<li>tatsächlich gewonnenen Commodities, z. B. Kupfer in Tonnen</li>
<li>beim Abbau gesammelten Nebenmaterialien</li>
<li>allgemeinen Oberflächenmaterialien des Bodys</li>
</ul>
<p>Ein Beispiel für einen persönlichen Fund wäre:</p>
<p><b>Kupfer – 40 t</b></p>
<p>Diese Angabe bedeutet, dass dieser Commander dort tatsächlich 40 t Kupfer gewonnen hat.</p>
<p>Die persönlichen Abbau-Funde werden commanderbezogen gespeichert und nicht mit den Funden anderer Commander vermischt.</p>

<h3>Oberflächenmaterialien des Bodys</h3>
<p><code>Scan.Materials</code> beschreibt die allgemeine Oberflächen-Materialzusammensetzung eines Körpers.</p>
<p>Beispielsweise können Eisen, Nickel, Schwefel oder andere Materialien mit Prozentwerten angezeigt werden.</p>
<p>Diese Werte dürfen nicht mit den Rohstoffen eines planetaren Abbaudepots verwechselt werden. Frontier stellt im Journal keine belegte direkte Zuordnung zwischen diesen allgemeinen Body-Materialien und dem Inhalt eines einzelnen Abbaustandorts bereit.</p>

<h3>Terraforming</h3>
<p>Das Symbol beziehungsweise die Kennzeichnung für Terraforming zeigt, dass ein Körper nach den vorhandenen Daten als Terraforming-Kandidat gilt.</p>

<h3>Erstentdeckung</h3>
<p>„Bei deinem Scan bereits entdeckt“ beschreibt den Zustand vor deinem damaligen Scan. Ja bedeutet zuvor entdeckt, Nein bedeutet damals noch nicht entdeckt; fehlende Informationen bleiben Unbekannt. ★ kennzeichnet einen First-Discovery-Kandidaten zum Scanzeitpunkt, keinen garantiert noch verfügbaren offiziellen Erstanspruch.</p>
<p>Ein historisches WasDiscovered=false oder WasMapped=false bedeutet nicht, dass der Körper heute noch unentdeckt oder unkartographiert ist. Auch nach Datenverkauf oder Wiederbesuch bleiben diese Angaben historische Beobachtungen. EDSM-Bekanntheit ist eine separate Information und kein Beweis für offizielle Elite-Erstentdeckung. Daraus werden keine offiziellen Erstentdecker abgeleitet.</p>

<h3>First Mapping</h3>
<p>CMDRHelper unterscheidet zwischen:</p>
<ul>
<li>◉ First-Mapping-Kandidat zum Scanzeitpunkt: beim eigenen Scan noch nicht kartographiert</li>
<li>◎ Von dir kartographiert: eigener DSS-Abschluss aufgezeichnet</li>
<li>◉✓ Kandidat beim Scan und eigene Kartographierung belegt; offizieller Erstanspruch unbestätigt</li>
</ul>
<p>„Bei deinem Scan bereits kartographiert“ wird unabhängig von der Entdeckung ausgewertet. Fehlende Informationen bleiben Unbekannt. Ein bereits entdeckter Körper kann beim Scan noch nicht kartographiert gewesen sein. Eigene Kartographierung bestätigt keinen offiziellen First-Mapping-Tag; bei mehreren Besuchen ist auch die Reihenfolge zum gespeicherten Scan nicht immer belegt.</p>
<p>Nach Abschluss einer eigenen DSS-Kartographierung werden Mapping-Zeitpunkt, verwendete Sonden und Effizienzziel zuverlässig gespeichert. Spätere Scan-Ereignisse lassen vorhandene Angaben nicht mehr verloren gehen.</p>

<h3>Landbar</h3>
<p>Die Landbarkeitsanzeige kennzeichnet Körper, auf denen nach den bekannten Daten eine Landung möglich ist.</p>

<h3>Goldrahmen / wertvolle Körper</h3>
<p>Besonders wertvolle Körper können in der Explorer-Darstellung hervorgehoben werden.</p>
<p>Der Goldrahmen kennzeichnet eine Kartographieschätzung ab dem eingestellten Schwellenwert. Er ist keine First-Discovery-Markierung und bestätigt weder unverkaufte Daten noch heute verfügbare Erstboni.</p>
<p>Er ersetzt nicht die detaillierte Wertanzeige des Körpers.</p>

<h3>Wertliste</h3>
<p>Die Wertliste zeigt Schätzungen nach dem gespeicherten Scanstand, keine sicher noch auszahlbaren Erlöse. Erstboni bleiben unbestätigt. Tooltips in Karte und Liste sowie das Körperdetail verwenden dieselben zeitlich eingeordneten Zustände.</p>
<p>Sie eignet sich besonders, um interessante oder wertvolle Körper eines Systems schnell miteinander zu vergleichen.</p>

<h3>BIO / GEO / ABBAU</h3>
<p>Diese Ansicht fasst Körper mit biologischen, geologischen oder planetaren Abbausignalen zusammen.</p>
<p>Dadurch müssen interessante Bodies nicht einzeln in der vollständigen Systemkarte gesucht werden.</p>
<p>Bei vorhandenen eigenen Surface-Mining-Daten können zusätzlich die persönlichen Abbau-Funde sichtbar werden.</p>
<p>Manuell angepasste Spaltenbreiten der gemeinsamen Explorer-Tabelle BIO / GEO / ABBAU bleiben nach erneutem Öffnen und Programmneustart erhalten. Gespeicherte Popup-Spaltenbreiten werden robuster wiederhergestellt; ungültige Werte fallen auf sichere Standardbreiten zurück.</p>

<h3>Tabellen bedienen</h3>
<p>Für Wertliste und BIO / GEO / ABBAU gilt: Ein Klick auf einen Spaltenkopf sortiert, ein erneuter Klick kehrt die Sortierrichtung um. Ziehe die Spaltengrenzen mit der Maus, um die Breiten zu ändern. Sortierung und Spaltenbreiten werden gespeichert; beide Tabellen besitzen getrennte Einstellungen. Körpernamen werden natürlich sortiert, beispielsweise A 2 vor A 10. Entfernungen, Credits und Anzahlen werden numerisch sortiert. Status, Analyse und Besucht werden nach ihrem fachlichen Zustand statt alphabetisch eingeordnet.</p>

<h3>Body-Detail</h3>
<p>Durch Anklicken eines Körpers öffnet sich die Detailansicht.</p>
<p>Dort können – soweit bekannt – unter anderem erscheinen:</p>
<ul>
<li>Körperart</li>
<li>Masse</li>
<li>Entfernung</li>
<li>Schwerkraft</li>
<li>Atmosphäre</li>
<li>Landbarkeit</li>
<li>Terraforming-Status</li>
<li>BIO-/GEO-Signale</li>
<li>planetare Abbaustandorte</li>
<li>Oberflächenmaterialien</li>
<li>eigene Abbau-Funde</li>
<li>Scanwert</li>
<li>Kartographiewert</li>
<li>aktueller Wert</li>
</ul>
<p>Nicht jeder Body besitzt alle Informationen.</p>

<h3>BIO-Prognosen</h3>
<p>CMDRHelper kann bei geeigneten Körpern anhand der vorhandenen Daten mögliche biologische Funde einschätzen.</p>
<p>Prognosen sind keine Garantie, dass eine bestimmte Spezies tatsächlich vorhanden ist. Sie dienen als Entscheidungshilfe für die Exploration.</p>
<p>Geschätzte BIO-Werte sind ebenfalls Prognosen und werden von tatsächlich bestätigten eigenen Funden getrennt behandelt.</p>

<h3>Noch nicht abgegeben</h3>
<p>CMDRHelper führt commanderbezogen bekannte, noch nicht abgegebene Kartographie- und BIO-Daten.</p>
<p>Kartographieverkäufe und biologische Abgaben werden anhand der entsprechenden Journalereignisse berücksichtigt.</p>
<p>Bereits verkaufte Kartographiedaten sollen nach einer Rekonstruktion nicht erneut als offen erscheinen.</p>

<h3>Auto einblenden</h3>
<p>Über die Schalter in der linken Seitenleiste können unterstützte Live-Hinweise wie Wertvolle Körper, BIO-Funde oder Frachtraum automatisch eingeblendet werden.</p>
<p>Diese kleinen Livefenster dienen als zusätzliche Hinweise während des Spielens und ersetzen nicht die vollständige Exploreransicht.</p>
<p>„Frachtraum“ zeigt den aktuell bestätigten Bestand des durch die aktive Journal-FID bestimmten Schiffs oder SRV. SRV-Fracht wird niemals als Schiffsfracht übernommen; Drohnen zählen zur Gesamtbelegung und werden in der Liste getrennt dargestellt.</p>
<p>Der BIO-Fortschritt erscheint kompakt: 1/3 gelb, 2/3 blau und 3/3 grün; der abgeschlossene Zustand „Fertig“ ist ebenfalls grün. Unter „auto einblenden“ besitzt GEO einen eigenen gespeicherten Schalter: BIO allein, GEO allein oder beide gemeinsam sind möglich.</p>
<p>Das Frachtraumfenster passt seine Höhe automatisch an den Inhalt an. Bei vielen Einträgen bleibt die Höhe begrenzt und die Tabelle lässt sich scrollen; Benutzerbreite und Fensterposition bleiben erhalten. Der vorhandene Schalter „Frachtraum-HUD“ befindet sich jetzt unter „auto einblenden“, nicht zusätzlich im Frachtraumfenster.</p>

<h3>Mehrere Commander</h3>
<p>Persönliche Explorationsergebnisse, Kartographie, BIO-Funde und eigene Surface-Mining-Funde werden dem jeweiligen Commander zugeordnet.</p>
<p>Globale astronomische Eigenschaften eines Bodys – beispielsweise die Anzahl bekannter planetarer Abbaustandorte – bleiben dagegen Eigenschaften des Körpers selbst.</p>

<h3>Tipp</h3>
<p>Bei einem interessanten Körper lohnt sich ein Klick auf die Detailansicht. Dort lässt sich am besten unterscheiden zwischen allgemeinen Körperdaten, möglichen Explorationsergebnissen und tatsächlich vom eigenen Commander belegten Funden.</p>

<h3>★ Favoriten</h3>
<p>Über den Button „★ Favoriten“ oben im Explorer öffnest du ein eigenes, wiederverwendbares Favoritenfenster. Dort speicherst du Systeme, Planeten/Monde und Oberflächenorte für den aktiven Commander.</p>
<p>Die alphabetisch nach Namen sortierte, scrollbare Liste zeigt Name, Typ, System, gegebenenfalls Body und Latitude/Longitude, Kategorie und eine kleine Bildvorschau. Freitextsuche, Typfilter und Kategoriefilter lassen sich gemeinsam verwenden. Die Suche berücksichtigt Name, System, Body und Notiz.</p>
<p>Mit „Öffnen / Anzeigen“ siehst du die gespeicherten Angaben, die Notiz und eine größere Bildvorschau. „Im Explorer anzeigen“ öffnet die vorhandene Systemübersicht beziehungsweise Body-Detailansicht, sofern der Favorit zum aktuellen Explorer-System gehört und passende Daten vorhanden sind. Für andere Systeme bleiben die gespeicherten Favoritendaten sichtbar; es wird keine Systemroute berechnet.</p>

<h3>Entfernungsfilter</h3>
<p>Der „Entfernungsfilter“ ist standardmäßig ausgeschaltet. „Max. Entfernung:“ hat den Vorgabewert 500 Lj; einstellbar sind 1 bis 100.000 Lj. Die Entfernung bezieht sich auf das aktuell bekannte System und verwendet vorhandene lokale Systemkoordinaten. Nur für diesen Filter erfolgt keine Liveabfrage.</p>
<p>Bekannte Favoriten außerhalb der Grenze werden ausgeblendet. Favoriten mit unbekannter Entfernung bleiben sichtbar. Fehlen die Koordinaten des aktuellen Systems, entfernt der Entfernungsfilter keine Einträge aus der Anzeige. Suche, Typ und Kategorie gelten weiterhin. Nach einem Systemwechsel wird automatisch neu gefiltert. Schalter und Maximalwert werden gespeichert.</p>

<h3>Favoriten exportieren</h3>
<p>„Exportieren“ erzeugt ein portables ZIP mit allen Favoriten des aktiven Commanders, nicht nur den durch Suche, Typ, Kategorie oder Entfernung sichtbaren Einträgen. favorites.json enthält die strukturierten Favoritendaten; vorhandene Favoritenbilder liegen im Paket unter images/. Das Paket lässt sich zwischen Linux und Windows übertragen.</p>
<p>Die vorhandenen Favoriten und Originalbilder werden nicht verändert. Identische Bildinhalte werden nur einmal im Paket gespeichert. Fehlende oder defekte Bilder verhindern den Export der Favoritendaten nicht. Für Import und Export gelten maximal 32 MiB je Datei und 256 MiB insgesamt für die unkomprimierten Paketinhalte.</p>

<h3>Favoriten importieren</h3>
<p>„Importieren“ prüft zuerst das ZIP und zeigt vor Änderungen eine Zusammenfassung mit neuen und bereits vorhandenen Favoriten. Importierte Favoriten werden dem aktuell aktiven Commander zugeordnet. Duplikate werden anhand von Typ, Kategorie, Name und Ortsdaten erkannt: bekannte System-/Körper-IDs und Koordinaten, andernfalls System-/Körpernamen. Auch Duplikate innerhalb des Pakets werden berücksichtigt.</p>
<p>Für die erkannten Duplikate gilt eine gemeinsame Auswahl: „Überspringen“ ist der Standard und lässt vorhandene Einträge unverändert; „Bestehenden Favoriten ersetzen“ übernimmt die importierten Daten in den bestehenden Favoriten; „Als neuen Eintrag übernehmen“ legt einen zusätzlichen Eintrag an. Abbrechen übernimmt nichts.</p>
<p>Ungültige Favoritendaten verhindern den gesamten Import. Bei einem Importfehler werden Datenbankänderungen zurückgerollt, damit kein Teilimport bleibt. Fehlende oder defekte Bilder verhindern den Import gültiger Favoritendaten nicht; diese Favoriten werden ohne Bild übernommen. Importierte Bilder werden lokal von CMDRHelper verwaltet.</p>

<h3>System, Planet oder aktuellen Standort speichern</h3>
<ul>
<li>„★ Aktuelles System speichern“ übernimmt das aktuelle System ohne Oberflächenkoordinaten.</li>
<li>„★ Planet / Mond speichern“ lässt dich einen bekannten Planeten oder Mond des aktuellen Systems auswählen. Auch dieser Favorit erhält keine Oberflächenkoordinaten.</li>
<li>„★ Aktuellen Standort speichern“ steht oben im Favoritenfenster neben den beiden anderen Speichermöglichkeiten und ist auch im Planeten-Navigator verfügbar. Im Favoritenfenster bleibt der Button immer sichtbar und ist ohne gültige aktuelle planetare Positionsdaten und aktiven Commander deaktiviert. Beim Klick werden Commander, System, Body, Latitude und Longitude festgehalten. Spätere Bewegungen im Spiel verändern diese Werte im geöffneten Dialog nicht.</li>
</ul>
<p>Gib einen frei wählbaren Namen ein und wähle genau eine Kategorie: Bio, Geo, Abbau, Aussicht, Landestelle, Interessant oder Sonstiges. Eine Notiz und ein Bild sind optional. Bekannte technische IDs werden intern übernommen; du musst sie nicht eingeben. Auch Latitude oder Longitude 0,0 sind gültige Koordinaten.</p>
<p>„Bearbeiten“ ändert Name, Kategorie, Notiz und Bild. System, Body und die gespeicherten Koordinaten bleiben dabei erhalten. Soll ein anderer Oberflächenort gespeichert werden, lege an dieser Position einen neuen Favoriten an.</p>

<h3>Schnell-Favorit ohne Maus</h3>
<p>Unter „Einstellungen → Schnell-Favorit“ kannst du einen globalen Hotkey frei festlegen, ändern oder entfernen. Nach der Installation ist er standardmäßig „Nicht belegt“: CMDRHelper registriert keine Taste ungefragt. Die Belegung wird gespeichert. Ist eine Kombination bereits belegt oder auf deinem System nicht verfügbar, erscheint eine Fehlermeldung; eine bisher funktionierende Belegung bleibt erhalten.</p>
<p>Unter Linux/X11 und Windows funktioniert der Hotkey auch, während Elite den Fokus besitzt – zu Fuß, im SRV und im Schiff. Ein Tastendruck speichert den aktuellen Oberflächenstandort sofort für den aktiven Commander, ohne Dialog und ohne Mausbedienung. Commander, System, Body und die aktuellen Latitude-/Longitude-Werte werden dabei eingefroren. Ohne gültige aktuelle planetare Koordinaten wird nichts gespeichert; frühere Koordinaten werden nicht wiederverwendet.</p>
<p>Der Favorit erhält einen eindeutigen vorläufigen Namen wie „Marker 07.09.2026 06:32:15“ und die Kategorie „Sonstiges“. Im normalen Favoritenfenster kannst du ihn später umbenennen, einer anderen Kategorie zuordnen, eine Notiz ergänzen oder ein Bild hinzufügen. Es wird kein automatischer Screenshot erstellt oder übernommen.</p>
<p>Für ungefähr zwei Sekunden erscheint direkt über dem aktiven Elite-Fenster „★ FAVORIT GESPEICHERT“ mit Body und Koordinaten; bei fehlendem Standort erscheint kurz „⚠ KEINE PLANETAREN KOORDINATEN“. Die Anzeige nimmt keinen Fokus und fängt keine Eingaben ab. Sie funktioniert auch bei ausgeschaltetem Navigations-HUD und verschwindet danach vollständig. Bei eingeschaltetem HUD bleibt anschließend die normale Navigationsanzeige bestehen. Der gespeicherte HUD-Schalter wird dabei nicht verändert. Die Anzeige nutzt denselben Overlay-Unterbau und dessen Plattformvoraussetzungen wie das Navigations-HUD.</p>

<h3>Favoritenbilder</h3>
<p>Favoritenbilder sind vom Bereich „Bilder“ getrennt. „Bild auswählen …“ erlaubt PNG, JPEG und WebP. Erst beim Speichern kopiert CMDRHelper das ausgewählte Bild in seinen eigenen Favoriten-Bildordner. Die Originaldatei wird weder verschoben noch verändert.</p>
<p>„Letzten Screenshot verwenden“ liest bei jedem Klick den eingestellten Screenshot-Quellordner neu ein und sucht lesbare Screenshots mit typischen Elite-Dateinamen. Ohne Einstellung werden die üblichen Elite-Screenshot-Verzeichnisse unter Windows beziehungsweise Steam/Proton berücksichtigt. Auch der zum aktiven Commander gehörende Ordner im konfigurierten Konvertierungsziel wird nach passenden konvertierten Elite-Screenshots durchsucht. So bleibt ein konvertierter Screenshot auffindbar, wenn sein ursprüngliches BMP gelöscht wurde. Für den neuesten Aufnahmezeitpunkt zählt eine eindeutige Zeitangabe im Dateinamen, andernfalls die Dateizeit; bei konvertierten Bildern zählt die im Namen gespeicherte Aufnahmezeit statt des Konvertierungszeitpunkts. CMDRHelper löst selbst keinen Screenshot aus und durchsucht keine beliebigen Bilderordner.</p>
<p>Vor der Verwendung werden Dateiname, Aufnahmezeit und eine frisch geladene Vorschau angezeigt. Bestätige mit „Dieses Bild verwenden“. Wird kein geeigneter Screenshot gefunden, kannst du weiterhin „Bild auswählen …“ verwenden. Elite-BMP-Screenshots werden als interne PNG-Kopie gespeichert.</p>
<p>Ein Bild lässt sich im Bearbeitungsdialog ersetzen oder mit „Bild entfernen“ abwählen. Beim Speichern wird die nicht mehr verwendete interne Kopie entfernt. Fehlt eine Bilddatei, bleibt der Favorit ohne Vorschau benutzbar.</p>
<p>Favoritenbilder können Bestandteil des Exports sein; beim Import werden sie lokal übernommen. Gemeinsam verwendete interne Bildkopien werden nicht entfernt, solange ein anderer Favorit sie noch benötigt. Beim Ersetzen von Favoriten durch einen Import bleiben alte Bilddateien derzeit vorsorglich erhalten.</p>

<h3>Favoritenziel und Commander</h3>
<p>„▶ Zur Route“ übernimmt das bekannte System des Favoriten als Ziel in den Routenplaner. Das Startsystem folgt der bestehenden Bedienlogik dem aktuellen AppState; ein manuell gesetzter Start bleibt erhalten. Es wird keine Route automatisch berechnet. „◎ Zu den Koordinaten“ startet bei gespeichertem System, Körper und gültigen Koordinaten die vorhandene Planetennavigation zum Oberflächenort mit dem bestehenden Navigations-HUD. Systemreise und Oberflächennavigation sind zwei getrennte Schritte, kein automatischer Reiseablauf. Ohne Oberflächenkoordinaten ist nur die Route verfügbar; fehlen notwendige Daten, wird die jeweilige Aktion ausgeblendet.</p>
<p>Für Oberflächenorte übergibt „◎ Zu den Koordinaten“ den gespeicherten Body, Latitude, Longitude und Favoritennamen an den vorhandenen Planeten-Navigator. Das neue Ziel ersetzt das bisherige Ziel. Favoriten besitzen keine eigene Navigationslogik. Der Navigator entscheidet unverändert selbst: passende gültige planetare Daten aktivieren die Navigation, andernfalls wartet er auf diese Daten.</p>
<p>Favoriten gehören ausschließlich zum aktiven Commander. Beim Commanderwechsel wird die Liste aktualisiert; ein offener Bearbeitungsdialog wird verworfen. Ein noch als Favoritenziel geführtes Ziel des vorherigen Commanders wird beendet. Die Commander-Auswahl der Chronik erweitert diese Favoritenliste nicht.</p>
<p>„Löschen“ verlangt eine Bestätigung und entfernt nur den Favoritendatensatz und seine interne Bildkopie. Der ursprüngliche Screenshot beziehungsweise das ausgewählte Originalbild und alle Explorer-, Journal- und Bodydaten bleiben erhalten.</p>""",
    ),
    "chronicle": (
        "Chronik",
        """<h2>Chronik</h2>
<h3>CMDRHelper</h3>
<p>System-Gesamtansicht: Die neue ED-artige Darstellung ersetzt die bisherige Miniübersicht und ist in Explorer und Chronik verfügbar. Sterne und Planeten bilden die Hauptstruktur, Monde verzweigen darunter; Mehrsternsysteme bleiben übersichtlich. Zoom, Scrollen, Anpassen an das Fenster und Körperklick öffnen den Zugang zu den Details.</p>
<p>Kompakte Asteroidengürtel: Belt-Cluster werden in Gesamtansicht und normalen Explorer-/Chronik-Systemkarten zu übersichtlichen Gürteln zusammengefasst. Alle einzelnen Clusterdaten bleiben erhalten.</p>
<p>Die Chronik ist die persönliche Reise- und Fundhistorie des Commanders. Sie verwendet die dauerhaft gespeicherten Journalinformationen, um bereits besuchte Systeme wiederzufinden, räumlich darzustellen und nach bekannten Entdeckungen zu durchsuchen.</p>

<h3>Besuchte Systeme</h3>
<p>Die Chronik zeigt die dem Commander bekannten besuchten Systeme und ihre Positionen in der Galaxie.</p>
<p>Soweit vorhanden, werden unter anderem erster und letzter Besuch sowie bekannte Körperinformationen berücksichtigt.</p>
<p>Bei aktivem Zeitraum beziehen sich Besuchszahl, erster Besuch und letzter Besuch in der Kartenansicht auf die gefilterten tatsächlichen Systembesuche.</p>
<p>Die Chronik ist damit nicht nur eine Karte, sondern auch ein Werkzeug zum Wiederfinden früherer Reiseziele und Entdeckungen.</p>

<h3>3D-Karte</h3>
<p>Die besuchten Systeme werden anhand ihrer galaktischen X-/Y-/Z-Koordinaten räumlich dargestellt.</p>
<p>Die Bedienhinweise befinden sich direkt oberhalb der Karte:</p>
<ul>
<li>linke Maustaste gedrückt halten → Ansicht drehen</li>
<li>mittlere Maustaste gedrückt halten und ziehen → Zoom-Fenster aufziehen</li>
<li>rechte Maustaste gedrückt halten → Ansicht verschieben</li>
</ul>
<p>Die kleine Achsenanzeige hilft bei der Orientierung im Raum.</p>

<p>Mit dem Mausrad zoomst du ohne Zusatztaste hinein oder heraus.</p>
<p>Ein Doppelklick auf freien Kartenraum stellt die anfängliche Schrägansicht wieder her, setzt die Verschiebung zurück und passt alle aktuell dargestellten Systeme ins Fenster ein. Filter und Systemauswahl bleiben erhalten.</p>
<p>Beim Beginn einer Drehung mit der linken Maustaste wird das angeklickte System zum Drehpunkt. Im freien Raum dient der Punkt unter der Maus auf der galaktischen Ebene als Drehpunkt; bei nahezu waagerechter Ansicht wird stattdessen die Kartenmitte auf dieser Ebene verwendet. Auch „Ausrichten“ dreht um das aktuelle Rotationszentrum.</p>
<p>Ein Klick auf ein System öffnet dessen Detailfenster. Dort kopiert ein linker Klick auf den Systemnamen oben oder auf das Kopiersymbol ⧉ daneben ausschließlich den Systemnamen in die Zwischenablage. Ein kurzes ✓ bestätigt das Kopieren.</p>

<h3>Aktuelle Position</h3>
<p>Mit „Aktuelle Position“ kann die Kartenansicht auf den aktuell bekannten Standort des aktiven Commanders ausgerichtet beziehungsweise dorthin zurückgeführt werden.</p>
<p>Zuerst wird der aktuelle Filterzustand angewendet. Nur wenn das aktuelle System in der resultierenden Karte enthalten ist, wird darauf zentriert.</p>
<p>Andernfalls erscheint „Das aktuelle System ist in dieser Filterauswahl nicht enthalten.“ Die Filter werden dadurch nicht aufgehoben.</p>

<h3>Ausrichten</h3>
<p>„Ausrichten“ setzt die Orientierung auf die galaktische Draufsicht zurück. Verschiebung und Zoom bleiben dabei erhalten.</p>
<p>Dies ist hilfreich, wenn die Karte nach starkem Drehen unübersichtlich geworden ist.</p>

<h3>Chronik aktualisieren</h3>
<p>„Chronik aktualisieren“ lädt die Chronikdaten anhand des aktuellen gemeinsamen Filterzustands neu und aktualisiert die Darstellung. Freitext, aktivierte Datumsgrenzen und Mining-Filter werden dabei erneut gemeinsam ausgewertet; aktive Filter werden nicht ignoriert.</p>
<p>Die Funktion verändert keine Journaldateien und erzeugt keine neuen Explorationdaten. Sie aktualisiert lediglich die Chronikdarstellung anhand der vorhandenen CMDRHelper-Daten.</p>

<h3>Freitextsuche</h3>
<p>Über das Feld „Chronik durchsuchen …“ können bereits bekannte Inhalte durchsucht werden.</p>
<p>Die Suche berücksichtigt – soweit im Datenbestand vorhanden – unter anderem:</p>
<ul>
<li>Systemnamen</li>
<li>Körpermerkmale</li>
<li>biologische Daten</li>
<li>Materialien</li>
<li>Codexdaten</li>
</ul>
<p>Freitext, Zeitraum und Mining befinden sich in einem gemeinsamen Filterbereich. „Anwenden“ wertet die gesetzten Filter gemeinsam aus. Enter im Freitextfeld startet denselben Filterlauf wie „Anwenden“.</p>

<h3>Zeitraum Von/Bis (UTC)</h3>
<p>Aktiviere „Von“ und „Bis“ jeweils über den zugehörigen Haken und wähle das gewünschte Datum. Auch nur eine Grenze ist möglich. Ohne aktivierten Haken besteht auf dieser Seite keine zeitliche Einschränkung; ohne beide Haken wird kein Zeitraum eingeschränkt.</p>
<ul>
<li><b>Von:</b> Ab Beginn des ausgewählten UTC-Kalendertages einschließlich.</li>
<li><b>Bis:</b> Der vollständige ausgewählte UTC-Kalendertag wird berücksichtigt, bis unmittelbar vor Beginn des folgenden Tages.</li>
</ul>
<p>UTC ist die koordinierte Weltzeit. Die Datumsgrenzen beziehen sich auf UTC-Kalendertage, nicht auf Kalendertage deiner lokalen Zeitzone.</p>
<p>Gefiltert werden tatsächliche Systembesuche aus <code>system_visits</code>. Ein tatsächlicher Besuch des jeweiligen Commanders innerhalb des Zeitraums ist erforderlich. Die gespeicherten Angaben <code>first_seen</code> und <code>last_seen</code> ersetzen keinen echten Besuch: Allein ein Zeitraum zwischen einem früheren ersten und einem späteren letzten Besuch genügt nicht.</p>
<p>Der Zeitraum filtert Besuche, nicht einzelne Entdeckungs-, BIO-, GEO- oder Mining-Ereignisse. Bekannte Fundinformationen und Mining-Mengen bleiben gespeicherte Gesamtwerte. Von/Bis können sowohl allein als auch gemeinsam mit Freitext und Mining verwendet werden.</p>
<p>Liegt Von nach Bis, erscheint „Das Von-Datum darf nicht nach dem Bis-Datum liegen.“ Es wird keine Datenbankabfrage gestartet. Korrigiere die Datumsgrenzen und wende die Filter erneut an.</p>

<h3>Suchergebnisse</h3>
<p>Treffer werden in der vorhandenen Ergebnisliste unterhalb der Chronik-Karte angezeigt.</p>
<p>Je nach Trefferart können System und Body sowie zusätzliche Informationen erscheinen.</p>
<p>Ein Treffer kann verwendet werden, um das entsprechende bereits bekannte System beziehungsweise den Körper wiederzufinden und die vorhandenen Detailinformationen zu öffnen.</p>

<h3>Keine Treffer</h3>
<p>Ergibt ein gültiger Filterlauf keine Treffer, werden Karte und Routen geleert. Die Trefferliste wird geleert und ausgeblendet, die Detailanzeige zurückgesetzt und ein geöffnetes Chronik-Systemdetailfenster geschlossen.</p>
<p>Alte Ergebnisse bleiben nicht sichtbar. Prüfe in diesem Fall die Kombination aus Suchtext, Zeitraum und Mining-Filtern sowie den für die jeweilige Ansicht verwendeten Commander.</p>

<h3>Planetare Abbaustandorte</h3>
<p>Mit dem Filter „Planetare Abbaustandorte“ können gezielt bereits bekannte Bodies gesucht werden, für die Elite Dangerous planetare Abbaustandorte gemeldet hat.</p>
<p>Die zugrunde liegende Anzeige entspricht dem aus dem Explorer bekannten:</p>
<p><b>ABBAU ×N</b></p>
<p>Die Anzahl gehört zum Body selbst und ist nicht commanderbezogen.</p>

<h3>Mindestens</h3>
<p>Über „Mindestens“ lässt sich festlegen, wie viele planetare Abbaustandorte ein Body mindestens besitzen soll.</p>
<p>Beispiel:</p>
<p><b>Mindestens 20</b></p>
<p>zeigt nur bekannte Bodies mit mindestens:</p>
<p><b>ABBAU ×20</b></p>
<p>Dadurch lassen sich besonders umfangreiche Mining-Gebiete gezielt wiederfinden.</p>

<h3>Eigene Abbau-Funde</h3>
<p>Mit „Eigene Abbau-Funde“ wird die Suche auf Bodies eingeschränkt, auf denen der betrachtete Commander nachweislich selbst Surface Mining betrieben hat.</p>
<p>Diese Information stammt aus der persönlichen Surface-Mining-Historie und wird strikt nach Commander getrennt.</p>
<p>Ein Body kann also globale ABBAU ×N-Signale besitzen, ohne dass der eigene Commander dort bereits etwas abgebaut hat.</p>

<h3>Rohstoff</h3>
<p>Ist „Eigene Abbau-Funde“ aktiviert, steht zusätzlich die Auswahl „Rohstoff“ zur Verfügung.</p>
<p>Die Liste enthält ausschließlich Commodities, die der betrachtete Commander tatsächlich schon selbst beim Surface Mining gewonnen hat.</p>
<p>Es handelt sich nicht um eine theoretische Liste aller möglichen Mining-Rohstoffe.</p>
<p>Für EXAMPLE kann beispielsweise erscheinen:</p>
<ul>
<li>Alle</li>
<li>Kupfer</li>
</ul>
<p>Werden später weitere Rohstoffe tatsächlich abgebaut, erscheinen diese automatisch in der persönlichen Auswahl.</p>

<h3>Gezielte Rohstoffsuche</h3>
<p>Wird beispielsweise „Kupfer“ ausgewählt und anschließend „Anwenden“ gedrückt, zeigt die Chronik nur Bodies, auf denen der betrachtete Commander nachweislich Kupfer abgebaut hat.</p>
<p>Beispiel:</p>
<p><b>Example System / 2 — ABBAU ×12 — Kupfer 40 t</b></p>
<p>Damit kann die Chronik als persönliche Fundort-Datenbank verwendet werden: Ein bereits früher abgebauter Rohstoff lässt sich später gezielt wiederfinden.</p>

<h3>Alle Rohstoffe</h3>
<p>Bei „Rohstoff: Alle“ werden alle passenden persönlichen Surface-Mining-Funde berücksichtigt.</p>
<p>Sind auf einem Body mehrere Commodities bekannt, können diese mit ihren bisher selbst gewonnenen Mengen gemeinsam angezeigt werden.</p>
<p>Beispiel:</p>
<p><b>ABBAU ×12 — Helium-3 10 t, Kupfer 40 t</b></p>
<p>Die Mengen sind persönliche, tatsächlich aus Journalereignissen belegte Abbauwerte des jeweiligen Commanders.</p>
<p>Auch bei aktivem Zeitraum bleiben persönliche Mining-Mengen gespeicherte Gesamtmengen. <b>Kupfer 40 t</b> bedeutet nicht automatisch <b>40 t im ausgewählten Zeitraum</b>. Der Zeitraum verlangt einen passenden Systembesuch, begrenzt aber nicht die angezeigte Abbaumenge auf diesen Zeitraum.</p>

<h3>Filter kombinieren</h3>
<p>Freitext, aktivierte Von-/Bis-Grenzen und Mining-Filter können miteinander kombiniert werden. Ein Treffer muss die gesetzten Bedingungen gemeinsam erfüllen.</p>
<p>Beispielsweise:</p>
<ul>
<li>Planetare Abbaustandorte aktiv</li>
<li>Mindestens 20</li>
<li>Eigene Abbau-Funde aktiv</li>
<li>Rohstoff Kupfer</li>
</ul>
<p>sucht nach bekannten Bodies mit mindestens 20 planetaren Abbaustandorten, auf denen der betrachtete Commander bereits selbst Kupfer gewonnen hat.</p>
<p>Mit zusätzlichem Suchtext wird auch dieser berücksichtigt. Bei zusätzlichem Zeitraum muss der betrachtete Commander das zugehörige System tatsächlich in diesem Zeitraum besucht haben; der Kupferabbau selbst muss nicht in diesen Zeitraum fallen.</p>

<h3>Anwenden</h3>
<p>„Anwenden“ führt einen gemeinsamen Filterlauf mit allen aktuell gesetzten Such-, Zeitraum- und Mining-Filtern aus:</p>
<ul>
<li>Freitext</li>
<li>Von, wenn aktiviert</li>
<li>Bis, wenn aktiviert</li>
<li>Planetare Abbaustandorte</li>
<li>Mindestanzahl</li>
<li>Eigene Abbau-Funde</li>
<li>Rohstoff, wenn „Eigene Abbau-Funde“ aktiviert ist</li>
</ul>
<p>Enter im Freitextfeld führt genau denselben Filterlauf aus. Ohne Freitext und Mining-Filter wird die normale Karte für die angehakten Karten-Commander geladen, gegebenenfalls eingeschränkt durch Von/Bis.</p>

<h3>Zurücksetzen</h3>
<p>„Zurücksetzen“ setzt den gemeinsamen Filterbereich auf seinen Ausgangszustand zurück:</p>
<ul>
<li>Freitext wird geleert.</li>
<li>Von und Bis werden deaktiviert; die Datumsfelder zeigen wieder das heutige Datum und sind deaktiviert.</li>
<li>Planetare Abbaustandorte wird deaktiviert.</li>
<li>Die Mindestanzahl wird auf 0 gesetzt.</li>
<li>Eigene Abbau-Funde wird deaktiviert.</li>
<li>Rohstoff wird auf „Alle“ zurückgesetzt.</li>
</ul>
<p>Die Commander-Auswahl bleibt erhalten. Anschließend wird die normale Chronik für diese Karten-Auswahl neu geladen; vorherige Suchtreffer und Detailanzeigen werden zurückgesetzt.</p>

<h3>Commander-Auswahl</h3>
<p>Die Chronik kann Daten verschiedener bekannter Commander darstellen.</p>
<p>Dabei gibt es zwei getrennte Auswahlkonzepte:</p>
<ul>
<li><b>Karten-Commander-Auswahl:</b> Die Commander-Haken bestimmen, welche Commander-Routen in der normalen Karte ohne Freitext-/Mining-Suche angezeigt werden. Ein aktivierter Zeitraum wird dabei berücksichtigt.</li>
<li><b>Betrachteter Commander:</b> Persönliche Freitext-/Mining-Suchen verwenden den betrachteten Commander (<code>viewed_commander_id</code>), ersatzweise den aktiven Commander. Nach ihm richten sich auch die persönlichen Rohstofflisten.</li>
</ul>
<p>Persönliche Informationen wie eigene Abbau-Funde und Rohstofflisten werden jedoch immer für den tatsächlich betrachteten Commander getrennt ausgewertet.</p>
<p>Ein Commander sieht in seiner Rohstoffauswahl keine Mining-Funde, die ausschließlich einem anderen Commander gehören.</p>

<h3>Alle Commander</h3>
<p>Die Karten-/Chronikdarstellung kann mehrere Commander berücksichtigen.</p>
<p>„Alle Commander“ bezieht sich auf die Karten-Commander-Auswahl. Die Commander-Haken erweitern persönliche Freitext-/Mining-Suchen nicht automatisch auf mehrere Commander.</p>
<p>Das ändert nichts an der persönlichen Zuordnung commanderbezogener Daten. Globale astronomische Eigenschaften eines Systems oder Bodys bleiben gemeinsam nutzbar, persönliche Funde bleiben getrennt.</p>

<h3>Suchhilfe / Legende</h3>
<p>Über „Suchhilfe / Legende“ können zusätzliche Hinweise zur Chronik-Suche und zur Bedeutung der Darstellung aufgerufen werden.</p>
<p>Ein angeklickter Suchbegriff wird in das Suchfeld übernommen und zusammen mit den bereits gesetzten Zeitraum-/Mining-Filtern ausgeführt.</p>
<p>Diese kontextbezogene Haupthilfe ergänzt die dort vorhandenen kurzen Bedienhinweise.</p>

<h3>Tipp</h3>
<p>Die Chronik eignet sich besonders, um interessante Orte wiederzufinden, die während einer längeren Reise entdeckt wurden.</p>
<p>Für Surface Mining kann sie beispielsweise beantworten:</p>
<p>„Auf welchem Planeten habe ich schon einmal Kupfer abgebaut?“</p>
<p>oder:</p>
<p>„Welche meiner bekannten Planeten besitzen besonders viele Abbaustandorte?“</p>""",
    ),
    "jump_tip": (
        'Analyse',
        """
<h2>Analyse</h2>
<p>Die Analyse basiert auf deiner persönlichen Explorationhistorie. Systemanalyse bewertet einen eingegebenen prozeduralen Systemnamen; Erfahrungsdaten erhält die bisherige Kürzelauswertung mit historischen Treffern und „Neu auswerten“. Beide Bereiche sind Entscheidungshilfen, keine Fundgarantie.</p>
<h3>Vergleichsgrundlage</h3>
<p>Der Massencode bildet die Grundschätzung. Region und Familie verfeinern sie vorsichtig. Kleine lokale Datenmengen werden zur größeren Datenbasis hin geglättet. Wenige Daten bedeuten Unsicherheit, nicht eine schlechte Bewertung. Unzureichend untersuchte Systeme zählen nicht als negative Treffer.</p>
<h3>Potenzialindex</h3>
<p>Potenzialindex 100 entspricht dem persönlichen historischen Durchschnitt des gedämpften Explorationspotenzials. Der Index ist keine Prozentwahrscheinlichkeit. Ein einheitliches Mapping-Szenario und gedämpfte Extremwerte ermöglichen den Vergleich; Median und geglättetes Potenzial sind geschätzte Credits, keine zugesicherten Erlöse.</p>
<h3>Besondere Funde</h3>
<p>Die Endnummer eines Systems wird nicht bewertet: Plio Aip KN-B d13-201 gehört zur Familie Plio Aip KN-B d13. BIO wird informativ gezeigt, nicht in der Hauptbewertung gewichtet. Fehlende Analysen bedeuten keine nachgewiesenen Nullwerte.</p>
<h3>Systemanalyse</h3>
<p>Systemnamen eingeben und Analysieren drücken oder Enter verwenden. Aktuelles System übernehmen nutzt den vorhandenen Spielstand. Die Analyse wird nur auf Benutzeraktion neu berechnet. Vergleichsgrundlage und Erfahrungswerte nennen ihre Ebene; ohne lokale Vergleiche wird übergeordnete Erfahrung verwendet. Die Datenbasis wird getrennt von der Empfehlung angezeigt.</p>
<p>Das Feld „System“ ist eine freie Namenseingabe. „Aktuelles System übernehmen“ füllt nur das Feld; starte danach mit „Analysieren“ oder Enter. Der Name wird lokal auf das unterstützte prozedurale Namensmuster geprüft. Eine Online-Systemauflösung oder Auswahlliste bei Mehrdeutigkeit gibt es hier nicht.</p>
<p>Bei leerer Eingabe, ungeeignetem Namen, fehlenden qualifizierten Vergleichsdaten oder einem Fehler erscheint ein Hinweis statt des bisherigen Ergebnisses. Eine erfolgreiche Analyse zeigt Empfehlung, Potenzialindex und lokale Datenbasis. Die Vergleichstabelle enthält Massencode, Region und Familie mit Systemanzahl und Datenbasis; darunter stehen Erfahrungswerte und bekannte besondere Funde.</p>
<h3>Erfahrungsdaten</h3>
<p>Historische Treffer nach Systemkürzel. Diese Werte zeigen deine bisherige Explorationserfahrung und sind keine direkte Prognose für ein einzelnes Zielsystem. Datenbasis und Aussagekraft beschreiben die Verlässlichkeit der Vergleichsdaten anhand der vorhandenen Stichprobe und ihrer Verteilung über Sektoren.</p>
<p>Im Reiter „Erfahrungsdaten“ wählst du unter „Ziel“ eine Fundart, kein Reiseziel: etwa ein Explorer-Ziel, eine BIO-Gattung oder BIO-Art. Die erste Auswertung erfolgt beim Aufbau der Ansicht. Nach Änderungen an Ziel oder Mindestanzahl bleibt die bisherige Rangliste stehen, bis du „Neu auswerten“ drückst.</p>
<p>Das Zahlenfeld neben der Zielauswahl legt die Mindeststichprobe je Kürzel fest: 1 bis 50 untersuchte Systeme, anfangs 3. Kürzel mit weniger Systemen oder ohne historischen Treffer für die gewählte Fundart erscheinen nicht in der Rangliste.</p>
<p>Die Tabelle „Historische Muster“ zeigt bis zu 50 Kürzel mit Rang, Erfolg bisher (Treffer-Systeme / untersuchte Systeme), Trefferquote und Aussagekraft. Die Reihenfolge folgt der geglätteten historischen Bewertung, nicht allein der Trefferquote. Beide Tabellen haben eine feste Reihenfolge ohne Spaltensortierung oder Detailaktion. Ohne passende Muster erscheint ein Leerhinweis; bei einem Auswertungsfehler wird die Rangliste geleert und ein Fehlerhinweis angezeigt. Die Analyse berechnet keine Reiseroute.</p>
""",
    ),
    "route_planner": (
        "Routenplaner",
        """<h2>Routenplaner</h2>
<h3>Überblick</h3>
<p>Der Routenplaner berechnet Strecken zwischen Systemen über Spansh. Wähle „Schiffsroute“ oder „Fleet Carrier / CTSVision“. Dafür ist eine Netzwerkverbindung erforderlich; CMDRHelper steuert weder Schiff noch Carrier.</p>

<h3>Start und Ziel</h3>
<p>„Startsystem“ folgt dem aktuell bekannten System des aktiven Commanders, bis du einen eigenen Start eingibst. Ein leeres Startfeld aktiviert diese Vorbelegung wieder. Gib das vollständige „Zielsystem“ ein; ein aus Favoriten übernommenes Routenziel bereitet die Schiffsroute vor, startet aber keine Berechnung.</p>
<p>Start und Ziel werden vor der Berechnung eindeutig geprüft. Ähnlich geschriebene Systeme werden nicht ersatzweise gewählt. Bei unbekannten oder mehrdeutigen Namen erscheint eine Meldung; korrigiere die Eingabe.</p>

<h3>Schiffsroute</h3>
<p>Eine Schiffsauswahl gibt es hier nicht: Bekannte Daten des aktiven Schiffs belegen die technischen Felder vor. Selbst geänderte Werte bleiben als manuelle Vorgaben erhalten. „Schiffsdaten übernehmen“ übernimmt erneut die verfügbaren Schiffsdaten. Beachte die Anzeige zu vollständigen, unvollständigen, veralteten oder unbekannten FSD-Daten.</p>
<p>Prüfe „Haupttankkapazität“, „Aktuelle Fracht“, „Basismasse“, „Reservetankkapazität“, „Reservekraftstoff“, „FSD-Optimalmasse“, „Maximales FSD-Fuel pro Sprung“, „Fuel Power“, „Fuel-Multiplikator“ und „Reichweitenbonus“. Die Sprungeigenschaften ergeben sich aus diesen Angaben; ein einzelnes Feld für die normale Schiffs-Sprungreichweite gibt es nicht. Änderungen an Fracht oder Ausstattung können die erreichbare Reichweite verändern.</p>

<h3>Schiffsoptionen und Berechnung</h3>
<p>„Routingalgorithmus“ bietet optimistic, pessimistic, fuel, fuel_jumps und guided. Diese Auswahl wird an Spansh übergeben.</p>
<p>Die Optionen sind „Supercharge/Neutronensterne verwenden“, „Schiff startet bereits supercharged“, „FSD-Injektionen verwenden“, „Sekundärsterne ausschließen“ und „An jedem scoopbaren Stern tanken“. Sie betreffen Neutronenunterstützung, einen bereits verstärkten Start, FSD-Injektionen, Sekundärsterne und Tankstopps. Starte mit „Schiffsroute mit Spansh berechnen“.</p>

<h3>Carrierroute</h3>
<p>„Fleet Carrier / CTSVision“ plant eine Carrierroute ohne Auswahl oder Steuerung eines bestimmten Carriers. Gib „Tritium im Tank“ und „Tritium im Carrier-Lager“ ein; zusammen sind höchstens 25.000 t zulässig. „Berechnete Carrier-Masse“ zeigt 25.000 t zuzüglich dieser beiden Angaben.</p>
<p>„Maximale Sprungreichweite“ ist von 1 bis 500 ly einstellbar, mit 500 ly als Vorgabe. „Route mit Spansh berechnen“ startet die Berechnung. Während dieser Anfrage ist der Carrier-Berechnungsbutton gesperrt.</p>

<h3>Spansh und Wartezeit</h3>
<p>Die eigentliche Routenberechnung läuft im Hintergrund bei Spansh. Die Statusanzeige meldet die laufende Anfrage und danach Erfolg oder Fehler. Hier werden Routen berechnet, keine Handelsmarktpreise oder Stationsinformationen abgerufen. Die Routenansicht bietet keinen Abbrechen-Button für eine laufende Berechnung.</p>

<h3>Routenergebnis</h3>
<p>Die Liste zeigt die feste Routenfolge mit Nummer, System, Sprungentfernung und Restentfernung. Sie ist keine frei sortierbare Angebotsliste. Bei Schiffsrouten kommen Treibstoffverbrauch, Tankinhalt, Neutronen- und Tankhinweise hinzu; bei Carrierrouten Tritiumverbrauch.</p>
<p>Darunter stehen Gesamtentfernung, Sprungzahl und Gesamtverbrauch beziehungsweise geschätztes Tritium. Fehlende Angaben bleiben als „–“ erkennbar. Prüfe die Planung gegen den tatsächlichen Zustand im Spiel.</p>

<h3>Fortschritt und nächstes Ziel</h3>
<p>Eine erfolgreich berechnete Schiffsroute wird automatisch übernommen. „Aktuelles System“, „Nächstes Ziel“ und „Routenstatus“ zeigen die aktuelle Position, den nächsten Routenschritt und den Zustand. Die Liste bleibt erhalten; erledigte Schritte erhalten keine zusätzliche Häkchenanzeige.</p>
<p>Ein erkannter Schiffssprung zum nächsten oder einem späteren System der Route setzt den Fortschritt vorwärts und kopiert den danach folgenden Systemnamen automatisch in die Zwischenablage. Wiederholte Standortmeldungen und Carrier-Sprünge zählen nicht als solche Fortschrittssprünge.</p>
<p>Beim Laden der Route wird noch kein Name automatisch kopiert. Verwende dafür „Nächstes Ziel kopieren“; der Button ist auch später verfügbar, solange ein nächstes Ziel existiert. Kopiert wird nur der Systemname: kein automatisches Einfügen und keine Steuerung von Elite.</p>

<h3>Abweichung und Abschluss</h3>
<p>Ein Sprung außerhalb der noch folgenden Route führt zu „Aktuelles System liegt außerhalb der Route“. Die Route und das bisherige nächste Ziel bleiben erhalten; es gibt keine automatische Neuberechnung. Ein späterer passender Vorwärtssprung kann die Route wieder aufnehmen. Alternativ berechnest du bewusst eine neue Route.</p>
<p>Am letzten Routensystem erscheint „Route abgeschlossen“. „Nächstes Ziel“ zeigt „–“, der Kopierbutton ist gesperrt und es wird kein weiterer Name kopiert. Der bisherige Inhalt der Zwischenablage wird nicht gelöscht. Die Ergebnisliste bleibt stehen.</p>

<h3>CTSVision-Export</h3>
<p>Nur die Carrierroute bietet „Für CTSVision exportieren“. Nach erfolgreicher Berechnung wählst du eine neue CSV-Datei. Sie enthält die Routenfolge und die verfügbaren Entfernungs-, Treibstoff-, Tritium- und Nachfüllangaben für die anschließende Verwendung in CTSVision.</p>
<p>Es handelt sich um einen Dateiexport, nicht um eine direkte Verbindung oder automatische Carriersteuerung. Eine vorhandene Datei wird nicht überschrieben. Abbrechen im Dateidialog erzeugt keine Datei; Schreibfehler werden gemeldet.</p>

<h3>Fehler und Hinweise</h3>
<p>Fehlende Systeme, unvollständige oder ungültige Schiffsparameter und zu hohe Tritiumangaben werden gemeldet. Erforderliche Tank-, Masse- und FSD-Werte müssen positiv sein; Reservekraftstoff darf die Reservetankkapazität nicht übersteigen.</p>
<p>Auch eine nicht gefundene Route, Netzwerkprobleme, zu lange Wartezeit oder eine unbrauchbare Spansh-Antwort führen zu einer Meldung statt zu einem erfundenen Ergebnis. Prüfe Systemnamen, Schiffsdaten und Optionen und berechne bei Bedarf erneut.</p>

<h3>Analyse und Commanderbezug</h3>
<p>„Analyse“ mit „Systemanalyse“ und „Erfahrungsdaten“ dient der Bewertung von Systemen und vorhandenen Erfahrungen. Der Routenplaner berechnet dagegen die konkrete Strecke zwischen Start und Ziel.</p>
<p>Die Vorbelegung verwendet den aktiven Commander und sein Schiff. Das bloße Betrachten eines anderen Commanders in der CMDR-Ansicht stellt diese Grundlage nicht um.</p>""",
    ),
    "images": (
        "Bilder",
        """<h2>Bilder</h2>
<p>Der Bereich „Bilder“ verwaltet die mit Elite Dangerous aufgenommenen Screenshots. CMDRHelper kann neue Aufnahmen automatisch erkennen, verarbeiten und commanderbezogen in einer Galerie ablegen.</p>

<h3>Quellordner</h3>
<p>Der Quellordner ist der Ordner, in dem Elite Dangerous seine Screenshots im BMP-Format speichert.</p>
<p>CMDRHelper kann diesen Ordner auf neue BMP-Dateien überwachen. Damit die automatische Verarbeitung funktioniert, muss der korrekte Screenshot-Ordner eingestellt sein.</p>

<h3>Zielordner</h3>
<p>Der Zielordner ist der gemeinsame Stammordner für die von CMDRHelper verarbeiteten Bilder.</p>
<p>Der Benutzer legt diesen Stammordner fest. CMDRHelper erstellt darunter bei der Verarbeitung automatisch die benötigten commanderbezogenen Unterordner.</p>

<h3>Automatische Verarbeitung</h3>
<p>Ist „Automatisch konvertieren“ aktiviert und sind gültige Quell- und Zielordner gesetzt, prüft CMDRHelper den Quellordner regelmäßig auf neue BMP-Screenshots.</p>
<p>Beim Aktivieren werden bereits vorhandene BMP-Dateien zunächst als bekannt markiert und nicht ungefragt automatisch konvertiert. Dafür steht die separate Funktion zum Konvertieren vorhandener BMPs bereit.</p>
<p>Eine neue Datei wird erst eingereiht, wenn sie bei zwei aufeinanderfolgenden Prüfungen dieselbe von null verschiedene Größe besitzt. Dadurch wird ein noch laufender Schreibvorgang nicht sofort verarbeitet.</p>

<h3>Bildkonvertierung</h3>
<p>Als Quelle verarbeitet CMDRHelper BMP-Dateien. Als Zielformat kann „PNG“ oder „JPG“ gewählt werden.</p>
<p>JPG-Dateien werden mit Qualitätsstufe 95 gespeichert. PNG-Dateien werden optimiert gespeichert.</p>
<p>Standardmäßig bleibt die ursprüngliche BMP-Datei erhalten. Ist „BMP nach Konvertierung löschen“ aktiviert, wird die Quell-BMP erst nach erfolgreicher Speicherung des Zielbildes gelöscht.</p>

<h3>Bild aufhellen</h3>
<p>Die Aufhellung wird über einen Schieberegler und ein gekoppeltes Zahlenfeld von 0 bis 50 Prozent eingestellt. Die Einstellung wird gespeichert.</p>
<p>Sie wird automatisch während jeder danach gestarteten Konvertierung angewendet – sowohl bei neu überwachten als auch bei manuell angestoßenen vorhandenen BMP-Dateien. 0 Prozent übernimmt die ursprüngliche Helligkeit; höhere Werte erhöhen die Helligkeit des erzeugten PNG- oder JPG-Bildes entsprechend.</p>
<p>Die Funktion ist keine reine Vorschau und wird nicht nachträglich auf ein in der Galerie ausgewähltes Bild angewendet. Die veränderte Helligkeit wird in der neuen Zieldatei gespeichert.</p>
<p>Die Quell-BMP bleibt dabei unverändert, sofern nicht zusätzlich das Löschen der BMP-Datei aktiviert ist. Journal-, Commander- und Explorationsdaten werden nicht verändert.</p>

<h3>Commanderbezogene Ablage</h3>
<p>Neue Screenshots werden anhand der im aktiven Live-AppState vorhandenen Journalidentität dem tatsächlich spielenden Commander zugeordnet.</p>
<p>Die Ordnerstruktur enthält Commandername und Frontier-ID, beispielsweise:</p>
<p><b>EXAMPLE_F12345678/</b></p>
<p>Die FID hält die Zuordnung auch bei mehreren Commandern eindeutig. Zwei Commander mit gleichem Namen können dadurch unterschieden werden.</p>

<h3>Dateinamen</h3>
<p>Neue verarbeitete Bilder erhalten einen Namen mit Aufnahmezeitpunkt, Commandername und – wenn vorhanden – dem beim Einreihen bekannten Sternensystem.</p>
<p>Beispiel:</p>
<p><b>2026-09-04_13-18-22_EXAMPLE_Sol.png</b></p>
<p>Die FID steht im commanderbezogenen Ordnernamen, nicht noch einmal im Bilddateinamen.</p>

<h3>Sichere Dateinamen</h3>
<p>CMDRHelper bereinigt Commander- und Systemnamen für die Verwendung als Datei- und Ordnerbestandteile.</p>
<p>Unzulässige Steuer- und Windows-Zeichen werden ersetzt, Leerraum wird vereinheitlicht, problematische Punkte oder Leerzeichen am Ende werden entfernt und reservierte Windows-Namen wie CON oder NUL abgesichert.</p>

<h3>Aufnahmezeitpunkt</h3>
<p>Für die Benennung verwendet CMDRHelper den Änderungszeitpunkt der stabil erkannten BMP-Datei. Nur falls dieser nicht gelesen werden kann, wird der aktuelle Zeitpunkt verwendet.</p>
<p>Damit richtet sich der Name normalerweise nach der Quelldatei und nicht nach dem späteren Konvertierungszeitpunkt.</p>

<h3>Mehrere Bilder in derselben Sekunde</h3>
<p>Existiert der vorgesehene Dateiname bereits oder ist er für eine laufende Konvertierung reserviert, ergänzt CMDRHelper fortlaufend <code>_2</code>, <code>_3</code>, <code>_4</code> und so weiter.</p>
<p>Dadurch überschreibt ein weiterer Screenshot mit demselben Zeitstempel kein vorhandenes Zielbild.</p>

<h3>Commanderwechsel während der Verarbeitung</h3>
<p>Commander, FID und System werden beim Einreihen eines Screenshots gemeinsam festgehalten.</p>
<p>Ein späterer Commanderwechsel verändert die Zuordnung dieses bereits wartenden Bildes nicht. Ein Screenshot von EXAMPLE wird dadurch nicht nachträglich in den Ordner eines anderen Commanders geschrieben.</p>

<h3>Galerie</h3>
<p>Die Galerie zeigt PNG-, JPG- und JPEG-Dateien aus den zum gewählten Filter gehörenden Verzeichnissen. Neue, gelöschte oder verschobene Bilder werden regelmäßig erkannt.</p>
<p>Der Galeriefilter verändert weder Ablageort noch Commanderzuordnung der Dateien.</p>

<h3>Aktueller Commander</h3>
<p>Der Filter „Aktueller Commander“ zeigt Bilder aus dem Ordner des derzeit in der CMDR-Ansicht betrachteten Commanders.</p>
<p>Der betrachtete Commander bestimmt nur die Galerieanzeige. Die Zuordnung eines neuen Live-Screenshots verwendet dagegen die beim Einreihen aktive Journalidentität.</p>

<h3>Alle Commander</h3>
<p>Der Filter „Alle Commander“ zeigt gemeinsam die Bilder aus den gültigen Unterordnern aller bekannten Commander. Auch der besondere Ordner für Aufnahmen ohne erkannte Identität wird berücksichtigt.</p>
<p>Die Dateien werden dabei nicht verschoben oder zusammengeführt.</p>

<h3>Nicht zugeordnet</h3>
<p>Der Filter „Nicht zugeordnet“ zeigt unterstützte Bilddateien, die direkt im gemeinsamen Ziel-Stammordner liegen.</p>
<p>So bleiben insbesondere ältere Bilder ohne commanderbezogenen Unterordner sichtbar. CMDRHelper versucht nicht, deren Zugehörigkeit nachträglich zu erraten.</p>

<h3>Bestehende Bilder</h3>
<p>Bereits vorhandene Bilder im Stammordner werden nicht automatisch verschoben oder umbenannt.</p>
<p>Sie bleiben über „Nicht zugeordnet“ erreichbar, sofern sie als PNG, JPG oder JPEG vorliegen.</p>

<h3>Bild auswählen und ansehen</h3>
<p>Ein einfacher Klick auf ein Vorschaubild zeigt das Bild skaliert im Vorschaubereich und blendet seinen Dateinamen ein.</p>
<p>Ein Doppelklick öffnet die Datei mit der für Bilder eingestellten Anwendung des Betriebssystems.</p>
<p>Mehrere Bilder können gleichzeitig markiert werden. Beim Ändern der Fenstergröße wird die Vorschau des aktuellen Bildes passend neu skaliert.</p>

<h3>Bild löschen</h3>
<p>Markierte Bilder können über „Ausgewählte löschen“ oder die Entf-Taste gelöscht werden. Vor dem Löschen erscheint eine Sicherheitsabfrage; ohne Auswahl wird zunächst auf die notwendige Auswahl hingewiesen.</p>
<p>Gelöscht werden ausschließlich die ausgewählten PNG-/JPG-/JPEG-Zieldateien aus den Verzeichnissen des derzeitigen Galeriefilters. Die ursprüngliche BMP-Quelldatei ist davon nicht betroffen.</p>

<h3>Zielordner öffnen</h3>
<p>„Zielordner öffnen“ öffnet den Ablageort im Dateimanager und legt den gemeinsamen Stammordner bei Bedarf an.</p>
<p>Beim Filter „Aktueller Commander“ wird dessen vorhandener Commander-Unterordner geöffnet. Existiert er noch nicht oder ist ein anderer Filter aktiv, wird der gemeinsame Stammordner geöffnet.</p>

<h3>Sicherheit der Bildpfade</h3>
<p>Vor dem Löschen prüft CMDRHelper den kanonischen Pfad jeder Datei. Er muss innerhalb des konfigurierten Zielordners und unmittelbar in einem durch den aktuellen Galeriefilter erlaubten Verzeichnis liegen.</p>
<p>Symbolische Verknüpfungen werden weder als Commanderordner noch als Galeriebilder verwendet und nicht über die Galerie gelöscht. Pfade außerhalb des Zielbereichs sowie Traversal-Pfade werden abgewiesen.</p>

<h3>Wenn kein Commander erkannt wurde</h3>
<p>Fehlen Commander und FID beim Einreihen einer neuen Aufnahme, wird die Datei nicht zurückgestellt und keinem bekannten Commander zugeordnet.</p>
<p>Sie wird im Unterordner <b>UNKNOWN_UNKNOWN/</b> verarbeitet; der Dateiname verwendet für den Commander ebenfalls <b>UNKNOWN</b>. Dieser Ordner kann über „Alle Commander“ angezeigt werden, nicht über den Stammordnerfilter „Nicht zugeordnet“.</p>

<h3>Mehrere Commander</h3>
<p>Für die Bilderverwaltung gelten zwei getrennte Regeln:</p>
<ul>
<li><b>Neue Bilder speichern:</b> Die beim Einreihen aktive Journalidentität mit Commander und FID bestimmt den Zielordner.</li>
<li><b>Bilder anzeigen:</b> Der betrachtete Commander beziehungsweise der ausgewählte Galeriefilter bestimmt die sichtbaren Bilder.</li>
</ul>
<p>So kann die Galerie eines anderen Commanders betrachtet werden, während EXAMPLE gespielt wird, ohne dass neue Screenshots im Ordner des betrachteten Commanders landen.</p>

<h3>Tipp</h3>
<p>Ein gemeinsamer Screenshot-Stammordner reicht aus. CMDRHelper übernimmt darunter für neu verarbeitete Bilder automatisch die Trennung nach Commander und FID.</p>
<p>Mit „Aktueller Commander“, „Alle Commander“ und „Nicht zugeordnet“ kann zwischen persönlicher Galerie, den Unterordnern aller Commander und älteren Bildern im Stammordner gewechselt werden.</p>
<p>Eine höhere Aufhellung kann bei dunklen Aufnahmen helfen; sie wirkt auf das bei der Konvertierung neu erzeugte Zielbild.</p>""",
    ),
    "commander_view": (
        'CMDR Ansicht',
        """<h2>CMDR Ansicht</h2>
<h3>Commander auswählen</h3>
<p>Die Auswahl oben bestimmt, wessen gespeicherte Daten du betrachtest. ● Live aktiv kennzeichnet den aktiven Journal-Commander; Nur Ansicht kennzeichnet eine andere gespeicherte Ansicht. Die Auswahl macht diesen Commander nicht zum aktiven Journal-Commander: Der Hauptbereich „Missionen &amp; Belohnungen“ verwendet weiterhin den tatsächlich aktiven Commander. Persönliche Daten bleiben auch bei gleichen Namen anhand der FID getrennt. Das Betrachten startet keine Online-Übertragung.</p>

<h3>Übersicht, Vermögen und Söldnermünzen</h3>
<p>„Übersicht“ zeigt Name, FID, Status, erste und letzte Erfassung, besuchte Systeme, Bio-/Geo-Funde, Codex-Einträge und Kartographieverkäufe, Standort, offene Missionen, Schiff, Carrier sowie unverkaufte Bio-/Kartographiedaten mit bekannten Schätzwerten. „Vermögen“ ist der zuletzt gespeicherte Creditstand. „Söldnermünzen“ zeigt Frontiers gemeldete Werte: „Aktuell“, „Insgesamt ausgegeben“, „Engineering“, „Ausrüstung“ und „Von Frontier gemeldet: insgesamt verdient“. Diese Zähler müssen rechnerisch nicht zusammenpassen; CMDRHelper korrigiert sie nicht und erfindet keine Buchungshistorie. Unbekannte Werte bleiben „–“.</p>

<h3>Missionen und Exploration</h3>
<p>„Missionen“ zeigt gespeicherte offene Missionen des betrachteten Commanders mit Status, Missionsbezeichnung, Ziel, Ablaufzeit und Belohnung. Die Tabelle dient zum Ansehen; hier gibt es keine Missionsdetails oder Missionsaktionen wie im Hauptbereich. „Exploration“ zeigt unverkaufte Bio-/Kartographiedaten, Bio-Funde, First Footfalls, selbst und effizient kartierte Körper sowie besuchte Systeme. „Chronik“ ist hier ein Platzhalter; die vollständige Chronik öffnest du im Hauptmenü.</p>

<h3>Flotte und Schiffsdetails</h3>
<p>„Schiffe“ zeigt oben das aktuelle bzw. zuletzt verwendete Schiff, darunter die gespeicherte Flotte dieses Commanders. Klicke auf den Kopf einer Schiffskarte, um Details aufzuklappen. Sortiere auf-/absteigend nach Verwendung, Name, Typ, Sprungreichweite, Frachtkapazität, Leermasse, Standort oder Zeitpunkt; filtere alle Schiffe oder solche mit Fahrzeug-/Fighter-Hangar. Grün kennzeichnet das Live-Schiff, andere Farben gruppieren bekannte Standorte. Details zeigen Kennung, ShipID, Standort, Zeitpunkte, FSD/Guardian-Booster, Reichweite, Masse, Fracht-/Tankkapazitäten und Ausrüstungsstatus (vollständig, unvollständig oder veraltet). Vorhandene Moduldaten ergänzen Hangars, Schilde und Verstärkungen, Waffen und Passagierkabinen. Fehlende Angaben bleiben „–“.</p>

<h3>Eigener Fleet Carrier</h3>
<p>„Eigener Fleet Carrier“ zeigt für den gespeicherten eigenen Carrier Name, Callsign, CarrierID, letzten Standort und letzte Aktualisierung. Das sind Angaben zum eigenen Carrier, keine Handelsangebote oder Mining-Bestände.</p>

<h3>Persönliche Schiffs- und Carrierbilder</h3>
<p>Wähle „Schiffsbild auswählen…“ in den aufgeklappten Schiffsdetails oder „Carrierbild auswählen…“ beim Carrier. Unterstützt werden PNG, JPG/JPEG und WEBP. CMDRHelper speichert eine eigene lokale Kopie, getrennt nach Commander und Schiff bzw. Carrier, auch über Neustarts hinweg. Erneutes Auswählen ersetzt diese Kopie. „Eigenes Bild entfernen“ entfernt die eigene Kopie und Zuordnung; die ursprüngliche Bilddatei bleibt erhalten. Ohne eigenes Bild erscheint eine verfügbare Standardvorschau oder ein Platzhalter. Ohne eindeutige Carrier-Zuordnung ist die Bildauswahl deaktiviert. Screenshots werden nicht automatisch zugeordnet.</p>

<h3>Bildbetrachter</h3>
<p>Ein Doppelklick auf ein verfügbares Schiffs- oder Carrierbild öffnet den separaten Bildbetrachter mit der Bilddatei statt nur der kleinen Vorschau. Die Darstellung passt sich proportional der Fenstergröße an. Du kannst das Fenster vergrößern oder maximieren und mit Esc oder dem Fensterschließen schließen. Es gibt hier keine Bildnavigation oder Zoomsteuerung. Der Hauptbereich „Bilder“ verwaltet dagegen Screenshots.</p>

<h3>Schiff löschen</h3>
<p>„Schiff löschen…“ verlangt eine ausdrückliche Bestätigung; Abbrechen ist vorausgewählt. Die Aktion entfernt den lokalen Schiffseintrag einschließlich gespeicherter Ausrüstungsdaten und persönlicher Bildkopie. Das aktuelle bzw. zuletzt verwendete Schiff und ein erkanntes Live-Schiff sind geschützt; während des Neueinlesens ist Löschen gesperrt. Eine lokale Löschmarkierung verhindert das sofortige Wiederauftauchen aus alten Journaldaten. Eine neue eindeutige Aktivmeldung dieses Schiffs im Live-Journal nach der Löschung kann es wieder anzeigen. Auch das bestätigte Neueinlesen kann die Markierung aufheben. Die gelöschte persönliche Bildkopie kehrt dadurch nicht zurück.</p>

<h3>Alle Schiffe neu einlesen</h3>
<p>„Alle Schiffe neu einlesen…“ ist sinnvoll, um Flottenangaben aus vorhandenen Journalen erneut zu gewinnen oder lokal entfernte Schiffe wiederzufinden. Nach Bestätigung werden bekannte Journaldateien und Dateien im eingestellten Journalordner für den betrachteten Commander erneut ausgewertet – nur für die Flotte. Elite muss dafür nicht laufen. Neuere gespeicherte Angaben und Schiffe ohne Fund in den verfügbaren Journalen bleiben erhalten; erkannte Verkäufe werden berücksichtigt. Bei Erfolg werden die manuellen Löschmarkierungen dieses Commanders aufgehoben. Vorhandene persönliche Bilder bleiben erhalten, bereits gelöschte nicht. Andere Commander bleiben unberührt. Schlägt das Lesen oder Übernehmen fehl, bleiben die Markierungen erhalten: Journalzugriff prüfen und erneut versuchen.</p>

<h3>Lokale Daten und Sicherheit</h3>
<p>Gespeicherte Angaben können auch offline und nach einem Neustart angezeigt werden; sie sind der letzte bekannte Stand. Bilder, Löschen und Neueinlesen betreffen ausschließlich CMDRHelper. Sie verändern keine Schiffe, Carrier oder Credits in Elite Dangerous und schreiben keine Journale um.</p>""",
    ),
    "settings": (
        "Einstellungen",
        """<h2>Einstellungen</h2>
<h3>CMDRHelper</h3>
<p>Bessere Updateinformation: Das Ja/Nein-Fenster zeigt installierte und verfügbare Version sowie bis zu sechs wichtige Änderungen, sofern eine Kurzbeschreibung vorliegt. Lange Listen scrollen, die Aktionen bleiben erreichbar.</p>
<p>Im Bereich „Einstellungen“ wird festgelegt, wie CMDRHelper mit Elite Dangerous, Journaldateien, Datenbank, Online-Diensten, Oberfläche und Updates arbeitet.</p>
<p>Änderungen an Zugangsdaten und Pfaden sollten sorgfältig vorgenommen werden. Commanderbezogene Einstellungen werden soweit erforderlich getrennt nach Frontier-ID verwaltet.</p>

<h3>Journal</h3>
<p>Der Journalordner ist eine der wichtigsten Einstellungen. Er muss auf den Ordner zeigen, in dem Elite Dangerous die <code>Journal*.log</code>-Dateien des verwendeten Windows- beziehungsweise Proton-Profils ablegt.</p>
<p>Die Journale liefern unter anderem:</p>
<ul>
<li>Commanderidentität, Standort und Reisen</li>
<li>Missionen, Schiffe und Vermögen</li>
<li>Exploration, Kartographie und BIO-Daten</li>
<li>Surface Mining, Söldnermünzen und weitere unterstützte Zustände</li>
</ul>

<h3>Journalanzeige und Bedienung</h3>
<p>Die Journalgruppe zeigt den eingestellten Ordner, die Zahl gefundener Journale, ältestes und neuestes Journal, den Namen der neuesten Datei sowie den Zeitpunkt des zuletzt gelesenen Eintrags.</p>
<p>„Journalordner wählen“ ändert den Ordner. „Jetzt einlesen“ stößt die normale Aktualisierung unmittelbar an.</p>
<p>Eindeutig identifizierbare Sitzungen werden per FID zugeordnet. Neue vollständige Einträge werden inkrementell verarbeitet; sichere Lesepositionen verhindern, dass beim nächsten Start unnötig jedes Journal vollständig neu gelesen wird.</p>

<h3>Datenbank</h3>
<p>CMDRHelper speichert dauerhaft benötigte Daten in einer lokalen SQLite-Datenbank. Dazu gehören globale System- und Körperdaten ebenso wie explizit einem Commander zugeordnete Informationen.</p>
<p>Die Einstellungsseite zeigt Statistiken zum gespeicherten Datenbestand. Die Datenbank sollte nicht manuell bearbeitet werden, während CMDRHelper läuft.</p>

<h3>Journal-Archiv importieren</h3>
<p>„Journal-Archiv importieren“ gleicht die Journaldateien des eingestellten Journalordners vollständig mit der Datenbank ab. Bereits bekannte Journalbereiche werden anhand der gespeicherten Importinformationen berücksichtigt und nicht blind als neue Daten dupliziert.</p>
<p>Während eines manuell sichtbaren Imports werden Fortschritt, Anzahl und aktuell bearbeitete Datei angezeigt. Nach Abschluss meldet CMDRHelper importierte beziehungsweise bereits bekannte Daten oder einen Fehler.</p>
<p>Der Archivimport dient auch dazu, unterstützte historische Informationen aus eindeutig zugeordneten Journals nachzulernen.</p>

<h3>Commanderbezogene Daten</h3>
<p>CMDRHelper trennt persönliche Informationen anhand der FID und der zugehörigen internen Commander-ID. Dazu gehören unter anderem Missionen, Vermögen, MercCoins, persönliche Exploration und Online-Zugänge.</p>
<p>Eine unbekannte oder mehrdeutige Journalsitzung darf nicht willkürlich einem Commander zugeordnet werden.</p>

<h3>Online-Dienste</h3>
<p>CMDRHelper unterstützt EDSM und Inara. Beide Zugänge werden getrennt für jeden bekannten Commander beziehungsweise jede FID bearbeitet und gespeichert.</p>
<p>Die Auswahl in den Einstellungen bestimmt nur, wessen Zugang gerade bearbeitet oder getestet wird. Live senden darf ausschließlich der durch die aktive Journalsitzung eindeutig bestimmte Commander.</p>

<h3>Spansh-Stationsinformationen</h3>
<p>Unter „ONLINE-DIENSTE“ schaltet „Spansh-Stationsinformationen ergänzen“ die optionale Ergänzung von Stationen und Einrichtungen im Explorer und in Systemansichten ein. Der Schalter ist anfangs aus. Übermittelt wird die öffentliche Systemkennung, keine Commanderinformationen; ein eigener API-Key ist nicht erforderlich. Die Option steuert keine Handelsmarktsuche.</p>
<p>Deaktiviert werden nur lokale Journalinformationen angezeigt und keine neuen Spansh-Stationsabfragen gestartet; auch die manuelle Aktualisierung ist gesperrt. Vorhandene Stationscache-Daten werden nicht gelöscht, aber nicht zur Anzeige ergänzt. Einschalten macht vorhandene Cachedaten wieder nutzbar, startet für sich allein jedoch keine Netzabfrage.</p>

<h3>Automatische Stationsabfrage und Cache</h3>
<p>Automatisch wird nur bei einem neu erkannten Live-Eintritt des aktiven Journal-Commanders in ein anderes System geprüft, etwa nach einem Schiffssprung, Carrier-Sprung oder einer neuen bestätigten Standortmeldung. Programmstart, Commanderwechsel, Archivimport und bloßes Öffnen des Explorers oder einer Systemansicht starten keine automatische Abfrage.</p>
<p>Der separate Stationscache bleibt über Helper-Neustarts erhalten. Ein Abruf, der weniger als 7 Tage zurückliegt, gilt als frisch und vermeidet eine neue automatische Netzabfrage. Fehlende oder ältere Daten können beim nächsten passenden Live-Systemeintritt aktualisiert werden. Pro System ist höchstens ein automatischer Versuch je lokalem Kalendertag vorgesehen; auch ein Fehlschlag zählt, über Neustarts hinweg. Es gibt keine laufende Hintergrundaktualisierung aller gespeicherten Systeme. Ältere verwendbare Cachedaten dürfen weiterhin angezeigt werden, auch offline.</p>
<p>Dieser Cache enthält ergänzende Stationsinformationen, keine Handelsmarktpreise. Spansh-Community-Marktdaten für Verkaufen, Einkaufen und Empfehlungen haben einen eigenen flüchtigen RAM-Suchcache. Selbst in Elite beobachtete Handelsmarktstände sind wiederum getrennt gespeichert: Sie überleben einen Neustart, sind aber nur unter 24 Stunden gültig.</p>

<h3>Stationsdaten manuell aktualisieren</h3>
<p>Öffne „Gesamtansicht“ und wähle „Spansh-Daten aktualisieren“. Aktualisiert werden nur die Spansh-Stationsinformationen des in diesem Fenster angezeigten Systems, nicht alle gespeicherten Systeme und keine Handelsmarktpreise. Der Schalter muss aktiv sein; während einer laufenden Abfrage für dieses System ist die Aktion gesperrt.</p>
<p>Die manuelle Aktion kann die 7-Tage-Frist und einen fehlgeschlagenen automatischen Tagesversuch umgehen. Wurde das System heute nach lokalem Kalender bereits erfolgreich abgerufen, erfolgt kein erneuter Abruf: „Spansh-Daten wurden heute bereits aktualisiert.“ Ein erfolgreicher Abruf erneuert den Stationscache. Bei Fehlern bleiben vorhandene lokale und verwendbare Cachedaten erhalten; die Statuszeile zeigt den Fehlschlag. Ein fehlgeschlagener manueller Versuch kann erneut gestartet werden.</p>

<h3>EDSM-Zugang für</h3>
<p>„EDSM-Zugang für:“ wählt den zu bearbeitenden Commander. Die Auswahl zeigt „eingerichtet“ oder „nicht eingerichtet“, abhängig davon, ob ein API-Key gespeichert ist.</p>
<p>Sichtbar sind Commandername, verdecktes API-Key-Feld, „EDSM verwenden“, ein Verbindungstest und dessen letzter Teststatus.</p>
<p>Jeder Commander benötigt seinen eigenen passenden EDSM-Zugang. Die Auswahl schaltet den Live-Uploader nicht auf diesen Commander um.</p>

<h3>EDSM verwenden und testen</h3>
<p>„EDSM verwenden“ aktiviert oder deaktiviert den Dienst für die ausgewählte FID. Fehlende oder deaktivierte Zugangsdaten beeinflussen die lokale Journalverarbeitung nicht.</p>
<p>„EDSM-Verbindung testen“ prüft die aktuell im Formular sichtbaren Zugangsdaten. Ein erfolgreicher Test bestätigt die Verbindung, ändert aber weder aktive Journal-FID noch Live-Commander.</p>

<h3>Inara-Zugang für</h3>
<p>„Inara-Zugang für:“ folgt demselben Multi-CMDR-Prinzip. Pro FID werden Aktivierung, Inara-Commandername und API-Key getrennt gespeichert.</p>
<p>Auch hier zeigt die Auswahl „eingerichtet“ oder „nicht eingerichtet“. Ein Key eines Commanders wird nicht automatisch für einen anderen Commander verwendet.</p>

<h3>Inara verwenden und testen</h3>
<p>Ist Inara für die aktive Journal-FID eingerichtet und aktiviert, kann CMDRHelper die unterstützten Reise-, Standort-, Missions- und Schiffsereignisse übertragen. Nicht jedes Journalereignis wird an Inara gesendet.</p>
<p>„Inara-Verbindung testen“ prüft die aktuell sichtbaren Zugangsdaten, ohne den Live-Commander zu ändern.</p>

<h3>Inara-Outbox</h3>
<p>Unterstützte Inara-Ereignisse werden vor der Netzwerkübertragung persistent in einer Outbox vorgemerkt.</p>
<p>Vorübergehende Fehler lassen diese Einträge für spätere Versuche erhalten. Der Worker verarbeitet nur die Outbox der eindeutig aktiven Journal-FID; Einträge anderer Commander werden nicht beigemischt.</p>

<h3>Online-Status im Header</h3>
<p>EDSM zeigt aktuell:</p>
<ul>
<li><b>EDSM aus</b> – für die aktive FID nicht verwendbar oder deaktiviert</li>
<li><b>EDSM wartet</b> – eingerichtet und ohne laufende Übertragung</li>
<li><b>EDSM Übertragung</b> – der letzte EDSM-Verarbeitungslauf endete ohne Fehler; der Tooltip nennt, ob Events gesendet, Journaldaten verarbeitet oder keine neuen Daten gefunden wurden</li>
<li><b>EDSM Fehler</b> – der letzte Übertragungszustand ist fehlerhaft</li>
</ul>
<p>Für EDSM existiert derzeit kein zusätzlicher, getrennt beschrifteter Zustand „EDSM aktiv“.</p>
<p>Inara unterscheidet genauer:</p>
<ul>
<li><b>INARA aus</b> – für die aktive Journal-FID deaktiviert</li>
<li><b>INARA bereit</b> – eingerichtet, aber in dieser Sitzung noch ohne bestätigte Übertragung</li>
<li><b>INARA Übertragung</b> – der Worker sendet gerade</li>
<li><b>INARA aktiv</b> – die letzte tatsächliche Übertragung wurde erfolgreich bestätigt</li>
<li><b>INARA Fehler</b> – der letzte Übertragungsversuch ist fehlgeschlagen</li>
</ul>

<h3>API-Key-Sicherheit</h3>
<p>API-Keys sind persönliche Zugangsdaten. Die Eingabefelder stellen sie verdeckt dar; gespeichert werden sie commanderbezogen in den Anwendungseinstellungen und nicht in der CMDRHelper-Datenbank.</p>
<p>Keys sollten nicht veröffentlicht, in Screenshots weitergegeben oder in öffentliche Repositories übernommen werden.</p>

<h3>Bilder / Screenshots</h3>
<p>Quellordner, Zielordner, PNG/JPG, automatische Verarbeitung, BMP-Löschen und Aufhellung von 0 bis 50 Prozent befinden sich ausschließlich im Hauptmenü „Bilder“, nicht auf der Einstellungsseite.</p>
<p>Die kontextbezogene Hilfe „Bilder“ beschreibt diese Optionen im Detail.</p>

<h3>Oberfläche</h3>
<p>Die Oberflächengruppe enthält Erscheinungsbild, Sprache, Schriftart, Schriftgröße und den Werteschwellwert für wertvolle Explorer-Körper.</p>

<h3>Dark- und Light-Mode</h3>
<p>Zwischen dunklem und hellem Erscheinungsbild kann direkt umgeschaltet werden. Das Theme wird sofort auf die Oberfläche sowie vorhandene System- und Chronikkarten angewendet und gespeichert.</p>

<h3>Sprache</h3>
<p>Die Oberfläche bietet zwölf Sprachen zur Auswahl. „Sprache speichern“ speichert die Auswahl; für eine vollständig einheitliche Umstellung vorhandener Widgets ist anschließend ein Neustart von CMDRHelper erforderlich.</p>

<h3>Schriftart und Schriftgröße</h3>
<p>Schriftfamilie und Schriftgröße von 7 bis 24 pt können ausgewählt und gespeichert werden.</p>
<p>Beide Änderungen werden erst nach einem Neustart vollständig wirksam. Die Oberfläche weist darauf ausdrücklich hin.</p>

<h3>Werteschwellwert</h3>
<p>Der Explorer-Werteschwellwert legt fest, ab welchem geschätzten Creditwert Körper als besonders wertvoll hervorgehoben werden. Die Änderung wird unmittelbar gespeichert und aktualisiert die entsprechende Explorer-Darstellung.</p>

<h3>Automatisch einblenden</h3>
<p>„Wertvolle Körper“, „BIO-Funde“ und „Frachtraum“ befinden sich fest in der linken Seitenleiste, nicht innerhalb der Einstellungsseite.</p>
<p>Die Schalter werden gespeichert und steuern die unterstützten kleinen Livefenster. Der Werteschwellwert für „Wertvolle Körper“ wird in den Oberflächeneinstellungen festgelegt.</p>
<p>Das Frachtraumfenster verwendet ausschließlich den für die aktive Journal-FID bestätigten Cargo-Snapshot. Der in der CMDR Ansicht betrachtete Commander beeinflusst dieses Livefenster nicht.</p>
<p>„EDSM-Status-HUD“ unter „auto einblenden“ ist standardmäßig AUS. Nach einem Systemeintritt erscheint für ungefähr 2,5 Sekunden eine Kurzmeldung über Elite. Mehrere Location-Ereignisse im selben Aufenthalt lösen keine Mehrfachmeldung aus; eine echte Rückkehr darf erneut geprüft werden.</p>
<p>„EDSM: BEKANNT“ bedeutet einen gültigen EDSM-Treffer für das System. „EDSM: NICHT BEKANNT“ bedeutet eine gültige EDSM-Antwort ohne Systemtreffer. „EDSM: KEINE ANTWORT“ bedeutet einen Netzwerk-, HTTP-, Timeoutfehler oder eine ungültige Antwort, niemals einen bestätigten fehlenden Treffer. EDSM-Bekanntheit ist nicht dasselbe wie offizielle Elite-Erstentdeckung; es werden keine Erstentdecker- oder Erstmeldernamen versprochen.</p>
<p>Die Kurzmeldung funktioniert unabhängig von Navigations- und Frachtraum-HUD. Dauerhafte HUD-Anzeigen und Schnellfavoriten-Meldungen bleiben erhalten. Die Abfrage blockiert die Oberfläche nicht; verspätete Antworten auf bereits verlassene Systeme werden verworfen.</p>

<h3>Updates</h3>
<p>Die Updategruppe zeigt installierte Version und GitHub-Status. „Jetzt prüfen“ sucht manuell nach einer neuen vorgesehenen CMDRHelper-Version; zusätzlich findet nach dem Start eine verzögerte automatische Prüfung statt.</p>
<p>Ist eine neue Version verfügbar, fragt CMDRHelper vor dem Herunterladen und Installieren nach. Ein angekündigtes Datenbankupdate wird in diesem Dialog gesondert ausgewiesen.</p>
<p>Für bestehende Installationen genügt im Normalfall: Update installieren → CMDRHelper starten. Notwendige historische Korrekturen für BIO-Daten, Besuchshistorie und DSS-Metadaten laufen automatisch; vor schreibenden Datenreparaturen wird eine DB-Sicherung erstellt. Die Reparaturen sind versioniert und idempotent: Erfolgreiche Revisionen werden nicht bei jedem Start erneut vollständig ausgeführt. Rekonstruktion ist nur mit vorhandenen, lesbaren und eindeutig einem Commander zuordenbaren Elite-Journalen möglich. Fehlende Quellen werden nicht ersetzt oder als Erfolg gewertet; offene Reparaturen werden beim nächsten Start erneut versucht. Datenbanklöschung, manuelle Skripte und Neuimport sind im Normalfall nicht nötig.</p>

<h3>Downloadfortschritt</h3>
<p>Der Download läuft im Hintergrund. Bei bekannter Gesamtgröße zeigt CMDRHelper Dateiname, empfangene und gesamte MiB, Prozent, Übertragungsrate und geschätzte Restzeit.</p>
<p>Ohne bekannte Gesamtgröße arbeitet der Fortschrittsbalken im Busy-Modus und zeigt weiterhin empfangene Datenmenge sowie – soweit bestimmbar – die Rate. Vor der Installation wird das heruntergeladene ZIP geprüft.</p>

<h3>Update abbrechen</h3>
<p>„Download abbrechen“ beendet einen laufenden Download kontrolliert. Ein abgebrochener, unvollständiger oder bei der Prüfung ungültiger Download wird nicht installiert.</p>

<h3>Update unter Windows</h3>
<p>Unter Windows wird der eigentliche Aktualisierungsprozess unabhängig von der ursprünglichen Startkonsole weitergeführt. Ein Konsolenabbruch soll ihn daher nicht unbeabsichtigt mit beenden.</p>
<p>Tritt nach begonnenen Dateiänderungen ein Fehler auf, versucht die vorhandene Rollback-Sicherung die vorherige Version wiederherzustellen.</p>

<h3>Neustart nach Update</h3>
<p>Nach erfolgreicher Installation startet der Updater CMDRHelper über den vorgesehenen Startpfad neu und prüft kurz, ob der neue Prozess stabil anläuft.</p>
<p>Falls ein Release eine einmalige Datenbankaktualisierung verlangt, wird nach dem Neustart zusätzlich das Journalarchiv neu ausgewertet.</p>

<h3>Mehrere Commander</h3>
<p><b>Einstellungs-Auswahl = Wessen Online-Zugang bearbeite ich?</b></p>
<p><b>Aktive Journal-FID = Wer darf live senden?</b></p>
<p>Weder die Online-Kontoauswahl noch die CMDR Ansicht darf einen Live-Uploader auf einen nur betrachteten Commander umschalten.</p>

<h3>Hilfe</h3>
<p>„? Hilfe“ befindet sich in der linken Seitenleiste oberhalb von „auto einblenden“ und öffnet die Hilfe des aktuell sichtbaren Hauptmenübereichs.</p>
<p>Im Bereich „Einstellungen“ öffnet der Button daher direkt diese Einstellungen-Hilfe.</p>

<h3>Tipp</h3>
<p>Bei einer Neuinstallation oder bei Problemen zuerst kontrollieren:</p>
<ul>
<li>richtiger Journalordner und erkannte Commanderidentität</li>
<li>gewünschte Sprache, Theme, Schrift und Explorer-Werteschwellwert</li>
<li>Online-Zugang der richtigen FID</li>
<li>bei Bildproblemen Quell- und Zielordner im Hauptmenü „Bilder“</li>
</ul>
<p>Bei mehreren Commandern immer beachten, für welche FID die sichtbaren Online-Zugangsdaten gelten.</p>""",
    ),
    "planet_navigation": (
        "Planeten-Navigation",
        """<h2>Planeten-Navigation</h2>
<p>Der Planeten-Navigator hilft dir ausschließlich dabei, auf einem Planeten oder Mond eine bestimmte Latitude/Longitude anzufliegen. Du gibst ein Koordinatenziel vor und erhältst Entfernung und Richtung dorthin.</p>
<p>Er ist kein interstellarer Routenplaner und übernimmt keine System- oder Sprungnavigation. Du steuerst dein Schiff selbst.</p>

<h3>Navigator öffnen und Ziel eingeben</h3>
<p>Öffne im Explorer „Planeten-Navigation“ und wähle „Manuelle Eingabe …“. Das Navigatorfenster kann auch ohne aktuelle Oberflächenposition geöffnet und ein Ziel vorab eingegeben werden.</p>
<ul>
<li><b>Body:</b> Wähle den Zielplaneten oder Zielmond aus der Liste oder verwende den bereits erkannten Body. Du kannst den Bodynamen auch selbst eingeben, wenn er noch nicht in der Liste steht. Verwende im Zweifel den vollständigen Namen einschließlich Systemname.</li>
<li><b>Breitengrad (Latitude):</b> Gib die Zielbreite zwischen −90° und +90° ein.</li>
<li><b>Längengrad (Longitude):</b> Gib die Ziellänge zwischen −180° und +180° ein. Achte bei beiden Koordinaten auf das Vorzeichen.</li>
<li><b>Zielname:</b> Optional kannst du eine Bezeichnung eingeben, damit du dein Ziel leichter wiedererkennst.</li>
</ul>
<p>Mit „Ziel setzen“ übernimmst du die Eingabe. Technische IDs wie BodyID und SystemAddress musst du nicht eingeben; sie sind keine normalen Benutzereingaben.</p>

<h3>Wann startet der Kompass?</h3>
<p>Sobald ein Ziel gesetzt ist und Elite für den passenden Body gültige planetare Positionsdaten liefert, wird die Navigation automatisch aktiv. Du musst keinen gesonderten Startknopf betätigen.</p>
<p>Fehlen diese Daten noch oder gehören sie zu einem anderen Body, wartet der Navigator mit „Warte auf planetare Koordinaten …“. Ein Ziel lässt sich auch schon vor dem Empfang dieser Daten eingeben.</p>

<p>Für eine aktive Navigation benötigt Elite gültige Koordinaten, Bodyname, Ausrichtung und Planetenradius für den Zielkörper. Eine Landung ist nicht erforderlich: passende Daten können bereits beim Anflug vorliegen. Ohne gültige Position oder bei einem anderen Körper wartet der Navigator; er erfindet keine Position.</p>

<h3>Aktuellen Standort speichern</h3>
<p>„★ Aktuellen Standort speichern“ speichert deine bestätigte aktuelle Position, nicht das eingegebene Navigationsziel. Dafür müssen eine gültige Elite-Position, ein zugeordneter Commander und das System bekannt sein. Fehlen diese Angaben, ist die Aktion gesperrt oder es erscheint ein Hinweis.</p>
<p>Beim Aufruf werden System, Körper und Koordinaten festgehalten. Im Favoriten-Dialog kannst du Name, Kategorie und Notiz bearbeiten und optional ein Bild zuordnen. Erst „Speichern“ legt den Eintrag lokal und commanderbezogen ab; Abbrechen speichert nichts. Spätere Bewegungen ändern die festgehaltene Position nicht.</p>

<h3>Gespeicherte Positionen verwenden</h3>
<p>Öffne „★ Favoriten“ im Explorer. Wähle einen gespeicherten Oberflächenort und „◎ Zu den Koordinaten“, um Körper, Koordinaten und Namen als Navigationsziel zu übernehmen. Das ersetzt ein bisheriges Ziel; auf einem anderen Körper wartet der Navigator auf passende Positionsdaten.</p>
<p>Über „Bearbeiten“ kannst du Name, Kategorie und Notiz ändern. „Löschen“ entfernt den Favoriten erst nach Bestätigung, keine Elite-Daten. Favoriten bleiben über Helper-Neustarts erhalten und sind nach Commander getrennt; das aktuelle Navigationsziel selbst ist nur für die laufende Sitzung gesetzt.</p>

<h3>Planetenkugel: mehr als 380 km</h3>
<p>Bei einer Zielentfernung größer als 380 km zeigt der Navigator die Planetenkugel.</p>
<ul>
<li>Der <b>weiße Kreis</b> markiert deine eigene Position.</li>
<li>Der <b>kleine Zielpunkt</b> ist orange, wenn das Ziel auf der sichtbaren Planetenseite liegt.</li>
<li>Liegt das Ziel auf der verdeckten Rückseite, wird der Zielpunkt rot dargestellt.</li>
<li>Deine Position bleibt in der Darstellung fest. Planet und Ziel werden relativ zu deiner Position und Ausrichtung dargestellt.</li>
</ul>
<p>Der weiße Pfeil zeigt nach vorn; der gelbe Pfeil weist in die relative Zielrichtung. Die Kugel ist eine schematische Orientierungshilfe, keine geografisch genaue Geländeansicht. Ein roter Punkt bedeutet Rückseite der Kugel, nicht automatisch „hinter deinem Schiff“.</p>

<h3>Perspektivraster: bis einschließlich 380 km</h3>
<p>Bei einer Zielentfernung bis einschließlich 380 km wechselt die Anzeige automatisch auf ein gekipptes Perspektivraster. Steigt die Entfernung wieder über 380 km, erscheint erneut die Kugel.</p>
<p>Die Querlinien bilden ein <b>50-km-Entfernungsraster</b>. Der Zielpunkt wird innerhalb des Rasters entsprechend Entfernung und relativer Richtung eingezeichnet. Die Perspektive hilft dir beim weiteren Anflug; die Abstände erscheinen durch die Neigung nach hinten dichter. Für den konkreten Steuerkurs beachte zusätzlich Zielkurs und relative Richtung.</p>

<h3>Navigationswerte richtig lesen</h3>
<ul>
<li><b>Zielentfernung:</b> Die große Anzeige zeigt die verbleibende Entfernung zum Ziel entlang der gedachten Planetenoberfläche.</li>
<li><b>Zielkoordinaten:</b> Das eingegebene Koordinatenpaar des Ziels, zuerst Breitengrad, dann Längengrad. Es bleibt stehen, während du dich bewegst.</li>
<li><b>Aktuelle Koordinaten:</b> Dein zuletzt bestätigtes Koordinatenpaar aus Elite, ebenfalls Breitengrad / Längengrad.</li>
<li><b>Entfernung über Oberfläche:</b> Derselbe Oberflächenabstand wie die Zielentfernung, in der Detailanzeige gegebenenfalls genauer gerundet. Das ist keine zweite Strecke und keine direkte räumliche Entfernung durch die Luft.</li>
<li><b>Peilung:</b> Die absolute Richtung zum Ziel von deiner aktuellen Position aus, als Kompasswinkel: 000° ist Norden, 090° Osten, 180° Süden und 270° Westen.</li>
<li><b>Heading:</b> Deine aktuelle Ausrichtung, wie Elite sie liefert. Sie zeigt, wohin du gerade ausgerichtet bist, und muss noch nicht mit der Peilung übereinstimmen.</li>
<li><b>Relative Richtung:</b> Der Unterschied zwischen deiner Ausrichtung und der Peilung, beispielsweise „23° rechts“, „10° links“ oder „Geradeaus“. Bei 180° liegt das Ziel hinter dir.</li>
<li><b>Zielkurs:</b> Die hervorgehobene Peilung als absoluter Kurs, auf den du im Elite-HUD drehen kannst. Er ist kein zusätzlicher Drehwinkel.</li>
</ul>
<p>Beispiel: Bei Heading 051° und Zielkurs 074° drehst du 23° nach rechts, bis dein Elite-Kompass ungefähr 074° zeigt. Beim Weiterflug können sich Peilung und Zielkurs ändern; orientiere dich an den aktualisierten Werten.</p>
<p>An derselben Position wie das Ziel, an einem Pol oder beim genau gegenüberliegenden Punkt auf dem Planeten kann die Richtung unbestimmt sein. Dann zeigt der Navigator den entsprechenden Hinweis statt eines erfundenen Kurses.</p>

<h3>Fenstergröße</h3>
<p>Das Navigatorfenster ist frei skalierbar. Kugel beziehungsweise Perspektivraster passen sich dem verfügbaren Platz proportional an. Die Mindestgröße schützt die Lesbarkeit der Detailwerte; die Kugel bleibt rund. Position und Größe des Fensters werden gespeichert.</p>

<h3>Navigations-HUD einschalten</h3>
<p>Aktiviere links im Hauptfenster unter <b>auto einblenden → Navigations-HUD</b> den Haken. Bei gültiger Planetennavigation erscheint das HUD direkt über dem sichtbaren Elite-Fenster im Vordergrund.</p>
<p>Es zeigt drei Zeilen:</p>
<ul>
<li>relative Richtung</li>
<li>Zielkurs</li>
<li>Entfernung</li>
</ul>
<p>Das HUD ist transparent, klickdurchlässig und fokusneutral: Es verdeckt das Spiel nicht mit einer undurchsichtigen Fläche, fängt keine Mausklicks ab und nimmt Elite beim automatischen Einblenden nicht den Eingabefokus.</p>
<p>Ohne gültige Navigation oder eindeutige Richtung wird es automatisch unsichtbar. Auch wenn Elite minimiert oder nicht im Vordergrund ist, wird es ausgeblendet. Der Sidebar-Haken kann trotzdem aktiviert bleiben; er beschreibt deinen Wunsch nach automatischer Anzeige, nicht die momentane Sichtbarkeit.</p>
<p>Das HUD ist nur eine zusätzliche Anzeige. Der normale Navigator funktioniert unabhängig davon, auch bei ausgeschaltetem oder nicht verfügbarem HUD.</p>

<h3>Ein neues Ziel setzen</h3>
<p>Auf demselben Body kannst du jederzeit erneut „Manuelle Eingabe …“ öffnen und andere Koordinaten setzen. Das neue Ziel ersetzt das bisherige Navigationsziel. Bei passenden Positionsdaten aktualisiert sich der Kompass unmittelbar.</p>
<p>Mit „Navigation beenden“ entfernst du das aktuelle Ziel. Für einen weiteren Anflug setzt du einfach ein neues Ziel.</p>

<p>Das Schließen des Navigatorfensters beendet das Ziel nicht. Ein eingeschaltetes Navigations-HUD kann weiterarbeiten; „Navigation beenden“ entfernt das Ziel. Beim Verlassen des passenden Körpers oder bei fehlenden Positionsdaten wartet die Navigation und das Navigations-HUD verschwindet.</p>

<h3>Datenstand und Grenzen</h3>
<p>Die Navigation basiert auf den von Elite gelieferten Statusdaten. Aktualisierungen können abhängig vom Spielzustand verzögert eintreffen. Die Altersanzeige im Navigator zeigt, wie lange die letzte bestätigte Statusmeldung zurückliegt.</p>
<p>Der Oberflächenabstand beschreibt den kürzesten Bogen auf einer gedachten Kugel. Er ist keine Gelände- oder Straßenroute. Der Navigator kennt keine Hindernisse und keine Geländehöhen entlang der Strecke; Flughöhe, sichere Geschwindigkeit und Hindernisvermeidung bleiben deine Aufgabe.</p>

<p>Die aktuelle Position kommt aus Status.json; das Journal ergänzt Körper- und Systemzuordnungen. Das Fenster und das aktivierte Navigations-HUD halten die Aktualisierung bei Bedarf aktiv. Die Anzeige hängt von den verfügbaren Elite-Daten ab und verspricht keine garantierte Genauigkeit in Metern.</p>

<h3>Tipp</h3>
<p>Prüfe vor dem Anflug Bodyname und Vorzeichen der Zielkoordinaten. Richte dich anschließend nach dem Zielkurs im Elite-Kompass aus und beobachte relative Richtung und Entfernung. Wenn der Navigator wartet, kontrolliere, ob Elite bereits planetare Koordinaten für den Zielbody liefert.</p>""",
    ),
}

DIALOG_TITLE = "Hilfe – {area}"
CLOSE_LABEL = "Schließen"


# Database update guidance; help itself remains version independent.
HELP_TOPICS["overview"] = (HELP_TOPICS["overview"][0], HELP_TOPICS["overview"][1] + '<h3>Datenbank-Aktualisierung erforderlich</h3><p>Die Datenbank-Aktualisierung korrigiert ältere gespeicherte Zuordnungen von Sternen, Planeten und Monden. Journale werden ausschließlich gelesen. Beende Elite Dangerous vorher und stelle möglichst auch historische Journale bereit. Die CMDRHelper-Datenbank wird vorher vollständig gesichert; bei Fehlern werden Änderungen zurückgerollt und nötigenfalls wird die Sicherung wiederhergestellt. Das Backup bleibt als Sicherheitskopie erhalten. Mit Abbrechen kannst du die Aktualisierung verschieben.</p>')

HELP_TOPICS["settings"] = (HELP_TOPICS["settings"][0], HELP_TOPICS["settings"][1] + '<h3>Diagnose und Protokolle</h3><p>Unter Einstellungen → Diagnose und Protokolle kannst du die Logdatei öffnen oder ein Diagnosepaket erstellen. Die Logs liegen im Installationsordner unter logs/ (cmdrhelper.log und bis zu vier Rotationen). Das ZIP enthält bereinigte technische Logs, system_info.json und diagnose_summary.txt, keine Journale, Datenbank, FID-/Commander-Daten, Zugangsdaten, Favoriten oder Bilder. Persönliche Pfade werden durch Platzhalter ersetzt. Inhalte alter, noch nicht datenschutzbereinigter Logs werden ausgelassen. Wähle selbst den Speicherort und gib das ZIP bei Bedarf an den Support weiter; es wird nie automatisch versendet.</p>')

HELP_TOPICS["trade"] = (
    'Handel',
    """<h2>Handel</h2>
<h3>Handel – Überblick</h3>
<p>„Verkaufen“ findet Märkte, die deine Ware ankaufen. „Einkaufen“ findet eine bestimmte Ware zum Kaufen. „Empfehlungen“ zeigt, was du an deiner aktuellen Station kaufen und unter deinen Vorgaben mit Gewinn weiterverkaufen kannst.</p>

<h3>Marktdaten und Datenalter</h3>
<p>Verkaufen und Einkaufen kombinieren automatisch gültige gespeicherte eigene Marktstände mit Community-Marktdaten über Spansh. Empfehlungen kaufen ausschließlich am aktuellen eigenen Elite-Markt ein; ihre Ziele stammen normalerweise aus eigenen Beobachtungen und Spansh. Community-Ergebnisse werden nur vorübergehend im Arbeitsspeicher gehalten.</p>
<p>Alle Marktstände sind Momentaufnahmen, auch eigene Beobachtungen. Preis, Angebot und Nachfrage können sich bis zur Ankunft ändern. Beachte das Datenalter: Weder Verfügbarkeit noch Gewinn sind garantiert.</p>
<p>Ist derselbe Markt aus eigener Beobachtung und über die Community bekannt, verwendet CMDRHelper den jüngeren gültigen Marktstand.</p>

<h3>Ware auswählen</h3>
<p>Klicke auf „Ware“, suche nach dem angezeigten Namen, dem englischen Namen oder dem Symbol und wähle die Ware aus. Deutsche Namen stammen aus dem gepflegten deutschen Warenkatalog. Fehlt ein gepflegter Sprachname, erscheint der englische Katalogname oder eine lesbare Bezeichnung.</p>

<h3>Verkaufen</h3>
<p>Gesucht wird in gültigen eigenen Marktständen und Community-Marktdaten. Wähle Ware, „Menge (t)“ und Filter, dann „Besten Verkauf suchen“. Gesucht werden Ankaufsangebote mit ausreichender Nachfrage für die eingegebene Menge. „Preis / t“ ist der Preis, den du beim Verkauf erhältst. „Möglicher Erlös“ = Preis × eingegebene Menge. Ausgangspunkt ist dein aktuelles Commander-System. Standardmäßig steht der höchste Verkaufspreis zuerst.</p>

<h3>Einkaufen</h3>
<p>Gesucht wird in gültigen eigenen Marktständen und Community-Marktdaten. Wähle Ware, gewünschte Menge und Filter, dann „Günstigsten Einkauf suchen“. Das gemeldete „Angebot“ muss für die ganze Menge reichen. „Preis / t“ ist dein Einkaufspreis; „Gesamtkosten“ = Preis × gewünschte Menge. Ausgangspunkt ist dein aktuelles System. Standardmäßig steht der günstigste Einkaufspreis zuerst. Dies ist eine gezielte Warensuche, keine Gewinnempfehlung.</p>

<h3>Filter und Ergebnistabellen</h3>
<ul>
<li><b>Umkreis (ly):</b> maximale Entfernung des Zielsystems vom Ausgangssystem.</li>
<li><b>Max. Marktdatenalter / Datenalter Ziel:</b> höchstes zugelassenes Alter des Marktstands; bei Empfehlungen gilt der Filter für das Ziel.</li>
<li><b>Landeplatz:</b> mindestens benötigte Landeplatzgröße, keine exakte Stationsgröße. „Mittel“ erlaubt auch große Landeplätze; „Alle“ schränkt nicht ein.</li>
<li><b>Fleet Carrier einbeziehen:</b> Carrier zulassen oder ausschließen.</li>
<li><b>Max. Anflug (Ls):</b> maximale Entfernung der Station vom Ankunftsstern. Leer bedeutet keine Einschränkung. Ohne bekannte Anflugdistanz kann ein Ziel diesen Filter nicht erfüllen.</li>
</ul>
<p>Für eigene und Community-Treffer gelten dieselben Filter für Datenalter, Umkreis, Landeplatz, Carrier und Anflug. Fehlende Angaben werden nicht geschätzt. Ziele ohne bekannte Systementfernung oder ohne Nachweis einer gesetzten Einschränkung werden ausgeschlossen. Das betrifft bei eigenen Märkten besonders fehlende Landeplatz- und Anflugdaten; bei ausgeschlossenen Carriern muss bekannt sein, dass ein Ziel kein Carrier ist.</p>
<p>Klicke auf Spaltenüberschriften zum Sortieren: Zahlen nach Zahlenwert, Datenalter nach tatsächlichem Alter und Landeplätze nach Größenklasse. Verkaufen und Einkaufen zeigen höchstens 100 Treffer. „Es gibt weitere Treffer. Filter einschränken.“ weist auf eine begrenzte Suche hin. Die verfügbaren eigenen und Community-Treffer werden gemeinsam nach Preis sortiert, bevor die Liste begrenzt wird. Wegen der Suchgrenzen des Community-Dienstes sind dies nicht garantiert die besten Angebote insgesamt.</p>
<p>Scheitert bei Verkaufen oder Einkaufen die Community-Suche, bleiben passende eigene Treffer nutzbar. CMDRHelper kennzeichnet die Suche dann als unvollständig: Möglicherweise fehlen bessere Community-Angebote.</p>

<h3>Eigene Marktdaten</h3>
<p>Öffne beim angedockten Commander den Warenmarkt in Elite. Während CMDRHelper läuft, übernimmt es den Markt automatisch, wenn die Zuordnung zur aktuellen Station sicher ist. Ein manueller Import ist nicht nötig. Erneutes Öffnen aktualisiert den Stand.</p>
<p>Pro Markt und Commander bleibt ein aktueller Stand erhalten, jünger als 24 Stunden. Ältere Stände werden automatisch entfernt; es gibt keine dauerhafte Preishistorie. Gültige eigene Stände überleben einen Helper-Neustart. „Eigene Marktdaten: X Stationen“ zählt die gültigen eigenen Stationsmärkte des aktiven Commanders. Der eingestellte Filter „Max. Marktdatenalter“ gilt zusätzlich für eigene Treffer.</p>
<ul>
<li><b>✓ Eingelesen:</b> Unter Empfehlungen liegt ein gültiger eigener Marktstand der aktuellen Station vor.</li>
<li><b>Warenmarkt öffnen:</b> Für diese Station fehlt ein verwendbarer eigener Stand.</li>
<li><b>Marktstand veraltet:</b> Ein zuvor angezeigter Stand ist inzwischen ungültig. Öffne den Warenmarkt erneut.</li>
</ul>
<p>Wurde ein alter Stand bereits vor Öffnen der Ansicht entfernt, erscheint ebenfalls „Warenmarkt öffnen“. Im Flug wird kein positiver Status für die vorige Station gezeigt.</p>

<h3>Empfehlungen</h3>
<p>Voraussetzungen sind die aktuelle Station, ihr gültiger eigener Marktstand sowie das bekannte aktuelle Schiff mit sicher bekanntem freiem Frachtraum. Bereits belegter Platz wird abgezogen. Bei unbekanntem oder vollem Frachtraum ist keine neue Suche möglich; Mengen werden nicht erfunden. Nach dem Abflug wird nicht auf Basis des alten Aufenthalts neu gerechnet.</p>
<p>Stelle „Mindestgewinn“ ein: 10 % berücksichtigt nur Möglichkeiten ab mindestens 10 % Marge. Gesucht wird für lokal angebotene Waren. Die Einkaufsstation selbst ist kein Ziel. Bei derselben Zielstation (gleiche MarketID) zählt der jüngere gültige Marktstand. Pro Ware erscheint das geprüfte Ziel mit dem höchsten „Möglicher Gewinn“ unter deinen Filtern, nicht zwingend das beste Ziel der gesamten Galaxis. Die Tabelle beginnt mit dem höchsten möglichen Gewinn; „Quelle“ zeigt „Elite lokal“ oder „Spansh“, „Datenalter Ziel“ das Alter des Zielstands.</p>

<h3>Nur eigene Marktdaten</h3>
<p>Diese Checkbox gibt es nur unter „Empfehlungen“. Verkaufen und Einkaufen verwenden automatisch beide Quellen. Diese Checkbox beschränkt die Empfehlungssuche auf gültige selbst beobachtete Zielmärkte. Es gibt keine Community-Abfrage; Spansh wird hierfür nicht benötigt. Umkreis, zusätzliches Zieldatenalter, Mindestgewinn sowie Landeplatz-, Carrier- und Anflugfilter gelten weiterhin und müssen anhand vorhandener Angaben erfüllbar sein. Das bewusste Auslassen der Community-Suche ist kein Fehler und macht die Suche nicht unvollständig. So kannst du schnell zwischen bereits besuchten Stationen suchen.</p>

<h3>Möglicher Gewinn und Menge</h3>
<ul>
<li><b>Gewinn / t:</b> Verkaufspreis am Ziel − Einkaufspreis hier. „Gewinn %“ = Gewinn pro Tonne ÷ Einkaufspreis × 100.</li>
<li><b>Menge (t):</b> die kleinste Menge aus freiem Frachtraum, Angebot am Einkaufsmarkt und Nachfrage am Ziel.</li>
<li><b>Möglicher Gewinn:</b> Gewinn pro Tonne × mögliche Menge; eine Schätzung anhand der bekannten Marktstände.</li>
</ul>
<p>Beispiel: 280 t frei, 150 t Angebot, 20.000 t Nachfrage → 150 t mögliche Menge. Nicht jede Ware füllt automatisch den gesamten freien Frachtraum.</p>

<h3>Gemerkter Handelsflug</h3>
<p>Merke mit dem Häkchen genau eine Empfehlung. Eine andere Auswahl ersetzt sie. Der separate Merkbereich zeigt Ware, Zielstation, Zielsystem und „Möglicher Gewinn“ zum Zeitpunkt des Merkens. Er ist ein Merkzettel, keine laufend neu berechnete Empfehlung.</p>
<p>Er bleibt bei Kauf, Frachtraumänderung, Abflug, Systemwechsel, Docking und Marktöffnung erhalten. Er verschwindet durch „Entfernen“ oder Abwählen des Häkchens, bei einer tatsächlich gestarteten neuen Empfehlungssuche, beim Commanderwechsel und beim Beenden des Helpers. Über einen Neustart wird er nicht gespeichert.</p>
<p>„System kopieren“ kopiert ausschließlich den Zielsystemnamen in die Zwischenablage. Die Zielstation bleibt im Merkbereich sichtbar; es wird keine Route erstellt.</p>

<h3>Suche, Fortschritt und Abbruch</h3>
<p>Starte Suchen manuell. Empfehlungen prüfen mehrere Waren und können länger dauern. Nach Ermittlung des Suchumfangs zeigen Fortschrittsbalken und „Prüfe Waren: x von y …“ die tatsächlich geprüften Waren. „Abbrechen“ ist nur während einer abbrechbaren Suche verfügbar; eine laufende Netzwerkantwort kann den Abbruch verzögern. Ein Reiterwechsel bricht die laufende Suche ab; die gemeinsamen Filter von Verkaufen/Einkaufen bleiben erhalten.</p>
<p>Bei einzelnen fehlgeschlagenen Community-Abfragen oder erreichten Suchgrenzen können gültige geprüfte Empfehlungen stehen bleiben. „Unvollständige Suche“ bedeutet: Die angezeigten Treffer gelten für die geprüften Daten, aber nicht alle Waren oder Ziele wurden vollständig geprüft. Prüfe den Hinweis, schränke bei Suchgrenzen die Filter ein oder versuche es später erneut. Ein manueller Abbruch verwirft die aktuelle Ergebnisliste.</p>

<h3>Diagnose bei Problemen</h3>
<p>„Diagnose kopieren“ kopiert technische Informationen zum letzten abgeschlossenen Empfehlungslauf für die Fehlersuche. Der Text enthält keine Commander-/FID-Daten und keine Marktpreise. Die Diagnose bleibt im Arbeitsspeicher; es wird keine dauerhafte Diagnosedatei angelegt und nichts automatisch übertragen. Gib den kopierten Text bei Bedarf selbst an den Support weiter.</p>

<h3>So funktioniert eine Handelsrunde</h3>
<ol>
<li>Lande auf einer Station und öffne in Elite den Warenmarkt.</li>
<li>Öffne „Handel“ → „Empfehlungen“ und achte auf „Eingelesen“.</li>
<li>Stelle Mindestgewinn und Filter ein, dann wähle „Empfehlungen suchen“.</li>
<li>Merke die gewünschte Empfehlung mit dem Häkchen und kaufe die Ware in Elite.</li>
<li>Nutze bei Bedarf „System kopieren“ und fliege zum Ziel; die Station bleibt im Merkzettel sichtbar.</li>
<li>Verkaufe in Elite. Öffne dort den Warenmarkt, um auch die eigenen Daten des neuen Markts zu aktualisieren.</li>
</ol>""",
)
