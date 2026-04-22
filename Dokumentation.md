# Dokumentation: Analyse der Flugverspätungen am Flughafen Zürich

## Einleitung

Bei der Wahl des Themas für das Modul "Data Engineering and Wrangling" war die ursprüngliche Idee, die Verspätungen bzw. die Wartezeiten der Achterbahn Silverstar im Europapark zu vorhersagen. Diese Idee mussten wir jedoch relativ schnell wieder verwerfen, da sich die Beschaffung der Daten als relativ schwer entpuppte und viele spannende Daten leider hinter einer Paywall stehen.
Als zweite Idee kam uns dann die Berechnung der Flugverspätungen am Flughafen Zürich. Das Projekt kombiniert mehrere Datenquellen, um Faktoren zu identifizieren, die zu Verspätungen bei Abflügen führen. Die kombinierten Daten umfassen den Zeitraum von 2019 bis 2026 und berücksichtigen operative, meteorologische und wirtschaftliche Einflussfaktoren.
Zum Schluss haben wir eine Datei erstellt, die die Korrelationen zwischen den einzelnen Daten errechnet und uns als Output eine Korrelationsmatrix für alle Daten sowie die Korrelationen nur in Bezug auf die Verspätungen generiert.  


## Datenquellen und ihre Bedeutung

Die Analyse basiert auf vier verschiedenen Datenquellen, die jeweils unterschiedliche Aspekte des Flugbetriebs abdecken. Die Verspätungsdaten stammen aus der Datei `Airports_Punctuality.xlsx`, welche die durchschnittlichen Abflugsverspätungen pro Tag für verschiedene Flughäfen enthält. Für diese Analyse wurden ausschliesslich Daten des Flughafens Zürich extrahiert und verwendet.

Die operativen Daten werden durch die Datei `zrh_abfluege_pro_tag.csv` bereitgestellt. Diese Datei enthält die tägliche Anzahl der Abflüge und deren Verteilung auf die verschiedenen Landebahnen des Flughafens Zürich. Der Flughafen Zürich verfügt über vier Hauptlandebahnen: Piste 16, 28, 32 und 34. Zusätzlich wird die Nutzung von Piste 10 erfasst, welche aufgrund ihrer seltenen Verwendung als binäre Variable kodiert wird (1 = genutzt, 0 = nicht genutzt). Dies ermöglicht eine aussagekräftige Analyse des Einflusses dieser Piste auf die Verspätungen.

Die Wetterdaten werden von der Messstation Kloten bereitgestellt, die sich in der Nähe des Flughafens Zürich befindet. Die Datei `Wetterdaten_Kloten.csv` enthält tägliche Messungen zu Niederschlag, Windgeschwindigkeit, maximaler Windgeschwindigkeit und Durchschnittstemperatur. Diese meteorologischen Faktoren sind bekannt dafür, dass sie die Flugoperationen beeinflussen können.

Für die wirtschaftliche Perspektive werden Rohölpreise aus der Datei `Crude_Oil_Prices_Brent_Europe.csv` herangezogen. Die Energiekosten beeinflussen die Betriebskosten von Fluggesellschaften und können möglicherweise Auswirkungen auf die Flugplanung und damit auf Verspätungen haben.


## Datenverarbeitung und Transformation

Der Datenprozess beginnt mit dem Laden und Filtern der Verspätungsdaten. Aus der Excel-Datei werden die Spalten «Date», «Airport» und «Avg Departure Schedule Delay» extrahiert. Die Daten werden auf den Flughafen Zürich gefiltert, und das Datumsformat wird in das standardisierte `datetime`-Format konvertiert. Dies ermöglicht eine nahtlose Integration mit anderen Datenquellen.

Die Abflugdaten erfordern eine aufwändigere Vorverarbeitung. Das Datumsformat in der CSV-Datei liegt im Format `dd.mm.yy` vor, wobei das Jahr nur zweistellig angegeben ist. Eine direkte Konvertierung hätte zu Datenverlusten beim Merge geführt, weshalb die Daten zunächst bereinigt, in Strings umgewandelt und anschliessend mit dem korrekten Format `%d.%m.%y` zu `YYYY-MM-DD` konvertiert werden. Die Variable «piste_10» wird dabei transformiert: Werte grösser als null werden zu 1 kodiert, ansonsten zu 0. Dies ermöglicht eine vereinfachte Analyse des Einflusses dieser seltener genutzten Bahn.

