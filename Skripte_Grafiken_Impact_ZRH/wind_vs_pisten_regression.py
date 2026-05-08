import pathlib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import statsmodels.api as sm


# ── ZRH Style ────────────────────────────────────────────────────────────────
ZRH_BLUE = "#003874"
ZRH_RED = "#DC0018"
ZRH_SKY = "#009EE0"
ZRH_GREY = "#939598"

ZRH_COLORS = [ZRH_BLUE, ZRH_SKY, ZRH_RED, ZRH_GREY]
ZRH_PALETTE = sns.color_palette(ZRH_COLORS)


def set_zrh_style():
    sns.set_theme(style="white", palette=ZRH_PALETTE)
    plt.rcParams.update({
        "font.sans-serif": "Arial",
        "axes.titleweight": "bold",
        "axes.titlesize": 14,
        "axes.titlepad": 20,
        "axes.labelcolor": "#58595B",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.frameon": False,
        "figure.figsize": (10, 6),
        "figure.dpi": 100,
    })


def standardize(series):
    return (series - series.mean()) / series.std()


def print_model_checks(model_data, predictors):
    print("Fehlende Werte pro Modellspalte:")
    print(model_data[["Avg Departure Schedule Delay"] + predictors].isna().sum().to_string())

    print("\nDatentypen pro Modellspalte:")
    print(model_data[["Avg Departure Schedule Delay"] + predictors].dtypes.to_string())


def fit_ols(model_data, target, predictors):
    y = model_data[target]
    x = sm.add_constant(model_data[predictors])
    return sm.OLS(y, x).fit()


set_zrh_style()

# ── Daten laden ───────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "merge.csv", parse_dates=["Date"])

# ── Modellvariablen vorbereiten ───────────────────────────────────────────────
df["Avg Departure Schedule Delay"] = df["Abflugverspätung ZRH"]
df["public_holiday"] = df["Feiertage"].astype(int)
df["schnee_vorhanden"] = df["schnee_vorhanden"].astype(int)
df["WEF"] = df["WEF"].astype(int)

df["Anteil_Piste_16"] = df["piste_16"] / df["anzahl_abfluege_total"] * 100
df["Anteil_Piste_28"] = df["piste_28"] / df["anzahl_abfluege_total"] * 100
df["Anteil_Piste_32"] = df["piste_32"] / df["anzahl_abfluege_total"] * 100
df["Anteil_Piste_34"] = df["piste_34"] / df["anzahl_abfluege_total"] * 100

target = "Avg Departure Schedule Delay"
predictors = [
    "windgeschwindigkeit",
    "anzahl_abfluege_total",
    "regen",
    "temperatur",
    "schnee_vorhanden",
    "public_holiday",
    "WEF",
    "Anteil_Piste_16",
    "Anteil_Piste_28",
    "Anteil_Piste_32",
]

# Piste 34 wird bewusst weggelassen, weil sich alle Pistenanteile zu 100 Prozent summieren.
model_data = df[["Date", target] + predictors + ["Anteil_Piste_34"]].dropna().copy()

print_model_checks(model_data, predictors)

# ── Modell 1: Originaleinheiten ───────────────────────────────────────────────
model_original = fit_ols(model_data, target, predictors)

print("\n" + "=" * 80)
print("MODELL 1: Originaleinheiten")
print("=" * 80)
print(model_original.summary())
print(f"\nR² Originalmodell: {model_original.rsquared:.4f}")
print("\np-Werte Originalmodell:")
print(model_original.pvalues.to_string())

# ── Modell 2: standardisierte numerische Variablen ────────────────────────────
continuous_predictors = [
    "windgeschwindigkeit",
    "anzahl_abfluege_total",
    "regen",
    "temperatur",
    "Anteil_Piste_16",
    "Anteil_Piste_28",
    "Anteil_Piste_32",
]
dummy_predictors = ["schnee_vorhanden", "public_holiday", "WEF"]

model_data_std = model_data.copy()
model_data_std[target] = standardize(model_data_std[target])

for col in continuous_predictors:
    model_data_std[col] = standardize(model_data_std[col])

model_standardized = fit_ols(
    model_data_std,
    target,
    continuous_predictors + dummy_predictors,
)

print("\n" + "=" * 80)
print("MODELL 2: Standardisierte Zielvariable und standardisierte numerische Features")
print("=" * 80)
print(model_standardized.summary())
print(f"\nR² standardisiertes Modell: {model_standardized.rsquared:.4f}")
print("\np-Werte standardisiertes Modell:")
print(model_standardized.pvalues.to_string())

