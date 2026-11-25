# Semantic factuality gate: labelled evaluation (2026-11-23)

**TUNING set: the rules were developed on these cases, so these scores are optimistic.**

71 explanations: 38 BAD, 33 GOOD. Positive class = BAD (should be rejected).
Cases written for this evaluation plus 2 real model outputs (41 = the Phase 3 Hindi monsoon error, 71). Labels by the developer; hi / hinglish / mr / pa labels and wording still need native review.

| gate | rejected BAD (TP) | rejected GOOD (FP) | missed BAD (FN) | precision | recall | false-rejection rate |
|---|---|---|---|---|---|---|
| rules only | 37/38 | 0/33 | 1 | 100% | 97% | 0% |
| rules + sentence support | 38/38 | 0/33 | 0 | 100% | 100% | 0% |
| rules + support + model self-check | 38/38 | 0/33 | 0 | 100% | 100% | 0% |

## By language (last gate)

| lang | n | precision | recall | false-rejection rate |
|---|---|---|---|---|
| en | 37 | 100% | 100% | 0% |
| hi | 17 | 100% | 100% | 0% |
| hinglish | 13 | 100% | 100% | 0% |
| mr | 2 | 100% | 100% | 0% |
| pa | 2 | 100% | 100% | 0% |

## By topic (last gate)

| topic | n | recall (BAD caught) | false rejections |
|---|---|---|---|
| category | 15 | 100% | 0/9 |
| contradiction | 4 | 100% | 0/0 |
| depletion | 11 | 100% | 0/9 |
| depth_direction | 14 | 100% | 0/5 |
| figures | 1 | - | 0/1 |
| pre_post_monsoon | 4 | 100% | 0/3 |
| recharge | 3 | - | 0/3 |
| recharge_vs_extraction | 5 | 100% | 0/3 |
| seasonal | 3 | 100% | 0/0 |
| stage_formula | 2 | 100% | 0/0 |
| unsupported_cause | 6 | 100% | 0/0 |
| unsupported_claim | 3 | 100% | 0/0 |

## Support threshold sweep (rules + support)

| sim threshold | precision | recall | FPR |
|---|---|---|---|
| 0.5 | 100% | 97% | 0% |
| 0.55 | 100% | 100% | 0% |
| 0.6 | 100% | 100% | 0% |
| 0.65 | 97% | 100% | 3% |
| 0.7 | 83% | 100% | 24% |
| 0.75 | 75% | 100% | 39% |

## Every case

