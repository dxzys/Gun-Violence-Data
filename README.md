# Gun Violence Data
An up-to-date master dataset of all [Gun Violence Archive](https://www.gunviolencearchive.org/) (GVA) mass shooting incidents (2013–present). Updated daily.

#### [View map](https://dxzys.github.io/Gun-Violence-Data/map.html)

## Statistics
>*Last updated: September 05, 2025*
- **Total Incidents**: 5737
- **Incidents in 2025**: 294
- **Most recent incident**: September 3, 2025 in Kansas City, Missouri
  - Casualties: 0 killed, 5 injured

# Framework
The Gun Violence Archive (GVA) offers public [reports](https://www.gunviolencearchive.org/reports) of gun violence incidents in the U.S. (most notably mass shootings) that are downloadable in `.csv` format. Mass shootings (defined by GVA as incidents where 4+ people are shot, excluding the perpetrator) unfortunately happen far too often in the United States and are reported both in general *(Mass Shootings - All Years)* and by year *(Mass Shootings in 20xx)* as a result.

Because GVA's data is extensive and continuously updated, downloading all mass shooting incidents in a single file isn't easy. The site's data is limited to the most recent 80 pages, which for the "All Years" mass shooting incidents, so the CSV only includes incidents up to the last page on its corresponding on-site report. Older entries can only be obtained by download each yearly report separately and combining them manually. This project cuts that work by maintaining an up-to-date "master" dataset of every catalogued mass shooting incident.
