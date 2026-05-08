import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


# ── ZRH Style ────────────────────────────────────────────────────────────────
ZRH_BLUE  = "#003874"
ZRH_RED   = "#DC0018"
ZRH_SKY   = "#009EE0"
ZRH_GREY  = "#939598"

ZRH_COLORS  = [ZRH_BLUE, ZRH_SKY, ZRH_RED, ZRH_GREY]
ZRH_PALETTE = sns.color_palette(ZRH_COLORS)


def set_zrh_style():
    sns.set_theme(style="white", palette=ZRH_PALETTE)
    plt.rcParams.update({
        "font.sans-serif":   "Arial",
        "axes.titleweight":  "bold",
        "axes.titlesize":    14,
        "axes.titlepad":     18,
        "axes.labelcolor":   "#58595B",
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "xtick.labelsize":   10,
        "ytick.labelsize":   10,
        "legend.frameon":    False,
        "figure.figsize":    (12, 6),
        "figure.dpi":        100,
    })


set_zrh_style()

# ── Daten ─────────────────────────────────────────────────────────────────────
df = pd.read_csv(ROOT / "merge.csv", parse_dates=["Date"])
wind = df["maximale_windgeschwindigkeit"].dropna()

sturm_grenze = 60
sturmtage = (wind >= sturm_grenze).sum()
anteil_sturmtage = sturmtage / len(wind) * 100

max_wind = np.ceil(wind.max() / 5) * 5
bins = np.arange(10, max_wind + 5, 5)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("white")

counts, bin_edges, patches = ax.hist(
    wind,
    bins=bins,
    color=ZRH_BLUE,
    edgecolor="white",
    linewidth=0.7,
    zorder=2,
)

for patch in patches:
    if patch.get_x() >= sturm_grenze:
        patch.set_facecolor(ZRH_RED)

ax.axvline(
    sturm_grenze,
    color=ZRH_RED,
    linestyle="--",
    linewidth=2,
    zorder=3,
)

ax.text(
    sturm_grenze + 1.5,
    max(counts) * 0.88,
    f"Sturmtage\nab {sturm_grenze} km/h\n{sturmtage} Tage ({anteil_sturmtage:.1f}%)",
    ha="left",
    va="top",
    fontsize=10,
    color=ZRH_RED,
    fontweight="bold",
)

ax.set_ylim(bottom=0)
ax.set_xlim(10, max_wind)
ax.set_xlabel("Maximale Windgeschwindigkeit (km/h)", color="#58595B", labelpad=10)
ax.set_ylabel("Anzahl Tage", color="#58595B", labelpad=10)
ax.set_title(
    "Normales Zürcher Wetter bleibt meist unter 50 km/h, Sturmtage bilden den rechten Rand",
    fontsize=13,
    fontweight="bold",
    color=ZRH_BLUE,
    pad=16,
)

ax.yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8, zorder=1)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

plt.tight_layout()

out_dir = ROOT / "Ist_Zustand" / "Grafiken"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "04_max_windgeschwindigkeit_histogramm.png", dpi=150, bbox_inches="tight")

print("Gespeichert: 04_max_windgeschwindigkeit_histogramm.png")
print(f"Sturmtage ab {sturm_grenze} km/h: {sturmtage} ({anteil_sturmtage:.1f}%)")
plt.close(fig)
