import pathlib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# ── ZRH Style ────────────────────────────────────────────────────────────────
ZRH_BLUE = "#003874"
ZRH_RED  = "#DC0018"
ZRH_SKY  = "#009EE0"
ZRH_GREY = "#939598"
ZRH_BG   = "#F2F2F2"

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
df = pd.read_csv(ROOT / "merge.csv", parse_dates=["Date"])

# ── Feature Engineering: relative Pistennutzung (Share) ──────────────────────
for piste in ["piste_16", "piste_28", "piste_32", "piste_34"]:
    df[f"{piste}_share"] = df[piste] / df["anzahl_abfluege_total"]

# ── Statistische Analyse: Korrelation Share → Verspätung ─────────────────────
share_cols = ["piste_16_share", "piste_28_share", "piste_32_share", "piste_34_share"]
target     = "Abflugverspätung ZRH"

df_clean = df[share_cols + [target]].dropna()

print("Korrelation (Pearson r) – Pistenanteil vs. Ø Abflugverspätung:")
print("-" * 55)
for col in share_cols:
    r = df_clean[col].corr(df_clean[target])
    print(f"  {col:<22}  r = {r:+.4f}")

# ── Visualisierung: Regplot für alle 4 Pisten in einem Bild ──────────────────
PISTEN_LABELS = {
    "piste_16_share": "Piste 16",
    "piste_28_share": "Piste 28",
    "piste_32_share": "Piste 32",
    "piste_34_share": "Piste 34",
}

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor("white")

for ax, (col, label) in zip(axes.flat, PISTEN_LABELS.items()):
    ax.set_facecolor("white")
    sns.regplot(
        data=df_clean,
        x=col,
        y=target,
        ax=ax,
        scatter_kws={"color": ZRH_BLUE, "alpha": 0.5, "s": 30, "linewidths": 0},
        line_kws={"color": ZRH_RED, "linewidth": 2},
    )
    r = df_clean[col].corr(df_clean[target])
    ax.set_title(f"{label}  (r = {r:+.3f})", fontweight="bold", color=ZRH_BLUE, fontsize=12)
    ax.set_xlabel(f"Anteil {label} an Gesamtabflügen [0–1]", color="#58595B")
    ax.set_ylabel("Ø Abflugverspätung (min)", color="#58595B")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)
    ax.yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8, zorder=1)
    ax.set_axisbelow(True)
    sns.despine(ax=ax)

fig.suptitle(
    "Relativ betrachtet entlastet Piste 28, während Piste 32 und 34 mit mehr Verspätung einhergehen",
    fontsize=15, fontweight="bold", color=ZRH_BLUE, y=1.02,
)
plt.tight_layout()

out_dir = ROOT / "Grafiken_Impact_ZRH"
out_dir.mkdir(exist_ok=True)
fig.savefig(out_dir / "Pisten_Einfluss_Analyse.png", dpi=150, bbox_inches="tight")
print("\nGespeichert: Pisten_Einfluss_Analyse.png")
plt.close(fig)
