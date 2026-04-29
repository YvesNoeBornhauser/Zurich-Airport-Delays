import pathlib
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
df = pd.read_csv(ROOT / "merge.csv", index_col=0, parse_dates=["Date"])

TARGET = "Avg Departure Schedule Delay"

if "schnee_vorhanden" not in df.columns:
    df["schnee_vorhanden"] = np.where((df["temperatur"] < 2) & (df["regen"] > 0), 1, 0)
if "schnee_intensität" not in df.columns:
    df["schnee_intensität"] = np.where((df["temperatur"] < 2) & (df["regen"] > 0), df["regen"], 0)

df_snow = df[df["schnee_vorhanden"] == 1][["schnee_intensität", TARGET]].dropna()
r = df_snow["schnee_intensität"].corr(df_snow[TARGET])

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("white")

sns.regplot(
    data=df_snow,
    x="schnee_intensität",
    y=TARGET,
    scatter_kws={"color": ZRH_BLUE, "alpha": 0.65, "s": 45, "linewidths": 0},
    line_kws={"color": ZRH_RED, "linewidth": 2.5},
    ci=95,
    ax=ax,
)

ax.set_xlim(left=0)
ax.set_ylim(bottom=0)
ax.set_xlabel("Schnee-Intensität (mm Niederschlag bei < 2 °C)", color="#58595B", labelpad=10)
ax.set_ylabel("Ø Abflugverspätung (min)", color="#58595B", labelpad=10)
ax.set_title(
    f"An Schneetagen steigt die Verspätung mit der Schnee-Intensität (r = {r:.2f})",
    fontsize=13,
    fontweight="bold",
    color=ZRH_BLUE,
    pad=16,
)

ax.text(
    0.98,
    0.05,
    f"n = {len(df_snow)} Schneetage",
    transform=ax.transAxes,
    ha="right",
    va="bottom",
    fontsize=10,
    color="#58595B",
)

ax.yaxis.grid(True, color="#E5E5E5", linewidth=0.6, zorder=1)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "schnee_intensitaet_delay_scatter.png", dpi=150, bbox_inches="tight")
print("Gespeichert: schnee_intensitaet_delay_scatter.png")
print(f"Schneetage: {len(df_snow)}")
print(f"Pearson r: {r:.3f}")
plt.close(fig)
