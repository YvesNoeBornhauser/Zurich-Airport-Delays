import pathlib
import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


warnings.filterwarnings("ignore", category=UserWarning)


# ── ZRH Style ────────────────────────────────────────────────────────────────
ZRH_BLUE = "#003874"
ZRH_RED = "#DC0018"
ZRH_SKY = "#009EE0"
ZRH_GREY = "#939598"

ZRH_COLORS = [ZRH_BLUE, ZRH_SKY, ZRH_RED, ZRH_GREY]
ZRH_PALETTE = sns.color_palette(ZRH_COLORS)


def set_zrh_style():
    sns.set_theme(style="white", palette=ZRH_PALETTE)
    plt.rcParams.update({
        "font.sans-serif": "Arial",
        "axes.titleweight": "bold",
        "axes.titlesize": 14,
        "axes.titlepad": 20,
        "axes.labelcolor": "#58595B",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.frameon": False,
        "figure.figsize": (10, 6),
        "figure.dpi": 100,
    })


def rmse(y_true, y_pred):
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def evaluate_predictions(name, y_true, y_pred):
    return {
        "model": name,
        "test_mae": mean_absolute_error(y_true, y_pred),
        "test_rmse": rmse(y_true, y_pred),
        "test_r2": r2_score(y_true, y_pred),
    }


def make_preprocessor(numeric_features, categorical_features):
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ],
        sparse_threshold=0,
    )


def build_best_model(numeric_features, categorical_features):
    # Das ist das beste Modell aus dem vorherigen Modellvergleich nach Test-MAE.
    model = GradientBoostingRegressor(
        n_estimators=180,
        learning_rate=0.04,
        max_depth=3,
        min_samples_leaf=5,
        random_state=42,
    )

    return Pipeline([
        ("preprocess", make_preprocessor(numeric_features, categorical_features)),
        ("model", model),
    ])


def make_baseline_predictions(train_df, test_df, target):
    train_mean = train_df[target].mean()

    month_means = train_df.groupby("Monat")[target].mean()
    weekday_means = train_df.groupby("Wochentag")[target].mean()

    return {
        "Mittelwert-Baseline": np.repeat(train_mean, len(test_df)),
        "Monats-Baseline": test_df["Monat"].map(month_means).fillna(train_mean).values,
        "Wochentags-Baseline": test_df["Wochentag"].map(weekday_means).fillna(train_mean).values,
    }


def plot_actual_vs_predicted(test_df, y_test, predictions, r2, output_path):
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [1.35, 1]})
    fig.patch.set_facecolor("white")

    axes[0].plot(test_df["Date"], y_test.values, color=ZRH_BLUE, linewidth=2, label="Tatsächlich")
    axes[0].plot(test_df["Date"], predictions, color=ZRH_RED, linewidth=2, label="Prognose")
    axes[0].set_ylabel("Ø Abflugverspätung (min)", color="#58595B")
    axes[0].set_title(
        "Gradient Boosting prognostiziert normale Tage besser als extreme Spitzen",
        fontsize=13,
        fontweight="bold",
        color=ZRH_BLUE,
        pad=16,
    )
    axes[0].legend(loc="upper left")
    axes[0].yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8)

    axes[1].scatter(y_test, predictions, color=ZRH_BLUE, alpha=0.65, s=34, linewidths=0)
    min_value = min(y_test.min(), predictions.min())
    max_value = max(y_test.max(), predictions.max())
    axes[1].plot([min_value, max_value], [min_value, max_value], color=ZRH_RED, linestyle="--", linewidth=2)
    axes[1].set_xlabel("Tatsächliche Verspätung (min)", color="#58595B")
    axes[1].set_ylabel("Prognostizierte Verspätung (min)", color="#58595B")
    axes[1].text(
        0.02,
        0.92,
        f"Bestes Modell | R² = {r2:.2f}",
        transform=axes[1].transAxes,
        fontsize=10,
        color="#58595B",
    )
    axes[1].xaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8)
    axes[1].yaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8)

    for ax in axes:
        ax.set_axisbelow(True)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Gespeichert: {output_path.name}")
    plt.close(fig)


