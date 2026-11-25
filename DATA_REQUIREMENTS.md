# Data requirements

What each feature needs, what JalMitra has, and what it shows meanwhile. Nothing is filled in by estimation.

| Feature | Needs | Have now | Shown meanwhile |
|---|---|---|---|
| Groundwater category and figures | GWRA 2025 | AI2025, RJ2025, NC2025 | Values with page references |
| Soil Health interpretation | User's own card + rating charts | ICAR-CRIDA (OC, P, K, Zn, Fe, Cu, Mn), TNAU (N, P, K, pH, EC) | S and B: "no verified rating range yet" |
| Soil type / profile for a place | NBSS&LUP soil map units and properties (texture, depth, AWC, CEC, CaCO3, drainage) | none | "Not available in the current dataset"; SKNAU zone description where it applies, labelled regional |
| Land condition (landform, slope, drainage, degradation, land use) | NBSS&LUP / Bhuvan layers | none | "Not available in the current dataset"; land-use classes "Insufficient data" |
| Crop suitability for a field | field soil test, ECe, irrigation water quality, rainfall, temperature, season, local recommendation, and a documented method | FAO salt tolerance and water need; SKNAU Zone II-A crop list | per-crop facts; class "Insufficient data" |
| Irrigation schedule | crop stage, ET0/weather, soil water, water supply | none | not calculated (stated) |
| Groundwater quality by place | CGWB station data | none imported | standards and the user's own test checker |
| Groundwater levels | CGWB year books / India-WRIS | none | "Not available in the current dataset" |
| Maps | official boundary GeoJSON with source and year | none | tables only |
| Weather / agromet advisories | IMD agromet | none | not shown; historical advisories are never presented as forecasts |

## File placement
- Raw downloads: `data/raw/<topic>/` (never edited).
- Reviewed CSV of a PDF table: `data/processed/<topic>/`.
- Boundary files: `data/geo/<name>.geojson` with `<name>.source.txt` (publisher, year, scale, licence).
- Import: `python import_dataset.py <table> <file> --source <SOURCE_ID>` then `--commit`.
