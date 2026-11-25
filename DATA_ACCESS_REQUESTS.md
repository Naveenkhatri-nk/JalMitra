# Data access requests and checklist (for naveen)

JalMitra did not create accounts, accept licences, pay, or bypass any website. These steps need you.

## 1. ICAR-NBSS&LUP (Bhoomi Geoportal) — permission required
The master instruction says access is on a paid basis; the geoportal metadata read on 22 Nov 2026 shows access
constraints "NA" and no price. Ask before deciding anything.

Contact: Director, ICAR-NBSS&LUP, Amravati Road, Nagpur 440033 · director-nbsslup@icar.org.in · +91-712-2500386

Draft email (edit and send yourself):
> Subject: Request for soil resource data for an academic Smart India Hackathon project (SIH25066, JalMitra)
>
> Respected Sir/Madam, we are students building JalMitra, a free, offline advisory prototype for the Ministry of Jal
> Shakti problem statement SIH25066. We request permission to use, for non-commercial demonstration only, the following
> layers for Rajasthan (to start with): soil resource map 1:250K (soil series / map units with texture, depth, drainage,
> AWC), soil fertility layers (OC, pH, micronutrients), soil erosion and salt-affected soil layers. Please let us know the
> terms, format, any fee, and the citation you require. We will display the source, year and scale with every value and
> will not redistribute the data. Thank you.

Checklist: ☐ email sent ☐ reply received ☐ terms acceptable (decide before paying or signing) ☐ files received
☐ source row added to `data/reference/source_catalog.csv` ☐ imported with `import_dataset.py`.

## 2. CGWB groundwater quality data 2019–2023 — manual download
Page: https://cgwb.gov.in/en/node/1852 (also publication-detail/293 for 2019, /295 for 2020).
☐ download each year to `data/raw/groundwater_quality/` ☐ if PDF, convert the station table to CSV and check 20 rows
by eye ☐ `python import_dataset.py groundwater_quality <file> --source CGWB_GWQ_DATA` (dry run) ☐ same with `--commit`.

## 3. CGWB Ground Water Year Book (Rajasthan) — manual download
☐ download ☐ convert water-level tables to CSV (`State, District, Block, Location, Latitude, Longitude, Date, Depth to water (mbgl)`)
☐ import into `groundwater_levels`. Do not use WIMS (authorised users only).

## 4. Soil Health Card portal
☐ check whether you can open soilhealth.dac.gov.in from your browser ☐ download your own (or a volunteer's, with consent)
card ☐ upload it in My Soil Report to test real cards (JalMitra was only tested with synthetic cards).

## 5. ISRO Bhuvan
☐ read the licence / terms for thematic layers (LULC, wasteland, land degradation) ☐ only if allowed, download and add
with a `.source.txt` file.

## 6. India-WRIS and IMD agromet
☐ check whether data export is offered and under what terms (both could not be read from the build environment).
