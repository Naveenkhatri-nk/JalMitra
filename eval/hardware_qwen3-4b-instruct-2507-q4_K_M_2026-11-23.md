# Hardware measurements: qwen3:4b-instruct-2507-q4_K_M (2026-11-23 15:41)

num_ctx 4096, temperature 0, think false unless stated. Measured by eval/measure_ollama.py.

## Versions

```
ollama version is 0.40.17
NVIDIA GeForce RTX 4050 Laptop GPU, 555.97
```

## Memory

- VRAM idle (model unloaded): 1391 MiB, 6141 MiB
- VRAM with model loaded: 4524 MiB, 6141 MiB
- ollama process RAM: 45 MB idle -> 783 MB loaded

  - ollama app.exe pid 37056: 14 MB
  - ollama.exe pid 17220: 32 MB
  - llama-server.exe pid 36992: 737 MB

`ollama ps`:

```
NAME                             ID              SIZE      PROCESSOR    CONTEXT    RUNNER      UNTIL              
qwen3:4b-instruct-2507-q4_K_M    0edcdef34593    3.2 GB    100% GPU     4096       llamacpp    4 minutes from now
```

## Cold load

- first request: total 6933 ms, load_duration 4168.3 ms, ok=True 

## Speed (warm model)

| think | question | ok | latency ms | prompt tok | gen tok | prompt tok/s | gen tok/s | thinking chars |
|---|---|---|---|---|---|---|---|---|
| off | Is groundwater in Jodhpur district safe? | True | 2745 | 43 | 36 | 2251.3 | 54.1 | 0 |
| off | फागी ब्लॉक की हालत बताइए | True | 2820 | 56 | 40 | 2043.8 | 57.1 | 0 |
| off | Ajnala block ka recharge figure kya hai? | True | 2736 | 44 | 34 | 1594.2 | 55.3 | 0 |
| off | ਲੁਧਿਆਣਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਪਾਣੀ ਦੀ ਸਥਿਤੀ ਕੀ ਹੈ? | True | 2852 | 99 | 43 | 2626.0 | 57.5 | 0 |
| off | दौंड तालुका सुरक्षित आहे का? | True | 2835 | 60 | 41 | 2290.1 | 56.7 | 0 |
| on | Is groundwater in Jodhpur district safe? | True | 2759 | 43 | 36 | 2429.4 | 55.3 | 0 |
| on | फागी ब्लॉक की हालत बताइए | True | 2757 | 56 | 40 | 3200.0 | 57.3 | 0 |
| on | Ajnala block ka recharge figure kya hai? | True | 2680 | 44 | 34 | 2471.9 | 55.3 | 0 |

- think=false: no thinking returned in 5/5 answers -> works
- median latency think off: 2820 ms; think on (3 questions): 2757 ms
- median generation speed: 56.0 tok/s

## Note (added after the run)

During this measurement VALORANT-Win64-Shipping.exe was also running on the GPU (nvidia-smi compute apps), which explains the 1391 MiB 'idle' VRAM. The model's own allocation is 4524 - 1391 = 3133 MiB, identical to qwen3:4b (/api/ps size_vram 3,180,247,121 bytes, 100% GPU). Cold load (4.2 s load_duration vs 2.0 s for qwen3:4b) and latencies may be slower than on an idle laptop. RAM after the run (Get-Process): llama-server.exe 798 MB working set / 4106 MB committed, ollama.exe 31 MB, ollama app.exe 14 MB. This model has no thinking mode, so the 'think on' rows behave the same as 'off'.