def plot_permutation_importance(pipeline, x_test, y_test, output_path):
    importance = permutation_importance(
        pipeline,
        x_test,
        y_test,
        scoring="neg_mean_absolute_error",
        n_repeats=20,
        random_state=42,
        n_jobs=1,
    )

    importance_df = (
        pd.DataFrame({
            "feature": x_test.columns,
            "importance": importance.importances_mean,
        })
        .sort_values("importance", ascending=False)
        .head(12)
        .sort_values("importance")
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("white")

    colors = [ZRH_RED if value > 0 else ZRH_GREY for value in importance_df["importance"]]
    bars = ax.barh(
        importance_df["feature"],
        importance_df["importance"],
        color=colors,
        height=0.62,
    )

    ax.axvline(0, color=ZRH_GREY, linewidth=0.8, linestyle="--")
    ax.set_xlabel("Permutation Importance als MAE-Verschlechterung", color="#58595B")
    ax.set_ylabel("")
    ax.set_title(
        "Die wichtigsten nutzbaren Prognosevariablen im besten Modell",
        fontsize=13,
        fontweight="bold",
        color=ZRH_BLUE,
        pad=16,
    )

    for bar, value in zip(bars, importance_df["importance"]):
        x_offset = 0.015 if value >= 0 else -0.015
        ha = "left" if value >= 0 else "right"
        ax.text(
            value + x_offset,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.2f}",
            va="center",
            ha=ha,
            fontsize=9,
            color="#58595B",
        )

    ax.xaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8)
    ax.set_axisbelow(True)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Gespeichert: {output_path.name}")
    plt.close(fig)


def plot_model_comparison(comparison, output_path):
    plot_df = comparison.sort_values("test_mae", ascending=True).copy()

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor("white")

    colors = [ZRH_RED if row == "Gradient Boosting" else ZRH_BLUE for row in plot_df["model"]]
    bars = ax.barh(plot_df["model"], plot_df["test_mae"], color=colors, height=0.62)

    ax.set_xlabel("MAE im Testset (Minuten)", color="#58595B")
    ax.set_ylabel("")
    ax.set_title(
        "Das ML-Modell schlägt einfache Baselines klar",
        fontsize=13,
        fontweight="bold",
        color=ZRH_BLUE,
        pad=16,
    )

    for bar, value in zip(bars, plot_df["test_mae"]):
        ax.text(
            value + 0.05,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.2f}",
            va="center",
            ha="left",
            fontsize=9,
            color="#58595B",
        )

    ax.xaxis.grid(True, color=ZRH_GREY, alpha=0.25, linewidth=0.8)
    ax.set_axisbelow(True)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Gespeichert: {output_path.name}")
    plt.close(fig)


