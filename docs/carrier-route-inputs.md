# Fleet-Carrier-Eingaben für Spansh

Persönliche Fleet Carrier verwenden das Spansh-Profil `mass=25000` und
`capacity=25000`. Diese beiden Größen sind unabhängig. CMDRHelper berechnet
keine Gesamtmasse und keine eigene Tritium-Verbrauchsformel.

`capacity_used` ist die gesamte belegte Kapazität, einschließlich Fracht,
Lagertritium, Diensten, Reservierungen, Schiff- und Modulpaketen.
`fuel_loaded` ist Tanktritium, `tritium_stored` der bereits in der Belegung
enthaltene Lagerbestand. `calculate_starting_fuel=0` erhält die ausdrücklich
bestätigten Bestände. Alle Verbrauchs-, Restbestands- und Nachfüllwerte der
Routenantwort sowie das CTSVision-CSV-Format bleiben unverändert.

## Quellen und Grenzen

- [Öffentlicher Spansh-Frontend-Quelltext (Source Map)](https://spansh.co.uk/assets/elite-dangerous-gui-4ce93861bd384bc982212db7e24f463c.map),
  Version `0.1.903+d0f304f7`, Quelle
  `elite-dangerous-gui/controllers/fleet-carrier.js`: `carrierStats` definiert
  das persönliche Profil; `calculate` überträgt die Belegung, Tank und Lager
  getrennt. Das ist kein Nachweis einer serverseitigen Gesamtmassenformel.
- [Spansh-Oberflächentexte](https://github.com/spansh/elite-dangerous-gui-translations/blob/master/translations/en.json):
  belegte Kapazität einschließlich Waren und installierter Dienste.
- [Frontier Journal Manual v37](https://hosting.zaonce.net/community/journal/v37/Journal_Manual_v37.pdf),
  Abschnitt 11.3 `CarrierStats`: Snapshot beim Öffnen der Carrier-Verwaltung;
  `SpaceUsage` beschreibt Kapazität und Belegung. Das oberste `Crew`-Feld ist
  eine Diensteliste, `SpaceUsage.Crew` dagegen ein Kapazitätsanteil.
  `CarrierStats` enthält keine vollständige Warenliste und keine bestätigte
  Tankkapazität. `LoadGame.FuelCapacity` betrifft das Schiff.
- [EDCD-Dokumentation der Frontier-CAPI](https://github.com/EDCD/FDevIDs/blob/master/Frontier%20API/FrontierDevelopments-CAPI-endpoints.md):
  dokumentierter persönlicher Carrier-Tank mit maximal 1000 t. Die Validierung
  nutzt diese Profilgrenze; die App ruft CAPI dafür nicht auf.
- [Aktueller Carrier-Journalparser von EliteDangerousCore](https://github.com/EDDiscovery/EliteDangerousCore/blob/master/EliteDangerous/JournalStatus/Events/JournalCarrier.cs):
  zusätzliche Typzuordnung über `CarrierType`. Automatisch unterstützt wird
  ausschließlich `FleetCarrier`; fehlender/anderer Typ erfordert manuelle
  Bestätigung eines persönlichen Carriers. Squadron Carrier sind nicht Teil
  dieser Implementierung.

## Datenweg und Bestätigung

`read_latest_state` reicht die bereits gelesenen, eindeutig einer FID
zugeordneten Ereignisse an `CarrierInputTracker` weiter. Es gibt keinen
zusätzlichen Journal-Scan, keine Inventarrekonstruktion und keine Persistenz
der neuen Daten in Datenbank, Cache oder QSettings.

Ein unveränderlicher `CarrierSnapshot` gelangt über AppState zur Eingabemaske.
`TotalCapacity - FreeSpace` liefert die Belegung. Fehlende Einzelanteile werden
nicht als null ergänzt. Bekannte Einzelanteile dürfen die Belegung nicht
überschreiten; bei vollständiger Aufschlüsselung muss ihre Summe passen.
Widersprüche machen die betroffene Belegung unbekannt. Tankwerte außerhalb
des persönlichen Profils bleiben ebenfalls unbekannt. Lagertritium muss der
Benutzer immer separat eingeben; im automatischen Modus darf es außerdem
nicht größer als ein bekannter `Cargo`-Wert sein.

FID, Journaldatei/Spielsitzung, CarrierID, Callsign, CarrierType und Zeitstempel
binden die automatische Übernahme. Nur die neueste eindeutig zugeordnete
Datei kann aktuelle Werte liefern. Datei-, Commander- und Sitzungswechsel
verwerfen ältere Beobachtungen. Erkannte Transfers, Sprünge, Markt- und
Dienständerungen machen den Snapshot unbrauchbar, ohne Bestände zu schätzen.
Diese Invalidierung ist vorsichtig: Auch ein Marktgeschäft außerhalb des
eigenen Carriers kann eine erneute Bestätigung nötig machen.

Die **15-Minuten-Grenze ist eine CMDRHelper-Sicherheitsregel**, keine von
Frontier garantierte Aktualität. Zukünftige/ungültige Zeitstempel werden
abgelehnt. Auch innerhalb dieser Frist ist ein Snapshot kein Live-Bestand:
Andere Spieler können beispielsweise Waren handeln, ohne dass im lokalen
Journal ein Ereignis erscheint. Deshalb muss der Benutzer die aktuellen
Werte ausdrücklich bestätigen. Quelle, Snapshot-Zeit und Bestätigungszeit
sind sichtbar. Manuelle Eingaben beginnen unbekannt und verlangen ein
Carrier-Rufzeichen und eine aktive Commander-FID. Bestätigungen gelten
höchstens 15 Minuten und werden bei jeder Eingabeänderung zurückgesetzt.
Nach einem erkannten Transfer sind neue Eingaben/CarrierStats erforderlich.
Ein nicht lokal protokollierter Transfer muss durch Bearbeiten und erneutes
Bestätigen der Werte berücksichtigt werden.

Die zentrale Prüfung in `CarrierRouteRequest.validation_error` verlangt:

- `0 <= capacity_used <= capacity`, persönliches Profil `capacity=25000`;
- `0 <= tritium_stored <= capacity_used`;
- `0 <= fuel_loaded <= 1000`, unabhängig von der Lagerkapazität;
- Identität, aktuelle Bestätigung und bei automatischer Quelle einen passenden
  Snapshot, dessen Werte unverändert übernommen wurden.

Worker und Client prüfen vor weiteren Arbeiten; der Client prüft nochmals
unmittelbar vor dem Absenden. Die Ansicht verwirft verspätete Ergebnisse nach
Kontextwechseln. Der vorhandene 500-ly-Spansh-Router bleibt unverändert.

## Regression: nyenyon

`25000 - 19666 = 5334 = 4404 + 930`. Von den 4404 Frachteinheiten sind
4400 Lagertritium. Der zuvor fehlende Anteil beträgt `5334 - 4400 = 934`.

```json
{
  "source": 11,
  "destinations": 22,
  "mass": 25000,
  "capacity": 25000,
  "capacity_used": 5334,
  "fuel_loaded": 1000,
  "tritium_stored": 4400,
  "calculate_starting_fuel": 0
}
```

11 und 22 sind ausschließlich Mock-Systemkennungen. Keine produktive
Spansh-Anfrage ist zur Prüfung erforderlich. Weder 30400 noch 31334 wird als
verifizierte Gesamtmasse ausgegeben.
