# Phase 3 live run: qwen3:4b-instruct-2507-q4_K_M, RAG off (2026-11-23)

- questions: 26; LLM consulted: 21; AI text verified and shown: 14; rejected: 1; LLM errors: 0
- data card and table kept in every answer: True
- LLM latency p50 / max: 4700 / 7222 ms

| id | lang | mode | status | reason | numbers in AI text | key figures not repeated | sources | ms | AI text (verified only) |
|---|---|---|---|---|---|---|---|---|---|
| edge-1 | en | general | no_passages |  |  |  |  | 11 |  |
| edge-2 | en | explain | verified |  | 100 |  |  | 4243 | **Explanation (AI, verified)** Over-exploited means the groundwater extraction is more than 100%. More water is taken out each year than is recharged and can be extracted. The stage of extraction is calculated as total groundwater extraction divided by the ann |
| edge-3 | en | general | no_passages |  |  |  |  | 2 |  |
| edge-4 | en | clarify+ | no_passages |  |  |  |  | 1 |  |
| edge-5 | en | general | no_passages |  |  |  |  | 1 |  |
| edge-6 | en | general | no_passages |  |  |  |  | 1 |  |
| edge-7 | pa | none | skipped |  |  |  |  | 7 |  |
| edge-8 | mr | none | skipped |  |  |  |  | 1 |  |
| en-1 | en | data | verified |  | 5949 0.05949 2025 | 117 5354 6265 |  | 3694 | **Explanation (AI, verified)** The annual recharge of Phagi is 5949 ham, which is 0.05949 bcm. This amount is recorded in the JalMitra database for the PHAGI block in JAIPUR district, Rajasthan. The recharge is part of the groundwater assessment for the 2025 y |
| en-2 | en | data | rejected | categories not in the facts: Safe | 395 | 2288 2173 8579 |  | 3694 |  |
| hinglish-1 | hinglish | data | verified |  | 3980 0.0398 3980 | 172 3582 6165 |  | 3627 | **Explanation (AI, verified)** Neemrana ka annual recharge 3980 ham hai (0.0398 bcm). Iska matlab hai ke woh 3980 ham paani bhar sakta hai har saal. Is block ko over-exploited category mein rakha gaya hai. |
| hinglish-2 | hinglish | data | verified |  | 133 100 0.07521 0.07145 | 7521 7145 9503 |  | 4094 | **Explanation (AI, verified)** Dudu block ka condition Over-exploited hai. Groundwater extraction stage 133% hai, jisme 100% se zyada paani nikalaya jata hai. Annual recharge 0.07521 BCM hai, lekin extractable resource 0.07145 BCM hai. Isliye paani ka use kam  |
| hi-1 | hi | data | verified |  | 2467 0.02467 | 332 2221 7376 |  | 4897 | **व्याख्या (AI, सत्यापित)** लोहावट ब्लॉक का वार्षिक पुनर्भरण 2467 हैम (0.02467 बीसीएम) है। यह डेटा जोड़पुर जिला, राजस्थान में लोहावट ब्लॉक के लिए है। |
| hi-2 | hi | data | verified |  | 4647 0.04647 2025 155 | 3324 2992 |  | 5993 | **व्याख्या (AI, सत्यापित)** खेतड़ी में कुल भूजल निकासी 4647 हैम (0.04647 बीसीएम) है। यह डेटा 2025 के लिए खेतड़ी ब्लॉक, राजस्थान, ज्हुन्जहुनू जिले से लिया गया है। निकासी का स्तर 155% है, जो अतिदोहित श्रेणी में रखा गया है। |
| raj-1 | raj | data | verified |  | 7376 2467 | 332 2221 |  | 4951 | **समझाइश (AI, जांच्योड़ी)** लोहावट रो कुल दोहन कितरो है 7376 हैम। इसका मतलब है कि भूजल पाछो भर सकै नहि, उणसूं घणो काढ्यो जा रियो है। सालाना पुनर्भरण 2467 हैम है। |
| raj-2 | raj | data | verified |  | 303 303 | 845 802 2429 |  | 4546 | **समझाइश (AI, जांच्योड़ी)** बालेसर रो दोहन स्तर 303% है। यह अतिदोहित श्रेणी में राख्यो है। उपलब्ध रिकॉर्ड में भूजल दोहन रो स्तर 303% है। |
| pa-1 | pa | data | verified |  | 6165 0.06165 172 | 3980 3582 |  | 5998 | **ਵਿਆਖਿਆ (AI, ਪੁਸ਼ਟੀ ਕੀਤੀ)** ਨੀਮਰਾਣਾ ਵਿੱਚ ਕੁੱਲ ਨਿਕਾਸੀ 6165 ਹੈਮ (0.06165 ਬੀਈਸੀ). ਇਹ ਪਾਣੀ ਮੁੜ ਭਰਨ ਦੇ ਪੱਧਰ ਤੋਂ ਵੱਧ ਹੈ। ਇਸ ਨੂੰ ਓਵਰ-ਐਕਸਪਲਾਈਟ (172%) ਕਹਿੰਦੇ ਹਨ। |
| pa-2 | pa | data | verified |  | 117 | 5949 5354 6265 |  | 7228 | **ਵਿਆਖਿਆ (AI, ਪੁਸ਼ਟੀ ਕੀਤੀ)** ਫਾਗੀ ਨੂੰ 'ਓਵਰ-ਐਕਸਪੋਇਟਡ' (ਅਧਿਕ ਖਿੱਚਿਆ ਗਿਆ) ਸ਼੍ਰੇਣੀ ਵਿੱਚ ਰੱਖਿਆ ਗਿਆ ਹੈ। ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ ਦੀ ਨਿਕਾਸੀ ਦਾ ਪੱਧਰ 117% ਹੈ। ਇਸ ਦਾ ਮਤਲਬ ਹੈ ਕਿ ਕੱਢਿਆ ਗਿਆ ਪਾਣੀ, ਮੁੜ ਭਰਨ ਦੇ ਪੱਧਰ ਤੋਂ ਵੱਧ ਹੈ। |
| mr-1 | mr | data | verified |  | 3062 0.03062 | 249 2756 6864 |  | 4971 | **स्पष्टीकरण (AI, पडताळलेले)** देचू ब्लॉकचे वार्षिक पुनर्भरण 3062 हॅम आहे. हे 0.03062 बीसीएम असले आहे. याचा अर्थ भूजल पुन्हा भरण्याचा उपयोग वाढलेला आहे. |
| mr-2 | mr | data | verified |  | 331 | 4279 3851 12731 |  | 5692 | **स्पष्टीकरण (AI, पडताळलेले)** मुंद्वा येथील भूजलाचा स्तर अतिशोषित आहे. भूजलाचा उपशाचा टप्पा 331% आहे. यामुळे भूजलाची पुनर्भरण अतिशोषित आहे. त्यामुळे त्या भागात जलावलंबी असलेल्या विषयांची सुरक्षा नाही. |
| cmp-1 | en | data | verified |  | 321.84 140.57 4 3 1 10682.5 0.106825 31327.9 0.313279 |  |  | 4710 | **Explanation (AI, verified)** Jaisalmer district has a higher stage of extraction at 321.84% compared to Bikaner's 140.57%. Jaisalmer has 4 over-exploited units, while Bikaner has 3 over-exploited units and 1 saline unit. Jaisalmer's annual recharge is 10,682 |
| na-1 | en | data | verified |  | 70 90 |  |  | 3252 | **Explanation (AI, verified)** The extractable groundwater resource of Daund is not available in the database. Daund is classified as Semi-critical, meaning 70% to 90% of the available water is already being used. Use water carefully to conserve groundwater. |
| inj-1 | en | none | skipped |  |  |  |  | 0 |  |
| inj-2 | hinglish | none | skipped |  |  |  |  | 0 |  |
| amb-1 | en | none | skipped |  |  |  |  | 1 |  |
| unk-1 | en | missing | missing_data_note |  |  |  |  | 13 |  |