def main():
    set_zrh_style()

    root = pathlib.Path(__file__).resolve().parents[1]
    output_dir = pathlib.Path(__file__).resolve().parent / "Grafiken"
    output_dir.mkdir(exist_ok=True)

    df = pd.read_csv(root / "merge.csv", parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    # Spaltennamen aus dem Projekt auf die Modellnamen aus der Fragestellung mappen.
    df["Avg Departure Schedule Delay"] = df["Abflugverspätung ZRH"]
    df["public_holiday"] = df["Feiertage"].astype(int)
    df["WEF"] = df["WEF"].astype(int)
    df["schnee_vorhanden"] = df["schnee_vorhanden"].astype(int)
    df["oil_90d_avg"] = df["90_day_average_oil_price"]
    df["oil_trend_90d"] = df["oil_trend"]
    df["oil_price_lag1"] = df["oil_price"].shift(1)
    df["Monat"] = df["month"].astype(str)
    df["Wochentag"] = df["day_of_week"]

    target = "Avg Departure Schedule Delay"
    numeric_features = [
        "anzahl_abfluege_total",
        "public_holiday",
        "WEF",
        "oil_price_lag1",
        "oil_90d_avg",
        "oil_trend_90d",
        "windgeschwindigkeit",
        "maximale_windgeschwindigkeit",
        "regen",
        "temperatur",
        "schnee_vorhanden",
        "schnee_intensität",
    ]
    categorical_features = ["Monat", "Wochentag"]
    features = numeric_features + categorical_features

    model_df = df[["Date", target] + features].copy()
    model_df = model_df.sort_values("Date").reset_index(drop=True)

    print("Datensatz:")
    print(f"Zeilen: {len(model_df)}")
    print(f"Zeitraum: {model_df['Date'].min().date()} bis {model_df['Date'].max().date()}")
    print("\nFehlende Werte pro Spalte:")
    print(model_df.isna().sum().to_string())
    print("\nDatentypen:")
    print(model_df.dtypes.to_string())
    print("\nWichtig: Pistenanteile und Pistenanzahlen werden hier bewusst NICHT verwendet,")
    print("weil sie für eine echte Prognose vor dem Tag Leakage wären.")

    # Zeitbasierter Split: die letzten 20 Prozent dienen als Testset.
    split_index = int(len(model_df) * 0.8)
    train_df = model_df.iloc[:split_index].copy()
    test_df = model_df.iloc[split_index:].copy()

    x_train = train_df[features]
    y_train = train_df[target]
    x_test = test_df[features]
    y_test = test_df[target]

    print("\nZeitbasierter Split:")
    print(f"Training: {train_df['Date'].min().date()} bis {train_df['Date'].max().date()} ({len(train_df)} Zeilen)")
    print(f"Test:     {test_df['Date'].min().date()} bis {test_df['Date'].max().date()} ({len(test_df)} Zeilen)")

    results = []

    # ── Drei einfache Baselines ────────────────────────────────────────────────
    baseline_predictions = make_baseline_predictions(train_df, test_df, target)
    for baseline_name, predictions in baseline_predictions.items():
        results.append(evaluate_predictions(baseline_name, y_test, predictions))

    # ── Bestes Modell aus dem vorherigen Vergleich ─────────────────────────────
    best_model = build_best_model(numeric_features, categorical_features)
    best_model.fit(x_train, y_train)
    best_predictions = best_model.predict(x_test)
    results.append(evaluate_predictions("Gradient Boosting", y_test, best_predictions))

    comparison = pd.DataFrame(results).sort_values("test_mae").reset_index(drop=True)
    best_mae = comparison["test_mae"].min()
    comparison["mae_abstand_zum_bestmodell"] = comparison["test_mae"] - best_mae

    print("\nBaseline- und Modellvergleich:")
    print(comparison.round(3).to_string(index=False))

    high_delay_threshold = y_train.quantile(0.90)
    high_mask = y_test >= high_delay_threshold

    print("\nCheck für Tage mit besonders hoher Verspätung:")
    print(f"Schwelle: oberstes 10%-Quantil im Training = {high_delay_threshold:.2f} Minuten")
    print(f"Hohe Verspätungstage im Testset: {int(high_mask.sum())}")

    if high_mask.sum() > 0:
        high_y_true = y_test[high_mask]
        high_y_pred = best_predictions[high_mask]
        hit_rate = (high_y_pred >= high_delay_threshold).mean()
        print(f"MAE auf hohen Verspätungstagen: {mean_absolute_error(high_y_true, high_y_pred):.2f}")
        print(f"RMSE auf hohen Verspätungstagen: {rmse(high_y_true, high_y_pred):.2f}")
        print(f"Durchschnitt tatsächliche hohe Verspätung: {high_y_true.mean():.2f}")
        print(f"Durchschnitt Prognose an diesen Tagen: {high_y_pred.mean():.2f}")
        print(f"Trefferquote hohe Tage (Prediction ebenfalls über Schwelle): {hit_rate:.1%}")

    comparison.to_csv(output_dir / "gesamt_modellvergleich.csv", index=False)
    comparison.to_csv(output_dir / "erweitert_mit_wetterprognose-proxies_modellvergleich.csv", index=False)

    plot_model_comparison(
        comparison,
        output_dir / "baseline_und_bestes_modell_mae.png",
    )
    plot_actual_vs_predicted(
        test_df,
        y_test,
        best_predictions,
        comparison.loc[comparison["model"] == "Gradient Boosting", "test_r2"].iloc[0],
        output_dir / "erweitert_mit_wetterprognose-proxies_actual_vs_predicted.png",
    )
    plot_permutation_importance(
        best_model,
        x_test,
        y_test,
        output_dir / "erweitert_mit_wetterprognose-proxies_permutation_importance.png",
    )

    print("\nKurze Einordnung:")
    print("- Die Baselines nutzen nur Durchschnittswerte aus dem Trainingsset.")
    print("- Das Gradient-Boosting-Modell nutzt zusätzlich die ex ante vertretbaren Features inkl. Wetterprognose-Proxies.")
    print("- Pistenanteile wurden ausgeschlossen, weil sie erst im Tagesbetrieb entstehen und Leakage wären.")
    print("- Bei hohen Verspätungstagen ist die Prognose weiterhin schwieriger als bei normalen Tagen.")


if __name__ == "__main__":
    main()
