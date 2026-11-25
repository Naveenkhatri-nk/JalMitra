# Known limitations

## Data
- No place-level soil, land-use, slope, degradation, groundwater-level or groundwater-quality data is loaded. Those
  sections say "Not available in the current dataset". See `DATA_ACCESS_REQUESTS.md`.
- Only one agro-climatic zone (Rajasthan Zone II-A: Sikar, Jhunjhunu, Nagaur, eastern Churu) has a published crop list.
- Soil ratings come from two general charts (ICAR-CRIDA, TNAU); no state- or crop-specific chart yet. Sulphur and boron
  have no verified range. TNAU pH 8.5–8.9 and EC above 4 dS/m are unclassified (shown as gaps).
- FAO salt tolerance covers 13 crops; mustard and pearl millet are not in it and no substitute is used. FAO water needs are
  rough whole-season estimates; the paddy figure is shown with a caveat.
- Crop suitability for a field is always "Insufficient data": no documented field-level method has the data it needs.
- Irrigation schedules are not calculated.
- Only 2025 groundwater data exists, so comparison with earlier years is unavailable.
- Explanatory texts (guidance, parameter meanings) were written for JalMitra and still need expert review.

## Software
- Scanned PDFs are not read (no OCR installed); the user types values. Text-layer PDF extraction was tested on synthetic
  cards only.
- PDF reports are English only (the PDF library does not shape Devanagari); Hindi reports download as Markdown.
- Explanatory content exists in English and Hindi; Marathi and Rajasthani answers show the Hindi text, Hinglish and
  Punjabi the English text, with a note. Interface: English and Hindi.
- "moth" (the crop) is also a block name in Uttar Pradesh: "Is moth safe?" is read as the block; "moth bean" is read
  as the crop.
- Maps are drawn only from GeoJSON files placed in `data/geo/`; none are supplied.
- Everyday conversation (small talk, "is this about X?", out-of-scope subjects) works from word lists, typo and SMS-spelling
  tolerance and word classes, not a language model. New slang or long mixed messages can still fall to the fallback;
  the fallback then suggests real questions. On three batches written after the rules, the first untuned runs were
  122/159, 107/133 and 89/109 right.
- Two gaps from the 2.0 place matching remain: "random words here" asks for the user's location ("here" = my area),
  and gibberish such as "hjkl" can be sound-matched to a place name.

## Not verified by the build environment (needs naveen)
- Real microphone and speaker test; browser speech recognition may use an online service, so voice input is not offline.
- Windows run and performance.
- Native-speaker review of Marathi, Punjabi and Rajasthani (Marwari phrase set only, not all Rajasthani dialects).
- An unseen question set written by someone else.
- Real Soil Health Card uploads.
