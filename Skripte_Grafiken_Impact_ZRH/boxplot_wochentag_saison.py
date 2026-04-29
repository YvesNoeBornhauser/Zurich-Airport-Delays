import pathlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
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
        "figure.figsize":    (13, 6),
        "figure.dpi":        100,
    })


set_zrh_style()

# ── Daten & Kategorien ────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "merge.csv", index_col=0, parse_dates=["Date"])

TARGET = "Avg Departure Schedule Delay"
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
SEASON_BY_MONTH = {
    12: "Winter", 1: "Winter", 2: "Winter",
    6: "Sommer", 7: "Sommer", 8: "Sommer",
    3: "Übergangszeit", 4: "Übergangszeit", 5: "Übergangszeit",
    9: "Übergangszeit", 10: "Übergangszeit", 11: "Übergangszeit",
}
SEASON_ORDER = ["Winter", "Übergangszeit", "Sommer"]
SEASON_COLORS = {
    "Winter": ZRH_BLUE,
    "Übergangszeit": ZRH_SKY,
    "Sommer": ZRH_RED,
}

df["weekday"] = pd.Categorical(
    df["Date"].dt.day_name(),
    categories=DAY_ORDER,
    ordered=True,
)
df["weekday_de"] = df["weekday"].map(DAY_LABELS)
df["season"] = pd.Categorical(
    df["month"].map(SEASON_BY_MONTH),
    categories=SEASON_ORDER,
    ordered=True,
)
df_plot = df[["weekday_de", "season", TARGET]].dropna()

weekday_order_de = [DAY_LABELS[day] for day in DAY_ORDER]
weekday_stats = (
    df_plot
    .groupby("weekday_de", observed=True)[TARGET]
    .agg(mean="mean", median="median")
    .reindex(weekday_order_de)
)
top_weekday = weekday_stats["median"].idxmax()
top_median = weekday_stats.loc[top_weekday, "median"]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 6))
fig.patch.set_facecolor("white")
x_positions = np.arange(len(weekday_order_de))

sns.boxplot(
    data=df_plot,
    x="weekday_de",
    y=TARGET,
    hue="season",
    order=weekday_order_de,
    hue_order=SEASON_ORDER,
    palette=SEASON_COLORS,
    width=0.72,
    linewidth=1,
    showfliers=False,
    ax=ax,
)

mean_values = weekday_stats["mean"].values
ax.plot(
    x_positions,
    mean_values,
    color="#222222",
    marker="D",
    markersize=5,
    linewidth=1.8,
    label="Ø gesamt je Wochentag",
    zorder=5,
)

for x_pos, mean_value in zip(x_positions, mean_values):
    ax.text(
        x_pos,
        mean_value + 0.8,
        f"{mean_value:.1f}",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#222222",
        fontweight="bold",
        zorder=6,
    )

ax.set_ylim(0, max(df_plot[TARGET].quantile(0.98) * 1.08, mean_values.max() + 5))
ax.set_xlabel("Wochentag", color="#58595B", labelpad=10)
ax.set_ylabel("Abflugverspätung (min)", color="#58595B", labelpad=10)
ax.set_title(
    f"Wochentag-Fingerabdruck: {top_weekday} hat den höchsten Median ({top_median:.1f} min)",
    fontsize=13,
    fontweight="bold",
    color=ZRH_BLUE,
    pad=16,
)
ax.tick_params(axis="x", rotation=0)
ax.yaxis.grid(True, color="#E5E5E5", linewidth=0.6, zorder=1)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

handles, labels = ax.get_legend_handles_labels()
handles.append(Line2D([0], [0], color="#222222", marker="D", linewidth=1.8, markersize=5))
labels.append("Ø gesamt je Wochentag")
ax.legend(
    handles=handles,
    labels=labels,
    title="Saison",
    loc="upper center",
    bbox_to_anchor=(0.5, -0.16),
    ncol=len(SEASON_ORDER) + 1,
)

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "boxplot_wochentag_saison.png", dpi=150, bbox_inches="tight")
print("Gespeichert: boxplot_wochentag_saison.png")
print("\nWochentags-Statistik:")
print(weekday_stats.round(2).to_string())
plt.close(fig)