Im nächsten Schritt werden die Abflugdaten mit den Verspätungsdaten zusammengeführt. Ein Left-Join wird verwendet, um sicherzustellen, dass alle Verspätungsdaten erhalten bleiben und mit den verfügbaren Abflugdaten angereichert werden.

Ein kritischer Datenpunkt in dieser Analyse ist der 1. März 2026. Ab diesem Datum sind keine Abflugdaten mehr verfügbar, weshalb alle Datensätze nach diesem Stichtag aus dem Datensatz entfernt werden. Dies stellt sicher, dass die Analyse nur auf vollständigen und zuverlässigen Daten basiert.

Die Wetterdaten werden anschliessend integriert. Die Spaltennamen werden zunächst vereinheitlicht: «prcp» wird zu «regen», «wspd» zu «windgeschwindigkeit», «wpgt» zu «maximale_windgeschwindigkeit» und «tavg» zu «temperatur». Das Datumsformat wird ebenfalls zu `datetime` konvertiert. Der Merge mit dem bestehenden Datensatz erfolgt erneut als Left-Join auf das Datum.

Die Rohölpreise werden nach einem ähnlichen Muster verarbeitet. Die Daten werden gefiltert, um nur Einträge vor dem 1. März 2026 zu behalten, und dann mit dem Hauptdatensatz gemergt. Sollten für bestimmte Tage (meist am Wochendene) keine Ölpreise verfügbar sein, entstehen fehlende Werte, die bei der späteren Analyse berücksichtigt werden müssen.

Abschliessend werden kategorische Variablen hinzugefügt, um weitere Informationen zu erfassen. Mit der Python-Bibliothek «holidays» werden die offiziellen Feiertage des Kantons Zürich für die Jahre 2022 bis 2026 extrahiert und als Boolean-Variable in den Datensatz integriert. Der Wochentag wird ebenfalls als Textfeld hinzugefügt, um Muster zu erkennen, die zwischen den Wochentagen variieren. Schliesslich wird der Monat als numerische Variable (1–12) hinzugefügt.


## Struktur des finalen Datensatzes

Der resultierende Datensatz wird in der Datei `merge.csv` gespeichert und enthält folgende Spalten: Das Datum («Date»), die durchschnittliche Verspätung in Minuten («Avg Departure Schedule Delay»), die Gesamtanzahl der Abflüge pro Tag («anzahl_abfluege_total»), die binäre Variable für Piste 10 («piste_10_binär»), sowie die Anzahl der Abflüge auf den Pisten 16, 28, 32 und 34. Zusätzlich sind die meteorologischen Variablen Niederschlag, Windgeschwindigkeit, maximale Windgeschwindigkeit und Temperatur enthalten. Der Rohölpreis («oil_price»), der Feiertagsstatus («public_holiday»), der Wochentag («day_of_week») und der Monat («month») runden den Datensatz ab.


## Annahmen und Limitierungen

Bei der Interpretation dieser Analyse sollten mehrere Annahmen berücksichtigt werden. Erstens wird angenommen, dass die Wetterdaten der Station Kloten repräsentativ für die Bedingungen am Flughafen Zürich sind. Zweitens wird unterstellt, dass Rohölpreise mit dem Flugverkehr und den Betriebskosten der Fluggesellschaften korrelieren. Drittens wird davon ausgegangen, dass Feiertagsdaten das Passagieraufkommen und damit die Belastung des Flughafens beeinflussen.

Die Analyse weist auch verschiedene Limitierungen auf. Es können Datenlücken bei den Wetter- oder Ölpreisangaben entstehen, die durch fehlende Werte in der Analyse dargestellt werden. Der Analysezeitraum von 2019 bis 2026 ist relativ begrenzt und könnte längerfristige Trends nicht vollständig abbilden. Die COVID-19-Pandemie hat erhebliche Auswirkungen auf den Flugverkehr gehabt und könnte die Daten verzerren. Schliesslich ist wichtig zu betonen, dass diese Analyse Korrelationen aufdeckt, nicht jedoch Kausalbeziehungen nachweist. Eine hohe Korrelation zwischen zwei Variablen bedeutet nicht zwingend, dass die eine die andere verursacht.


## Technische Umsetzung

Die Analyse wird in Python 3.9 oder höher durchgeführt. Hauptsächlich werden die Bibliotheken pandas für die Datenverarbeitung, numpy für numerische Berechnungen und holidays zur Verwaltung von Feiertagsdaten verwendet. Der Datenprozess wird durch ein einziges Python-Skript namens `Wrangling.py` orchestriert, das alle beschriebenen Transformationsschritte sequenziell ausführt.

## Fazit