# ── Wind vs. Pistennutzung vergleichen ────────────────────────────────────────
comparison_vars = [
    "windgeschwindigkeit",
    "Anteil_Piste_16",
    "Anteil_Piste_28",
    "Anteil_Piste_32",
]

comparison = pd.DataFrame({
    "Variable": comparison_vars,
    "Koeffizient": model_standardized.params[comparison_vars],
    "p_wert": model_standardized.pvalues[comparison_vars],
})
comparison["abs_koeffizient"] = comparison["Koeffizient"].abs()

print("\nVergleich Wind vs. Pistennutzung im standardisierten Modell:")
print(
    comparison
    .sort_values("abs_koeffizient", ascending=False)
    .round(4)
    .to_string(index=False)
)

wind_abs = comparison.loc[
    comparison["Variable"] == "windgeschwindigkeit",
    "abs_koeffizient",
].iloc[0]
piste_max_abs = comparison.loc[
    comparison["Variable"].str.startswith("Anteil_Piste"),
    "abs_koeffizient",
].max()

if piste_max_abs > wind_abs:
    print("\nInterpretation: Die Pistennutzung hat im Modell den stärkeren eigenständigen Effekt als Wind allein.")
else:
    print("\nInterpretation: Wind hat im Modell den stärkeren eigenständigen Effekt als die einzelnen Pistenanteile.")

# ── Grafik: standardisierte Koeffizienten ─────────────────────────────────────
labels = {
    "windgeschwindigkeit": "Windgeschwindigkeit",
    "anzahl_abfluege_total": "Anzahl Abflüge",
    "regen": "Regen",
    "temperatur": "Temperatur",
    "schnee_vorhanden": "Schnee vorhanden",
    "public_holiday": "Feiertag",
    "WEF": "WEF",
    "Anteil_Piste_16": "Anteil Piste 16",
    "Anteil_Piste_28": "Anteil Piste 28",
    "Anteil_Piste_32": "Anteil Piste 32",
}

coef_df = pd.DataFrame({
    "Variable": model_standardized.params.index,
    "Koeffizient": model_standardized.params.values,
    "p_wert": model_standardized.pvalues.values,
})
coef_df = coef_df[coef_df["Variable"] != "const"].copy()
coef_df["Label"] = coef_df["Variable"].map(labels)
coef_df["Signifikant"] = coef_df["p_wert"] < 0.05
coef_df["Fokus"] = coef_df["Variable"].isin(comparison_vars)
coef_df = coef_df.sort_values("Koeffizient")

bar_colors = [
    ZRH_RED if fokus and value > 0 else
    ZRH_BLUE if fokus else
    ZRH_SKY if value > 0 else
    ZRH_GREY
    for fokus, value in zip(coef_df["Fokus"], coef_df["Koeffizient"])
]

fig, ax = plt.subplots(figsize=(11, 7))
fig.patch.set_facecolor("white")

bars = ax.barh(
    coef_df["Label"],
    coef_df["Koeffizient"],
    color=bar_colors,
    height=0.62,
)

ax.axvline(0, color=ZRH_GREY, linewidth=0.9, linestyle="--")
ax.set_xlabel("Standardisierter Koeffizient", color="#58595B")
ax.set_ylabel("")
ax.set_title(
    "Pistenanteile erklären Verspätungen eigenständiger als Wind allein",
    fontsize=13,
    fontweight="bold",
    color=ZRH_BLUE,
    pad=16,
)

for bar, value, p_value in zip(bars, coef_df["Koeffizient"], coef_df["p_wert"]):
    x_offset = 0.015 if value >= 0 else -0.015
    ha = "left" if value >= 0 else "right"
    stars = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else ""
    ax.text(
        value + x_offset,
        bar.get_y() + bar.get_height() / 2,
        f"{value:+.2f}{stars}",
        va="center",
        ha=ha,
        fontsize=9,
        color="#58595B",
    )

ax.text(
    0.01,
    0.02,
    f"R² = {model_standardized.rsquared:.2f} | Referenz: Piste 34 | * p < 0.05",
    transform=ax.transAxes,
    fontsize=9,
    color="#58595B",
)

ax.xaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "wind_vs_pisten_regression.png", dpi=150, bbox_inches="tight")
print("\nGespeichert: wind_vs_pisten_regression.png")
plt.close(fig)
