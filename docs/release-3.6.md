# CMDRHelper 3.6 — Release-Notes-Entwurf

## Neu

- Stationen und Einrichtungen in der Systemkarte, mit sicheren Körperzuordnungen und gruppierten weiteren Einrichtungen.
- Eigener STATIONEN-Reiter mit Suche, Typ-/Körperfiltern, Sortierung und aufklappbaren Details.
- Stationsbilder und Bildviewer; bekannte Services, Landeplätze, Quellen und Zeitstempel auf einen Blick.
- Optionale Spansh-Stationsinformationen unter Einstellungen → Online Services, standardmäßig ausgeschaltet. Ohne Spansh erklärt ein Hinweis die Beschränkung auf Journalwissen.
- Persönliche Schiffs- und Carrierbilder, Bildviewer und Flottenverwaltung mit Entfernen und erneutem Einlesen von Schiffen.

## Verbessert

- Systemkarte und Explorer-Wertliste mit klar unterscheidbarem Kartierungsstatus.
- Cargo-HUD mit sicherer Schiff-/SRV-Trennung und geprüftem Status-Fallback.
- Navigation und HUD-Fenstererkennung unter Linux; weniger unnötige Hintergrundarbeit in Explorer, Galerie und Animationen.
- Spansh: Nach einem erfolgreichen Abruf genügt der Cache für weitere manuelle Klicks am selben lokalen Kalendertag. Fehler dürfen erneut versucht werden; Offlinebetrieb verwendet vorhandenes Wissen.

## Behoben

- Verkaufte Schiffe werden auch bei Verkauf im Rahmen eines Kaufs, Tauschs oder Rebuy korrekt berücksichtigt.
- Harmlose kurze Elite-Journale mit Fileheader/Friends unterbrechen die Mining-Carrierkontinuität nicht mehr. Unsichere Journalfolgen werden weiterhin abgelehnt.
- Automatische, geprüfte Datenbanksicherung vor dem Upgrade von Schema 17–19 auf Schema 20.

Bestehende persönliche Daten bleiben erhalten. Spansh-Daten und persönliche Bilder werden getrennt von den mitgelieferten Programmdateien gespeichert. Spansh bleibt optional; Stationen sind keine garantierte vollständige Live-Liste.

Dieser Entwurf wurde nicht veröffentlicht.
