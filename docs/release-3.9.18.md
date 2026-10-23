# CMDRHelper v3.9.18

- Wartungs- und Zuverlässigkeitsupdate für den EDSM-Journalupload; keine neuen Funktionen.
- Die obere EDSM-Ampel und ihr Tooltip bewerten ausschließlich Uploads: Grün OK, Gelb Wartet, Rot Fehler, Grau Unbekannt oder Aus. Downloads, Cachetreffer und Verbindungstests ändern die Farbe nicht.
- HTTP-, Gesamt- und Einzelantworten werden gemeinsam geprüft. Fehlende oder unbekannte Bestätigungen geben keinen Checkpoint frei; 500/501 gelten nicht als bestätigte Speicherung.
- 100–103 zählen als Registrierungsnachweis; 104/304 können Ereignisse abschließen, erzeugen allein aber keine grüne Ampel. Nur ein eindeutig abgeschlossener Präfix bringt den Checkpoint voran.
- Endpunkte, Batchgröße, Timeouts, Wiederholungsintervalle, Upload-Reihenfolge und Commander-/FID-Zuordnung bleiben unverändert. Originaljournale werden nicht verändert; Datenbankschema bleibt 23.
- Bestätigte Ereignisse hinter einer Lücke können erneut gesendet werden. Abgelehnte Ereignisse werden nicht automatisch übersprungen; die Ampel beginnt nach Neustart ohne Erfolgsnachweis. Keine native Windows-Prüfung.

Dieses Wartungsrelease trennt den Journaluploadstatus von EDSM-Downloads, Körperdaten, Cachetreffern und Verbindungstests. Gelb umfasst laufende Uploads und geplante Wiederholungen. Rot kennzeichnet einen offenen Uploadfehler außerhalb dieser Warteanzeige. Grün beschreibt bestätigte Uploadergebnisse, keine aktuelle Verfügbarkeitsgarantie des Dienstes. Tooltiptexte enthalten Uploadinformationen und begrenzte Fehlercodes statt beliebiger Serverantworten.

HTTP-Erfolg allein genügt nicht: Gesamtcode 100 und eine vollständige, typgültige Einzelantwortliste müssen die Zuordnung erlauben. 100 bestätigt neue Speicherung; 101–103 zählen als bereits registriert bzw. Duplikat. 104 und 304 schließen ohne Registrierungsnachweis ab. 402 bleibt zur Wiederholung offen; 500/501 werden konservativ als technische Fehler behandelt. Unbekannte oder abgelehnte Antworten bleiben offen und können eine manuelle Prüfung erfordern.

Bei Teilbestätigungen bleibt die bestehende Präfixlogik erhalten: [100, 100, 402, 100] verschiebt den Checkpoint nur über die ersten beiden Ereignisse. Das vierte Ereignis kann erneut gesendet werden. Es gibt keine persistenten Einzelbestätigungsdateien, neuen EDSM-Datenbanktabellen, automatische Überspringlogik für abgelehnte Ereignisse oder neue Retry-Architektur. Die zurückgestellte Live-Journalereignis-Korrektur, neue Explorer-Funktionen, commanderübergreifende Favoriten und weitere Performance-Optimierungen sind nicht enthalten. Datenbankschema Version 23 bleibt unverändert.

Prüfumfang: gezielte automatisierte Tests mit synthetischen HTTP-Antworten, temporären Journalen und Datenbanken sowie Qt offscreen für Dark-/Light-Mode und zwölf Sprachen. Keine vollständige Regression, keine Live-EDSM-Ende-zu-Ende-Prüfung und keine native Windows-Prüfung. Die Uploadanzeige wird nicht dauerhaft gespeichert; bestehende Checkpoints bleiben für den Neustart maßgeblich.
