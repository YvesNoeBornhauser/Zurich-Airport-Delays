import csv
import pdfplumber

pdf_path = "Quellen/monatliche-flugbewegungen_20260320.pdf"
csv_path = "Quellen/zrh_abfluege_pro_tag.csv"

# Erwartete Buchstabenfolge in der Kopfzeile:
# ABCD = Piste 10 | EFG = Piste 16 | IK = Piste 28 | NO = Piste 32 | NO = Piste 34
ERWARTET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'I', 'K', 'N', 'O', 'N', 'O']


def find_col_grenzen(words):
    """
    Sucht die Buchstaben-Kopfzeile (A B C D E F G I K N O N O + Abflüge)
    auf einer Seite und berechnet die x-Grenzen zwischen den Pistenspalten.
    Gibt None zurück, wenn die Kopfzeile nicht gefunden wird.
    """
    # Das Wort "Abflüge" in der Buchstabenzeile = Header der Total-Spalte.
    # Es gibt auch ein linkes "Abflüge" (Abschnittsüberschrift) — wir brauchen das rechte.
    # Wir erkennen es daran, dass in derselben Zeile (top ± 3) auch die Buchstaben A…O stehen.
    for ab_word in sorted(
        [w for w in words if w["text"] == "Abflüge"],
        key=lambda w: w["x0"],
        reverse=True          # von rechts starten: das Total-"Abflüge" steht weiter rechts
    ):
        top_ref = ab_word["top"]
        same_row = sorted(
            [w for w in words
             if abs(w["top"] - top_ref) < 3 and w["text"] in set(ERWARTET)],
            key=lambda w: w["x0"]
        )

        # Buchstaben in der erwarteten Reihenfolge einlesen
        col_x = []
        ci = 0
        for w in same_row:
            if ci < len(ERWARTET) and w["text"] == ERWARTET[ci]:
                col_x.append(w["x0"])
                ci += 1

        if len(col_x) == 13:
            x_total = ab_word["x0"]
            grenzen = [(col_x[i] + col_x[i + 1]) / 2 for i in range(12)]
            grenzen.append(x_total)
            return grenzen

    return None


def get_col_index(x, grenzen):
    """Gibt den Spaltenindex 0–12 zurück; 13 = Total-Spalte."""
    for i, g in enumerate(grenzen):
        if x < g:
            return i
    return 13


def col_to_piste(ci):
    if 0 <= ci <= 3:   return 'piste_10'   # A B C D
    if 4 <= ci <= 6:   return 'piste_16'   # E F G
    if 7 <= ci <= 8:   return 'piste_28'   # I K
    if 9 <= ci <= 10:  return 'piste_32'   # N O (links)
    if 11 <= ci <= 12: return 'piste_34'   # N O (rechts)
    return 'total'


# ── Hauptprogramm ─────────────────────────────────────────────────────────────

daten = []
fehlerhafte_tage = []

with pdfplumber.open(pdf_path) as pdf:

    grenzen_aktuell = None  # wird pro Seite neu gesetzt
    im_abfluege_block = False

    for page in pdf.pages:
        words = page.extract_words()
        if not words:
            continue

        # Spalten-Grenzen für diese Seite neu bestimmen
        neue_grenzen = find_col_grenzen(words)
        if neue_grenzen is not None:
            grenzen_aktuell = neue_grenzen

        if grenzen_aktuell is None:
            continue  # Noch keine bekannten Grenzen → überspringen

        # Zeilen gruppieren (Toleranz 4 Punkte)
        lines = []
        words.sort(key=lambda w: w["top"])
        for w in words:
            if not lines:
                lines.append([w])
            elif abs(w["top"] - lines[-1][0]["top"]) < 4:
                lines[-1].append(w)
            else:
                lines.append([w])

        for line in lines:
            line.sort(key=lambda w: w["x0"])
            text_line = " ".join(w["text"] for w in line)

            # Abschnittserkennung: Abflüge / Anflüge
            if "Abflüge" in text_line:
                im_abfluege_block = True
            if "Anflüge" in text_line:
                im_abfluege_block = False
                continue

            if not im_abfluege_block:
                continue

            # Nur Zeilen mit Datum (Format TT.MM.JJ)
            datum_word = line[0]["text"]
            if not (len(datum_word) >= 8 and datum_word[2] == "." and datum_word[5] == "."):
                continue

            datum = datum_word[:8]
            piste_counts = {
                'piste_10': 0, 'piste_16': 0,
                'piste_28': 0, 'piste_32': 0, 'piste_34': 0
            }
            actual_total = 0

            for w in line[1:]:
                # Apostrophe (Tausendertrennzeichen) entfernen, Bindestriche überspringen
                text_val = w["text"].replace("\u2019", "").replace("'", "")
                try:
                    val = int(text_val)
                except ValueError:
                    continue  # Wochentag-Kürzel (Mo, Di …) und "-" ignorieren

                ci = get_col_index(w["x0"], grenzen_aktuell)
                piste = col_to_piste(ci)

                if piste == 'total':
                    actual_total = val
                else:
                    piste_counts[piste] += val

            # Leere Zeilen überspringen
            if actual_total == 0 and all(v == 0 for v in piste_counts.values()):
                continue

            # ── Validierung mit Rohzahlen (nicht Binär) ──────────────────────
            calculated_total = sum(piste_counts.values())
            if calculated_total != actual_total:
                fehlerhafte_tage.append((datum, calculated_total, actual_total))

            # ── CSV-Zeile: Abflüge pro Piste als Rohzahl ─────────────────────
            daten.append([
                datum,
                piste_counts['piste_10'],
                piste_counts['piste_16'],
                piste_counts['piste_28'],
                piste_counts['piste_32'],
                piste_counts['piste_34'],
                actual_total
            ])

# ── CSV speichern ─────────────────────────────────────────────────────────────
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "datum",
        "piste_10", "piste_16", "piste_28", "piste_32", "piste_34",
        "anzahl_abfluege_total"
    ])
    writer.writerows(daten)

# ── Terminal-Ausgabe ──────────────────────────────────────────────────────────
print(f"Fertig! {len(daten)} Tage in die CSV geschrieben.")
if fehlerhafte_tage:
    print(f"\nACHTUNG: Diskrepanz bei {len(fehlerhafte_tage)} Tagen "
          f"(Spaltensumme ≠ PDF-Total):")
    for f_datum, calc, act in fehlerhafte_tage:
        print(f"  {f_datum}  |  Berechnet: {calc}  |  PDF Total: {act}")
else:
    print("\nPerfekt! Alle Spaltensummen stimmen exakt mit dem PDF-Total überein.")
