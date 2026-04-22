import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Deutsche Schriftarten aktivieren
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Datensatz laden
df = pd.read_csv('merge.csv')

# Datumsformat konvertieren
df['Date'] = pd.to_datetime(df['Date'])

# Numerische Spalten für Korrelation extrahieren
numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

print("=" * 80)
print("KORRELATIONSANALYSE: FLUGVERSPÄTUNGEN AM FLUGHAFEN ZÜRICH")
print("=" * 80)
print(f"\nAnalysedaten: {len(df)} Tage ({df['Date'].min().date()} bis {df['Date'].max().date()})")
print(f"Numerische Variablen: {len(numeric_columns)}")

# Fehlende Werte analysieren
print("\n" + "=" * 80)
print("FEHLENDE WERTE (MISSING DATA)")
print("=" * 80)
missing_data = df[numeric_columns].isnull().sum()
missing_percent = (missing_data / len(df)) * 100
missing_df = pd.DataFrame({
    'Spalte': missing_data.index,
    'Fehlende Werte': missing_data.values,
    'Prozentanteil': missing_percent.values
}).sort_values('Fehlende Werte', ascending=False)

print(missing_df.to_string(index=False))

# Datenset bereinigen (nur vollständige Fälle für Korrelationsanalyse)
df_clean = df[numeric_columns].dropna()
print(f"\nDaten nach Entfernung fehlender Werte: {len(df_clean)} Tage ({(len(df_clean)/len(df)*100):.1f}%)")

# Deskriptive Statistik
print("\n" + "=" * 80)
print("DESKRIPTIVE STATISTIK")
print("=" * 80)
descriptive_stats = df_clean.describe().T
descriptive_stats.columns = ['Anzahl', 'Mittelwert', 'Std.Abw.', 'Min', '25%', '50%', '75%', 'Max']
print(descriptive_stats.round(2).to_string())

# Abhängige Variable (Verspätung)
target_var = 'Avg Departure Schedule Delay'
print(f"\n\nFOKUS: {target_var}")
print(f"  Mittelwert: {df_clean[target_var].mean():.2f} Minuten")
print(f"  Median: {df_clean[target_var].median():.2f} Minuten")
print(f"  Std.Abw.: {df_clean[target_var].std():.2f} Minuten")
print(f"  Min: {df_clean[target_var].min():.2f} Minuten")
print(f"  Max: {df_clean[target_var].max():.2f} Minuten")

# Korrelationsmatrix berechnen
print("\n" + "=" * 80)
print("PEARSON-KORRELATIONEN MIT VERSPÄTUNGEN")
print("=" * 80)

correlations = df_clean.corr()[target_var].drop(target_var).sort_values(ascending=False)
correlation_stats = []

for feature, corr_value in correlations.items():
    # Pearson-Korrelationstest durchführen
    x = df_clean[feature]
    y = df_clean[target_var]
    
    # Korrelationskoeffizient und p-Wert berechnen
    r, p_value = stats.pearsonr(x, y)
    
    # Signifikanz bewerten
    if p_value < 0.001:
        significance = '***'
    elif p_value < 0.01:
        significance = '**'
    elif p_value < 0.05:
        significance = '*'
    else:
        significance = ''
    
    correlation_stats.append({
        'Feature': feature,
        'Korrelation': r,
        'p-Wert': p_value,
        'Signifikanz': significance
    })

corr_df = pd.DataFrame(correlation_stats).sort_values('Korrelation', key=abs, ascending=False)
print("\n(***) p < 0.001 | (**) p < 0.01 | (*) p < 0.05")
print()
print(corr_df.to_string(index=False))

# Interpretation der Korrelationen
print("\n" + "=" * 80)
print("INTERPRETATION DER KORRELATIONEN")
print("=" * 80)

strong_positive = corr_df[(corr_df['Korrelation'] > 0.3) & (corr_df['p-Wert'] < 0.05)]
strong_negative = corr_df[(corr_df['Korrelation'] < -0.3) & (corr_df['p-Wert'] < 0.05)]

if len(strong_positive) > 0:
    print("\nStarke POSITIVE Korrelationen (r > 0.3, signifikant):")
    for idx, row in strong_positive.iterrows():
        print(f"  • {row['Feature']}: r = {row['Korrelation']:.3f}")
        print(f"    → Höhere Werte sind mit höheren Verspätungen verbunden")
else:
    print("\nKeine starken positiven Korrelationen gefunden.")

if len(strong_negative) > 0:
    print("\nStarke NEGATIVE Korrelationen (r < -0.3, signifikant):")
    for idx, row in strong_negative.iterrows():
        print(f"  • {row['Feature']}: r = {row['Korrelation']:.3f}")
        print(f"    → Höhere Werte sind mit niedrigeren Verspätungen verbunden")
else:
    print("\nKeine starken negativen Korrelationen gefunden.")

# Schwache Korrelationen
weak_corr = corr_df[abs(corr_df['Korrelation']) <= 0.3]
if len(weak_corr) > 0:
    print(f"\nSchwache Korrelationen (|r| ≤ 0.3): {len(weak_corr)} Features")
    print("  Diese zeigen wenig bis gar keinen linearen Zusammenhang mit Verspätungen")

