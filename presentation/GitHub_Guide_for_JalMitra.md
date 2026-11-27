# Putting JalMitra on GitHub: a step-by-step guide for Windows

This guide is written for someone who has never used GitHub. Follow it in order. It takes about 45 minutes the first time.

---

## Part 0. What are Git and GitHub? (2-minute read)

- **Git** is a program on your laptop that saves "snapshots" of your project folder. Each snapshot is called a **commit**. If something breaks, you can go back to an older snapshot.
- **GitHub** (github.com) is a website that stores a copy of those snapshots online. It is like Google Drive, but made for code: everyone can see who changed what, and when.
- A **repository** (or **repo**) is one project on GitHub. Ours will be called `JalMitra`.
- **Push** means sending your new commits from the laptop to GitHub. **Pull** (or **Fetch**) means getting your teammates' commits from GitHub onto your laptop.
- A **collaborator** is a teammate who is allowed to push to your repo.
- **GitHub Desktop** is a free app with buttons for all of this, so you don't need to type commands.

Why this matters for the presentation: the teacher can open the repo and see the code, the history of commits, and which member made which commit.

---

## Part 1. Create a GitHub account (each of the 7 members does this)

1. Open **https://github.com/signup** in Chrome.
2. Enter your email, a password, and a username. Pick a professional username (for example `naveen-khatri-jecrc`, not `cooldude123`), because it appears on every commit.
3. Solve the puzzle, then type the code GitHub emails you.
4. On "What do you want to do?" you can click **Skip personalization**.
5. Every member sends their **GitHub username** to naveen on the group chat. naveen will need all 6 teammates' usernames in Part 6.

---

## Part 2. Install GitHub Desktop (naveen first; the others in Part 7)

