import pandas as pd
import holidays 
import numpy as np


#Verspätungsdaten als Dataframe setzen und nach Zürich filtern
df = pd.read_excel("Airports_Punctuality.xlsx")
df = df[["Date", "Airport", "Avg Departure Schedule Delay"]]
df = df[df["Airport"] == "Zurich"]
df["Date"] = pd.to_datetime(df["Date"])

#Abflüge pro Tag als erstes Feature reinholen und Datum strukturieren für Merge mit Verspätungs Dataframe
df_abfluege = pd.read_csv("zrh_abfluege_pro_tag.csv")

#Datum korrekt formatieren für den Merge, da das Jahr in der CSV nur zweistellig ist
#Dies weil es sonst extrem buggy war und beim mergen teilweise Daten verloren gingen
#Piste 10 wird zu binär umgewandelt weil sie selten genutzt wird und somit ist es deutlich spannender auszuwerten ob es einen Einfluss hat wenn sie genutz wird oder nicht statt wie viele Flüge
df_abfluege["datum"] = df_abfluege["datum"].astype(str).str.strip()
df_abfluege["datum"] = pd.to_datetime(df_abfluege["datum"], format="%d.%m.%y").dt.normalize()
df_abfluege["piste_10_binär"] = np.where(df_abfluege["piste_10"] > 0, 1, 0)

#Mergen von Dataframes
df = df.merge(df_abfluege, "left", left_on="Date", right_on="datum")

#Alle Daten nach dem 1. März werden gelöscht, da ab dann keine Daten mehr vom Flughafen Zürich zu Abflügen bekannt waren
df = df[df["Date"] < "2026-03-01"]
df.to_csv("merge.csv")

#Wetter Daten hinzufügen
df_wetter = pd.read_csv("Wetterdaten_Kloten.csv")
df_wetter = df_wetter[["date", "prcp", "wspd", "wpgt", "tavg"]]
df_wetter = df_wetter.rename(columns={
    "prcp": "regen",
    "wspd": "windgeschwindigkeit",
    "wpgt": "maximale_windgeschwindigkeit", 
    "tavg": "temperatur"
})
df_wetter["date"] = pd.to_datetime(df_wetter["date"])

#Mergen, wichtige Variablen selektieren
df = df.merge(df_wetter, "left", left_on="Date", right_on="date")

#Rohölpreise hinzufügen
df_oil = pd.read_csv("Crude_Oil_Prices_Brent_Europe.csv")
df_oil["oil_date"] = pd.to_datetime(df_oil["oil_date"])
df_oil = df_oil[df_oil["oil_date"] < "2026-03-01"]
df = df.merge(df_oil, "left", left_on="Date", right_on="oil_date")

df = df[["Date", "Avg Departure Schedule Delay", "anzahl_abfluege_total", "piste_10_binär", "piste_16", "piste_28", "piste_32", "piste_34", "regen", "windgeschwindigkeit", "maximale_windgeschwindigkeit", "temperatur", "oil_price"]]
df.to_csv("merge.csv")

#Schauen ob Datum in Ferien, Wochentag und Monat hinzufügen
schweiz_ferien = holidays.Switzerland(subdiv="ZH", years=[2022, 2023, 2024, 2025, 2026])
schweiz_ferien = pd.to_datetime(list(schweiz_ferien.keys()))
df["public_holiday"] = df["Date"].isin(schweiz_ferien)
df["day_of_week"] = df['Date'].dt.day_name()
df["month"] = df["Date"].dt.month

df.to_csv("Merge.csv")
