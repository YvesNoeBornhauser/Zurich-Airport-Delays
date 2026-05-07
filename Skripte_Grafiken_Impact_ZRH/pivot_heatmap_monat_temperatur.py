import pathlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import pandas as pd
import numpy as np

# ── ZRH Style ────────────────────────────────────────────────────────────────
ZRH_BLUE = "#003874"
ZRH_RED  = "#DC0018"
ZRH_SKY  = "#009EE0"
ZRH_GREY = "#939598"

def set_zrh_style():
    sns.set_theme(style="white", palette=sns.color_palette([ZRH_BLUE, ZRH_SKY, ZRH_RED, ZRH_GREY]))
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
        "figure.figsize":    (13, 7),
        "figure.dpi":        100,
    })

set_zrh_style()

zrh_cmap = mcolors.LinearSegmentedColormap.from_list(
    "zrh_seq", ["#F2F2F2", ZRH_SKY, ZRH_BLUE, ZRH_RED]
)

# ── Daten & Bins ──────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "merge.csv", index_col=0)

BIN_EDGES  = list(range(-10, 31, 5))
BIN_LABELS = [f"{lo}–{lo+5} °C" for lo in BIN_EDGES[:-1]]
MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez",
}

df["temp_bin"] = pd.cut(df["temperatur"], bins=BIN_EDGES, labels=BIN_LABELS, right=False)
df["month_name"] = df["month"].map(MONTH_NAMES)

pivot = (
    df.groupby(["month", "temp_bin"], observed=True)["Abflugverspätung ZRH"]
    .mean()
    .unstack("temp_bin")
)
pivot.index = [MONTH_NAMES[m] for m in pivot.index]

# Stichprobenanzahl für Annotation (n)
counts = (
    df.groupby(["month", "temp_bin"], observed=True)["Abflugverspätung ZRH"]
    .count()
    .unstack("temp_bin")
)
counts.index = [MONTH_NAMES[m] for m in counts.index]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 7))
fig.patch.set_facecolor("white")

sns.heatmap(
    pivot,
    cmap=zrh_cmap,
    annot=pivot.round(1).astype(str).where(pivot.notna(), other="–"),
    fmt="",
    annot_kws={"size": 9},
    linewidths=0.25,
    linecolor="#E6E6E6",
    cbar_kws={"label": "Ø Verspätung (min)", "shrink": 0.75},
    ax=ax,
    mask=pivot.isna(),
)

ax.set_title(
    "Sommer bleibt auch bei tieferen Temperaturen verspätungsstark; Temperatur allein erklärt den Effekt nicht",
    fontsize=13, fontweight="bold", color=ZRH_BLUE, pad=16,
)
ax.set_xlabel("Temperaturklasse (5 °C-Bins)", color="#58595B", labelpad=10)
ax.set_ylabel("Monat", color="#58595B", labelpad=10)
ax.tick_params(axis="x", rotation=0)
ax.tick_params(axis="y", rotation=0)

for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "pivot_heatmap_monat_temperatur.png", dpi=150, bbox_inches="tight")
print("Gespeichert: pivot_heatmap_monat_temperatur.png")
plt.close(fig)
