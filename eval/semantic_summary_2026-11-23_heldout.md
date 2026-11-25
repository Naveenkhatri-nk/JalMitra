# Semantic factuality gate: labelled evaluation (2026-11-23_heldout)

**HELD-OUT set: written after tuning, scored once, rules not changed afterwards.**

24 explanations: 16 BAD, 8 GOOD. Positive class = BAD (should be rejected).
Cases written for this evaluation plus 2 real model outputs (41 = the Phase 3 Hindi monsoon error, 71). Labels by the developer; hi / hinglish / mr / pa labels and wording still need native review.

| gate | rejected BAD (TP) | rejected GOOD (FP) | missed BAD (FN) | precision | recall | false-rejection rate |
|---|---|---|---|---|---|---|
| rules only | 4/16 | 0/8 | 12 | 100% | 25% | 0% |
| rules + sentence support | 8/16 | 0/8 | 8 | 100% | 50% | 0% |
| rules + support + model self-check | 15/16 | 0/8 | 1 | 100% | 94% | 0% |

## By language (last gate)

| lang | n | precision | recall | false-rejection rate |
|---|---|---|---|---|
| en | 15 | 100% | 100% | 0% |
| hi | 5 | 100% | 75% | 0% |
| hinglish | 4 | 100% | 100% | 0% |

## By topic (last gate)

| topic | n | recall (BAD caught) | false rejections |
|---|---|---|---|
| category | 4 | 100% | 0/1 |
| contradiction | 4 | 100% | 0/0 |
| depletion | 3 | 100% | 0/2 |
| depth_direction | 6 | 67% | 0/3 |
| pre_post_monsoon | 1 | - | 0/1 |
| seasonal | 1 | 100% | 0/0 |
| stage_formula | 2 | 100% | 0/1 |
| unsupported_cause | 2 | 100% | 0/0 |
| unsupported_claim | 1 | 100% | 0/0 |

## Every case

| id | lang | topic | label | rule hits | min sim | min overlap | rejected by | text |
|---|---|---|---|---|---|---|---|---|
| 101 | en | depth_direction | bad |  | 0.751 | 0.17 | L3 | Groundwater levels go down sharply when the monsoon rains arrive. |
| 102 | en | depth_direction | good |  | 0.704 | 0.5 | - | The monsoon recharges aquifers, so wells usually have water closer to the surface afterwards. |
| 103 | en | pre_post_monsoon | good |  | 0.86 | 0.6 | - | Before the monsoon, the groundwater table is generally at its deepest. |
| 104 | en | seasonal | bad |  | 0.797 | 0.6 | L3 | The water table is shallowest in May, just before the monsoon. |
| 105 | en | depletion | bad |  | 0.737 | 0.4 | L3 | Taking out more water than is recharged makes groundwater more plentiful. |
| 106 | en | category | bad | category_threshold | 0.713 | 0.75 | L1 | A block is Critical when its stage of extraction is below 50%. |
| 107 | en | category | good |  | 0.726 | 1.0 | - | A block is Over-exploited when extraction is more than the annual extractable resource. |
| 108 | en | stage_formula | good |  | 0.819 | 0.86 | - | Stage of extraction compares total extraction with the annual extractable resource. |
| 109 | en | stage_formula | bad | stage_formula | 0.823 | 1.0 | L1 | Stage of extraction is the extractable resource divided by the extraction. |
| 110 | en | unsupported_cause | bad |  | 0.554 | 0.2 | L2 | Over-exploitation in Rajasthan is caused mainly by urbanisation. |
| 111 | en | depletion | good |  | 0.735 | 0.67 | - | Rainwater harvesting can help to recharge groundwater in stressed areas. |
| 112 | en | unsupported_claim | bad |  | 0.642 | 0.0 | L3 | Groundwater depletion can only be solved by importing water from other states. |
| 113 | en | contradiction | bad |  | 0.58 | 0.25 | L2 | Phagi is replenished faster than it is used. |
| 114 | en | depletion | good |  | 0.644 | 0.5 | - | In Phagi, use of groundwater is greater than what is replaced each year. |
| 115 | en | contradiction | bad |  | 0.543 | 0.5 | L2 | In Todaraisingh more water is pumped out than is recharged. |
| 116 | hi | depth_direction | bad |  | 0.635 | 0.0 | - | मानसून आने पर कुओं का पानी और नीचे चला जाता है। |
| 117 | hi | depth_direction | good |  | 0.662 | 0.0 | - | मानसून की बारिश से कुओं में पानी का स्तर ऊपर आ जाता है। |
| 118 | hi | category | bad | category_threshold | 0.563 | 0.0 | L1 | गंभीर श्रेणी का मतलब है दोहन का स्तर 50% से कम। |
| 119 | hi | unsupported_cause | bad |  | 0.604 | 0.0 | L3 | भूजल में गिरावट की वजह शहरीकरण है। |
| 120 | hi | contradiction | bad |  | 0.646 | 0.57 | L3 | फागी में जितना पानी निकलता है उससे ज़्यादा भर जाता है। |
| 121 | hinglish | depth_direction | bad |  | 0.513 | 0.0 | L2 | Barsaat mein kuon ka paani aur gehra chala jata hai. |
| 122 | hinglish | depth_direction | good |  | 0.631 | 0.2 | - | Monsoon ki barish se kuon mein paani upar aata hai. |
| 123 | hinglish | category | bad | category_threshold | 0.679 | 0.5 | L1 | Critical ka matlab hai stage 50% se kam. |
| 124 | hinglish | contradiction | bad |  | 0.594 | 0.75 | L3 | Phagi mein paani nikalne se zyada recharge hota hai. |