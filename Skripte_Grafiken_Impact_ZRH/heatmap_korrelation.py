import pathlib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import pandas as pd
import numpy as np

# ── ZRH Style ────────────────────────────────────────────────────────────────
ZRH_BLUE  = "#003874"
ZRH_RED   = "#DC0018"
ZRH_SKY   = "#009EE0"
ZRH_GREY  = "#939598"
ZRH_BG    = "#F2F2F2"

ZRH_COLORS  = [ZRH_BLUE, ZRH_SKY, ZRH_RED, ZRH_GREY]
ZRH_PALETTE = sns.color_palette(ZRH_COLORS)

def set_zrh_style():
    sns.set_theme(style="white", palette=ZRH_PALETTE)
    plt.rcParams.update({
        "font.sans-serif":   "Arial",
        "axes.titleweight":  "bold",
        "axes.titlesize":    14,
        "axes.titlepad":     20,
        "axes.labelcolor":   "#58595B",
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "xtick.labelsize":   10,
        "ytick.labelsize":   10,
        "legend.frameon":    False,
        "figure.figsize":    (10, 6),
        "figure.dpi":        100,
    })

set_zrh_style()

# ── Colormap ZRH Blue → Weiss → ZRH Red ──────────────────────────────────────
zrh_cmap = mcolors.LinearSegmentedColormap.from_list(
    "zrh_diverging", [ZRH_BLUE, "white", ZRH_RED]
)

# ── Daten laden ───────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "merge.csv", index_col=0, parse_dates=["Date"])

if "schnee_vorhanden" not in df.columns:
    df["schnee_vorhanden"] = np.where((df["temperatur"] < 2) & (df["regen"] > 0), 1, 0)
if "schnee_intensität" not in df.columns:
    df["schnee_intensität"] = np.where((df["temperatur"] < 2) & (df["regen"] > 0), df["regen"], 0)

# Kategorische Spalten kodieren
df["WEF"]            = df["WEF"].map({True: 1, False: 0, "True": 1, "False": 0})
df["Feiertage"]     = df["Feiertage"].map({True: 1, False: 0, "True": 1, "False": 0})

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
df["day_of_week"] = pd.Categorical(df["day_of_week"], categories=DAY_ORDER, ordered=True).codes

NUMERIC_COLS = [
    "Abflugverspätung ZRH",
    "anzahl_abfluege_total",
    "piste_16", "piste_28", "piste_32", "piste_34", "piste_10_binär",
    "regen", "windgeschwindigkeit", "maximale_windgeschwindigkeit",
    "temperatur", "schnee_vorhanden", "schnee_intensität",
    "oil_price", "90_day_average_oil_price",
    "oil_trend", "oil_volatility_90",
    "Feiertage", "WEF", "day_of_week", "month",
]

LABELS = {
    "Abflugverspätung ZRH": "Ø Abflugverspätung",
    "anzahl_abfluege_total":        "Anzahl Abflüge",
    "piste_16":                     "Piste 16",
    "piste_28":                     "Piste 28",
    "piste_32":                     "Piste 32",
    "piste_34":                     "Piste 34",
    "piste_10_binär":               "Piste 10 (binär)",
    "regen":                        "Regen",
    "windgeschwindigkeit":          "Windgeschwindigkeit",
    "maximale_windgeschwindigkeit": "Max. Windgeschwindigkeit",
    "temperatur":                   "Temperatur",
    "schnee_vorhanden":             "Schnee vorhanden",
    "schnee_intensität":            "Schnee-Intensität",
    "oil_price":                    "Ölpreis",
    "90_day_average_oil_price":     "90-Tage-Ø Ölpreis",
    "oil_trend":                    "Ölpreis-Trend",
    "oil_volatility_90":            "Ölpreis-Volatilität (90 T.)",
    "Feiertage":                    "Feiertag",
    "WEF":                          "WEF",
    "day_of_week":                  "Wochentag",
    "month":                        "Monat",
}

numeric_df = df[NUMERIC_COLS].rename(columns=LABELS).dropna()
corr = numeric_df.corr()

