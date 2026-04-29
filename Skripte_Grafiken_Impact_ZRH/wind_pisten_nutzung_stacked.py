import pathlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
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

# ── Daten laden ───────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]

df_weather = pd.read_csv(ROOT / "merge.csv", index_col=0, parse_dates=["Date"])
df_flights = pd.read_csv(ROOT / "Quellen" / "zrh_abfluege_pro_tag.csv")
df_flights["datum"] = pd.to_datetime(df_flights["datum"], format="%d.%m.%y").dt.normalize()

PISTE_COLS = ["piste_10", "piste_16", "piste_28", "piste_32", "piste_34"]
PISTE_LABELS = {
    "piste_10": "Piste 10",
    "piste_16": "Piste 16",
    "piste_28": "Piste 28",
    "piste_32": "Piste 32",
    "piste_34": "Piste 34",
}
PISTE_COLORS = {
    "piste_10": ZRH_GREY,
    "piste_16": ZRH_SKY,
    "piste_28": ZRH_BLUE,
    "piste_32": ZRH_RED,
    "piste_34": "#58595B",
}

df = df_weather[["Date", "windgeschwindigkeit"]].merge(
    df_flights[["datum"] + PISTE_COLS],
    left_on="Date",
    right_on="datum",
    how="inner",
)
df = df.dropna(subset=["windgeschwindigkeit"] + PISTE_COLS)

# ── Windgeschwindigkeit in 5-km/h-Klassen einteilen ───────────────────────────
max_wind = df["windgeschwindigkeit"].max()
max_edge = int(np.ceil(max_wind / 5) * 5) + 5
bin_edges = list(range(0, max_edge + 1, 5))
bin_labels = [f"{lo}-{hi} km/h" for lo, hi in zip(bin_edges[:-1], bin_edges[1:])]

df["wind_bin"] = pd.cut(
    df["windgeschwindigkeit"],
    bins=bin_edges,
    labels=bin_labels,
    right=False,
    include_lowest=True,
)

usage_by_bin = df.groupby("wind_bin", observed=True)[PISTE_COLS].sum()
usage_by_bin = usage_by_bin[usage_by_bin.sum(axis=1) > 0]
share_by_bin = usage_by_bin.div(usage_by_bin.sum(axis=1), axis=0) * 100
days_by_bin = df.groupby("wind_bin", observed=True).size().reindex(share_by_bin.index)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6.5))
fig.patch.set_facecolor("white")

x_positions = np.arange(len(share_by_bin))
bottom = np.zeros(len(share_by_bin))

for piste in PISTE_COLS:
    values = share_by_bin[piste].values
    bars = ax.bar(
        x_positions,
        values,
        bottom=bottom,
        width=0.72,
        color=PISTE_COLORS[piste],
        label=PISTE_LABELS[piste],
        zorder=2,
    )

    for bar, value, base in zip(bars, values, bottom):
        if value < 7:
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            base + value / 2,
            f"{value:.0f}%",
            ha="center",
            va="center",
            fontsize=8,
            color="white",
            fontweight="bold",
        )

    bottom += values

tick_labels = [
    f"{wind_bin}\n(n={int(days_by_bin.loc[wind_bin])})"
    for wind_bin in share_by_bin.index
]

ax.set_xticks(x_positions)
ax.set_xticklabels(tick_labels)
ax.set_ylim(0, 100)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))
ax.set_ylabel("Anteil an Abflügen", color="#58595B")
ax.set_xlabel("Windgeschwindigkeit", color="#58595B")
ax.set_title(
    "Stärkere Winde verändern die Zusammensetzung der Pistennutzung",
    fontsize=13,
    fontweight="bold",
    color=ZRH_BLUE,
    pad=16,
)

ax.yaxis.grid(True, color="#E5E5E5", linewidth=0.6, zorder=1)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.16),
    ncol=len(PISTE_COLS),
)

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "wind_pisten_nutzung_stacked.png", dpi=150, bbox_inches="tight")
print("Gespeichert: wind_pisten_nutzung_stacked.png")
plt.close(fig)
