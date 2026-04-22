import pdfplumber
import csv
import re

def parse_date(date_string):
    """Konvertiert Datum von 'dd. Monat. yyyy' zu 'yyyy-mm-dd'"""
    if not date_string or not isinstance(date_string, str):
        return ""
    
    monate = {
        "januar": "01", "februar": "02", "märz": "03", "april": "04",
        "mai": "05", "juni": "06", "juli": "07", "august": "08",
        "september": "09", "oktober": "10", "november": "11", "dezember": "12"
    }
    
    try:
        date_string = date_string.replace(".", " ").strip()
        parts = date_string.split()
        
        if len(parts) < 3:
            return ""
        
        day = parts[0].zfill(2)
        month_name = parts[1].lower()
        year = parts[2]
        
        for monat_name, monat_num in monate.items():
            if monat_name in month_name:
                return f"{year}-{monat_num}-{day}"
    except:
        pass
    
    return ""

def extract_ferien_to_csv(pdf_path, csv_path):
    ferien_liste = []
    date_pattern = r'(\d{1,2})\.\s+(\w+)\.\s+(\d{4})'
    
    current_year_context = ""
    ferien_arten = ["Herbstferien", "Weihnachtsferien", "Sportferien", "Frühlingsferien", "Sommerferien"]

    with pdfplumber.open(pdf_path) as pdf:
        all_text = ""
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"
        
        lines = all_text.split('\n')
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            if not line_clean:
                continue
            
            # Erfasse Schuljahr
            if "Schuljahr" in line_clean and "/" in line_clean:
                current_year_context = line_clean
                continue
            
            # Suche nach Ferienarten
            for art in ferien_arten:
                if art in line_clean:
                    # Entferne Wochentage (Mo, Fr, etc.)
                    line_dates = re.sub(r'(Mo|Di|Mi|Do|Fr|Sa|So),?\s+', '', line_clean)
                    
                    # Extrahiere alle Daten
                    dates = re.findall(date_pattern, line_dates)
                    
                    start_date = ""
                    end_date = ""
                    
                    if len(dates) > 0:
                        start_date = parse_date(f"{dates[0][0]}. {dates[0][1]}. {dates[0][2]}")
                    if len(dates) > 1:
                        end_date = parse_date(f"{dates[1][0]}. {dates[1][1]}. {dates[1][2]}")
                    
                    ferien_liste.append({
                        "Schuljahr": current_year_context,
                        "Ferienart": art,
                        "Start": start_date,
                        "Ende": end_date
                    })
                    break

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Schuljahr", "Ferienart", "Start", "Ende"])
        writer.writeheader()
        writer.writerows(ferien_liste)

extract_ferien_to_csv('ferienplan_2019-2025.pdf', 'ferienplan_2019-2025.csv')