| id | lang | topic | label | rule hits | min sim | min overlap | rejected by | text |
|---|---|---|---|---|---|---|---|---|
| 1 | en | category | good |  | 0.783 | 1.0 | - | PHAGI block is Over-exploited, with a stage of extraction of 117%. |
| 2 | en | depletion | good |  | 0.812 | 1.0 | - | More groundwater is taken out each year than is replaced, so the stage is above 100%. |
| 3 | en | recharge_vs_extraction | good |  | 0.796 | 0.83 | - | Total extraction of 6265 ham is higher than the annual recharge of 5949 ham. |
| 4 | en | figures | good |  | 0.823 | 1.0 | - | The annual recharge of Phagi is 5949 ham (0.05949 bcm). |
| 5 | en | contradiction | bad | contradicts_figures | 0.792 | 0.8 | L1 | Annual recharge of 5949 ham is more than the extraction of 6265 ham, so the block is safe. |
| 6 | en | unsupported_cause | bad | unsupported_causal_claim; unsupported_cause | 0.68 | 0.29 | L1 | Phagi is Over-exploited because of rapid industrial growth and factories. |
| 7 | en | depletion | bad | depletion_direction | 0.627 | 0.43 | L1 | Because extraction is more than recharge, the water level in Phagi keeps rising. |
| 8 | en | category | bad | category_threshold | 0.725 | 0.75 | L1 | Over-exploited means the stage of extraction is between 70% and 90%. |
| 9 | en | stage_formula | bad | stage_formula | 0.666 | 0.71 | L1 | The stage of extraction is calculated as annual recharge divided by total extraction. |
| 10 | en | unsupported_claim | bad |  | 0.523 | 0.29 | L2 | Phagi receives heavy rainfall every year, so farmers need not worry. |
| 11 | en | recharge | good |  | 0.815 | 0.8 | - | Groundwater recharge is water that rain and other sources add to the aquifer each year. |
| 12 | en | pre_post_monsoon | good |  | 0.939 | 0.89 | - | The water table is usually deeper before the monsoon and becomes shallower during the monsoon. |
| 13 | en | depth_direction | good |  | 0.759 | 0.67 | - | During the monsoon, recharge from rainfall raises the groundwater level. |
| 14 | en | recharge | good |  | 0.873 | 0.75 | - | Rainfall is the main source of groundwater recharge. |
| 15 | en | category | good |  | 0.885 | 1.0 | - | Semi-critical means the stage of extraction is more than 70% and up to 90%. |
| 16 | en | category | good |  | 0.858 | 1.0 | - | Safe means the stage of extraction is up to 70%. |
| 17 | en | depletion | good |  | 0.736 | 0.8 | - | When extraction is more than recharge, groundwater levels fall over time. |
| 18 | en | category | good |  | 0.881 | 1.0 | - | Critical means the stage of extraction is more than 90% and up to 100%. |
| 19 | en | depth_direction | bad | monsoon_direction | 0.832 | 1.0 | L1 | During the monsoon the water table becomes deeper. |
| 20 | en | seasonal | bad | monsoon_direction; unsupported_causal_claim | 0.806 | 0.17 | L1 | In the rainy season the groundwater level falls because more water is used. |
| 21 | en | depth_direction | bad | monsoon_direction | 0.738 | 0.6 | L1 | Depth to water increases during the monsoon months. |
| 22 | en | recharge_vs_extraction | bad | recharge_direction | 0.737 | 0.5 | L1 | Recharge lowers the water level in the aquifer. |
| 23 | en | depletion | bad | depletion_direction | 0.74 | 0.4 | L1 | If extraction exceeds recharge the groundwater situation improves. |
| 24 | en | category | bad | category_threshold | 0.778 | 1.0 | L1 | Safe means the stage of extraction is more than 100%. |
| 25 | en | unsupported_cause | bad | unsupported_causal_claim; unsupported_cause | 0.759 | 0.14 | L1 | Groundwater is falling mainly because of climate change and global warming. |
| 26 | en | stage_formula | bad | stage_formula | 0.728 | 1.0 | L1 | The stage of extraction is recharge divided by extraction, in percent. |
| 27 | en | unsupported_claim | bad | rain_irrelevant | 0.634 | 0.5 | L1 | Monsoon rains do not matter for groundwater in India. |
| 28 | en | depth_direction | bad | extraction_direction | 0.762 | 0.0 | L1 | Pumping more groundwater raises the water level. |
| 29 | en | depletion | good |  | 0.778 | 0.62 | - | Rainwater harvesting and artificial recharge structures can help reduce groundwater depletion. |
| 30 | en | depletion | good |  | 0.825 | 0.5 | - | Restricting new wells in over-exploited areas is one recommended measure. |
| 31 | en | unsupported_claim | bad | wrong_remedy | 0.622 | 0.0 | L1 | Building more borewells is the best way to reduce groundwater depletion. |
| 32 | en | seasonal | bad | wrong_remedy | 0.64 | 0.0 | L1 | Depletion can be reduced by pumping more water during the monsoon. |
| 33 | hi | category | good |  | 0.674 | 0.71 | - | फागी ब्लॉक अतिदोहित श्रेणी में है, यहाँ दोहन का स्तर 117% है। |
| 34 | hi | depletion | good |  | 0.684 | 0.62 | - | यहाँ जितना पानी हर साल भरता है उससे ज़्यादा पानी निकाला जा रहा है। |
| 35 | hi | contradiction | bad | contradicts_figures | 0.707 | 0.33 | L1 | फागी में पुनर्भरण 5949 हैम निकासी 6265 हैम से अधिक है, इसलिए स्थिति ठीक है। |
| 36 | hi | unsupported_cause | bad | unsupported_cause | 0.527 | 0.29 | L1 | फागी अतिदोहित है क्योंकि वहाँ बहुत सारे कारखाने हैं। |
| 37 | hi | depth_direction | bad | extraction_direction | 0.664 | 0.67 | L1 | दोहन ज़्यादा होने से भूजल स्तर बढ़ता है। |
| 38 | hi | category | bad | category_threshold | 0.638 | 0.83 | L1 | अतिदोहित का मतलब है कि दोहन का स्तर 70% से 90% के बीच है। |
| 39 | hi | depth_direction | good |  | 0.693 | 0.0 | - | मानसून के दौरान बारिश से पुनर्भरण होता है और भूजल स्तर ऊपर आता है। |
| 40 | hi | pre_post_monsoon | good |  | 0.747 | 0.0 | - | मानसून से पहले भूजल तल आमतौर पर गहरा होता है। |
| 41 | hi | pre_post_monsoon | bad | monsoon_direction | 0.741 | 0.0 | L1 | बरसात के मौसम में भूजल तल गहरा होता है और बरसात के बाद इसका स्तर घटता है। |
| 42 | hi | depth_direction | bad | monsoon_direction | 0.748 | 0.0 | L1 | बारिश के मौसम में जल स्तर नीचे चला जाता है। |
| 43 | hi | category | good |  | 0.678 | 0.0 | - | सुरक्षित श्रेणी का मतलब है दोहन का स्तर 70% तक। |
| 44 | hi | category | bad | category_threshold | 0.608 | 0.0 | L1 | सुरक्षित का मतलब है दोहन 100% से अधिक। |
| 45 | hi | recharge | good |  | 0.696 | 0.0 | - | भूजल पुनर्भरण वह पानी है जो बारिश और अन्य स्रोतों से हर साल ज़मीन में जाता है। |
| 46 | hi | recharge_vs_extraction | bad | recharge_direction | 0.619 | 0.0 | L1 | पुनर्भरण से भूजल स्तर नीचे गिरता है। |
| 47 | hi | unsupported_cause | bad | unsupported_cause | 0.599 | 0.0 | L1 | भूजल घटने का मुख्य कारण जलवायु परिवर्तन है। |
| 48 | hi | depletion | good |  | 0.623 | 0.0 | - | जब निकासी पुनर्भरण से अधिक होती है तो भूजल स्तर गिरता है। |
| 49 | hi | depletion | good |  | 0.675 | 0.0 | - | वर्षा जल संचयन और कृत्रिम पुनर्भरण से भूजल की कमी कम की जा सकती है। |
| 50 | hinglish | category | good |  | 0.738 | 1.0 | - | Phagi block Over-exploited category mein hai, extraction stage 117% hai. |
| 51 | hinglish | depletion | good |  | 0.719 | 0.5 | - | Yahan jitna paani har saal bharta hai usse zyada paani nikala ja raha hai. |
| 52 | hinglish | contradiction | bad | contradicts_figures | 0.62 | 0.67 | L1 | Phagi mein recharge extraction se zyada hai, isliye block safe hai. |
| 53 | hinglish | unsupported_cause | bad | unsupported_cause | 0.636 | 0.4 | L1 | Phagi Over-exploited hai kyunki wahan factory bahut hain. |
| 54 | hinglish | category | bad | category_threshold | 0.687 | 0.75 | L1 | Over-exploited ka matlab stage 70% se 90% ke beech hai. |
| 55 | hinglish | depth_direction | good |  | 0.677 | 0.33 | - | Monsoon mein barish se recharge hota hai aur water level upar aata hai. |
| 56 | hinglish | depth_direction | bad | monsoon_direction | 0.702 | 0.2 | L1 | Monsoon mein water level neeche chala jata hai. |
| 57 | hinglish | seasonal | bad | monsoon_direction | 0.528 | 0.0 | L1 | Barish ke mausam mein paani ka level girta hai. |
| 58 | hinglish | pre_post_monsoon | good |  | 0.658 | 0.17 | - | Monsoon se pehle water level aam taur par gehra hota hai. |
| 59 | hinglish | depth_direction | bad | extraction_direction | 0.696 | 0.2 | L1 | Extraction zyada hone se water level badhta hai. |
| 60 | hinglish | category | good |  | 0.803 | 0.6 | - | Safe ka matlab hai stage of extraction 70% tak. |
| 61 | hinglish | unsupported_cause | bad | unsupported_causal_claim; unsupported_cause | 0.653 | 0.0 | L1 | Groundwater kam hone ka sabse bada karan jalvayu parivartan hai. |
| 62 | hinglish | depletion | good |  | 0.678 | 0.33 | - | Jab extraction recharge se zyada hota hai to water level girta hai. |
| 63 | en | category | good |  | 0.76 | 1.0 | - | TODARAISINGH is Safe; its stage of extraction is 64%. |
| 64 | en | recharge_vs_extraction | good |  | 0.814 | 1.0 | - | Annual recharge of 6079 ham is more than the extraction of 3627 ham. |
| 65 | en | contradiction | bad | contradicts_figures | 0.76 | 1.0 | L1 | Extraction of 3627 ham is more than the recharge of 6079 ham. |
| 66 | en | category | bad | category_threshold | 0.705 | 0.75 | L1 | TODARAISINGH is Safe because its stage is 95%. |
| 67 | mr | depth_direction | bad | monsoon_direction | 0.733 | 0.0 | L1 | पावसाळ्यात भूजल पातळी खोल जाते. |
| 68 | mr | depth_direction | good |  | 0.715 | 0.0 | - | पावसाळ्यात पुनर्भरणामुळे भूजल पातळी वर येते. |
| 69 | pa | depth_direction | bad | monsoon_direction | 0.65 | 0.0 | L1 | ਮਾਨਸੂਨ ਵਿੱਚ ਪਾਣੀ ਦਾ ਪੱਧਰ ਹੇਠਾਂ ਜਾਂਦਾ ਹੈ। |
| 70 | pa | depth_direction | good |  | 0.7 | 0.0 | - | ਮਾਨਸੂਨ ਵਿੱਚ ਮੀਂਹ ਨਾਲ ਪਾਣੀ ਦਾ ਪੱਧਰ ਉੱਪਰ ਆਉਂਦਾ ਹੈ। |
| 71 | en | recharge_vs_extraction | good |  | 0.72 | 0.44 | - | Recharge is the amount of water that naturally enters the ground, like from rainfall or streams, to refill aqu |