# Heatmap der Gesamtkorrelation
print("\n" + "=" * 80)
print("ERSTELLUNG VON VISUALISIERUNGEN")
print("=" * 80)

# 1. Heatmap aller Korrelationen
fig, ax = plt.subplots(figsize=(12, 8))
corr_matrix = df_clean.corr()
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, 
            square=True, ax=ax, cbar_kws={'label': 'Korrelationskoeffizient'})
plt.title('Korrelationsmatrix: Alle Variablen', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('01_korrelationsmatrix_alle.png', dpi=300, bbox_inches='tight')
print("✓ Datei erstellt: 01_korrelationsmatrix_alle.png")
plt.close()

# 2. Balkendiagramm der Korrelationen mit Verspätungen
fig, ax = plt.subplots(figsize=(10, 8))
colors = ['#d62728' if x > 0 else '#1f77b4' for x in corr_df['Korrelation']]
ax.barh(range(len(corr_df)), corr_df['Korrelation'], color=colors)
ax.set_yticks(range(len(corr_df)))
ax.set_yticklabels(corr_df['Feature'])
ax.set_xlabel('Pearson-Korrelationskoeffizient', fontweight='bold')
ax.set_title('Korrelation mit Flugverspätungen\n(Rot: positiv | Blau: negativ)', 
             fontsize=12, fontweight='bold')
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('02_korrelationen_verspätungen.png', dpi=300, bbox_inches='tight')
print("✓ Datei erstellt: 02_korrelationen_verspätungen.png")
plt.close()

# 3. Streudiagramme für Top 4 Korrelationen
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

top_features = abs(corr_df['Korrelation']).nlargest(4).index.tolist()

for idx, feature in enumerate(top_features):
    ax = axes[idx]
    corr_val = corr_df[corr_df['Feature'] == feature]['Korrelation'].values[0]
    p_val = corr_df[corr_df['Feature'] == feature]['p-Wert'].values[0]
    
    # Streudiagramm
    ax.scatter(df_clean[feature], df_clean[target_var], alpha=0.5, s=20)
    
    # Regressionslinie
    z = np.polyfit(df_clean[feature], df_clean[target_var], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df_clean[feature].min(), df_clean[feature].max(), 100)
    ax.plot(x_line, p(x_line), "r--", linewidth=2, label='Regressionslinie')
    
    ax.set_xlabel(feature, fontweight='bold')
    ax.set_ylabel(target_var, fontweight='bold')
    ax.set_title(f'r = {corr_val:.3f}, p = {p_val:.4f}', fontweight='bold')
    ax.grid(alpha=0.3)
    ax.legend()

plt.tight_layout()
plt.savefig('03_streudiagramme_top4.png', dpi=300, bbox_inches='tight')
print("✓ Datei erstellt: 03_streudiagramme_top4.png")
plt.close()

# 4. Verteilung der Verspätungen
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Histogramm
axes[0].hist(df_clean[target_var], bins=30, color='steelblue', edgecolor='black', alpha=0.7)
axes[0].axvline(df_clean[target_var].mean(), color='red', linestyle='--', linewidth=2, label=f'Mittelwert: {df_clean[target_var].mean():.2f}')
axes[0].set_xlabel('Verspätung (Minuten)', fontweight='bold')
axes[0].set_ylabel('Häufigkeit', fontweight='bold')
axes[0].set_title('Verteilung der Flugverspätungen', fontweight='bold')
axes[0].legend()
axes[0].grid(alpha=0.3)

# Boxplot nach Wochentag
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
df_day = df.copy()
df_day['day_of_week'] = pd.to_datetime(df_day['Date']).dt.day_name()
sns.boxplot(data=df_day, x='day_of_week', y=target_var, order=day_order, ax=axes[1])
axes[1].set_xlabel('Wochentag', fontweight='bold')
axes[1].set_ylabel('Verspätung (Minuten)', fontweight='bold')
axes[1].set_title('Verspätungen nach Wochentag', fontweight='bold')
axes[1].tick_params(axis='x', rotation=45)
axes[1].grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('04_verteilung_verspätungen.png', dpi=300, bbox_inches='tight')
print("✓ Datei erstellt: 04_verteilung_verspätungen.png")
plt.close()

# Export der Korrelationen in CSV
corr_df.to_csv('Korrelationen.csv', index=False)
print("✓ Datei erstellt: Korrelationen.csv")

print("\n" + "=" * 80)
print("ANALYSE ABGESCHLOSSEN")
print("=" * 80)
print("\nErstellte Dateien:")
print("  1. 01_korrelationsmatrix_alle.png - Heatmap aller Korrelationen")
print("  2. 02_korrelationen_verspätungen.png - Balkendiagramm der Verspätungskorrelationen")
print("  3. 03_streudiagramme_top4.png - Streudiagramme der stärksten Korrelationen")
print("  4. 04_verteilung_verspätungen.png - Histogramm und Wochentag-Analyse")
print("  5. Korrelationen.csv - Tabellarische Übersicht aller Korrelationen")