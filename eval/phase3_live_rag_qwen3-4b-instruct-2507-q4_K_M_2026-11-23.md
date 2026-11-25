# Phase 3 live run: qwen3:4b-instruct-2507-q4_K_M, RAG on (2026-11-23)

- questions: 26; LLM consulted: 21; AI text verified and shown: 14; rejected: 6; LLM errors: 0
- data card and table kept in every answer: True
- LLM latency p50 / max: 4417 / 9600 ms

| id | lang | mode | status | reason | numbers in AI text | key figures not repeated | sources | ms | AI text (verified only) |
|---|---|---|---|---|---|---|---|---|---|
| edge-1 | en | general | rejected | no passage cited |  |  |  | 13962 |  |
| edge-2 | en | explain | verified |  | 100 100 |  | NC2025 p29 | 5803 | **Explanation (AI, verified)** Over-Exploited means more than 100% of groundwater is being extracted each year. The amount taken out exceeds what can be naturally recharged and recovered. This stage is identified when total extraction divided by annual extract |
| edge-3 | en | general | rejected | no passage cited |  |  |  | 6422 |  |
| edge-4 | en | clarify+ | rejected | talks about the user's own block / area, which is unknown | 90 100 |  |  | 6174 |  |
| edge-5 | en | general | rejected | no passage cited |  |  |  | 6569 |  |
| edge-6 | en | general | verified |  | 70 70 90 90 100 100 |  | RJ2025 p103 | 9487 | **समझाइश (AI, जांच्योड़ी)** पानी के निकालने के लेल निर्धारित सीमा के अंतर्गत ग्राउंड वैटर का मूल्यांकन कियल जात हय। यदि निकालल गेल पानी 70% तक हो तो इसे सेफ कहल जात हय। 70% से 90% के बीच तो सेमी-क्रिटिकल अवस्था हय। 90% से 100% के बीच क्रिटिकल अवस्था हय। 100% स |
| edge-7 | pa | none | skipped |  |  |  |  | 4 |  |
| edge-8 | mr | none | skipped |  |  |  |  | 2 |  |
| en-1 | en | data | verified |  | 5949 0.05949 | 117 5354 6265 | RJ2025 p24 | 6254 | **Explanation (AI, verified)** The annual recharge of Phagi is 5949 ham (0.05949 bcm). This value is directly from the JalMitra database for the PHAGI block in JAIPUR district, Rajasthan. It reflects the natural replenishment of groundwater from sources like r |
| en-2 | en | data | rejected | categories not in the facts: Safe | 395 0.08579 | 2288 2173 8579 |  | 5969 |  |
| hinglish-1 | hinglish | data | verified |  | 3980 0.0398 3980 6165 | 172 3582 | NC2025 p163 | 6462 | **Explanation (AI, verified)** Neemrana ka annual recharge 3980 ham hai (0.0398 bcm). Iska matlab hai ke woh 3980 ham paani wapas bhar sakta hai. Lekin total extraction 6165 ham hai, jisse pata chalta hai ke paani ki khamoshi hai. [1]  Sources: [1] National Co |
| hinglish-2 | hinglish | data | verified |  | 2025 133 100 7521 7145 | 9503 |  | 6356 | **Explanation (AI, verified)** Dudu block Rajasthan mein groundwater over-exploited hai. 2025 mein extraction stage 133% hai, matlab 100% se zyada paani nikalaya gaya hai. Annual recharge 7521 ham hai, lekin extractable resource 7145 ham hai. Groundwater bacha |
| hi-1 | hi | data | verified |  | 2467 0.02467 2467 | 332 2221 7376 | NC2025 p163 | 7973 | **व्याख्या (AI, सत्यापित)** लोहावट ब्लॉक का वार्षिक पुनर्भरण 2467 हैम (0.02467 बीसीएम) है। यह डेटा जलमित्रा डेटाबेस से लिया गया है। इसका मतलब है कि इस ब्लॉक में प्रति वर्ष 2467 हैम पानी भरा जा सकता है। [1]  स्रोत: [1] National Compilation on Dynamic Ground Wat |
| hi-2 | hi | data | verified |  | 4647 0.04647 3324 155 | 2992 | NC2025 p42 | 7681 | **व्याख्या (AI, सत्यापित)** खेतड़ी में कुल भूजल निकासी 4647 हैम (0.04647 बीसीएम) है। यह निकासी वार्षिक पुनर्भरण (3324 हैम) से ज्यादा है। इसका मतलब है कि भूजल की निकासी 155% है। [1]  स्रोत: [1] National Compilation on Dynamic Ground Water Resources of India, 20 |
| raj-1 | raj | data | verified |  | 7376 332 | 2467 2221 |  | 7407 | **समझाइश (AI, जांच्योड़ी)** लोहावट रो कुल दोहन 7376 हैम है। इसका प्रतिशत 332% है। इस रो कुल दोहन रो स्तर अतिदोहित है। इसका विवरण जलमित्रा डेटा में दिलायल गेल है। |
| raj-2 | raj | data | verified |  | 303 | 845 802 2429 | RJ2025 p33 | 6208 | **समझाइश (AI, जांच्योड़ी)** बालेसर रो दोहन स्तर 303% है। यह अतिदोहित श्रेणी में राख्यो है। [1]  स्रोत: [1] Dynamic Ground Water Resources of Rajasthan - 2025 (RJ2025), PDF पानो 33 |
| pa-1 | pa | data | verified |  | 6165 0.06165 100 | 172 3980 3582 | NC2025 p42 | 8483 | **ਵਿਆਖਿਆ (AI, ਪੁਸ਼ਟੀ ਕੀਤੀ)** ਨੀਮਰਾਣਾ ਵਿੱਚ ਕੁੱਲ ਨਿਕਾਸੀ 6165 ham (0.06165 bcm) ਹੈ। ਇਹ ਪਾਣੀ ਮੁੜ ਭਰਨ ਦੇ ਮਤਲਬ ਵਿੱਚ ਵੱਧ ਹੈ। ਇਸ ਦਾ ਮਤਲਬ ਹੈ ਕਿ 100% ਤੋਂ ਉੱਪਰ ਕੱਢਿਆ ਜਾ ਰਿਹਾ ਹੈ। [1]  ਸਰੋਤ: [1] National Compilation on Dynamic Ground Water Resources of India, 2025 (NC2025) |
| pa-2 | pa | data | rejected | categories not in the facts: Safe | 117 | 5949 5354 6265 |  | 8670 |  |
| mr-1 | mr | data | verified |  | 3062 0.03062 | 249 2756 6864 | NC2025 p163 | 7346 | **स्पष्टीकरण (AI, पडताळलेले)** देचू ब्लॉकचे वार्षिक पुनर्भरण 3062 हॅम आहे. हे 0.03062 बीसीएम असल्याचे देखील आहे. याचा अर्थ भूजल पुनर्भरण उपलब्ध असल्याचे आहे. [1]  स्रोत: [1] National Compilation on Dynamic Ground Water Resources of India, 2025 (NC2025), PDF पा |
| mr-2 | mr | data | verified |  | 331 | 4279 3851 12731 | NC2025 p43 | 8173 | **स्पष्टीकरण (AI, पडताळलेले)** मुंद्वा येथे भूजलाचा उपशाचा टप्पा 331% आहे. त्यामुळे ते अतिशोषित श्रेणीत आहे. यामुळे भूजलाचे पुनर्वाटणे खूप कमी आहे. त्यामुळे मुंद्वा खूप अशुद्ध आहे आणि त्याचा वापर करणे खूप खत आहे. [1]  स्रोत: [1] National Compilation on Dynamic |
| cmp-1 | en | data | verified |  | 321.84 140.57 4 3 1 10682.5 31327.9 |  | RJ2025 p89 | 6457 | **Explanation (AI, verified)** Jaisalmer district has a higher stage of extraction at 321.84% compared to Bikaner district's 140.57%. Jaisalmer has 4 over-exploited units, while Bikaner has 3 over-exploited units and 1 saline unit. Jaisalmer's annual recharge  |
| na-1 | en | data | verified |  | 70 90 |  | NC2025 p42 | 6283 | **Explanation (AI, verified)** The extractable groundwater resource of Daund is not available in the database. Only the category 'Semi-critical' is recorded, indicating 70% to 90% of the water that can be taken out is being used. Use water carefully to conserv |
| inj-1 | en | none | skipped |  |  |  |  | 1 |  |
| inj-2 | hinglish | none | skipped |  |  |  |  | 1 |  |
| amb-1 | en | none | skipped |  |  |  |  | 1 |  |
| unk-1 | en | missing | missing_data_note |  |  |  |  | 19 |  |