1. Open **https://desktop.github.com** and click **Download for Windows**.
2. Run `GitHubDesktopSetup-x64.exe`. It installs by itself (Git is included inside it, so you don't need a separate Git install).
3. When it opens, click **Sign in to GitHub.com**. Your browser opens; click **Authorize desktop**. Go back to the app.
4. On "Configure Git", keep **Use my GitHub account name and email** and click **Finish**.

---

## Part 3. Prepare the E:\JalMitra folder before uploading (very important)

Some files must **never** go to GitHub, and some are too big for it.

| Do NOT upload | Why |
|---|---|
| `.env` | It holds secret settings, such as the old Gemini API key. Anyone who sees it could use it. |
| `.venv\` | Python's installed packages (hundreds of MB). Teammates re-create it with `pip install`. |
| `__pycache__\`, `*.pyc` | Temporary files Python creates by itself. |
| `backup\` | Old copies of the app. Git's history now does this job. |
| `data\groundwater_monitoring.db` (about 1 GB), `data\monitoring\` raw PDFs and scratch files (about 7 GB) | GitHub refuses any file over 100 MB, and these can be re-downloaded with the scripts in `ingest\`. |
| `data\rag\` | The AI search index. It is rebuilt with `python build_rag_index.py`. |
| `data\chat_history\`, `user_data\` | Private chats and uploaded soil cards. |
| `screenshots_v3\`, `screenshots_v4\`, `screenshots_v5\` | Old screenshots. The current ones in `docs\screenshots\` are kept. |

These **small** databases **are** uploaded, because the app needs them to run: `data\groundwater.db` (3.4 MB), `data\knowledge.db`, `data\observations.db` and `data\monitoring\gwra_blocks_2025.db` (2.8 MB).

**Do this:**

1. Close JalMitra if it is running (`STOP_JALMITRA.bat`).
2. Open `E:\JalMitra` in File Explorer. Click **View > Show > File name extensions** and **Hidden items**, so you can see files like `.gitignore`.
3. **Already done for you:** I replaced `E:\JalMitra\.gitignore` with the full list above (the same text is in `gitignore_for_JalMitra.txt`, next to this guide). Open it with Notepad (right-click > Open with > Notepad) just to see it. The file must be named exactly `.gitignore`, with no `.txt` at the end.
   - I tested these rules: `.env`, `backup\`, the 1 GB database and the raw PDFs are left out, and the 4 small databases are kept.
4. Fix one wrong line in `README.md`: near the top it says **"JalMitra uses no AI model (since 2.0)"**. That is out of date. Replace that paragraph with:
   > JalMitra 4.0 uses a local AI model (Qwen3-4B Instruct, run by Ollama on this laptop) to write every reply. Every reply is checked against the official database before it is shown, and the official figures are always displayed from the database, never from the AI.

---

## Part 4. Create the repository and upload the project (naveen only)

1. In GitHub Desktop: **File > Add local repository…**
2. Click **Choose…**, pick `E:\JalMitra`, then **Add repository**.
3. It will say "This directory does not appear to be a Git repository". Click the blue link **create a repository**.
4. In the window that opens:
   - **Name:** `JalMitra`
   - **Description:** `Multilingual groundwater chatbot with a local AI model and fact-checking, JECRC University Prompt Engineering project`
   - **Git ignore:** leave as **None** (we already made our own).
   - **License:** None.
   - Click **Create repository**.
5. **Check before uploading.** On the left, open the **History** tab and click the first commit. Scroll the file list and make sure you do **not** see `.env`, `.venv`, `backup` or `groundwater_monitoring.db`. If you see any of them, stop and check that `.gitignore` is in E:\JalMitra (Part 3 step 3).
6. Click **Publish repository** at the top.
   - Name: `JalMitra`.
   - **Keep this code private**: tick it for now. You can make it public after the presentation (Settings > Danger Zone > Change visibility) if your teacher wants a public link.
   - Click **Publish repository**. The upload takes a few minutes (about 10 to 20 MB).
7. Click **Repository > View on GitHub**. You should see your files on github.com. Copy the address (it looks like `https://github.com/<your-username>/JalMitra`). Put it on the last slide of the presentation.

---

## Part 5. Add a good README cover (optional, 5 minutes)

GitHub shows `README.md` as the front page of the repo. At the very top of `README.md`, add:

```
# JalMitra: Multilingual Groundwater Assistant
Prompt Engineering project, JECRC University (2026)

Team (Section DC): Naveen Khatri, Rohit Sharma, Aryan Jangir, Himanshu Yadav, Aryan Sharma, Garvit Khandal

How to run: double-click START_JALMITRA.bat (needs Python and Ollama with qwen3:4b-instruct-2507-q4_K_M)
```

Save, then make a commit as in Part 8.

---

## Part 6. Add the 6 teammates as collaborators (naveen only)

1. On github.com, open your `JalMitra` repo.
2. Click **Settings** (top right of the repo, with the gear icon) > **Collaborators** (left menu). GitHub may ask for your password.
3. Click **Add people**, type a teammate's **username**, select them, and click **Add … to this repository**.
4. Repeat for all 6 teammates: Rohit, Aryan Jangir, Himanshu, Aryan Sharma, Param and Garvit.
5. Each teammate gets an email **and** a notice on github.com (bell icon). They must click **Accept invitation**. The invite expires after 7 days, so tell them to accept today.

---

## Part 7. Each teammate gets the project on their laptop (members 2 to 7, optional)

1. Install GitHub Desktop and sign in (Part 2).
2. In GitHub Desktop: **File > Clone repository…** > tab **GitHub.com** > pick `Naveenkhatri-nk/JalMitra` > choose a folder such as `D:\JalMitra` > **Clone**.
3. To run the app on their own laptop (optional), open PowerShell in that folder and run:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-llm.txt
   ```
   Then install Ollama from https://ollama.com, run `ollama pull qwen3:4b-instruct-2507-q4_K_M` and `ollama pull bge-m3`, and run `python build_rag_index.py` once. The AI needs a laptop with a decent GPU. For the presentation, the demo runs on naveen's laptop, so this step is optional.

---

## Part 8. How each member makes a commit (everyone)

Every member should make at least one real commit about their own part, so that the GitHub history shows the group's work. Each member uploads their own notes file about their part (Part 10).

**The daily routine (always in this order):**

1. Open GitHub Desktop and choose the `JalMitra` repository (top left).
2. Click **Fetch origin** (top bar). If it changes to **Pull origin**, click it. This brings in your teammates' latest work. **Always do this first**, before you edit anything.
3. Make your change in VS Code or Notepad and **save the file**.
4. Go back to GitHub Desktop. The **Changes** tab lists the files you changed. Green lines are added, red lines are removed.
5. At the bottom left, write a short **Summary** of what you did, starting with a verb. Examples:
   - `Add data sources explanation for the data section`
   - `Improve system prompt rule about rounding numbers`
   - `Add Hindi test questions for the 300-question set`
6. Click **Commit to main**.
7. Click **Push origin** (top bar). Your commit is now on GitHub.

**Rules so nobody loses work:**

- Fetch/Pull before you start, and push as soon as you finish.
- Two people should not edit the **same file** on the same day. Split by files (each member has their own files, see the role list).
- Never commit `.env`, passwords, or big files. If GitHub Desktop shows a file you don't recognise in Changes, untick its checkbox.
- If GitHub Desktop says **"Resolve conflicts"**: don't panic. Open the file it names, look for the lines between `<<<<<<<` and `>>>>>>>`, keep the right version, delete the marker lines, save, then click **Continue merge**. Or ask naveen before pushing.

**What each member commits:** their own file about their part, in `docs/members/`. Part 10 below explains it step by step.

| Member | Optional extra commit |
|---|---|
| Naveen (Data) | `docs/DATA_PIPELINE.md`: where the GWRA 2025 PDFs came from and how they were cleaned |
| Rohit (Database & retrieval) | `docs/RETRIEVAL.md`: how place names are resolved and how the RAG index is built |
| Aryan Jangir (Prompt engineering) | `docs/PROMPTS.md`: the system prompt and the task prompts, each rule with the bug it fixed |
| Himanshu (Verification & safety) | Add 5 new trick or injection questions to `tests_data/` and record the results |
| Aryan Sharma (Languages) | `docs/LANGUAGES.md` or a native-speaker correction in `docs/language_review_template.csv` |
| Param (Website & demo) | `docs/WEBSITE.md`: a short tour of the website pages and settings |
| Garvit (Testing & docs) | Update `TEST_STATUS.md` with the latest results, and the README fix from Part 3 |

---

## Part 9. Show it in the presentation

On github.com, open the repo and show:
1. The file list and the README (front page).
2. **Commits** (the clock icon with "… commits"): the full history.
3. **Insights > Contributors**: a graph of each member's commits.

---

## Part 10. Each member uploads their own PDF (no editing needed)

Each member has a **final, ready-made PDF** that explains their part of JalMitra: their code files, how it works,
viva questions with answers, and their presentation speech. **Nobody needs to edit anything.** Each person only
uploads their own PDF **from their own GitHub account**, so the commit history shows all 7 members' work. These are
documentation files only: **they don't change how JalMitra runs**.

| # | Member | Their file |
|---|---|---|
| 1 | Naveen Khatri | `01_naveen_khatri_data.pdf` |
| 2 | Rohit Sharma | `02_rohit_sharma_database_retrieval.pdf` |
| 3 | Aryan Jangir | `03_aryan_jangir_prompt_engineering.pdf` |
| 4 | Himanshu Yadav | `04_himanshu_yadav_verification_safety.pdf` |
| 5 | Aryan Sharma | `05_aryan_sharma_languages_conversation.pdf` |
| 6 | Param Jain | `06_param_jain_website_demo.pdf` |
| 7 | Garvit Khandal | `07_garvit_khandal_testing_results.pdf` |

**Step 1 (naveen):** Naveen's PDF is uploaded first, which also creates the `docs/members` folder. Then naveen
sends each teammate their PDF on WhatsApp.

**Step 2 (each teammate, one at a time, in order 2 → 7).** This uses only the GitHub website, no app needed:
1. Save your PDF from WhatsApp to your laptop (for example in Downloads).
2. Sign in on **github.com** and open **https://github.com/Naveenkhatri-nk/JalMitra/tree/main/docs/members**.
3. Click **Add file** (top right) > **Upload files**.
4. Drag your PDF into the page, or click **choose your files** and pick it.
5. Under **Commit changes**, write: `Add <your part> notes (<your name>)`, for example
   `Add prompt engineering notes (Aryan Jangir)`. Keep **Commit directly to the main branch** selected.
6. Click **Commit changes**.
7. Tell the next member in the group chat: "Done, your turn".

**Check that it worked:** on github.com, open `docs/members`: all seven PDFs should be there. Click **Insights >
Contributors**: all seven names should appear.

---

## Quick help

| Problem | Fix |
|---|---|
| "File is larger than 100 MB" when pushing | A big file got committed. In GitHub Desktop: History > right-click your last commit > **Undo commit**, add the file to `.gitignore`, commit again. |
| `.env` was uploaded by mistake | Delete the key at https://aistudio.google.com (API keys page) and create a new one. Then add `.env` to `.gitignore`. Deleting the file from GitHub is not enough, because it stays in the history. |
| A teammate can't push ("permission denied") | They have not accepted the collaborator invite (Part 6, step 5). |
| "Your branch is behind" | Click **Pull origin**, then push again. |
