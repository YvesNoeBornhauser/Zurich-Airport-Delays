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
        "figure.figsize":    (10, 6),
        "figure.dpi":        100,
    })

set_zrh_style()

# ── Daten ─────────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "merge.csv")

TARGET = "Abflugverspätung ZRH"
VOLUME = "anzahl_abfluege_total"

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez",
}
SOMMER = {6, 7, 8}

monthly_stats = (
    df.dropna(subset=[TARGET, VOLUME])
    .groupby("month")
    .agg(
        avg_delay=(TARGET, "mean"),
        avg_flights=(VOLUME, "mean"),
        days=("Date", "count"),
    )
    .reindex(range(1, 13))
)
top_month = monthly_stats["avg_delay"].idxmax()
top_delay = monthly_stats.loc[top_month, "avg_delay"]
monthly_corr = monthly_stats["avg_flights"].corr(monthly_stats["avg_delay"])

colors = [ZRH_SKY if m in SOMMER else ZRH_BLUE for m in monthly_stats.index]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("white")
x = np.arange(len(monthly_stats))

bars = ax.bar(
    x,
    monthly_stats["avg_delay"],
    color=colors,
    width=0.65,
    zorder=2,
)

ax.set_ylim(0, monthly_stats["avg_delay"].max() * 1.22)
ax.set_xticks(x)
ax.set_xticklabels([MONTH_NAMES[m] for m in monthly_stats.index])
ax.set_ylabel("Ø Abflugverspätung (min)", color="#58595B")
ax.set_title(
    f"{MONTH_NAMES[top_month]} ist der stärkste Verspätungsmonat; Flugvolumen und Verspätung hängen monatlich zusammen (r = {monthly_corr:.2f})",
    fontsize=13, fontweight="bold", color=ZRH_BLUE, pad=16,
)

ax.yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8, zorder=1)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

for bar, value in zip(bars, monthly_stats["avg_delay"]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + monthly_stats["avg_delay"].max() * 0.025,
        f"{value:.1f}",
        ha="center",
        va="bottom",
        fontsize=9,
        color=ZRH_BLUE,
        fontweight="bold",
    )

ax2 = ax.twinx()
ax2.plot(
    x,
    monthly_stats["avg_flights"],
    color=ZRH_RED,
    marker="o",
    linewidth=3,
    markersize=7,
    zorder=5,
)
ax2.set_ylim(0, monthly_stats["avg_flights"].max() * 1.18)
ax2.set_ylabel("Ø Anzahl Abflüge pro Tag", color=ZRH_RED, fontweight="bold")
ax2.tick_params(axis="y", colors=ZRH_RED)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(True)

for x_pos, value in zip(x, monthly_stats["avg_flights"]):
    ax2.text(
        x_pos,
        value + monthly_stats["avg_flights"].max() * 0.025,
        f"{value:.0f}",
        ha="center",
        va="bottom",
        fontsize=9,
        color=ZRH_RED,
        fontweight="bold",
    )

legend_handles = [
    Patch(color=ZRH_BLUE, label="Ø Abflugverspätung übrige Monate"),
    Patch(color=ZRH_SKY, label="Ø Abflugverspätung Sommermonate"),
    Line2D([0], [0], color=ZRH_RED, marker="o", linewidth=3, markersize=7, label="Ø Anzahl Abflüge"),
]
ax.legend(handles=legend_handles, loc="upper left")

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "verzoegerung_nach_monat.png", dpi=150, bbox_inches="tight")
print("Gespeichert: verzoegerung_nach_monat.png")
print("\nMonats-Statistik:")
print(monthly_stats[["avg_delay", "avg_flights", "days"]].round(2).to_string())
plt.close(fig)
