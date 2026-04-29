import pathlib
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

# Kategorische Spalten kodieren
df["WEF"]            = df["WEF"].map({True: 1, False: 0, "True": 1, "False": 0})
df["public_holiday"] = df["public_holiday"].map({True: 1, False: 0, "True": 1, "False": 0})

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
df["day_of_week"] = pd.Categorical(df["day_of_week"], categories=DAY_ORDER, ordered=True).codes

NUMERIC_COLS = [
    "Avg Departure Schedule Delay",
    "anzahl_abfluege_total",
    "piste_16", "piste_28", "piste_32", "piste_34", "piste_10_binär",
    "regen", "windgeschwindigkeit", "maximale_windgeschwindigkeit",
    "temperatur", "oil_price", "90_day_average_oil_price",
    "oil_trend", "oil_volatility_90",
    "public_holiday", "WEF", "day_of_week", "month",
]

LABELS = {
    "Avg Departure Schedule Delay": "Ø Abflugverspätung",
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
    "oil_price":                    "Ölpreis",
    "90_day_average_oil_price":     "90-Tage-Ø Ölpreis",
    "oil_trend":                    "Ölpreis-Trend",
    "oil_volatility_90":            "Ölpreis-Volatilität (90 T.)",
    "public_holiday":               "Feiertag",
    "WEF":                          "WEF",
    "day_of_week":                  "Wochentag",
    "month":                        "Monat",
}

numeric_df = df[NUMERIC_COLS].rename(columns=LABELS).dropna()
corr = numeric_df.corr()

# ── Grafik 1: Vollständige Korrelationsmatrix ─────────────────────────────────
fig, ax = plt.subplots(figsize=(15, 13))
fig.patch.set_facecolor("white")

mask = np.triu(np.ones_like(corr, dtype=bool), k=1)  # oberes Dreieck ausblenden

sns.heatmap(
    corr,
    mask=mask,
    cmap=zrh_cmap,
    vmin=-1, vmax=1,
    annot=True, fmt=".2f",
    annot_kws={"size": 7},
    linewidths=0.4, linecolor="#DDDDDD",
    square=True,
    cbar_kws={"shrink": 0.7, "label": "Pearson r"},
    ax=ax,
)

ax.set_title(
    "Windgeschwindigkeit und Pistennutzung korrelieren am stärksten\n"
    "mit der mittleren Abflugverspätung",
    fontsize=13, fontweight="bold", color=ZRH_BLUE, pad=16,
)
ax.tick_params(axis="x", labelrotation=45)
ax.tick_params(axis="y", labelrotation=0)
ax.set_facecolor("white")

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

fig2, ax2 = plt.subplots(figsize=(10, 8))
fig2.patch.set_facecolor("white")

bars = ax2.barh(delay_corr.index, delay_corr.values, color=colors, height=0.6)
ax2.axvline(0, color=ZRH_GREY, linewidth=0.8, linestyle="--")
ax2.set_xlim(-1, 1)
ax2.set_xlabel("Pearson r", color="#58595B")
ax2.set_title(
    "Anzahl Abflüge und Windgeschwindigkeit treiben die Verspätung –\n"
    "Temperatur wirkt leicht dämpfend",
    fontsize=13, fontweight="bold", color=ZRH_BLUE, pad=16,
)

for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)

ax2.set_facecolor("white")
plt.tight_layout()

fig2.savefig(out_dir / "heatmap_korrelation_delay_fokus.png", dpi=150, bbox_inches="tight")
print("Gespeichert: heatmap_korrelation_delay_fokus.png")
plt.close(fig2)
