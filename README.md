# Gun Violence Data
An up-to-date master dataset of all [Gun Violence Archive](https://www.gunviolencearchive.org/) (GVA) mass shooting incidents (2013–present). Updated daily.

#### [View map](https://dxzys.github.io/Gun-Violence-Data/map.html)

## Statistics
>*Last updated: November 25, 2025*
- **Total Incidents**: 5827
- **Incidents in 2025**: 384
- **Most recent incident**: November 23, 2025 in Union City, Tennessee
  - Casualties: 1 killed, 3 injured

# Framework
The Gun Violence Archive (GVA) provides public [reports](https://www.gunviolencearchive.org/reports) of gun violence incidents in the U.S. (most notably mass shootings) that are downloadable in `.csv` format. Mass shootings (defined by GVA as incidents where 4+ people are shot, excluding the perpetrator) unfortunately happen far too often in the United States and are reported both in general *(Mass Shootings - All Years)* and by year *(Mass Shootings in 20xx)* as a result.

Because GVA's data is extensive and continuously updated, downloading all mass shooting incidents in a single file isn't easy. The site's "All Years" report only displays a limited number of the most recent incidents (up to 80 pages), so the corresponding CSV file is incomplete. Older incidents can only be obtained by downloading each yearly report separately and combining them manually.

This project cuts that work by maintaining an up-to-date "master" dataset of every mass shooting incident catalogued by GVA. It does this by checking for new incidents in the latest yearly report daily and automatically adding any data to the master dataset in this repository.

## Architecture
The project is entirely Python-based and relies on two scripts: 
- `gva.py` initiates the process and handles the data after the latest CSV is downloaded. After processing, new incidents are added to the master dataset (`master_gva.csv`).
- `export_gva.py` is called by gva.py. It automates the CSV downloading process using Selenium WebDriver. It dynamically constructs the correct URL for the current year's report (datetime) so that it automatically works for future years without needing manual updates.

A GitHub Actions workflow runs the process daily to keep the master CSV in this repository current.

## Data collection and processing
Since no public API is available for GVA's reports, data is collected by downloading CSV files directly from their website. This process is made more tedious as GVA generates dynamic export links with unique query identifiers, so we can't simply reuse a static download URL for a faster and more repetitive approach to downloading the data. Instead, we have to navigate the site and click the "Export CSV" button for each download (hence why webdriver is used).

The exporter script locates this dynamic link by searching for anchor elements containing "export-csv" in their href attribute:
```html
<a href="/query/0484b316-f676-44bc-97ed-ecefeabae077/export-csv?year=2025" class="button">Export as CSV</a>
```

After download, the up-to-date data for the current year is compared against the existing master dataset. Incidents are identified by GVA with a unique **Incident ID**, which are read from both files using Python's `csv.DictReader`. Any incidents found in the new data that are missing from the master CSV are considered new and thus added.

Geographical coordinates are added to each incident. GVA's data only includes address information (street addresses, city/county, and state), so each new incident is geocoded using the **ArcGIS** geocoder from the `geopy` library to add approximate latitude and longitude values based on the provided address information.
