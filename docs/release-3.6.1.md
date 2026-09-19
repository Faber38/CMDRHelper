# CMDRHelper 3.6.1

Patch-Release auf Basis des Entwicklungsstands seit 3.6. Feature Freeze: nur
notwendige Releaseblocker dürfen noch korrigiert werden.

## Neu

- Kopfgeldanzeige unter Missionen mit commanderbezogener, persistenter
  Live-Erfassung und bestätigtem manuellem Reset.
- Encounter-/Messenger-Aufträge aus Weltraumbegegnungen sind bereits vor der
  endgültigen MissionID sichtbar.

## Verbessert

- Encounter-Angebote werden persistent und FID-getrennt geführt. Eindeutige
  Bestätigung über MissionAccepted, Missions.Active oder CargoDepot überführt
  sie ohne Dublette in eine normale Mission.
- Der Matcher berücksichtigt Ware, Menge, Zielstation, Zielsystem, Belohnung
  und Zeit. Widersprüche verhindern Matches; Mehrdeutigkeit führt nicht zum Raten.
- Unbestätigte Angebote werden nach 24 Stunden bei bestehenden Verarbeitungs-
  und Ladeanlässen bereinigt, ohne zusätzlichen Timer. Ihre angebotene Belohnung
  zählt nicht zur bestätigten Gesamtbelohnung.
- Commander → Missionen zeigt aktuelle Missionen. Neue Abschlussereignisse
  entfernen die aktuelle Missionszeile, statt weitere Abschlussarchive aufzubauen.
  Missions.Complete und inaktive Zeilen werden konservativ behandelt.

## Behoben

- Encounter-Verarbeitung wieder vollständig an die inkrementelle Verarbeitung
  angebunden; keine Dubletten bei späterer MissionID.
- Alte Missionsereignisse können den neueren Bestand nicht zurücksetzen.
- Widersprüchlicher Missionsreset aus der aktiven Oberfläche entfernt.

## Daten und Umfang

Schema 20 bleibt bestehen. Keine strukturelle Migration und keine automatische
Bereinigung bestehender historischer Missionszeilen beim Update. Abschlussereignisse
bleiben für Odyssey, Materialien, Mining, INARA und andere Verbraucher verfügbar.
Die Chronik benötigt die Missionshistorie nicht.

Keine Ingenieur-Funktion, Combat Bonds, EngineerContribution/Bounty, zusätzlichen
Missions-, Mining- oder Performance-Funktionen. Weitere Agenda-Punkte bleiben
außerhalb dieses Patch-Releases.

Die offiziellen lokalisierten Kurztexte kommen aus `release_summaries.py` und
den zwölf vorhandenen Sprachkatalogen. Der Publisher und Releaseworkflow bleiben
unverändert.
