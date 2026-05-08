import pathlib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

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
df = pd.read_csv(ROOT / "merge.csv", parse_dates=["Date"])

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez",
}

target = "Abflugverspätung ZRH"
feature = "oil_trend"

df_corr = df[["Date", target, feature]].dropna()
df_corr["year_month"] = df_corr["Date"].dt.to_period("M")

# Pearson-Korrelation pro einzelnem Monat im Zeitverlauf.
period_range = pd.period_range(
    df_corr["year_month"].min(),
    df_corr["year_month"].max(),
    freq="M",
)
monthly_corr = (
    df_corr
    .groupby("year_month")[[target, feature]]
    .apply(lambda month_df: month_df[target].corr(month_df[feature]))
    .reindex(period_range)
)
mean_abs_corr = monthly_corr.abs().mean()

colors = [
    ZRH_GREY if pd.isna(value) else ZRH_RED if value > 0 else ZRH_BLUE
    for value in monthly_corr.values
]
labels = [f"{MONTH_NAMES[period.month]} {str(period.year)[-2:]}" for period in monthly_corr.index]
x_positions = range(len(monthly_corr))

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(18, 7))
fig.patch.set_facecolor("white")

bars = ax.bar(
    x_positions,
    monthly_corr.values,
    color=colors,
    width=0.72,
    zorder=2,
)

ax.axhline(0, color=ZRH_GREY, linewidth=0.8, linestyle="--", zorder=1)
ax.set_ylim(-1, 1)
ax.set_ylabel("Pearson r", color="#58595B")
ax.set_xlabel("Monat und Jahr", color="#58595B")
ax.set_title(
    "Ölpreis-Trends zeigen kein stabiles Muster zur Verspätung",
    fontsize=13, fontweight="bold", color=ZRH_BLUE, pad=16,
)
tick_step = 3
ax.set_xticks(list(x_positions)[::tick_step])
ax.set_xticklabels(labels[::tick_step], rotation=0)

ax.yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8, zorder=1)
ax.set_axisbelow(True)

for bar, value in zip(bars, monthly_corr.values):
    if pd.isna(value):
        continue
    y_offset = 0.04 if value >= 0 else -0.04
    va = "bottom" if value >= 0 else "top"
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + y_offset,
        f"{value:.2f}",
        ha="center",
        va=va,
        fontsize=7,
        color="#58595B",
    )

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "oelpreis_trend_korrelation_monat.png", dpi=150, bbox_inches="tight")
print("Gespeichert: oelpreis_trend_korrelation_monat.png")
plt.close(fig)
