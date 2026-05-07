import pathlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
        "figure.figsize":    (12, 6),
        "figure.dpi":        100,
    })

set_zrh_style()

# ── Daten & Bins ──────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "merge.csv", index_col=0)

# 5-Grad-Bins von -10 bis 30 (deckt -8.4 bis 27.0 ab)
BIN_EDGES  = list(range(-10, 31, 5))
BIN_LABELS = [f"{lo}–{lo+5} °C" for lo in BIN_EDGES[:-1]]

df["temp_bin"] = pd.cut(
    df["temperatur"],
    bins=BIN_EDGES,
    labels=BIN_LABELS,
    right=False,
)

stats = (
    df.groupby("temp_bin", observed=True)["Abflugverspätung ZRH"]
    .agg(mean="mean", count="count")
    .dropna()
)
top_bin = stats["mean"].idxmax()
top_delay = stats.loc[top_bin, "mean"]

# Farbe: Kältebins ZRH Blue → Hitze ZRH Red (Gradient über SKY)
n = len(stats)
palette = []
for i in range(n):
    t = i / max(n - 1, 1)
    if t < 0.5:
        r = int(0x00 + t * 2 * (0x00 - 0x00))
        g = int(0x38 + t * 2 * (0x9E - 0x38))
        b = int(0x74 + t * 2 * (0xE0 - 0x74))
    else:
        t2 = (t - 0.5) * 2
        r = int(0x00 + t2 * (0xDC - 0x00))
        g = int(0x9E + t2 * (0x00 - 0x9E))
        b = int(0xE0 + t2 * (0x18 - 0xE0))
    palette.append(f"#{r:02X}{g:02X}{b:02X}")

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("white")

x = np.arange(len(stats))
bars = ax.bar(x, stats["mean"].values, color=palette, width=0.65, zorder=2)

ax.set_xticks(x)
ax.set_xticklabels(stats.index.tolist(), rotation=0)
ax.set_ylim(0, stats["mean"].max() * 1.22)
ax.set_ylabel("Ø Abflugverspätung (min)", color="#58595B")
ax.set_xlabel("Temperaturklasse", color="#58595B")

ax.set_title(
    f"Extreme Kälte führt zur höchsten Verspätung ({top_bin}: {top_delay:.1f} min); Hitze ist saisonal verzerrt",
    fontsize=13, fontweight="bold", color=ZRH_BLUE, pad=16,
)

# Stichprobenanzahl als Annotation über jedem Balken
for bar, cnt in zip(bars, stats["count"].values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.3,
        f"n={int(cnt)}",
        ha="center", va="bottom",
        fontsize=8, color=ZRH_GREY,
    )

ax.yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8, zorder=1)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

legend_handles = [
    mpatches.Patch(color=ZRH_BLUE, label="Kalt (< 0 °C)"),
    mpatches.Patch(color=ZRH_SKY,  label="Mild (0–20 °C)"),
    mpatches.Patch(color=ZRH_RED,  label="Warm (> 20 °C)"),
]
ax.legend(handles=legend_handles, loc="upper left")

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "verzoegerung_nach_temperatur.png", dpi=150, bbox_inches="tight")
print("Gespeichert: verzoegerung_nach_temperatur.png")
plt.close(fig)
