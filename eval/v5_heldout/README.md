# JalMitra v5 held-out evaluation set

A labelled set of 200 short groundwater explanations of the kind an AI assistant might write for a farmer. Each one is labelled `good` (factually correct and supported by its context) or `bad` (contains at least one error). It is meant to measure an automatic GOOD/BAD checker.

**Important: these labels were written by an AI (Claude), not by a hydrogeologist. A human expert should review them before anyone relies on the scores.** See "Limitations" below.

## Independence

The set was built without opening the checker or answer pipeline. I did not open semantic_gate.py, answer_verifier.py, llm_compose.py, rag.py, any test_v4_* or test_v5_* file, eval\semantic_*, any other eval\v5_* folder, LLM_ARCHITECTURE.md, or any other project Python source. I used only two inputs:

- `data/groundwater.db`, opened read-only (`file:E:/JalMitra/data/groundwater.db?mode=ro`, `uri=True`)
- `data/rag/chunks.jsonl`

No existing file was modified. Only this folder was written.

## Files

`items.tsv` is UTF-8, tab-separated, with one header row and no quoting. No field contains a tab, a newline or a double quote. Its columns are:

| column | meaning |
|---|---|
| id | H001 to H200 (order is shuffled) |
| split | `dev` (50), `test_a` (75), `test_b` (75) |
| lang | `en`, `hinglish` (Hindi in Latin letters), `hi` (Devanagari) |
| context_type | `place` or `general` |
| place | `state\|district\|unit` for place items. The unit is empty for a district. Empty for general items. |
| chunk_ids | 1 to 3 chunk ids separated by `;` for general items. Empty for place items. |
| error_type | `none` for good items. For bad items, one value from the taxonomy below. |
| label | `good` or `bad` |
| text | the explanation, 1 to 3 sentences |
| rationale | one short sentence saying why the item is good or what is wrong, citing the DB fact or chunk |

## Contexts

### Place items (86 items, 40 distinct places)

- **Rajasthan assessment units with figures (26 units).** The place string uses `state`, `district` and `assessment_unit` exactly as stored in `groundwater_assessment`, for example `Rajasthan|JAIPUR|PHAGI`. The facts used are category, `stage_of_extraction_pct`, `annual_recharge_original`, `extractable_resource_original` and `total_extraction_original` (ham).
  - Units: PHAGI, CHHABRA, ARTHOONA, BAGIDORA, KUSHALGARH, KHAJUWALA (Saline), TIWARI, ANUPGARH, CHITALWANA, ITAWA, KHERWARA, CHOHTAN, ROHAT, LALSOT, FATEHPUR, SAM, ASPUR, SARDARSHAHAR, PILIBANGA, MAKRANA, BEHROR, PINDWARA, JAIPUR_URBAN, NADOTI, MANDAL, TARANAGAR (Saline).
- **Rajasthan districts (5).** These are written `Rajasthan|JAIPUR|`, `Rajasthan|GANGANAGAR|`, `Rajasthan|JAISALMER|`, `Rajasthan|TONK|` and `Rajasthan|BANSWARA|`. The state and district spelling follows `groundwater_assessment`. The district figures come from `national_district_summary`, where the same rows are stored as state `RAJASTHAN` and district `Jaipur`, `Ganganagar` and so on. The match is case-insensitive.
  - Facts used: `stage_of_extraction_pct`, `annual_recharge`, `extractable_resource` and `total_extraction` (ham). None of the GOOD district items state a district category, because the DB does not store one.
- **Non-Rajasthan units, category only (9).** `Punjab|Bathinda|Maur`, `Haryana|SIRSA|ELLENABAD`, `Uttar Pradesh|BAREILLY|MEERGANJ`, `Tamil Nadu|CHENNAI|AMBATTUR`, `Delhi|CENTRAL|KAROL BAGH`, `West Bengal|SOUTH 24 PARGANAS|BHANGAR-II`, `Karnataka|Belagavi|Gokak`, `Gujarat|BANASKANTHA|DHANERA`, `Bihar|PATNA|BELCHHIA`.

