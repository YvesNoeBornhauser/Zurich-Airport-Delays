import csv
import pdfplumber

pdf_path = "monatliche-flugbewegungen_20260320.pdf"
csv_path = "zrh_abfluege_pro_tag.csv"

daten = []
im_abfluege_block = False

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue

        for line in text.split("\n"):
            line = line.strip()

            if line == "Abflüge":
                im_abfluege_block = True
                continue

            if line == "Anflüge":
                im_abfluege_block = False
                continue

            if not im_abfluege_block:
                continue

            if line.startswith("Total"):
                continue

            teile = line.split()

            if len(teile) < 3:
                continue

            datum = teile[0]

            if len(datum) != 8 or datum[2] != "." or datum[5] != ".":
                continue

            try:
                anzahl_abfluege = int(teile[-1].replace("’", "").replace("'", ""))
                daten.append([datum, anzahl_abfluege])
            except:
                pass

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["datum", "anzahl_abfluege"])
    writer.writerows(daten)