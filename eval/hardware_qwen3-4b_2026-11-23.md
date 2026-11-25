# Hardware measurements: qwen3:4b (2026-11-23 14:40)

num_ctx 4096, temperature 0, think false unless stated. Measured by eval/measure_ollama.py.

## Versions

```
ollama version is 0.40.17
NVIDIA GeForce RTX 4050 Laptop GPU, 555.97
```

## Memory

- VRAM idle (model unloaded): 0 MiB, 6141 MiB
- VRAM with model loaded: 3133 MiB, 6141 MiB
- ollama process RAM: 81 MB idle -> 81 MB loaded

  - ollama app.exe pid 37056: 29 MB
  - ollama.exe pid 17220: 52 MB

`ollama ps`:

```
NAME        ID              SIZE      PROCESSOR    CONTEXT    RUNNER      UNTIL              
qwen3:4b    359d7dd4bcda    3.2 GB    100% GPU     4096       llamacpp    4 minutes from now
```

## Cold load

- first request: total 4647 ms, load_duration 2014.1 ms, ok=True 

## Speed (warm model)

| think | question | ok | latency ms | prompt tok | gen tok | prompt tok/s | gen tok/s | thinking chars |
|---|---|---|---|---|---|---|---|---|
| off | Is groundwater in Jodhpur district safe? | True | 2637 | 45 | 33 | 1094.9 | 61.2 | 0 |
| off | फागी ब्लॉक की हालत बताइए | True | 2738 | 58 | 39 | 1269.1 | 58.8 | 0 |
| off | Ajnala block ka recharge figure kya hai? | True | 2674 | 46 | 33 | 1015.5 | 61.0 | 0 |
| off | ਲੁਧਿਆਣਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਪਾਣੀ ਦੀ ਸਥਿਤੀ ਕੀ ਹੈ? | True | 2750 | 101 | 25 | 815.2 | 47.2 | 0 |
| off | दौंड तालुका सुरक्षित आहे का? | True | 3012 | 62 | 42 | 627.5 | 49.7 | 0 |
| on | Is groundwater in Jodhpur district safe? | False | 35998 | 45 | 2048 | 1388.9 | 60.4 | 8505 |
| on | फागी ब्लॉक की हालत बताइए | False | 36034 | 58 | 2048 | 1371.2 | 60.5 | 6649 |
| on | Ajnala block ka recharge figure kya hai? | True | 19343 | 46 | 1059 | 1069.8 | 61.8 | 4353 |

- think=false: no thinking returned in 5/5 answers -> works
- median latency think off: 2738 ms; think on (3 questions): 35998 ms
- median generation speed: 60.5 tok/s

## Correction (added after the run)

The RAM line above missed the model runner: Ollama 0.40.17 runs the model in a separate `llama-server.exe`. Measured with Get-Process while qwen3:4b was loaded: llama-server.exe working set 1363 MB, private/committed 4673 MB; ollama.exe 53 MB; ollama app.exe 29 MB. `/api/ps`: size 3,180,247,121 bytes, size_vram 3,180,247,121 (100% GPU), context_length 4096. (measure_ollama.py now includes llama-server.exe.)

`ollama run qwen3:4b --think=false` on the CLI still printed reasoning text followed by </think> in the answer; through the API (`think: false` in /api/chat) no thinking was returned (0/5), which is what llm_provider.py uses.

