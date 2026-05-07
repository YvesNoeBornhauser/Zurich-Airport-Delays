from pathlib import Path
import sys

import holidays
import pandas as pd
from ydata_profiling import ProfileReport


# Pfade
projekt_root = Path(__file__).resolve().parents[1]
sys.path.append(str(projekt_root))

verspaetung_datei = projekt_root / "Quellen" / "Airports_Punctuality.xlsx"
abfluege_datei = projekt_root / "Quellen" / "zrh_abfluege_pro_tag.csv"
wetter_datei = projekt_root / "Quellen" / "Wetterdaten_Kloten.csv"
oelpreis_datei = projekt_root / "Quellen" / "Crude_Oil_Prices_Brent_Europe.csv"
output_datei = Path(__file__).resolve().parent / "Qualitaetsprofil_merge.html"


# Verspätungsdaten direkt aus der Quelle lesen und Zürich auswählen
df = pd.read_excel(verspaetung_datei)
verspaetung_spalte = [spalte for spalte in df.columns if "Departure Schedule Delay" in spalte][0]
df = df[["Date", "Airport", verspaetung_spalte]]
df = df.rename(columns={verspaetung_spalte: "Abflugverspätung ZRH"})
df = df[df["Airport"] == "Zurich"].copy()
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df[df["Date"] < "2026-03-01"]
df = df[["Date", "Abflugverspätung ZRH"]]


# Abflüge direkt aus der Quelle hinzufügen
df_abfluege = pd.read_csv(abfluege_datei)
df_abfluege["datum"] = df_abfluege["datum"].astype(str).str.strip()
df_abfluege["datum"] = pd.to_datetime(
    df_abfluege["datum"],
    format="%d.%m.%y",
    errors="coerce",
)
df_abfluege = df_abfluege[df_abfluege["datum"] >= "2022-01-01"]
df_abfluege = df_abfluege[
    ["datum", "anzahl_abfluege_total", "piste_10", "piste_16", "piste_28", "piste_32", "piste_34"]
]

df = df.merge(df_abfluege, how="left", left_on="Date", right_on="datum")
df = df.drop(columns=["datum"])


# Wetterdaten direkt aus der Quelle hinzufügen
df_wetter = pd.read_csv(wetter_datei)
df_wetter = df_wetter[["date", "prcp", "wspd", "wpgt", "tavg"]]
df_wetter = df_wetter.rename(
    columns={
        "date": "Date",
        "prcp": "regen",
        "wspd": "windgeschwindigkeit",
        "wpgt": "maximale_windgeschwindigkeit",
        "tavg": "temperatur",
    }
)
df_wetter["Date"] = pd.to_datetime(df_wetter["Date"], errors="coerce")

# Schnee ist in der Rohdatei nicht gefüllt, deshalb wie im Wrangling ableiten
df_wetter["schnee_vorhanden"] = (
    (df_wetter["temperatur"] < 2) & (df_wetter["regen"] > 0)
)
df_wetter["schnee_intensität"] = 0.0
df_wetter.loc[df_wetter["schnee_vorhanden"], "schnee_intensität"] = df_wetter.loc[
    df_wetter["schnee_vorhanden"], "regen"
]

df = df.merge(df_wetter, how="left", on="Date")


# Ölpreise direkt aus der Quelle hinzufügen, ohne Wochenenden aufzufüllen
df_oel = pd.read_csv(oelpreis_datei)
df_oel["oil_date"] = pd.to_datetime(df_oel["oil_date"], errors="coerce")
df_oel = df_oel[["oil_date", "oil_price"]]

df = df.merge(df_oel, how="left", left_on="Date", right_on="oil_date")
df = df.drop(columns=["oil_date"])


# Feiertage erzeugen, da es dafür keine eigene Quelldatei gibt
jahre = range(df["Date"].dt.year.min(), df["Date"].dt.year.max() + 1)
schweiz_feiertag = holidays.Switzerland(subdiv="ZH", years=jahre)
schweiz_feiertag = pd.to_datetime(list(schweiz_feiertag.keys()))
df["Feiertage"] = df["Date"].isin(schweiz_feiertag)


# WEF über den bestehenden Scraper holen; falls das nicht klappt, aus merge.csv übernehmen
try:
    from Andere_Skripte.WEF_scraper import fetch_wef_dates

    df_wef = pd.to_datetime(fetch_wef_dates())
    df["WEF"] = df["Date"].isin(df_wef)
except Exception as fehler:
    print("Warnung: WEF-Daten konnten nicht direkt geladen werden:", fehler)
    print("WEF wird deshalb aus merge.csv übernommen.")
    df_merge = pd.read_csv(projekt_root / "merge.csv", usecols=["Date", "WEF"])
    df_merge["Date"] = pd.to_datetime(df_merge["Date"], errors="coerce")
    df = df.merge(df_merge, how="left", on="Date")


# Relevante Spalten auswählen
spalten = [
    "Date",
    "schnee_vorhanden",
    "Feiertage",
    "WEF",
    "anzahl_abfluege_total",
    "piste_10",
    "piste_16",
    "piste_28",
    "piste_32",
    "piste_34",
    "Abflugverspätung ZRH",
    "regen",
    "windgeschwindigkeit",
    "maximale_windgeschwindigkeit",
    "temperatur",
    "schnee_intensität",
    "oil_price",
]

df = df[spalten].copy()


# Numerische Spalten umwandeln
numerische_spalten = [
    "anzahl_abfluege_total",
    "piste_10",
    "piste_16",
    "piste_28",
    "piste_32",
    "piste_34",
    "Abflugverspätung ZRH",
    "regen",
    "windgeschwindigkeit",
    "maximale_windgeschwindigkeit",
    "temperatur",
    "schnee_intensität",
    "oil_price",
]

for spalte in numerische_spalten:
    df[spalte] = pd.to_numeric(df[spalte], errors="coerce")


# Kurze Qualitätschecks in der Konsole
print("Qualitätscheck aus Rohquellen")
print("-----------------------------")
print("Anzahl Zeilen:", len(df))
print("Anzahl Spalten:", len(df.columns))
print()

print("Fehlende Werte pro Spalte:")
print(df.isna().sum())
print()

print("Anzahl Duplikate:", df.duplicated().sum())
print()


# Einfacher Plausibilitätscheck
if (df["anzahl_abfluege_total"] < 0).any():
    print("Warnung: Negative Werte bei anzahl_abfluege_total gefunden")

if (df["regen"] < 0).any():
    print("Warnung: Negative Werte bei regen gefunden")

if (df["windgeschwindigkeit"] < 0).any():
    print("Warnung: Negative Werte bei windgeschwindigkeit gefunden")


# Automatisches Profil erstellen
profil = ProfileReport(df, title="Qualitaetsprofil aus Rohquellen", explorative=True)
profil.to_file(output_datei)

print("HTML-Profil erstellt:", output_datei)
