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
        "figure.figsize":    (12, 7),
        "figure.dpi":        100,
    })


set_zrh_style()

# ── Daten ─────────────────────────────────────────────────────────────────────
df = pd.read_csv(ROOT / "merge.csv", parse_dates=["Date"])

TARGET = "Abflugverspätung ZRH"
delay = df[TARGET].dropna()

mittelwert = delay.mean()
q1 = delay.quantile(0.25)
q2 = delay.median()
q3 = delay.quantile(0.75)
iqr = q3 - q1
ausreisser_grenze = q3 + 1.5 * iqr
ausreisser = delay[delay > ausreisser_grenze]
unterer_whisker = delay[delay >= q1 - 1.5 * iqr].min()
oberer_whisker = delay[delay <= ausreisser_grenze].max()

max_delay = np.ceil(delay.max() / 5) * 5
bins = np.arange(0, max_delay + 2.5, 2.5)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, (ax_hist, ax_box) = plt.subplots(
    2,
    1,
    figsize=(12, 7),
    sharex=True,
    gridspec_kw={"height_ratios": [4, 1.45], "hspace": 0.06},
)
fig.patch.set_facecolor("white")

ax_hist.hist(
    delay,
    bins=bins,
    color=ZRH_BLUE,
    edgecolor="white",
    linewidth=0.7,
    zorder=2,
)

ax_hist.axvline(q2, color=ZRH_SKY, linestyle=":", linewidth=2, label=f"Median: {q2:.1f} min")
ax_hist.axvline(mittelwert, color=ZRH_RED, linestyle="--", linewidth=2, label=f"Durchschnitt: {mittelwert:.1f} min")
ax_hist.set_ylim(bottom=0)
ax_hist.set_ylabel("Anzahl Tage", color="#58595B", labelpad=10)
ax_hist.set_title(
    "Die meisten ZRH-Tage liegen im Normalbereich, wenige Ausreisser ziehen den Durchschnitt nach rechts",
    fontsize=13,
    fontweight="bold",
    color=ZRH_BLUE,
    pad=16,
)
ax_hist.yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8, zorder=1)
ax_hist.set_axisbelow(True)
ax_hist.legend(loc="upper right")

ax_box.boxplot(
    delay,
    vert=False,
    patch_artist=True,
    widths=0.48,
    boxprops={"facecolor": ZRH_BLUE, "edgecolor": ZRH_BLUE, "alpha": 0.85},
    medianprops={"color": "white", "linewidth": 2},
    whiskerprops={"color": ZRH_BLUE, "linewidth": 1.6},
    capprops={"color": ZRH_BLUE, "linewidth": 1.6},
    flierprops={
        "marker": "o",
        "markerfacecolor": ZRH_RED,
        "markeredgecolor": "white",
        "markersize": 5,
        "alpha": 0.9,
    },
)
ax_box.set_yticks([])
ax_box.set_ylim(0.35, 1.85)
ax_box.set_xlim(0, max_delay)
ax_box.set_xlabel("Abflugverspätung ZRH (Minuten)", color="#58595B", labelpad=10)
ax_box.xaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8, zorder=1)
ax_box.set_axisbelow(True)

boxplot_labels = [
    ("Unterer\nWhisker", unterer_whisker, 0.58, ZRH_GREY),
    ("Q1", q1, 1.48, ZRH_BLUE),
    ("Q2 / Median", q2, 1.70, ZRH_SKY),
    ("Q3", q3, 1.48, ZRH_BLUE),
    ("Oberer\nWhisker", oberer_whisker, 0.58, ZRH_GREY),
]

for label, value, y_text, color in boxplot_labels:
    ax_box.annotate(
        f"{label}\n{value:.1f} min",
        xy=(value, 1),
        xytext=(value, y_text),
        ha="center",
        va="center",
        fontsize=8.5,
        color=color,
        fontweight="bold",
        arrowprops={"arrowstyle": "-", "color": color, "linewidth": 0.9},
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none", "alpha": 0.9},
    )

ax_box.text(
    0.98,
    0.12,
    f"{len(ausreisser)} Ausreisser über {ausreisser_grenze:.1f} Minuten",
    transform=ax_box.transAxes,
    ha="right",
    va="center",
    fontsize=10,
    color=ZRH_RED,
    fontweight="bold",
)

for ax in [ax_hist, ax_box]:
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

fig.subplots_adjust(left=0.08, right=0.97, top=0.88, bottom=0.12)

out_dir = ROOT / "Ist_Zustand" / "Grafiken"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "01_02_verspaetung_histogramm_boxplot.png", dpi=150, bbox_inches="tight")

print("Gespeichert: 01_02_verspaetung_histogramm_boxplot.png")
print(f"Q1: {q1:.2f} min")
print(f"Q2 / Median: {q2:.2f} min")
print(f"Q3: {q3:.2f} min")
print(f"Durchschnitt: {mittelwert:.2f} min")
print(f"Ausreisser: {len(ausreisser)}")
plt.close(fig)
