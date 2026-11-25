# How to run JalMitra on your own laptop (Windows)

This takes about 30–45 minutes the first time, mostly for downloads (about 4 GB). After that, starting
JalMitra is a double-click.

## What your laptop needs

| | Needed | Why |
|---|---|---|
| Windows 10 or 11 | yes | the start script is a Windows `.bat` file |
| Free disk space | about 6 GB | Python packages and the two AI models |
| RAM | 8 GB minimum, 16 GB better | the AI model loads into memory |
| NVIDIA graphics card with 4 GB+ memory | strongly recommended | on naveen's RTX 4050 a reply takes about 13 s. Without a GPU, the AI runs on the processor and can take a minute or more per reply, and some replies may time out. |
| Internet | only for the setup | after setup, JalMitra runs fully offline |

If your laptop has no NVIDIA GPU, you can still set it up and try it. For the presentation, the demo runs on
naveen's laptop.

## Step 1. Get the project (GitHub Desktop)

1. Accept naveen's collaborator invite (check your email).
2. In GitHub Desktop: **File > Clone repository… > GitHub.com** tab > `Naveenkhatri-nk/JalMitra`.
3. Choose a folder, for example `D:\JalMitra`, and click **Clone**.

## Step 2. Install Python

1. Download **Python 3.14** from https://www.python.org/downloads/windows/ (naveen uses 3.14.7).
2. Run the installer and **tick "Add python.exe to PATH"** at the bottom of the first screen. Then click
   **Install Now**.

## Step 3. Install the Python packages

1. Open the JalMitra folder in File Explorer. Click the address bar, type `powershell` and press Enter. A
   PowerShell window opens in that folder.
2. Run these lines one by one:

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-llm.txt
```

The last line downloads Streamlit, pandas, chromadb and the other packages. It takes a few minutes.

## Step 4. Install Ollama and the two AI models

1. Download Ollama from https://ollama.com/download and install it. It runs in the system tray.
2. In PowerShell, run:

```
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama pull bge-m3
```

The first model is the AI that writes replies (2.5 GB). The second is the document search model (1.2 GB).

## Step 5. Start JalMitra

Double-click **`START_JALMITRA.bat`** in the JalMitra folder. It checks everything, loads the model, and opens
http://localhost:8501 in your browser. Wait for the green **"Local AI connected"** light, then ask
"Is Osian block safe?".

To stop it, double-click **`STOP_JALMITRA.bat`**.

## If something goes wrong

| Message | Fix |
|---|---|
| `.venv was not found` | Step 3 was skipped, or you ran it in a different folder. |
| `streamlit or chromadb is missing` | Run the `pip install` line from Step 3 again. |
| `Ollama is not installed` | Step 4. Restart the laptop after installing. |
| `The AI model ... is not installed` | Run the `ollama pull` lines from Step 4. |
| "Local AI service is not available" in the chat | Open the Ollama app from the Start menu, then run `START_JALMITRA.bat` again. |
| Replies are very slow or say "could not be verified" | Normal on a laptop without an NVIDIA GPU. Close games and other heavy apps and try again. |
| `python` is not recognised | Reinstall Python with "Add python.exe to PATH" ticked. |

Nothing in JalMitra needs an API key or a `.env` file.
