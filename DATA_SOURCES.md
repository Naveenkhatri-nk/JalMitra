# Data sources

_Generated from `data/reference/source_catalog.csv` (the machine-readable copy). Last updated 22 November 2026._

Access classes: publicly downloadable · free web page · permission required · paid · manual upload required · not currently accessible · project text.

| ID | Title | Publisher | Year | Access | Used in JalMitra | Notes |
|---|---|---|---|---|---|---|
| AI2025 | [All India Blockwise GWRA 2025 (categorization of assessment units)](https://cgwb.gov.in/cgwbpnm/public/publication-detail/1913) | Central Ground Water Board | 2025 | publicly_downloadable | groundwater.db (unchanged) | Imported in JalMitra 2.0 |
| RJ2025 | [Dynamic Ground Water Resources of Rajasthan - 2025](https://cgwb.gov.in/cgwbpnm/public/publication-detail/2120) | CGWB Western Region Jaipur and Ground Water Department Govt. of Rajasthan | 2025 | publicly_downloadable | groundwater.db (unchanged) | Imported in JalMitra 2.0 |
| NC2025 | [National Compilation on Dynamic Ground Water Resources of India 2025](https://www.jalshakti-dowr.gov.in/static/uploads/2025/11/711d8d476bbf498cd90f8038e7371227.pdf) | Central Ground Water Board Ministry of Jal Shakti | 2025 | publicly_downloadable | groundwater.db (unchanged) | Imported in JalMitra 2.0 |
| BIS_IS10500_2012 | [IS 10500:2012 Drinking Water - Specification (Second Revision)](https://consumerhelpline.gov.in/public/assets/docs/bis/IS10500-2012.pdf) | Bureau of Indian Standards | 2012 | publicly_downloadable | reference_ranges (drinking water) | Tables 1-3 pages 2-4. Later amendments may change values; see CGWB_GWQ_2024 |
| CGWB_GWQ_2024 | [Report on Groundwater Quality of Shallow Aquifers in India 2024 (Annual Ground Water Quality Report)](https://cgwb.gov.in/cgwbpnm/public/uploads/documents/173951023952337139file.pdf) | Central Ground Water Board | 2024 | publicly_downloadable | reference_ranges (drinking and irrigation water) | Table 1 p4 (BIS 10500 subset as used by CGWB); Table 2 p5 (IS:11624-1986 EC limits); Table 3 p6 (SAR RSC %Na). Station data are not in this file |
| IS11624_1986 | [IS 11624:1986 Guidelines for the quality of irrigation water (as reproduced in CGWB_GWQ_2024 Table 2)](https://cgwb.gov.in/cgwbpnm/public/uploads/documents/173951023952337139file.pdf) | Bureau of Indian Standards | 1986 | publicly_downloadable | reference_ranges (irrigation EC) | Secondary citation only |
| CRIDA_SOIL | [Soil Analysis for Fertility Management in Rainfed Agriculture (S S Balloli)](https://krishi.icar.gov.in/jspui/bitstream/123456789/67531/1/SSB.pdf) | ICAR-Central Research Institute for Dryland Agriculture | - | publicly_downloadable | reference_ranges (soil OC P K and DTPA micronutrients) | Tables 2a and 2b p310. Publication year not found in the file. N pH EC B S not given |
| TNAU_SOIL_RATING | [Soil Rating Chart (TNAU Agritech Portal)](https://agritech.tnau.ac.in/agriculture/agri_soil_rating.html) | Tamil Nadu Agricultural University | 2013 | free_web_page | reference_ranges (soil N P K pH soluble salts) | OC row has a typo (0.5 - 7.5%) and is NOT used. pH 8.5-8.9 is not classified on the page. No S or micronutrient rows |
| FAO_SALT_TOLERANCE | [Annex 1 Crop salt tolerance data (FAO document Y4263E)](https://www.fao.org/3/Y4263E/y4263e0e.htm) | Food and Agriculture Organization of the United Nations | - | free_web_page | crop_salt_tolerance | Data from FAO Irrigation and Drainage Paper 29 Rev.1 (1985) and Maas & Grattan (1999). Values are soil ECe (saturation extract) in dS/m. Not comparable with 1:2 or 1:2.5 soil:water EC from a Soil Health Card |
| FAO_CROP_WATER | [Chapter 3 Crop water needs - Table 14 Indicative values of crop water needs and sensitivity to drought (FAO document S2022E)](https://www.fao.org/4/s2022e/s2022e07.htm) | Food and Agriculture Organization of the United Nations | - | free_web_page | crop_water_needs | FAO calls the values a rough estimate to use only when crop water needs cannot be calculated; maximum for long and minimum for short growing periods. Manual title and year not confirmed on the fetched page |
| SKNAU_FATEHPUR | [Agricultural Research Station Fatehpur (Sikar) - Zone II-A profile](https://www.old.sknau.ac.in/arsfatehpur) | Sri Karan Narendra Agriculture University Jobner | - | free_web_page | agro_climatic_zones; zone_crops | Published regional description of the zone; not field data for any farm |
| SHC_PORTAL | [Soil Health Card portal](https://soilhealth.dac.gov.in) | Department of Agriculture and Farmers Welfare | - | not_currently_accessible | (none yet) | naveen to check portal access and terms |
| NBSSLUP_BHOOMI | Bhoomi Geoportal - soil resource maps fertility and degradation layers | ICAR-National Bureau of Soil Survey and Land Use Planning | - | permission_required | (none yet) | See DATA_ACCESS_REQUESTS.md; geoportal URL was read during the 22 Nov 2026 investigation but is not recorded here: confirm the official URL before use |
| BHUVAN | [ISRO Bhuvan thematic services (land use land cover wasteland land degradation)](https://bhuvan.nrsc.gov.in) | ISRO NRSC | - | not_currently_accessible | (none yet) | naveen to check licence and whether WMS use is allowed |
| CGWB_GWQ_DATA | [Ground Water Quality Data 2019-2023 (station data downloads)](https://cgwb.gov.in/en/node/1852) | Central Ground Water Board | - | manual_upload_required | (importer ready) | Use import_dataset.py groundwater_quality; individual years also listed in the CGWB publications warehouse e.g. https://www.cgwb.gov.in/cgwbpnm/publication-detail/293 (2019) and /295 (2020) |
| CGWB_YEARBOOK | Ground Water Year Books (national and state including Rajasthan) | Central Ground Water Board | - | manual_upload_required | (importer ready) | WIMS is for authorised users only - do not use; URL of the CGWB water-level page to be confirmed |
| INDIA_WRIS | [India-WRIS groundwater level and quality](https://indiawris.gov.in) | National Water Informatics Centre | - | not_currently_accessible | (none yet) | naveen to check export options and terms |
| IMD_AGROMET | [IMD Agromet advisories](https://imdagrimet.gov.in) | India Meteorological Department | - | not_currently_accessible | (none yet) |  |
| JALMITRA_GENERAL | JalMitra general educational text (written for this app; pending expert review) | JalMitra project | 2026 | project_text | parameter_info; methods | Not a government recommendation. Must be reviewed by an agronomist or soil scientist before field use |

## Known differences between sources

- **Iron (drinking water):** IS 10500:2012 text gives 0.3 mg/L with no relaxation; the CGWB 2024 report's Table 1 lists 1 mg/L. Both are shown.
- **Arsenic (drinking water):** IS 10500:2012 gives 0.01 mg/L acceptable and 0.05 mg/L permissible; CGWB 2024 lists 10 µg/L with no relaxation. Both are shown.
- **Soil P and K:** ICAR-CRIDA and TNAU charts use different class limits (P medium up to 25 vs 22 kg/ha; K low below 120 vs 110 kg/ha). Both ratings are shown.
- **Soil EC vs ECe:** Soil Health Cards report EC in a 1:2 or 1:2.5 soil:water extract; FAO crop thresholds use ECe (saturation extract). JalMitra never compares the two.
- **Assam source conflict (groundwater.db):** kept as recorded in Phase 2.0 and shown on the Data Sources page.

## Groundwater database (unchanged)

`data/groundwater.db` holds AI2025, RJ2025 and NC2025 exactly as imported in JalMitra 2.0, including quality flags and the Assam conflict.
