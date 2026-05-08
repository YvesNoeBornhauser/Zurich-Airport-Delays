import pathlib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
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
        "axes.titlepad":     20,
        "axes.labelcolor":   "#58595B",
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "xtick.labelsize":   10,
        "ytick.labelsize":   10,
        "legend.frameon":    False,
        "figure.figsize":    (11, 6),
        "figure.dpi":        100,
    })


set_zrh_style()

# ── Daten ─────────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "merge.csv", parse_dates=["Date"])

TARGET = "Abflugverspätung ZRH"
VOLUME = "anzahl_abfluege_total"
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_LABELS = {
    "Monday": "Montag",
    "Tuesday": "Dienstag",
    "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag",
    "Friday": "Freitag",
    "Saturday": "Samstag",
    "Sunday": "Sonntag",
}

df["weekday"] = pd.Categorical(
    df["Date"].dt.day_name(),
    categories=DAY_ORDER,
    ordered=True,
)

weekday_stats = (
    df.dropna(subset=[VOLUME, TARGET])
    .groupby("weekday", observed=True)
    .agg(
        avg_flights=(VOLUME, "mean"),
        avg_delay=(TARGET, "mean"),
        days=("Date", "count"),
    )
    .reindex(DAY_ORDER)
)
weekday_stats["weekday_de"] = [DAY_LABELS[day] for day in weekday_stats.index]

top_day = weekday_stats["avg_delay"].idxmax()
top_day_label = DAY_LABELS[top_day]
top_delay = weekday_stats.loc[top_day, "avg_delay"]
weekday_corr = weekday_stats["avg_flights"].corr(weekday_stats["avg_delay"])

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax1 = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor("white")

x = np.arange(len(weekday_stats))

bars = ax1.bar(
    x,
    weekday_stats["avg_flights"],
    color=ZRH_BLUE,
    alpha=0.42,
    width=0.68,
    zorder=2,
)

ax1.set_ylim(0, weekday_stats["avg_flights"].max() * 1.18)
ax1.set_xticks(x)
ax1.set_xticklabels(weekday_stats["weekday_de"])
ax1.set_ylabel("Ø Anzahl Abflüge pro Tag", color=ZRH_BLUE, fontweight="bold")
ax1.set_xlabel("")
ax1.tick_params(axis="y", colors=ZRH_BLUE)
ax1.yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8, zorder=1)
ax1.set_axisbelow(True)

for bar, value in zip(bars, weekday_stats["avg_flights"]):
    ax1.text(
        bar.get_x() + bar.get_width() / 2,
        value + weekday_stats["avg_flights"].max() * 0.018,
        f"{value:.0f}",
        ha="center",
        va="bottom",
        fontsize=9,
        color=ZRH_BLUE,
        fontweight="bold",
    )

ax2 = ax1.twinx()
ax2.plot(
    x,
    weekday_stats["avg_delay"],
    color=ZRH_RED,
    marker="o",
    linewidth=3,
    markersize=7,
    zorder=5,
)

ax2.set_ylim(0, weekday_stats["avg_delay"].max() * 1.28)
ax2.set_ylabel("Ø Abflugverspätung (min)", color=ZRH_RED, fontweight="bold")
ax2.tick_params(axis="y", colors=ZRH_RED)

for x_pos, value in zip(x, weekday_stats["avg_delay"]):
    ax2.text(
        x_pos,
        value + weekday_stats["avg_delay"].max() * 0.045,
        f"{value:.1f}",
        ha="center",
        va="bottom",
        fontsize=9,
        color=ZRH_RED,
        fontweight="bold",
    )

ax1.set_title(
    f"{top_day_label} hat die höchste Verspätung; über die Woche folgt sie stark dem Flugvolumen (r = {weekday_corr:.2f})",
    fontsize=13,
    fontweight="bold",
    color=ZRH_BLUE,
    pad=16,
)

for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(True)

legend_handles = [
    Patch(facecolor=ZRH_BLUE, alpha=0.42, label="Ø Anzahl Abflüge"),
    Line2D([0], [0], color=ZRH_RED, marker="o", linewidth=3, markersize=7, label="Ø Abflugverspätung"),
]
ax1.legend(handles=legend_handles, loc="upper left")

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "wochentag_volumen_delay_dual_axis.png", dpi=150, bbox_inches="tight")
print("Gespeichert: wochentag_volumen_delay_dual_axis.png")
print("\nWochentags-Statistik:")
print(weekday_stats[["avg_flights", "avg_delay", "days"]].round(2).to_string())
plt.close(fig)
