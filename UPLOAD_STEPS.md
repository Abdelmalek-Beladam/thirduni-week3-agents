# Publish this repository to GitHub

`gh` CLI is not installed. Use the steps below. Git 2.50.0 is available and identity is configured.

## Pre-flight checks completed

- No existing `.git` directory in this folder — safe to initialize fresh.
- No private `.env` files present.
- No real API key values found in any file (see VERIFICATION.md).
- `.gitignore` covers dependencies, environment files, IDE state and course screenshots.

## Step 1 — Create the GitHub repository

Go to https://github.com/new and create an **empty public** repository:
- Owner: your GitHub account
- Repository name: `thirduni-week3-agents`
- Description: `Gemini-based agent experiments covering tools, memory, MCP, multi-agent coordination, middleware and human approval, with saved execution evidence.`
- Visibility: Public
- **Do NOT** tick "Add a README file", "Add .gitignore" or "Choose a license" — the repository must be empty.

Copy the HTTPS remote URL shown after creation (e.g. `https://github.com/YOUR_USERNAME/thirduni-week3-agents.git`).

## Step 2 — Initialize, stage, commit and push

Open PowerShell in this folder:

```powershell
git init
git add .
git status --short
# Review the staged list carefully.
# .env, .venv/, node_modules/, course-screenshots/ must NOT appear.
git commit -m "Add Week 3 agent implementations and execution evidence"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/thirduni-week3-agents.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username. Authenticate using GitHub's normal browser credential flow. Never paste a token into the remote URL or into chat.

## Step 3 — Update SUBMISSION.md

After the push succeeds, update the Repository URL line in SUBMISSION.md with the actual GitHub URL, then:

```powershell
git add SUBMISSION.md README.md
git commit -m "Add GitHub repository URL to SUBMISSION.md and README"
git push
```

## Step 4 — Verify

```powershell
git remote -v
git log --oneline -3
```

Confirm the remote points to your account and the commits are present on GitHub.

## Step 5 — Thirduni submission

Copy the title, description and GitHub URL from SUBMISSION.md to your Thirduni project page. Do not claim pending tasks (browser UI test, outside tester, from-memory RAG drawing, Community posts) as complete.
