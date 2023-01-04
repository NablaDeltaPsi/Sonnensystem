
Kleines Python GUI zur Ansicht der Planetenstellungen bei beliebigen Daten.

Für Windows-Benutzer ist unter Releases eine ZIP-Datei mit kompiliertem Programm verfügbar. Zum Starten nach Herunterladen und Entzippen "Sonnensystem.exe" ausführen.

###############################################

![grafik](https://user-images.githubusercontent.com/98178269/210569379-362148c9-2703-4154-9f00-a72964684468.png)
![grafik](https://user-images.githubusercontent.com/98178269/210569401-2f97c7b2-51c4-43d4-b802-c6ac27787071.png)
![grafik](https://user-images.githubusercontent.com/98178269/210569415-c91bf66c-3ddd-4b6d-9c1a-274ada5952b5.png)
![grafik](https://user-images.githubusercontent.com/98178269/210569427-00bf9f89-40ab-4032-94a7-72653927ffee.png)

###############################################

Ansichten: Das Startfenster zeigt die Planetenstellungen mit äquidistanten Bahnen. Die Erde ist im Winter der Nordhalbkugel oberhalb, im Frühling links, im Sommer unterhalb und im Herbst rechts der Sonne. Die Planeten sind auf kreisförmige Bahnen mit gleichem Abstand gezeichnet. Die Erde wird vom Mond begleitet. Mit der Schaltfläche O, oder mit der Tab-Taste erreicht man alternative, heliozentrische Ansichten der inneren und äußeren Planeten mit realen Orbits. Einzig der Abstand des Mondes zur Erde ist in diesen Ansichten nicht maßstabsgetreu. Als optische Hilfe für Oppositionen und Konjunktionen ist die dunkelblaue Linie eine erweiterte Verbindungslinie von der Sonne zur Erde. Planeten sind nachts auf der der Sonne abgewandten Seite der Erde sichtbar, dabei rechts der blauen Linie eher Abends, links der blauen Linie eher morgens. Die vierte Ansicht ist eine geozentrische Ansicht der Mondposition. Im Gegensatz zu den Orbits der vorherigen Ansichten ist der Orbit des Mondes hier nach seinem mittleren Abstand kreisförmig gezeichnet, um Perigäum und Apogäum besser nachvollziehen zu können. Die durchgezogene bzw. gestrichelte blaue Linie weist hier zur Sonne bzw. von der Sonne weg und zeigt bei überschreiten des Mondes Neumond bzw. Vollmond an.

Datum: Es lässt sich oben ein beliebiges Datum einstellen und das Datum auch alternativ per rechts/links Pfeiltasten oder dem Mausrad verändern (Strg+Pfeiltasten in 3-Tage Schritten statt 1-Tage Schritten, alternativ je nach Klick ins Tage/Monat/Jahr-Feld). Die Taste H führt zurück zum heutigen Datum, die Taste J führt zur Epoche J2000.0 (01.01.2000 12:00 Uhr), von welcher ausgehend die Positionen berechnet werden. Die Positionen beziehen sich daher auch am jeweiligen Tag auf 12:00 Uhr mittags.

Fenstergröße: Programmiertechnisch schwierig ist ein Fenster, welches vom Benutzer größer gezogen werden kann, aber das Seitenverhältnis beibehält. Deshalb gibt es die Buttons oben rechts, F+ und F- (F für Fenster) vergrößern und verkleinern das Fenster etwas. So kann man sich die gewünschte Fenstergröße selbst festlegen. Die Einstellungen werden für den nächsten Start in eine config-Datei geschrieben und dann übernommen. S+ und S- verändern die Schriftgröße der Schaltflächen.

Features (Perihels, Orbit- und Polneigungen): Kleine Striche an den Planetenbahnen zeigen die Position des Perihels. Außerdem bestehen alle Bahnen außer die der Erde aus einer etwas helleren und einer etwas dunkleren Hälfte, was veranschaulichen soll, wie die jeweilige Bahnebene relativ zur der der Erde geneigt ist. Der Übergang von der dunkleren zur helleren Hälfte ist der aufsteigende Knoten. Bei Erde, Mars, Saturn, Uranus und Neptun ist die Richtung der Polneigung mit einem schwarzen Einschnitt markiert. So kann man nachvollziehen, ob wir aktuell auf die Nord- oder die Südhalbkugel des jeweiligen Planeten schauen, oder wann Saturn bspw. wieder eine Kantenstellung erreicht.

Winkelanzeige: Am unteren Rand kann ein Planet oder der Mond ausgewählt werden (alternativ mit Pfeiltasten hoch/runter), für den dann rechts davon Winkel angezeigt werden. E ist die Elongation des ausgewählten Planeten zur Erde (nahe E=180° in Opposition, nahe E=0° in oberer und unterer Konjunktion, E maximal für beste Sichtbarkeit von Merkur und Venus). Lon ist die ekliptikale Länge, d.h. der Winkel des Planeten innerhalb der Ebene der Erdbahn relativ zum Frühlingspunkt (L=0° für die Erde am 23.9.). Lat ist die eklitikale Breite, d.h. der Winkel des Planeten senkrecht zur Ebene der Erdbahn.

Auswahl bestimmter Daten: Der Benutzer hat die Möglichkeit, rechts der Datumseingabe bestimmte Daten auszuwählen. Die Daten werden aus der Datei "Sonnensystem_Daten.txt" geladen und können dort beliebig verändert werden, solange das Format beibehalten wird. Die Beschreibung wird nach Auswahl (oder auch bei zufälligem Vorbeikommen an dem Datum) unter der Datumsauswahl angezeigt.

Beispiel: Kurz vor Marsopposition 2003, Opposition nahezu exakt an Marsperihel, Blick dabei auf seine Südhalbkugel

![grafik](https://user-images.githubusercontent.com/98178269/210571597-e673d2cb-22b7-418c-bcc7-a22cd111d2df.png)

Beispiel: Saturnopposition mit großer Ringöffnung und Blick auf Nordpol (03.06.2016)

![grafik](https://user-images.githubusercontent.com/98178269/210572642-2b7ffc66-3dd3-45d5-bb28-ca6644b06e3e.png)

Beispiel: Saturnopposition mit Kantenstellung (07.09.2024)

![grafik](https://user-images.githubusercontent.com/98178269/210572862-f6f75aae-6d1d-4e07-8814-fed618541e6a.png)

Beispiel: Supermond (01.08.2023)

![grafik](https://user-images.githubusercontent.com/98178269/210573619-6b247b82-38fb-4899-ad93-4efb888aa01c.png)

Beispiel: Venus am Morgenhimmel mit maximaler Elongation (24.10.2023)

![grafik](https://user-images.githubusercontent.com/98178269/210573980-ad0f45a0-c48c-4fad-ae54-0eede8cf99e1.png)


