# Putting JalMitra on the internet (Streamlit Community Cloud)

This guide is written in simple steps. It takes about 20 minutes. Everything used here is free.

## What you get

* A public website like `https://jalmitra.streamlit.app` that anyone can open.
* Visitors must **create an account or log in** before they can use JalMitra.
* Each user's chats are **private** and saved in a database, so they are still there tomorrow.
* An **Admin** page for you (see users, unlock or disable accounts, give a temporary password, see security events).

## How the security works (short)

| Protection | What it does |
|---|---|
| Argon2id password hashing | Passwords are never stored. Only a slow, salted hash is stored, so even a stolen database does not show passwords. |
| Strong password rules | At least 10 characters, not a common password, not your name or email. |
| Lockout | 5 wrong passwords lock the account for 15 minutes (then 30 min, 1 h ... up to 24 h). |
| Rate limits | Too many logins, sign-ups or reset requests from one place are blocked for a while. |
| Same error message | "Email or password is not correct" never tells an attacker which emails exist. |
| Server-side sessions | The browser keeps only a random token. Logout, password change, or an admin disabling the account ends the session within a minute. Idle sessions end after 60 minutes, all sessions after 12 hours. |
| Password reset by email code | One-time 8-letter code, valid 15 minutes, 5 tries, stored only as a hash. |
| Private chats | Each user sees only their own chats. Deleting the account deletes all their data. |
| Secrets kept out of GitHub | Database password, API keys and email password live only in Streamlit "Secrets" (or `.streamlit/secrets.toml`, which is in `.gitignore`). |
| No error details for visitors | Visitors see a short message with a code; the details go to the app log only. |
| Security log | Logins, failed logins, lockouts, resets and admin actions are recorded, with emails and IP addresses stored only as one-way codes. |

## Step 1: Make a free database (Neon)

Streamlit Cloud deletes its files every time the app restarts, so accounts must live in a real database.

1. Go to <https://neon.tech> and sign up (you can use your GitHub account).
2. Create a project. Name: `jalmitra`. Region: pick **Asia Pacific (Singapore)** or the closest one.
3. On the project page click **Connect**, and copy the **connection string**. It looks like
   `postgresql://neondb_owner:xxxx@ep-xxxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`
4. Keep it secret. Do not put it in any file that goes to GitHub.

## Step 2 (optional but recommended): Get a free cloud AI key (Groq)

On your laptop JalMitra uses Ollama. Streamlit Cloud has no Ollama, so without a cloud AI the website shows the
official figures but cannot write the AI explanation.

1. Go to <https://console.groq.com/keys>, sign up, click **Create API Key** and copy it.

## Step 3 (optional): Email for "Forgot password"

Without this, users who forget their password ask you, and you give them a temporary password on the Admin page.
To send reset codes by email with Gmail:

1. Turn on 2-Step Verification on the Gmail account.
2. Open <https://myaccount.google.com/apppasswords>, create an app password named `JalMitra`, and copy the 16 letters.

## Step 4: Create the app on Streamlit Cloud

1. Go to <https://share.streamlit.io> and sign in with GitHub (the account that owns `Naveenkhatri-nk/JalMitra`).
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Repository: `Naveenkhatri-nk/JalMitra`, Branch: `main`, Main file path: `app.py`.
4. App URL: choose a name, for example `jalmitra`.
5. Open **Advanced settings**:
   * Python version: **3.12**
   * Secrets: copy everything from `.streamlit/secrets.toml.example`, then fill in your real values:
     the Neon connection string, a long random `secret_key`, your email in `admin_emails`, and (if you have them)
     the Groq key and the Gmail settings.
     To make a random `secret_key`, run on your laptop:
     `python -c "import secrets; print(secrets.token_urlsafe(48))"`
6. Click **Deploy**. The first start takes a few minutes.

## Step 5: First login

1. Open your new website and click **Create account**, using the same email you put in `admin_emails`.
2. You are now an admin. Open the sidebar → **More pages** → **Admin**.

## Keeping it healthy

* **Health check:** `https://<your-app>.streamlit.app/_stcore/health` answers `ok` when the app is running.
* **Logs:** on share.streamlit.io open your app → **Manage app** (bottom right) to see the log. Errors shown to
  visitors have a code; search the log for that code.
* **Updates:** every `git push` to `main` updates the website automatically.
* **Close sign-ups:** set `allow_signup = false` in Secrets (existing users can still log in).
* **If a secret leaks:** change it at the source (Neon: reset the password; Groq: delete the key), then update
  Secrets on Streamlit Cloud.

## Running on your own computer

Nothing changes: `START_JALMITRA.bat` still works. Login is also on locally; accounts are stored in
`data/users/jalmitra_users.db` (never uploaded). To use JalMitra alone without login, set `JALMITRA_AUTH=off`
before starting it.

## Known limits

* The big monitoring database (`data/groundwater_monitoring.db`, about 1 GB) is too large for GitHub, so the
  website does not have the well-by-well monitoring answers; everything else works.
* The document search (RAG) uses the local `bge-m3` model through Ollama, so on the website general "explain" answers
  have fewer document passages to cite.
* Streamlit Community Cloud apps go to sleep after some days without visitors; the first visitor wakes them up
  (about 1 minute).
