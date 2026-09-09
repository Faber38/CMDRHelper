"""Deutsche Inhalte für die kontextbezogene Hilfe."""


HELP_TOPICS = {
    "materials": (
        "Materialien",
        """<h2>Materialien</h2>
<h3>CMDRHelper v3.2</h3>
<p>Engineering-Materialverwaltung: Alle 146 Materialien in Raw, Manufactured und Encoded, mit Graden, Maximalbeständen und Sonderfällen. Commanderbezogene Live-Bestände, Suche, Filter, fünf dezente Zeilenhintergründe und gespeicherte Spaltenbreiten/-reihenfolge erleichtern die Übersicht. Unbekannter Bestand bleibt von null unterschieden.</p>
<p>Odyssey-Inventar: Der vierte Materialreiter enthält 223 Katalogidentitäten für Güter, Komponenten, Daten und Verbrauch. Schließfach, Rucksack und verlässlicher Gesamtbestand bleiben getrennt; Missionsstapel, Missionsstatus und Engineering-Verwendung sind sichtbar. Positive Bestandszahlen erscheinen in Gold. Fehlende Namensübersetzungen verwenden Englisch.</p>
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
<p>Der vierte Reiter enthält Güter, Komponenten, Daten und Verbrauchsgegenstände. Schließfach und Rucksack werden getrennt angezeigt. Gesamt erscheint nur, wenn beide Zustände zuverlässig zusammenpassen. Ein veralteter Rucksack wird nicht hinzugezählt; unbekannte Werte erscheinen als ?. Die Grenze 1000 gilt für die jeweilige Schließfachkategorie, nicht für einzelne Gegenstände. Für Verbrauchsgegenstände wird keine unbestätigte Kapazität angezeigt.</p>
<p>Die Kennzeichnung Mission gehört zum jeweiligen Bestandsstapel. Normale und missionsgebundene Gegenstände bleiben getrennt. Auch nach Missionsabschluss bleibt ein Gegenstand gekennzeichnet, solange das Journal ihn im Bestand führt. Der Tooltip zeigt Missionsnummer und bekannten Status. Engineering weist auf mindestens eine Verwendung für Anzug, Waffen oder Ingenieurfreischaltung hin; die einzelnen Verwendungen stehen im Tooltip.</p>
<p>Die Suche findet lokale und englische Namen. Die Odyssey-Filter zeigen alle Gegenstände, Missionsstapel, Engineering-Gegenstände, positiven Rucksack- oder Schließfachbestand oder sicher bekannten Gesamtbestand 0. Unbekannt ist nicht 0. Fehlende Übersetzungen fallen auf den englischen Namen zurück.</p>
<p>Der Bestand wird im Hintergrund automatisch aktualisiert. Bestätigte neue Aufnahmen können kurz hervorgehoben werden. Beim Commanderwechsel werden alte Bestände sofort entfernt. Unterreiter, Filter sowie Spaltenbreiten und Reihenfolge werden für Odyssey separat gespeichert.</p>""",
    ),
    "overview": (
        "Übersicht",
        """<h2>Übersicht</h2>
<p>Die Übersicht ist die Startseite von CMDRHelper. Sie fasst die wichtigsten Informationen des aktuell aktiven Commanders zusammen und zeigt auf einen Blick, ob Journal, Standort und Online-Dienste korrekt erkannt werden.</p>

<h3>Commander &amp; Schiff</h3>
<p>Hier werden der aus dem Elite-Dangerous-Journal erkannte Commander und das aktuell verwendete Schiff angezeigt.</p>
<p>CMDRHelper ordnet persönliche Daten anhand der Frontier-ID (FID) dem jeweiligen Commander zu. Dadurch bleiben Daten verschiedener Commander voneinander getrennt.</p>
<p>Beim Wechsel des Commanders werden die zum neuen Commander gehörenden gespeicherten Informationen geladen.</p>

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
<p>Wenn Commander, Schiff oder Standort nicht zum aktuellen Spielstand passen, zuerst die Journalanzeige oben und anschließend unter „Einstellungen“ den eingestellten Journalordner prüfen.</p>""",
    ),
    "missions": (
        "Missionen",
        """<h2>Missionen</h2>
<p>Die Missionsansicht zeigt die aus dem Elite-Dangerous-Journal bekannten Missionen des aktuell betrachteten Commanders. CMDRHelper speichert Missionsdaten commanderbezogen, damit offene Missionen auch nach einem Neustart von Elite Dangerous oder CMDRHelper erhalten bleiben.</p>

<h3>Offene Missionen</h3>
<p>Neue Missionen werden aus <code>MissionAccepted</code> übernommen und dauerhaft gespeichert.</p>
<p>Solange kein abschließendes Missionsereignis vorliegt, bleibt die Mission als offen erhalten. Eine neue Spielsitzung ohne Missionsliste darf bereits bekannte offene Missionen nicht automatisch entfernen.</p>

<h3>Missionsstatus</h3>
<p>CMDRHelper verarbeitet unter anderem folgende Statusänderungen:</p>
<ul>
<li>Mission angenommen</li>
<li>Mission abgeschlossen</li>
<li>Mission fehlgeschlagen</li>
<li>Mission abgebrochen</li>
<li>Missionsziel umgeleitet</li>
<li>Fortschritt bei unterstützten Fracht-/Depotmissionen</li>
</ul>
<p>Ein abschließendes Ereignis verändert nur die dazugehörige Mission.</p>

<h3>Missionen aus dem Journal</h3>
<p>Elite Dangerous liefert Missionsinformationen über verschiedene Journalereignisse. CMDRHelper führt diese Ereignisse zu einem dauerhaften Missionszustand zusammen.</p>
<p>Ein echtes vollständiges Missions-Ereignis kann als autoritativer Snapshot dienen. Fehlt ein solches Ereignis, werden ältere offene Missionen nicht allein deshalb geschlossen.</p>

<h3>Ziele und Orte</h3>
<p>Soweit Elite die Informationen im Journal liefert, zeigt CMDRHelper:</p>
<ul>
<li>Zielsystem</li>
<li>Zielstation oder Zielort</li>
<li>Zielplanet beziehungsweise Body</li>
<li>Missionsbezeichnung</li>
<li>bekannten Fortschritt</li>
<li>aktuellen Status</li>
</ul>
<p>Nicht jede Mission liefert alle Angaben. Fehlende Daten werden nicht von CMDRHelper erfunden.</p>

<h3>Persistenz und Neustart</h3>
<p>Offene Missionen werden in der commanderbezogenen Datenbank gespeichert.</p>
<p>Dadurch bleiben sie auch erhalten, wenn:</p>
<ul>
<li>Elite Dangerous beendet und später neu gestartet wird</li>
<li>CMDRHelper zwischendurch geschlossen wird</li>
<li>die neue Journalsitzung zunächst keine Missionsereignisse enthält</li>
</ul>
<p>Erst ein belegtes Missionsereignis ändert den gespeicherten Zustand.</p>

<h3>Mehrere Commander</h3>
<p>Missionen werden strikt nach Commander getrennt.</p>
<p>Ein Missionsereignis wird nur dem Commander zugeordnet, dessen Journalsitzung eindeutig identifiziert wurde. Missionen eines anderen Commanders dürfen weder angezeigt noch verändert werden.</p>

<h3>Verwaiste oder nicht mehr gültige Missionen</h3>
<p>Falls ältere Journaldaten oder ein früherer Import eine Mission offen halten, obwohl sie im Spiel nicht mehr existiert, kann die vorhandene Reset-/Bereinigungsfunktion für verwaiste Missionen verwendet werden.</p>
<p>Diese Funktion sollte nur eingesetzt werden, wenn eindeutig feststeht, dass die angezeigte Mission nicht mehr aktiv ist.</p>

<h3>Online-Dienste</h3>
<p>Unterstützte Missionsereignisse können zusätzlich an Inara übertragen werden, wenn für die aktive Journal-FID ein gültiger und aktivierter Inara-Zugang eingerichtet ist.</p>
<p>Eine fehlende oder nicht erreichbare Inara-Verbindung beeinflusst die lokale Missionsspeicherung nicht.</p>

<h3>Tipp</h3>
<p>Wenn eine Mission nicht erscheint oder einen falschen Status zeigt, zuerst prüfen, ob Elite Dangerous das entsprechende Missionsereignis bereits ins Journal geschrieben hat.</p>
<p>CMDRHelper kann nur Informationen anzeigen, die das Journal tatsächlich liefert oder die bereits aus früheren eindeutigen Missionsereignissen gespeichert wurden.</p>""",
    ),
    "explorer": (
        "Explorer",
        """<h2>Explorer</h2>
<h3>CMDRHelper v3.2</h3>
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
<p><b>ABBAU ×24</b></p>
<p>bedeutet, dass für diesen Body 24 planetare Abbaustandorte gemeldet wurden.</p>
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
<p><b>Kupfer – 56 t</b></p>
<p>Diese Angabe bedeutet, dass dieser Commander dort tatsächlich 56 t Kupfer gewonnen hat.</p>
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

<h3>Favoritenziel und Commander</h3>
<p>Für Oberflächenorte übergibt „▶ Zum Ziel“ den gespeicherten Body, Latitude, Longitude und Favoritennamen an den vorhandenen Planeten-Navigator. Das neue Ziel ersetzt das bisherige Ziel. Favoriten besitzen keine eigene Navigationslogik. Der Navigator entscheidet unverändert selbst: passende gültige planetare Daten aktivieren die Navigation, andernfalls wartet er auf diese Daten.</p>
<p>Favoriten gehören ausschließlich zum aktiven Commander. Beim Commanderwechsel wird die Liste aktualisiert; ein offener Bearbeitungsdialog wird verworfen. Ein noch als Favoritenziel geführtes Ziel des vorherigen Commanders wird beendet. Die Commander-Auswahl der Chronik erweitert diese Favoritenliste nicht.</p>
<p>„Löschen“ verlangt eine Bestätigung und entfernt nur den Favoritendatensatz und seine interne Bildkopie. Der ursprüngliche Screenshot beziehungsweise das ausgewählte Originalbild und alle Explorer-, Journal- und Bodydaten bleiben erhalten.</p>""",
    ),
    "chronicle": (
        "Chronik",
        """<h2>Chronik</h2>
<h3>CMDRHelper v3.2</h3>
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
<p>Für FABER38 kann beispielsweise erscheinen:</p>
<ul>
<li>Alle</li>
<li>Kupfer</li>
</ul>
<p>Werden später weitere Rohstoffe tatsächlich abgebaut, erscheinen diese automatisch in der persönlichen Auswahl.</p>

<h3>Gezielte Rohstoffsuche</h3>
<p>Wird beispielsweise „Kupfer“ ausgewählt und anschließend „Anwenden“ gedrückt, zeigt die Chronik nur Bodies, auf denen der betrachtete Commander nachweislich Kupfer abgebaut hat.</p>
<p>Beispiel:</p>
<p><b>Prua Hypai NV-E c28-66 / 2 — ABBAU ×24 — Kupfer 56 t</b></p>
<p>Damit kann die Chronik als persönliche Fundort-Datenbank verwendet werden: Ein bereits früher abgebauter Rohstoff lässt sich später gezielt wiederfinden.</p>

<h3>Alle Rohstoffe</h3>
<p>Bei „Rohstoff: Alle“ werden alle passenden persönlichen Surface-Mining-Funde berücksichtigt.</p>
<p>Sind auf einem Body mehrere Commodities bekannt, können diese mit ihren bisher selbst gewonnenen Mengen gemeinsam angezeigt werden.</p>
<p>Beispiel:</p>
<p><b>ABBAU ×24 — Helium-3 18 t, Kupfer 56 t</b></p>
<p>Die Mengen sind persönliche, tatsächlich aus Journalereignissen belegte Abbauwerte des jeweiligen Commanders.</p>
<p>Auch bei aktivem Zeitraum bleiben persönliche Mining-Mengen gespeicherte Gesamtmengen. <b>Kupfer 56 t</b> bedeutet nicht automatisch <b>56 t im ausgewählten Zeitraum</b>. Der Zeitraum verlangt einen passenden Systembesuch, begrenzt aber nicht die angezeigte Abbaumenge auf diesen Zeitraum.</p>

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
        "Sprungtipp",
        """<h2>Sprungtipp</h2>
<p>Der Sprungtipp unterstützt bei der Exploration, indem bereits bekannte Systemdaten ausgewertet und interessante Zielsysteme hervorgehoben werden.</p>
<p>Die Funktion ist als Entscheidungshilfe gedacht. Sie garantiert nicht, dass ein empfohlenes System tatsächlich seltene oder besonders wertvolle Funde enthält.</p>

<h3>Grundlage der Auswertung</h3>
<p>CMDRHelper verwendet vorhandene Journal- und Datenbankinformationen, um bekannte Muster in Systemnamen und Systemklassen auszuwerten.</p>
<p>Dabei können unter anderem Systemkürzel, bereits bekannte Körperarten und frühere Funde berücksichtigt werden.</p>

<h3>Systemkürzel</h3>
<p>Viele prozedural erzeugte Systeme in Elite Dangerous enthalten Buchstaben- und Zahlenkombinationen, die bestimmte Systemgruppen kennzeichnen.</p>
<p>CMDRHelper kann diese Kürzel statistisch auswerten und anzeigen, in welchen Gruppen in den eigenen bisher bekannten Daten häufiger interessante Funde aufgetreten sind.</p>

<h3>Neu auswerten</h3>
<p>Mit „Neu auswerten“ wird die vorhandene Datenbasis erneut analysiert.</p>
<p>Dabei werden die gespeicherten Daten des Commanders verwendet. Die Funktion erzeugt keine neuen Elite-Daten und verändert keine Journaldateien.</p>

<h3>Ergebnisliste</h3>
<p>Die Ergebnisliste zeigt die nach der aktuellen Auswertung interessantesten Systemkürzel beziehungsweise Kandidaten.</p>
<p>Je nach vorhandener Datenbasis können dort unter anderem Hinweise auf:</p>
<ul>
<li>interessante Planetenklassen</li>
<li>biologische Funde</li>
<li>Wasserwelten</li>
<li>terraformierbare Körper</li>
<li>andere auffällige Explorationsergebnisse</li>
</ul>
<p>erscheinen.</p>

<h3>Wahrscheinlichkeit statt Garantie</h3>
<p>Ein hoher Wert oder eine gute Platzierung bedeutet nur, dass in den bisher ausgewerteten Daten ein bestimmtes Muster häufiger mit interessanten Funden verbunden war.</p>
<p>Es handelt sich nicht um eine Garantie.</p>
<p>Ein empfohlenes System kann trotzdem vollständig uninteressant sein, während ein niedrig bewertetes System wertvolle Funde enthalten kann.</p>

<h3>Eigene Datenbasis</h3>
<p>Der Sprungtipp arbeitet mit den bereits bekannten Daten des Commanders.</p>
<p>Je mehr Systeme und Bodies im Laufe der Zeit erfasst werden, desto größer wird die persönliche Datenbasis für die Auswertung.</p>
<p>Dadurch kann sich die Rangfolge später verändern.</p>

<h3>Mehrere Commander</h3>
<p>Persönliche Auswertungen werden commanderbezogen behandelt.</p>
<p>Daten eines anderen Commanders dürfen die persönliche Bewertung nicht unbemerkt verfälschen.</p>
<p>Globale astronomische Stammdaten können dagegen gemeinsam genutzt werden, sofern sie nicht commanderbezogene persönliche Funde darstellen.</p>

<h3>Verwendung in der Praxis</h3>
<p>Der Sprungtipp eignet sich besonders, wenn mehrere mögliche Ziele zur Auswahl stehen und eine zusätzliche Entscheidungshilfe gewünscht ist.</p>
<p>Er ersetzt keinen vollständigen Routenplaner und berechnet keine sichere optimale Route.</p>
<p>Für konkrete Streckenplanung steht der Menüpunkt „Routenplaner“ zur Verfügung.</p>

<h3>Tipp</h3>
<p>Verwende den Sprungtipp als zusätzliche Explorationhilfe:</p>
<p>„Welches System wirkt nach meinen bisherigen Daten interessanter?“</p>
<p>Nicht als Vorhersage:</p>
<p>„In diesem System befindet sich garantiert ein bestimmter Fund.“</p>""",
    ),
    "route_planner": (
        "Routenplaner",
        """<h2>Routenplaner</h2>
<h3>CMDRHelper v3.2</h3>
<p>Routenplaner verbessert: Das aktuelle System wird als Start automatisch nachgeführt, bis du einen eigenen Start eingibst; ein leeres Startfeld aktiviert die Automatik erneut. Schiff und Carrier verwenden exakt geprüfte ID64-Systemadressen statt ähnlicher Namen. Bei „Unable to find route“ erklärt Spansh, dass keine Route gefunden wurde; prüfe Ziele, Reichweite und Routeneinstellungen.</p>
<p>Der Routenplaner unterstützt bei der Planung längerer Reisen mit Schiff oder Fleet Carrier. CMDRHelper kann dafür externe Routendaten von Spansh verwenden und die geplante Strecke für die weitere Nutzung aufbereiten.</p>

<h3>Start und Ziel</h3>
<p>Für eine Routenberechnung werden Start- und Zielsystem benötigt.</p>
<p>Soweit möglich, kann CMDRHelper das aktuell bekannte System des Commanders als Ausgangspunkt verwenden. Start und Ziel sollten vor der Berechnung kontrolliert werden.</p>

<h3>Schiff oder Fleet Carrier</h3>
<p>Der Routenplaner unterscheidet zwischen Reisen mit einem normalen Schiff und mit einem Fleet Carrier.</p>
<p>Beide verwenden unterschiedliche Anforderungen und Berechnungsverfahren. Deshalb muss vor der Planung der passende Routentyp gewählt werden.</p>

<h3>Schiffsroute</h3>
<p>Bei einer Schiffsroute werden die für das aktive Schiff bekannten beziehungsweise eingegebenen Sprungeigenschaften berücksichtigt.</p>
<p>Je nach verfügbarer Datenlage können FSD-Daten, Schiffsdaten, Masse, Treibstoff und weitere Sprungparameter in die Planung einfließen.</p>
<p>Eine berechnete Route ist eine Planungshilfe. Änderungen am Schiff oder seiner Masse können die tatsächlich im Spiel erreichbare Sprungweite verändern.</p>

<h3>Fleet-Carrier-Route</h3>
<p>Fleet Carrier besitzen andere Sprungregeln als normale Schiffe.</p>
<p>CMDRHelper verwendet für entsprechende Routen die dafür vorgesehene Spansh-Carrierplanung.</p>
<p>Die Route dient der Planung der Sprungfolge. Tatsächlicher Tritiumverbrauch und verfügbare Reichweite können zusätzlich von Masse und aktuellem Carrierzustand abhängen.</p>

<h3>Spansh</h3>
<p>Für die eigentliche Routenberechnung kann CMDRHelper den externen Dienst Spansh verwenden.</p>
<p>Die Anfrage wird im Hintergrund verarbeitet, damit die Oberfläche während einer längeren Berechnung bedienbar bleibt.</p>
<p>CMDRHelper hat keinen Einfluss auf die Verfügbarkeit oder Antwortzeit des externen Dienstes.</p>

<h3>Berechnung</h3>
<p>Nach dem Start einer Berechnung wird die Anfrage an den gewählten Routenplaner übergeben.</p>
<p>Je nach Strecke und Dienst kann die Berechnung einige Zeit benötigen. Währenddessen sollte keine zweite identische Berechnung unnötig gestartet werden.</p>

<h3>Ergebnis</h3>
<p>Eine erfolgreich berechnete Route zeigt die vorgesehenen Systeme beziehungsweise Sprungpunkte in ihrer Reihenfolge.</p>
<p>Je nach Routentyp erscheinen zusätzliche Informationen zu Entfernung, Sprüngen, Treibstoff beziehungsweise Tritium und weiteren verfügbaren Routendaten.</p>

<h3>Route und aktueller Commander</h3>
<p>Aktuelles System und Schiff können – soweit im aktiven AppState eindeutig bekannt – zur Vorbelegung beziehungsweise Unterstützung der Planung verwendet werden.</p>
<p>Die eigentliche Route bleibt jedoch eine Planung und verändert keine Journal- oder Commander-Daten.</p>

<h3>CTSVision-Export</h3>
<p>Berechnete Fleet-Carrier-Routen können für CTSVision als CSV exportiert werden.</p>
<p>Dadurch kann eine in CMDRHelper geplante Carrierroute anschließend in CTSVision für die dortige Sprungsteuerung beziehungsweise Routenverarbeitung verwendet werden.</p>
<p>Der Export verändert die Route in CMDRHelper nicht.</p>

<h3>CSV-Datei</h3>
<p>Die exportierte Datei enthält die für CTSVision benötigten Routendaten in der vorgesehenen Reihenfolge.</p>
<p>Die Datei sollte nach dem Export nicht unkontrolliert strukturell verändert werden, wenn sie anschließend von CTSVision eingelesen werden soll.</p>

<h3>Fehler und externe Dienste</h3>
<p>Kann Spansh nicht erreicht werden oder liefert der Dienst einen Fehler, zeigt CMDRHelper eine entsprechende Fehlermeldung.</p>
<p>Ein Fehler bei der Online-Routenberechnung verändert keine lokalen Commander- oder Journaldaten.</p>

<h3>Routenplaner und Sprungtipp</h3>
<p>Sprungtipp und Routenplaner erfüllen unterschiedliche Aufgaben:</p>
<ul>
<li>Sprungtipp bewertet mögliche interessante Explorationsziele anhand vorhandener Daten.</li>
<li>Routenplaner berechnet eine konkrete Strecke zwischen Start und Ziel.</li>
</ul>
<p>Ein guter Sprungtipp ist daher nicht automatisch Bestandteil einer optimalen Route.</p>

<h3>Mehrere Commander</h3>
<p>Soweit commanderbezogene Daten wie aktuelles System oder Schiff verwendet werden, stammen diese aus dem aktiven Live-AppState und müssen dort eindeutig zugeordnet sein.</p>
<p>Das bloße Betrachten eines anderen Commanders in der CMDR-Ansicht stellt den Routenplaner nicht auf dessen System oder Schiff um.</p>
<p>Eine Routenberechnung selbst verändert keine persönlichen Daten eines anderen Commanders.</p>

<h3>Tipp</h3>
<p>Kontrolliere vor einer längeren Reise immer noch einmal:</p>
<ul>
<li>Startsystem</li>
<li>Zielsystem</li>
<li>Routentyp Schiff/Carrier</li>
<li>bei Schiffsrouten die zugrunde gelegten Schiff-, FSD- und Sprungparameter</li>
<li>bei Carrierrouten die verfügbare Tritiumreserve</li>
</ul>
<p>Für Fleet-Carrier-Reisen empfiehlt es sich, zusätzlich ausreichend Reserve für Rückweg oder ungeplante Umwege einzuplanen.</p>""",
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
<p><b>FABER38_F12520967/</b></p>
<p>Die FID hält die Zuordnung auch bei mehreren Commandern eindeutig. Zwei Commander mit gleichem Namen können dadurch unterschieden werden.</p>

<h3>Dateinamen</h3>
<p>Neue verarbeitete Bilder erhalten einen Namen mit Aufnahmezeitpunkt, Commandername und – wenn vorhanden – dem beim Einreihen bekannten Sternensystem.</p>
<p>Beispiel:</p>
<p><b>2026-09-04_13-18-22_FABER38_Prua-Hypai-RB-D-c29-71.png</b></p>
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
<p>Ein späterer Commanderwechsel verändert die Zuordnung dieses bereits wartenden Bildes nicht. Ein Screenshot von FABER38 wird dadurch nicht nachträglich in den Ordner eines anderen Commanders geschrieben.</p>

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
<p>So kann die Galerie eines anderen Commanders betrachtet werden, während FABER38 gespielt wird, ohne dass neue Screenshots im Ordner des betrachteten Commanders landen.</p>

<h3>Tipp</h3>
<p>Ein gemeinsamer Screenshot-Stammordner reicht aus. CMDRHelper übernimmt darunter für neu verarbeitete Bilder automatisch die Trennung nach Commander und FID.</p>
<p>Mit „Aktueller Commander“, „Alle Commander“ und „Nicht zugeordnet“ kann zwischen persönlicher Galerie, den Unterordnern aller Commander und älteren Bildern im Stammordner gewechselt werden.</p>
<p>Eine höhere Aufhellung kann bei dunklen Aufnahmen helfen; sie wirkt auf das bei der Konvertierung neu erzeugte Zielbild.</p>""",
    ),
    "commander_view": (
        "CMDR Ansicht",
        """<h2>CMDR Ansicht</h2>
<p>Die CMDR Ansicht fasst dauerhaft gespeicherte persönliche Informationen eines Commanders zusammen.</p>
<p>Sie ermöglicht außerdem, zwischen den CMDRHelper bekannten Commandern zu wechseln und deren jeweils eigene Daten anzusehen. Persönliche Daten werden anhand der Frontier-ID (FID) voneinander getrennt.</p>

<h3>Commander auswählen</h3>
<p>Sind mehrere Commander bekannt, kann über die Auswahl oben festgelegt werden, wessen gespeicherte Informationen angezeigt werden. Dieser Commander ist der betrachtete Commander.</p>
<p>Die Anzeige kennzeichnet ihn entweder als „Live aktiv“ oder als „Nur Ansicht“.</p>

<h3>Betrachteter Commander und Live-Commander</h3>
<p>Das Auswählen eines anderen Commanders in der CMDR Ansicht macht ihn nicht zum aktiven Journal-Commander.</p>
<p>Der Live-Commander wird ausschließlich aus der aktuell eindeutig identifizierten Elite-Dangerous-Journalsitzung bestimmt. So kann die Historie eines anderen Commanders betrachtet werden, während Elite Dangerous weiterhin mit FABER38 läuft.</p>

<h3>Frontier-ID (FID)</h3>
<p>Die FID ist die stabile Frontier-Kennung eines Commanders.</p>
<p>CMDRHelper verwendet sie und die daraus aufgelöste interne Commander-ID, um persönliche Daten sicher voneinander zu trennen. Auch ähnlich oder identisch benannte Commander bleiben dadurch getrennt.</p>

<h3>Übersicht</h3>
<p>Der Tab „Übersicht“ zeigt ausschließlich dauerhaft gespeicherte Angaben des betrachteten Commanders:</p>
<ul>
<li>Commandername, FID und Status „Live aktiv“ oder „Nur Ansicht“</li>
<li>erster und letzter bekannter Zeitpunkt</li>
<li>Anzahl besuchter Systeme, Bio- und Geo-Funde, Codex-Einträge und Kartographieverkäufe</li>
<li>letzter bekannter Standort und Anzahl offener Missionen</li>
<li>aktuelles beziehungsweise letztes Schiff</li>
<li>Fleet Carrier und Carrier-Standort</li>
<li>Vermögen</li>
<li>offene Biodaten und offene Kartographiedaten samt vorhandener Schätzwerte</li>
</ul>

<h3>Vermögen / Credits</h3>
<p>Das Feld „Vermögen“ zeigt den zuletzt aus einem geeigneten Journalereignis gespeicherten Creditstand des betrachteten Commanders, formatiert beispielsweise als <b>1.234.567 Cr</b>.</p>
<p>CMDRHelper ergänzt keine fiktiven Einnahmen oder Ausgaben, wenn kein neuer sicherer Journalstand vorliegt.</p>

<h3>Söldnermünzen</h3>
<p>Die Söldnermünzen stammen aus den von Elite Dangerous gelieferten MercCoins-Feldern unter <code>Statistics → Bank_Account</code> und werden commanderbezogen als Frontier-Snapshot gespeichert.</p>
<p>Sichtbar sind:</p>
<ul>
<li>Aktuell</li>
<li>Insgesamt ausgegeben</li>
<li>Engineering</li>
<li>Ausrüstung</li>
<li>Von Frontier gemeldet: insgesamt verdient</li>
</ul>

<h3>Aktuell und Ausgaben</h3>
<p>„Aktuell“ zeigt <code>MercCoins_Current</code>. „Insgesamt ausgegeben“ übernimmt <code>MercCoins_Total_Spent</code>.</p>
<p>„Engineering“ und „Ausrüstung“ zeigen die von Frontier separat gemeldeten Anteile <code>MercCoins_Spent_On_Engineering</code> und <code>MercCoins_Spent_On_MercGear</code>.</p>
<p>Für FABER38 wurden beispielsweise ein aktueller Bestand von <b>1.275</b>, insgesamt <b>220</b> ausgegeben und davon <b>220</b> für Engineering gemeldet.</p>

<h3>Insgesamt verdient</h3>
<p>„Von Frontier gemeldet: insgesamt verdient“ zeigt <code>MercCoins_Total_Earned</code>. CMDRHelper berechnet daraus keine eigene Bilanz.</p>
<p>Frontiers kumulierter Wert muss rechnerisch nicht zum aktuellen Bestand und den gemeldeten Ausgaben passen. Beispielsweise können gleichzeitig 1.275 aktuell, 25 insgesamt verdient und 220 insgesamt ausgegeben gemeldet sein.</p>
<p>CMDRHelper korrigiert diese Werte nicht, sondern zeigt die einzelnen Frontier-Zähler unverändert an.</p>

<h3>Warum keine eigene MercCoins-Bilanz?</h3>
<p>Elite Dangerous liefert nicht für jede einzelne Einnahme oder Ausgabe von Söldnermünzen einen eindeutigen Journalbuchungssatz. Die MercCoins erscheinen als Gesamtstände in Statistics.</p>
<p>Eine selbst errechnete Buchungshistorie wäre deshalb nicht zuverlässig. CMDRHelper speichert stattdessen den neuesten bekannten Frontier-Snapshot.</p>

<h3>Missionen</h3>
<p>Der Tab „Missionen“ zeigt die gespeicherten Missionen des betrachteten Commanders als Tabelle mit Status, Missionsbezeichnung, Ziel, Ablaufzeit und Belohnung.</p>

<h3>Exploration</h3>
<p>Der Tab „Exploration“ zeigt offene Biodaten, offene Kartographiedaten, Bio-Funde, First Footfalls, selbst kartierte und effizient kartierte Körper sowie die Anzahl besuchter Systeme.</p>
<p>Der eigene Tab „Chronik“ innerhalb der CMDR Ansicht ist derzeit noch ein Platzhalter. Die vollständige Chronik befindet sich im gleichnamigen Hauptmenüpunkt.</p>

<h3>Schiffe / Flotte</h3>
<p>Der Tab „Schiffe“ zeigt zunächst das aktive beziehungsweise zuletzt verwendete Schiff mit Schiffsname, Schiffstyp, Standort und ShipID.</p>
<p>Darunter erscheinen die gespeicherten Schiffe des betrachteten Commanders als aufklappbare Karten. Sie können auf- oder absteigend sortiert werden nach:</p>
<ul>
<li>zuletzt beziehungsweise aktuell verwendet</li>
<li>Schiffname oder Schiffstyp</li>
<li>maximaler Sprungreichweite</li>
<li>Frachtkapazität oder Leermasse</li>
<li>letztem bekannten Standort oder Zeitpunkt</li>
</ul>
<p>Zusätzlich kann nach allen Schiffen, Schiffen mit Fahrzeughangar oder Schiffen mit Fighter-Hangar gefiltert werden.</p>

<h3>Schiffsdetails</h3>
<p>Eine aufgeklappte Schiffskarte zeigt – soweit gespeichert – Schiffskennung, ShipID, Standort, letzten Zeitpunkt, maximale Sprungreichweite, FSD und Guardian-Booster, Masse, Fracht- und Tankkapazitäten sowie Loadout-Zeitpunkt und -Status.</p>
<p>Bei vorhandenen Moduldaten werden außerdem Fahrzeug- und Fighter-Hangar, Schildgenerator und Shield Booster, Guardian-Schildverstärkungen, Waffen, Hüllen- und Modulverstärkungen sowie Passagierkabinen zusammengefasst.</p>
<p>Der Loadout-Status kann vollständig, unvollständig oder veraltet sein. Fehlende Angaben werden als „–“ angezeigt und nicht erfunden.</p>

<h3>Fleet Carrier</h3>
<p>Für einen gespeicherten eigenen Fleet Carrier zeigt die Ansicht Carriername, Callsign, CarrierID, letzten Standort und den Zeitpunkt der letzten Aktualisierung.</p>

<h3>Persistenter Commanderzustand</h3>
<p>Wichtige Commanderinformationen bleiben dauerhaft gespeichert. Dadurch können bekannte Werte nach einem Neustart von CMDRHelper oder Elite Dangerous wieder angezeigt werden, ohne jedes Journal erneut vollständig auszuwerten.</p>
<p>Neue eindeutige Journalereignisse aktualisieren den gespeicherten Zustand.</p>

<h3>Historische Rekonstruktion</h3>
<p>Für später ergänzte Funktionen kann CMDRHelper vorhandene, eindeutig einem Commander zugeordnete Journalbereiche einmalig nach bereits bekannten Angaben durchsuchen.</p>
<p>So können beispielsweise ältere MercCoins-Snapshots übernommen werden. Wiederholte Prüfungen sollen keine doppelten Daten erzeugen und verändern die normalen Journal-Lesepositionen nicht.</p>

<h3>Mehrere Commander</h3>
<p>Commanderbezogen getrennt bleiben insbesondere:</p>
<ul>
<li>Vermögen und Missionen</li>
<li>eigene Kartographie und BIO-Funde</li>
<li>Surface-Mining-Historie und Söldnermünzen</li>
<li>Online-Zugangsdaten</li>
<li>commanderbezogene Screenshots</li>
</ul>
<p>Globale astronomische Eigenschaften eines Systems oder Bodys können dagegen gemeinsam genutzt werden.</p>

<h3>Auswirkungen auf andere Ansichten</h3>
<p>Ein Wechsel des betrachteten Commanders aktualisiert die CMDR Ansicht selbst, die persönliche Mining-Rohstoffauswahl der Chronik und bei entsprechendem Filter die Screenshot-Galerie.</p>
<p>Er ersetzt nicht den tatsächlichen Live-Commander für Journalverarbeitung oder Online-Uploads.</p>

<h3>Inara und EDSM</h3>
<p>Inara- und EDSM-Zugänge werden separat pro Commander beziehungsweise FID verwaltet.</p>
<p>Das bloße Betrachten eines Commanders startet keine Übertragung mit dessen API-Key. Für Live-Uploads ist ausschließlich die aktive Journal-FID maßgeblich.</p>
<p>Die Zugangsdaten werden unter „Einstellungen“ im Bereich der Online-Dienste verwaltet.</p>

<h3>Tipp</h3>
<p>Verwende die CMDR Ansicht, wenn du gespeicherte persönliche Daten eines bestimmten Commanders ansehen möchtest.</p>
<p><b>CMDR Ansicht = Wen möchte ich betrachten?</b></p>
<p><b>Aktive Journal-FID = Wer spielt gerade tatsächlich?</b></p>
<p>Diese Trennung verhindert, dass persönliche Daten oder Online-Uploads verschiedener Commander miteinander vermischt werden.</p>""",
    ),
    "settings": (
        "Einstellungen",
        """<h2>Einstellungen</h2>
<h3>CMDRHelper v3.2</h3>
<p>Bessere Updateinformation: Das Ja/Nein-Fenster zeigt installierte und verfügbare Version sowie bis zu sechs wichtige Änderungen, sofern eine Kurzbeschreibung vorliegt. Lange Listen scrollen, die Aktionen bleiben erreichbar. Die neue Darstellung wird mit v3.2 installiert; ein unveränderter v3.1-Client zeigt sie noch nicht.</p>
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
<p>Öffne in der Übersicht „Planeten-Navigation“ und wähle „Manuelle Eingabe …“.</p>
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

<h3>Datenstand und Grenzen</h3>
<p>Die Navigation basiert auf den von Elite gelieferten Statusdaten. Aktualisierungen können abhängig vom Spielzustand verzögert eintreffen. Die Altersanzeige im Navigator zeigt, wie lange die letzte bestätigte Statusmeldung zurückliegt.</p>
<p>Der Oberflächenabstand beschreibt den kürzesten Bogen auf einer gedachten Kugel. Er ist keine Gelände- oder Straßenroute. Der Navigator kennt keine Hindernisse und keine Geländehöhen entlang der Strecke; Flughöhe, sichere Geschwindigkeit und Hindernisvermeidung bleiben deine Aufgabe.</p>

<h3>Tipp</h3>
<p>Prüfe vor dem Anflug Bodyname und Vorzeichen der Zielkoordinaten. Richte dich anschließend nach dem Zielkurs im Elite-Kompass aus und beobachte relative Richtung und Entfernung. Wenn der Navigator wartet, kontrolliere, ob Elite bereits planetare Koordinaten für den Zielbody liefert.</p>""",
    ),
}

DIALOG_TITLE = "Hilfe – {area}"
CLOSE_LABEL = "Schließen"
