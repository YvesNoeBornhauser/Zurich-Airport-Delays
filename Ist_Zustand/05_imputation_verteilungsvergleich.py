from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MERGE_DATEI = ROOT / "merge.csv"

SPALTEN = {
    "regen": "regen_imputiert",
    "maximale_windgeschwindigkeit": "maximale_windgeschwindigkeit_imputiert",
    "oil_price": "oil_price_imputiert",
}


def als_bool(spalte):
    if pd.api.types.is_bool_dtype(spalte):
        return spalte

    werte = spalte.astype("string").str.strip().str.lower()
    bool_mapping = {
        "true": True,
        "false": False,
        "1": True,
        "0": False,
        "ja": True,
        "nein": False,
    }
    konvertiert = werte.map(bool_mapping)

    if konvertiert.isna().any():
        ungueltig = sorted(spalte[konvertiert.isna()].dropna().astype(str).unique())
        raise ValueError(f"Ungueltige Werte in Indikatorspalte: {ungueltig}")

    return konvertiert.astype(bool)


def formatiere_zahl(wert):
    if pd.isna(wert):
        return "-"
    return f"{wert:.2f}"


def kennzahlen(werte):
    return {
        "Mittelwert": formatiere_zahl(werte.mean()),
        "Median": formatiere_zahl(werte.median()),
        "Std.": formatiere_zahl(werte.std()),
    }


def main():
    df = pd.read_csv(MERGE_DATEI)

    benoetigte_spalten = set(SPALTEN.keys()) | set(SPALTEN.values())
    fehlende_spalten = sorted(benoetigte_spalten - set(df.columns))
    if fehlende_spalten:
        raise ValueError(f"Fehlende Spalten in merge.csv: {fehlende_spalten}")

    zeilen = []
    for wert_spalte, indikator_spalte in SPALTEN.items():
        werte = pd.to_numeric(df[wert_spalte], errors="coerce")
        imputiert = als_bool(df[indikator_spalte])
        vorhanden = ~imputiert

        vorher = werte[vorhanden].dropna()
        nachher = werte.dropna()

        vorher_stats = kennzahlen(vorher)
        nachher_stats = kennzahlen(nachher)

        zeilen.append(
            {
                "Spalte": wert_spalte,
                "Vorhanden (n)": int(vorhanden.sum()),
                "Imputiert (n)": int(imputiert.sum()),
                "Mittelwert vorher": vorher_stats["Mittelwert"],
                "Mittelwert nachher": nachher_stats["Mittelwert"],
                "Median vorher": vorher_stats["Median"],
                "Median nachher": nachher_stats["Median"],
                "Std. vorher": vorher_stats["Std."],
                "Std. nachher": nachher_stats["Std."],
            }
        )

    tabelle = pd.DataFrame(zeilen)

    print("Verteilungsvergleich vor/nach Imputation")
    print(f"Datei: {MERGE_DATEI.name}")
    print()
    print(tabelle.to_string(index=False))


if __name__ == "__main__":
    main()
