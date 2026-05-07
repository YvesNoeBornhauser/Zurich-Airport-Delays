import pandas as pd
import holidays 
import numpy as np
from Andere_Skripte.WEF_scraper import fetch_wef_dates


#Verspätungsdaten als Dataframe setzen und nach Zürich filtern
df = pd.read_excel("Quellen/Airports_Punctuality.xlsx")
verspaetung_spalte = [spalte for spalte in df.columns if "Departure Schedule Delay" in spalte][0]
df = df[["Date", "Airport", verspaetung_spalte]]
df = df.rename(columns={verspaetung_spalte: "Abflugverspätung ZRH"})
df = df[df["Airport"] == "Zurich"]
df["Date"] = pd.to_datetime(df["Date"])

#Abflüge pro Tag als erstes Feature reinholen und Datum strukturieren für Merge mit Verspätungs Dataframe
df_abfluege = pd.read_csv("Quellen/zrh_abfluege_pro_tag.csv")

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
df_wetter = pd.read_csv("Quellen/Wetterdaten_Kloten.csv")
df_wetter = df_wetter[["date", "prcp", "wspd", "wpgt", "tavg"]]
df_wetter = df_wetter.rename(columns={
    "prcp": "regen",
    "wspd": "windgeschwindigkeit",
    "wpgt": "maximale_windgeschwindigkeit", 
    "tavg": "temperatur"
})
df_wetter["date"] = pd.to_datetime(df_wetter["date"])

#Fehlende Regenwerte mit häufigsten Regenwert überschreiben
regen_modus = df_wetter["regen"].mode()[0]
df_wetter["regen"] = df_wetter["regen"].fillna(regen_modus)

#Fehlende maximale Windgeschwindigkeit mit Verhältnis von maximaler zu durchschnittlicher Windgeschwindigkeit schätzen
#Es fehlten 12 Tage am Stück, deshalb nicht einfach die maximale Geschwindigkeit vom Vortag genommen
verhaeltnis_wind = (df_wetter["maximale_windgeschwindigkeit"] / df_wetter["windgeschwindigkeit"]).mean()
df_wetter["maximale_windgeschwindigkeit"] = df_wetter["maximale_windgeschwindigkeit"].fillna(df_wetter["windgeschwindigkeit"] * verhaeltnis_wind)

#Schnee hinzufügen, sobald Temperatur unter 2 Grad und Regen vorhanden (Schnee kann anscheinend schon ab 2 Grad fallen)
df_wetter["schnee_vorhanden"] = np.where((df_wetter["temperatur"] < 2) & (df_wetter["regen"] > 0), 1, 0)
df_wetter["schnee_intensität"] = np.where((df_wetter["temperatur"] < 2) & (df_wetter["regen"] > 0), df_wetter["regen"], 0)

#Mergen, wichtige Variablen selektieren
df = df.merge(df_wetter, "left", left_on="Date", right_on="date")

#Ölpreise hinzufügen
df_oil = pd.read_csv("Quellen/Crude_Oil_Prices_Brent_Europe.csv")
df_oil["oil_date"] = pd.to_datetime(df_oil["oil_date"])

#Ölpreise vom Wochende, die fehlen mit Daten vom Vortag bzw. Freitag befüllen
df_oil = df_oil.sort_values("oil_date").set_index("oil_date").asfreq("D")
df_oil["oil_price"] = df_oil["oil_price"].ffill()
df_oil = df_oil.reset_index()

#Durchschnittlicher Ölpreis der letzten 90 Tage 
df_oil["90_day_average_oil_price"] = (df_oil["oil_price"].rolling(window=90).mean().shift(1))

#Trend berechnen von Ölpreis (Formel ist Durchschnitt der letzten 7 Tage - Durchschnitt der letzten 90 Tage, positiver Wert = Ölpreis gestiegen)
df_oil["7_day_average_oil_price"] = df_oil["oil_price"].rolling(window=7).mean().shift(1)
df_oil["oil_trend"] = df_oil["7_day_average_oil_price"] - df_oil["90_day_average_oil_price"]

#Standardabweichung von Ölpreis für letzte 90 Tage berechnen
df_oil["oil_volatility_90"] = df_oil["oil_price"].rolling(window=90).std().shift(1)

df = df.merge(df_oil, "left", left_on="Date", right_on="oil_date")
df = df[["Date", "Abflugverspätung ZRH", "anzahl_abfluege_total", "piste_10_binär", "piste_16", "piste_28", "piste_32", "piste_34", "regen", "windgeschwindigkeit", "maximale_windgeschwindigkeit", "temperatur", "oil_price", "90_day_average_oil_price", "oil_trend", "oil_volatility_90", "schnee_vorhanden", "schnee_intensität"]]

#Schauen ob Datum in Ferien, Wochentag und Monat hinzufügen
schweiz_feiertag = holidays.Switzerland(subdiv="ZH", years=[2022, 2023, 2024, 2025, 2026])
schweiz_feiertag = pd.to_datetime(list(schweiz_feiertag.keys()))
df["Feiertage"] = df["Date"].isin(schweiz_feiertag)
df["day_of_week"] = df['Date'].dt.day_name()
df["month"] = df["Date"].dt.month

#WEF hinzufügen, ob es an dem Tag war, ja/nein
df_wef = fetch_wef_dates()
df["WEF"] = df["Date"].isin(df_wef)

df.to_csv("merge.csv")
