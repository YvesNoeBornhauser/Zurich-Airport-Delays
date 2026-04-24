import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def fetch_wef_dates():
    url = "https://en.wikipedia.org/wiki/World_Economic_Forum"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    tables = soup.find_all('table', {'class': 'wikitable'})
    wef_table = tables[1]

    dates_list = []

    for row in wef_table.find_all('tr')[1:]:
        cols = row.find_all(['th', 'td'])
        if len(cols) >= 2:
            year_text = cols[0].get_text(strip=True)
            
            if year_text.isdigit() and int(year_text) >= 2022:
                year = year_text
                date_raw = cols[1].get_text(strip=True)
                
                range_match = re.search(r'(\d+)[–-](\d+)\s+([a-zA-Z]+)', date_raw)
                
                if range_match:
                    start_day = int(range_match.group(1))
                    end_day = int(range_match.group(2))
                    month = range_match.group(3)
                    
                    for day in range(start_day, end_day + 1):
                        date_string = f"{day} {month} {year}"
                        try:
                            # .normalize() entfernt die Uhrzeitanteile
                            ts = pd.to_datetime(date_string).normalize()
                            dates_list.append(ts)
                        except:
                            continue
    
    return dates_list

if __name__ == "__main__":
    wef_liste = fetch_wef_dates()
    print(wef_liste)