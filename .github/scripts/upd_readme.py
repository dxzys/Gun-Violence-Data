import csv
from datetime import datetime

CSV_PATH = 'data/gva_master.csv'
README_PATH = 'README.md'

README_TEMPLATE = '''# Gun Violence Data
An up-to-date master dataset of all [Gun Violence Archive](https://www.gunviolencearchive.org/) (GVA) mass shooting incidents (2013–present). Updated daily.

#### [View map](https://dxzys.github.io/Gun-Violence-Data/map.html)

## Statistics
>*Last updated: {last_updated}*
- **Total Incidents**: {total_incidents}
- **Incidents in {current_year}**: {incidents_this_year}
- **Most recent incident**: {most_recent_date} in {most_recent_location}
  - Casualties: {most_recent_deaths} killed, {most_recent_injuries} injured

# Framework
The Gun Violence Archive (GVA) offers public [reports](https://www.gunviolencearchive.org/reports) of gun violence incidents in the U.S. (most notably mass shootings) that are downloadable in `.csv` format. Mass shootings (defined by GVA as incidents where 4+ people are shot, excluding the perpetrator) unfortunately happen far too often in the United States and are reported both in general *(Mass Shootings - All Years)* and by year *(Mass Shootings in 20xx)* as a result.

Because GVA's data is extensive and continuously updated, downloading all mass shooting incidents in a single file isn't easy. The site's data is limited to the most recent 80 pages, which for the "All Years" mass shooting incidents, so the CSV only includes incidents up to the last page on its corresponding on-site report. Older entries can only be obtained by download each yearly report separately and combining them manually. This project cuts that work by maintaining an up-to-date "master" dataset of every catalogued mass shooting incident.
'''

def parse_csv(csv_path):
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows

def get_stats(rows, year):
    total_incidents = len(rows)
    incidents_this_year = sum(1 for row in rows if str(year) in row['Incident Date'])
    most_recent = rows[0] if rows else None
    if most_recent:
        most_recent_date = most_recent['Incident Date'].replace('"', '')
        most_recent_location = f"{most_recent['City Or County']}, {most_recent['State']}"
        most_recent_deaths = most_recent['Victims Killed']
        most_recent_injuries = most_recent['Victims Injured']
    else:
        most_recent_date = most_recent_location = most_recent_deaths = most_recent_injuries = 'N/A'
    return {
        'total_incidents': total_incidents,
        'incidents_this_year': incidents_this_year,
        'most_recent_date': most_recent_date,
        'most_recent_location': most_recent_location,
        'most_recent_deaths': most_recent_deaths,
        'most_recent_injuries': most_recent_injuries,
    }

def main():
    from datetime import timezone
    now_utc = datetime.now(timezone.utc)
    current_year = now_utc.year
    last_updated = now_utc.strftime('%B %d, %Y')
    rows = parse_csv(CSV_PATH)
    stats = get_stats(rows, current_year)
    readme_content = README_TEMPLATE.format(
        last_updated=last_updated,
        current_year=current_year,
        total_incidents=stats['total_incidents'],
        incidents_this_year=stats['incidents_this_year'],
        most_recent_date=stats['most_recent_date'],
        most_recent_location=stats['most_recent_location'],
        most_recent_deaths=stats['most_recent_deaths'],
        most_recent_injuries=stats['most_recent_injuries'],
    )
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(readme_content)

if __name__ == '__main__':
    main()