HEATMAP_LABELS = {
    "Ø Abflugverspätung": "Ø Abflug-\nverspätung",
    "Anzahl Abflüge": "Anzahl\nAbflüge",
    "Piste 10 (binär)": "Piste 10\n(binär)",
    "Windgeschwindigkeit": "Wind-\ngeschw.",
    "Max. Windgeschwindigkeit": "Max. Wind-\ngeschw.",
    "Schnee vorhanden": "Schnee\nvorhanden",
    "Schnee-Intensität": "Schnee-\nIntensität",
    "90-Tage-Ø Ölpreis": "90-Tage-Ø\nÖlpreis",
    "Ölpreis-Trend": "Ölpreis-\nTrend",
    "Ölpreis-Volatilität (90 T.)": "Ölpreis-\nVolatilität\n(90 T.)",
}

# ── Grafik 1: Vollständige Korrelationsmatrix ─────────────────────────────────
fig, ax = plt.subplots(figsize=(20, 17))
fig.patch.set_facecolor("white")

mask = np.triu(np.ones_like(corr, dtype=bool), k=1)  # oberes Dreieck ausblenden
corr_heatmap = corr.rename(index=HEATMAP_LABELS, columns=HEATMAP_LABELS)

sns.heatmap(
    corr_heatmap,
    mask=mask,
    cmap=zrh_cmap,
    vmin=-1, vmax=1,
    annot=True, fmt=".2f",
    annot_kws={"size": 6},
    linewidths=0.25, linecolor="#E6E6E6",
    square=True,
    cbar_kws={"shrink": 0.7, "label": "Pearson r"},
    ax=ax,
)

ax.tick_params(axis="y", labelrotation=0)
ax.tick_params(axis="x", labelrotation=0, labelsize=8)
ax.set_xticklabels(ax.get_xticklabels(), ha="center")
ax.set_facecolor("white")
ax.set_title(
    "Erster Überblick: Abfluganzahl, Temperatur, Schnee und Piste 32 zeigen die stärksten Zusammenhänge",
    fontsize=13,
    fontweight="bold",
    color=ZRH_BLUE,
    pad=18,
)

for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()

out_dir = pathlib.Path(__file__).resolve().parents[1] / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "heatmap_korrelation_voll.png", dpi=150, bbox_inches="tight")
print("Gespeichert: heatmap_korrelation_voll.png")
plt.close(fig)

# ── Grafik 2: Fokus – Korrelation mit Ø Abflugverspätung ─────────────────────
delay_corr = (
    corr["Ø Abflugverspätung"]
    .drop("Ø Abflugverspätung")
    .sort_values()
)

colors = [ZRH_RED if v > 0 else ZRH_BLUE for v in delay_corr.values]

fig2, ax2 = plt.subplots(figsize=(10, 9))
fig2.patch.set_facecolor("white")

bars = ax2.barh(delay_corr.index, delay_corr.values, color=colors, height=0.6)
ax2.axvline(0, color=ZRH_GREY, linewidth=0.8, linestyle="--")
ax2.set_xlim(-1, 1)
ax2.set_xlabel("Pearson r", color="#58595B")
ax2.set_title(
    "Abfluganzahl ist der stärkste lineare Treiber, Ölpreis-Signale bleiben schwach erklärbar",
    fontsize=13, fontweight="bold", color=ZRH_BLUE, pad=16,
)

for bar, value in zip(bars, delay_corr.values):
    x_offset = 0.02 if value >= 0 else -0.02
    ha = "left" if value >= 0 else "right"
    ax2.text(
        value + x_offset,
        bar.get_y() + bar.get_height() / 2,
        f"{value:.2f}",
        va="center",
        ha=ha,
        fontsize=9,
        color="#58595B",
        clip_on=False,
    )

for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)

ax2.set_facecolor("white")
plt.tight_layout()

fig2.savefig(out_dir / "heatmap_korrelation_delay_fokus.png", dpi=150, bbox_inches="tight")
print("Gespeichert: heatmap_korrelation_delay_fokus.png")
plt.close(fig2)
