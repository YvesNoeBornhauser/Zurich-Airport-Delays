import pathlib
import matplotlib.pyplot as plt
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
        "figure.figsize":    (14, 6),
        "figure.dpi":        100,
    })


set_zrh_style()

# ── Daten & Relative Delay Index ──────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "merge.csv", index_col=0, parse_dates=["Date"])

TARGET = "Avg Departure Schedule Delay"
MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez",
}

df["WEF"] = df["WEF"].astype(str).str.lower().eq("true")
df["year_month"] = df["Date"].dt.to_period("M")
df["monthly_avg_delay"] = df.groupby("year_month")[TARGET].transform("mean")
df["relative_delay_index"] = df[TARGET] - df["monthly_avg_delay"]
df["gruppe"] = np.where(df["WEF"], "WEF-Tage", "Andere Tage")

df_plot = df[["Date", "year_month", "gruppe", "WEF", "relative_delay_index"]].dropna()

group_order = ["Andere Tage", "WEF-Tage"]
group_colors = {"Andere Tage": ZRH_BLUE, "WEF-Tage": ZRH_RED}
group_stats = (
    df_plot
    .groupby("gruppe")["relative_delay_index"]
    .agg(mean="mean", median="median", count="count")
    .reindex(group_order)
)

wef_monthly = (
    df_plot[df_plot["WEF"]]
    .groupby("year_month")["relative_delay_index"]
    .agg(mean="mean", count="count")
    .sort_index()
)
wef_labels = [
    f"{MONTH_NAMES[period.month]} {str(period.year)[-2:]}"
    for period in wef_monthly.index
]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(
    1,
    2,
    figsize=(14, 6),
    gridspec_kw={"width_ratios": [1, 1.25]},
)
fig.patch.set_facecolor("white")

sns.boxplot(
    data=df_plot,
    x="gruppe",
    y="relative_delay_index",
    order=group_order,
    hue="gruppe",
    palette=group_colors,
    showfliers=False,
    width=0.48,
    linewidth=1.1,
    legend=False,
    ax=ax1,
)
sns.stripplot(
    data=df_plot[df_plot["WEF"]],
    x="gruppe",
    y="relative_delay_index",
    order=group_order,
    color=ZRH_RED,
    size=5,
    jitter=0.12,
    alpha=0.75,
    ax=ax1,
)

for x_pos, group in enumerate(group_order):
    mean_value = group_stats.loc[group, "mean"]
    count = int(group_stats.loc[group, "count"])
    ax1.scatter(
        x_pos,
        mean_value,
        marker="D",
        s=58,
        color="white",
        edgecolor="#58595B",
        linewidth=1.1,
        zorder=4,
    )
    ax1.text(
        x_pos,
        mean_value + 1.0,
        f"Ø {mean_value:+.1f} min\nn={count}",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#58595B",
    )

ax1.axhline(0, color=ZRH_GREY, linewidth=0.8, linestyle="--", zorder=1)
ax1.set_xlabel("")
ax1.set_ylabel("Abweichung vom Monatsmittel (min)", color="#58595B")
ax1.set_title("WEF-Tage vs. übrige Tage", fontsize=12, fontweight="bold", color=ZRH_BLUE)
ax1.yaxis.grid(True, color="#E5E5E5", linewidth=0.6, zorder=1)
ax1.set_axisbelow(True)

x = np.arange(len(wef_monthly))
bar_colors = [ZRH_RED if value >= 0 else ZRH_BLUE for value in wef_monthly["mean"].values]
bars = ax2.bar(
    x,
    wef_monthly["mean"].values,
    color=bar_colors,
    width=0.62,
    zorder=2,
)

lower = min(0, wef_monthly["mean"].min() * 1.18)
upper = max(0, wef_monthly["mean"].max() * 1.25)
ax2.set_ylim(lower, upper)
ax2.axhline(0, color=ZRH_GREY, linewidth=0.8, linestyle="--", zorder=1)
ax2.set_xticks(x)
ax2.set_xticklabels(wef_labels, rotation=0)
ax2.set_ylabel("Ø Abweichung WEF-Tage (min)", color="#58595B")
ax2.set_xlabel("WEF-Monat", color="#58595B")
ax2.set_title("WEF 2022 wird im Mai korrekt normalisiert", fontsize=12, fontweight="bold", color=ZRH_BLUE)
ax2.yaxis.grid(True, color="#E5E5E5", linewidth=0.6, zorder=1)
ax2.set_axisbelow(True)

for bar, value, count in zip(bars, wef_monthly["mean"].values, wef_monthly["count"].values):
    y_offset = 0.45 if value >= 0 else -0.45
    va = "bottom" if value >= 0 else "top"
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        value + y_offset,
        f"{value:+.1f}\nn={int(count)}",
        ha="center",
        va=va,
        fontsize=9,
        color="#58595B",
    )

for ax in [ax1, ax2]:
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

wef_mean = group_stats.loc["WEF-Tage", "mean"]
fig.suptitle(
    f"Relative Delay Index: WEF-Tage liegen im Schnitt {wef_mean:+.1f} min über ihrem Monatsmittel",
    fontsize=14,
    fontweight="bold",
    color=ZRH_BLUE,
    y=1.02,
)

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "wef_relative_delay_index.png", dpi=150, bbox_inches="tight")
print("Gespeichert: wef_relative_delay_index.png")
print("\nRelative Delay Index nach Gruppe:")
print(group_stats.round(2).to_string())
print("\nRelative Delay Index pro WEF-Monat:")
print(wef_monthly.round(2).to_string())
plt.close(fig)
