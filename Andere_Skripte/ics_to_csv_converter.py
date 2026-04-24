import csv
from icalendar import Calendar
from datetime import datetime

def ics_to_csv(ics_file_path, csv_file_path):
    with open(ics_file_path, 'rb') as f:
        calendar = Calendar.from_ical(f.read())

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        writer.writerow(['Summary', 'Start Date', 'End Date', 'Location', 'Description'])

        for component in calendar.walk():
            if component.name == "VEVENT":
                summary = component.get('summary', 'Kein Titel')
                dtstart = component.get('dtstart').dt if component.get('dtstart') else ''
                dtend = component.get('dtend').dt if component.get('dtend') else ''
                location = component.get('location', '')
                description = component.get('description', '')

                writer.writerow([summary, dtstart, dtend, location, description])

ics_to_csv('Quellen/ferienplan_2025-2026.ics', 'Quellen/ferienplan_2025-2026.csv')