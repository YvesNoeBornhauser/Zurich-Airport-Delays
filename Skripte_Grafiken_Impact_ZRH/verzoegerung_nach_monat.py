import pathlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
df = pd.read_csv(ROOT / "merge.csv", index_col=0)

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez",
}
SOMMER = {6, 7, 8}

monthly = (
    df.groupby("month")["Abflugverspätung ZRH"]
    .mean()
    .reindex(range(1, 13))
)
top_month = monthly.idxmax()
top_delay = monthly.loc[top_month]

colors = [ZRH_SKY if m in SOMMER else ZRH_BLUE for m in monthly.index]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("white")

bars = ax.bar(
    [MONTH_NAMES[m] for m in monthly.index],
    monthly.values,
    color=colors,
    width=0.65,
    zorder=2,
)

ax.set_ylim(0, monthly.max() * 1.18)
ax.set_ylabel("Ø Abflugverspätung (min)", color="#58595B")
ax.set_title(
    f"{MONTH_NAMES[top_month]} ist der stärkste Verspätungsmonat; Sommer und September liegen klar höher",
    fontsize=13, fontweight="bold", color=ZRH_BLUE, pad=16,
)

ax.yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8, zorder=1)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

legend_handles = [
    mpatches.Patch(color=ZRH_BLUE, label="Übrige Monate"),
    mpatches.Patch(color=ZRH_SKY,  label="Sommermonate (Jun–Aug)"),
]
ax.legend(handles=legend_handles, loc="upper left")

plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "verzoegerung_nach_monat.png", dpi=150, bbox_inches="tight")
print("Gespeichert: verzoegerung_nach_monat.png")
plt.close(fig)