GOOD place texts use only the DB facts for that place, with numbers written as stored (117, 5949, 217.01 and so on), plus the standard category definitions: Safe <=70%, Semi-critical >70-90%, Critical >90-100%, Over-exploited >100%, Saline = poor-quality groundwater. Simple comparisons such as "extraction is more than the extractable resource" or "more than double" are allowed. GOOD place texts contain no causes, trends or advice.

Some items are deliberately tricky:

- KHERWARA: stage stored as 100, category Over-exploited.
- CHOHTAN: stage 70, category Semi-critical.
- SARDARSHAHAR: stage 70, category Safe.
- Negations such as "not Safe" and "not Over-exploited" appear in GOOD items.

### General items (114 items)

Each general item cites 1 to 3 chunk ids. GOOD general texts paraphrase what those chunks say and avoid statistics that are not essential. These are the 34 chunks used:

- **NC2025:** p023-c0, p023-c1, p024-c0, p024-c1, p027-c0, p029-c1, p030-c0, p035-c0, p036-c0, p039-c0, p040-c0, p042-c0, p043-c0, p044-c0, p070-c0, p071-c0, p072-c0, p073-c0, p083-c0, p088-c0, p163-c0
- **RJ2025:** p010-c0, p014-c0, p014-c1, p015-c0, p029-c0, p031-c0, p061-c0, p062-c0, p065-c0, p073-c0, p079-c0, p089-c0, p105-c0

Topics covered:

- category thresholds and the quality hazard tag
- the stage-of-extraction definition and how it is validated against water level trends
- rainfall as the main recharge source, with June to September as the main rainy season
- monitoring months: May is pre-monsoon, August is peak monsoon, November is post-monsoon, January is the irrigation period
- water levels being shallower after the monsoon than before it
- draft above recharge leading to falling water levels
- other recharge sources: canal seepage, return flow, tanks, ponds and conservation structures
- the extractable resource as recharge minus natural discharge
- the evaporation and transpiration depth rules
- region-specific causes of over-exploitation
- comparisons between 2024 and 2025 as reported in the documents
- Rajasthan recommendations: rainwater harvesting, artificial recharge, restricting new wells, conjunctive use
- schemes: Atal Jal, PMKSY

## Error taxonomy (bad items)

| error_type | meaning | count |
|---|---|---|
| contradiction_db | contradicts the DB category or figure for the place | 10 |
| unsupported_causal | gives a cause the context does not support | 13 |
| wrong_seasonal | confuses pre- and post-monsoon, or misreads seasons or monitoring months | 9 |
| wrong_depth_direction | states the wrong direction for a rise or fall in level, or for depth increasing or decreasing | 7 |
| recharge_extraction_confusion | swaps recharge and extraction, or counts a recharge component as extraction | 11 |
| wrong_stage_interpretation | wrong formula, meaning or denominator for the stage of extraction | 13 |
| wrong_category_explanation | wrong thresholds or wrong meaning of a category, including Saline | 15 |
| wrong_historical_comparison | a trend or earlier-year claim. For place items the DB has only 2025, so any trend is unsupported. For general items the claim contradicts the 2024 vs 2025 comparison in the chunks. | 11 |
| unsupported_statistics | numbers that are not in the context | 12 |
| invented_location_fact | a wrong or invented location attribute | 9 |

Bad items by context and type:

| error_type | place | general |
|---|---|---|
| contradiction_db | 10 | 0 |
| unsupported_causal | 4 | 9 |
| wrong_seasonal | 1 | 8 |
| wrong_depth_direction | 2 | 5 |
| recharge_extraction_confusion | 4 | 7 |
| wrong_stage_interpretation | 7 | 6 |
| wrong_category_explanation | 7 | 8 |
| wrong_historical_comparison | 5 | 6 |
| unsupported_statistics | 5 | 7 |
| invented_location_fact | 3 | 6 |

