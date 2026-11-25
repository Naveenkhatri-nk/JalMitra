# JalMitra roadmap

## Done
- 2.0: offline groundwater chatbot (6,762 assessment units, six languages).
- 3.0 Phase 1: website, memory, answer styles and lengths.
- 3.0 Phases 2–8: soil health, soil profile, land, land degradation, crop advisor, irrigation advisor, groundwater
  quality, explorer boundary layer, six report types, 190 domain tests, status documents.

## Next (needs data or people)
| Step | Blocked on | Then |
|---|---|---|
| Groundwater quality by station | CGWB files downloaded by naveen | import with `import_dataset.py`; answers and the Groundwater Quality page show them automatically |
| Groundwater levels | CGWB year books converted to CSV and reviewed | import into `groundwater_levels` |
| Soil and land maps (soil type, AWC, depth, slope, erosion, salt-affected) | NBSS&LUP permission (Bhoomi Geoportal) | catalogue source, import, then add a documented land-evaluation method before any suitability class is shown |
| Land use / wasteland | Bhuvan licence check | same |
| More agro-climatic zones | reading each zone's published description (RAU Bikaner, SKNAU, MPUAT, AU Jodhpur, AU Kota) | add rows to `agro_zones.csv`, `zone_districts.csv`, `zone_crops.csv` |
| Crop requirements beyond FAO | ICAR / state university package-of-practices documents | add rows to `data/reference`, never to Python code |
| Sulphur and boron ratings | a citable rating chart | add ranges |
| Native-speaker review | naveen's reviewers | record corrections |
| Real voice test | naveen with a microphone and speaker | record results |
| Windows performance run | naveen's computer | add to `TEST_STATUS.md` |

## Not planned
- Paid datasets or licences without naveen's decision; LLM APIs; React or FastAPI migration (no technical reason found:
  Streamlit handles all 17 pages, uploads and downloads).
