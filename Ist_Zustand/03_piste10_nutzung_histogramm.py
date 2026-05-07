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
        "xtick.labelsize":   9,
        "ytick.labelsize":   10,
        "legend.frameon":    False,
        "figure.figsize":    (12, 6),
        "figure.dpi":        100,
    })


set_zrh_style()

# ── Daten direkt aus der Originaldatei laden ─────────────────────────────────
df = pd.read_csv(ROOT / "Quellen" / "zrh_abfluege_pro_tag.csv")
df["datum"] = pd.to_datetime(df["datum"].astype(str).str.strip(), format="%d.%m.%y")
df = df[df["datum"] >= "2022-01-01"].copy()

piste10 = df["piste_10"].dropna()
tage_ohne_piste10 = (piste10 == 0).sum()
tage_mit_piste10 = (piste10 > 0).sum()
anteil_ohne_piste10 = tage_ohne_piste10 / len(piste10) * 100

# 0 wird bewusst als eigener Balken gezeigt, danach folgen 25er-Klassen
bin_edges = [-0.5, 0.5] + list(range(25, 300, 25)) + [300.5]
bin_labels = ["0", "1-24"] + [f"{start}-{start + 24}" for start in range(25, 276, 25)]

df["piste10_klasse"] = pd.cut(
    df["piste_10"],
    bins=bin_edges,
    labels=bin_labels,
    right=False,
)
counts = df["piste10_klasse"].value_counts().reindex(bin_labels, fill_value=0)

# ── Plot mit Achsenunterbrechung ───────────────────────────────────────────────
fig, (ax_top, ax_bottom) = plt.subplots(
    2,
    1,
    sharex=True,
    figsize=(12, 7),
    gridspec_kw={"height_ratios": [1, 3], "hspace": 0.06},
)
fig.patch.set_facecolor("white")

x_positions = np.arange(len(counts))
colors = [ZRH_GREY if label == "0" else ZRH_RED for label in counts.index]

for ax in [ax_top, ax_bottom]:
    ax.bar(
        x_positions,
        counts.values,
        color=colors,
        width=0.72,
        zorder=2,
    )
    ax.yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8, zorder=1)
    ax.set_axisbelow(True)
    for spine in ["right"]:
        ax.spines[spine].set_visible(False)

ax_bottom.set_ylim(0, 30)
ax_top.set_ylim(1300, counts.max() * 1.04)

ax_top.spines["bottom"].set_visible(False)
ax_bottom.spines["top"].set_visible(False)
ax_top.tick_params(axis="x", bottom=False, labelbottom=False)

ax_bottom.set_xticks(x_positions)
ax_bottom.set_xticklabels(counts.index)
ax_bottom.tick_params(axis="x", rotation=0)
ax_bottom.set_xlabel("Tägliche Abflüge auf Piste 10", color="#58595B", labelpad=10)
fig.text(0.015, 0.5, "Anzahl Tage", va="center", rotation="vertical", color="#58595B", fontsize=12)

ax_top.set_title(
    f"Piste 10 ist der Ausnahmefall: {anteil_ohne_piste10:.1f}% Nulltage, sonst bis {int(piste10.max())} Abflüge",
    fontsize=13,
    fontweight="bold",
    color=ZRH_BLUE,
    pad=16,
)

ax_top.text(
    x_positions[0],
    counts.iloc[0] + counts.max() * 0.01,
    f"{tage_ohne_piste10} Tage ohne Nutzung",
    ha="center",
    va="bottom",
    fontsize=10,
    color="#58595B",
    fontweight="bold",
)

ax_bottom.text(
    0.98,
    0.92,
    f"{tage_mit_piste10} Tage mit Piste 10\nMaximum: {int(piste10.max())} Abflüge",
    transform=ax_bottom.transAxes,
    ha="right",
    va="top",
    fontsize=10,
    color=ZRH_RED,
    fontweight="bold",
)

# Achsenbruch mit identischen Schrägstrich-Markern markieren
bruch_marker = [(-1, -0.7), (1, 0.7)]
bruch_kwargs = dict(
    marker=bruch_marker,
    markersize=14,
    linestyle="none",
    color="#2F2F2F",
    markeredgewidth=1.2,
    clip_on=False,
)
ax_top.plot([0, 1], [0, 0], transform=ax_top.transAxes, **bruch_kwargs)
ax_bottom.plot([0, 1], [1, 1], transform=ax_bottom.transAxes, **bruch_kwargs)

fig.subplots_adjust(left=0.12, right=0.97, bottom=0.12, top=0.9)

out_dir = ROOT / "Ist_Zustand" / "Grafiken"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "03_piste10_nutzung_histogramm.png", dpi=150, bbox_inches="tight")

print("Gespeichert: 03_piste10_nutzung_histogramm.png")
print(f"Tage ohne Piste 10: {tage_ohne_piste10} ({anteil_ohne_piste10:.1f}%)")
print(f"Tage mit Piste 10: {tage_mit_piste10}")
plt.close(fig)