## Counts

The totals are 200 items: 90 good (45%) and 110 bad (55%). By language there are 89 en, 69 hinglish and 42 hi. By context there are 86 place items (38 good, 48 bad) and 114 general items (52 good, 62 bad).

| split | total | good | bad | en (g/b) | hinglish (g/b) | hi (g/b) | place | general |
|---|---|---|---|---|---|---|---|---|
| dev | 50 | 24 | 26 | 22 (11/11) | 17 (9/8) | 11 (4/7) | 21 | 29 |
| test_a | 75 | 33 | 42 | 34 (16/18) | 26 (12/14) | 15 (5/10) | 31 | 44 |
| test_b | 75 | 33 | 42 | 33 (15/18) | 26 (12/14) | 16 (6/10) | 34 | 41 |

Bad items by type and split:

| error_type | dev | test_a | test_b |
|---|---|---|---|
| contradiction_db | 3 | 3 | 4 |
| invented_location_fact | 1 | 4 | 4 |
| recharge_extraction_confusion | 4 | 5 | 2 |
| unsupported_causal | 3 | 5 | 5 |
| unsupported_statistics | 4 | 3 | 5 |
| wrong_category_explanation | 4 | 5 | 6 |
| wrong_depth_direction | 1 | 2 | 4 |
| wrong_historical_comparison | 3 | 3 | 5 |
| wrong_seasonal | 1 | 4 | 4 |
| wrong_stage_interpretation | 2 | 8 | 3 |

Splits were assigned by stratifying on language and label, with a fixed pattern of 3 test_a : 3 test_b : 2 dev. The seed (20251152) was the first one where every error type appears at least once in dev and at least twice in each test split. Only dev should be shown to the checker author. test_a and test_b should each be scored once.

## DB queries used (all read-only)

```sql
SELECT category, stage_of_extraction_pct, annual_recharge_original,
       extractable_resource_original, total_extraction_original
FROM groundwater_assessment
WHERE state=? AND district=? AND assessment_unit=? AND year='2025';

SELECT stage_of_extraction_pct, annual_recharge, extractable_resource, total_extraction
FROM national_district_summary
WHERE upper(state)=upper(?) AND upper(district)=upper(?) AND year='2025';

-- exploration: list of all Rajasthan units with figures; random samples of non-Rajasthan units
SELECT state, district, assessment_unit, assessment_unit_type, category
FROM groundwater_assessment WHERE state=? ORDER BY random() LIMIT 6;
```

## Verification done

- Every place string was checked to exist in the DB. Every chunk id was checked to exist in chunks.jsonl.
- For every GOOD place item, a script took each number in the text and checked it against the DB facts for that place, allowing also the threshold numbers 70, 90 and 100. The DB category was printed next to each text and compared by hand. All matched. The only number flagged was "24", which is part of the name "South 24 Parganas".
- For every GOOD general item, a script checked that each number in the text appears in the cited chunks or is a threshold. Each statement was also compared with the chunk text by hand.
- I checked that no field contains a tab, newline or double quote, and that every line has exactly 10 fields.

## Limitations

- An AI wrote all the texts and labels. Some judgements are open to debate, and a human expert should review them. Examples:
  - Whether "most wells are shallower after the monsoon" is fully supported by the depth distributions in NC2025-p070/p071.
  - Whether a simple comparison in a place item, such as "more than three times", counts as supported.
  - Whether "about 95%" for a stored stage of 95 is acceptable wording.
  - Some bad items carry more than one error. Each is labelled with its main error only.
- Some bad general items, such as the solar-panel and desalination causes, are fairly easy to spot. Others, such as wrong thresholds, swapped numbers and the 70% boundary cases, are subtle.
- The Hindi and Hinglish texts were written by an AI and may read less naturally than text from native writers.
- Real-world truth was not used as a label source. A statement can be BAD here only because the given context does not support it, even if it happens to be true elsewhere.
