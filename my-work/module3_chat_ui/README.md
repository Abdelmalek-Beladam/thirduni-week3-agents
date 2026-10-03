# Inbox Doorman - Agent Chat UI

Adapted from the included LangChain Agent Chat UI. All emails and credentials are dummy demonstrations, not a production mailbox or authentication service.

## Start (from the repository root, two PowerShell terminals)

Terminal 1:
```powershell
Set-Location .\my-work\module3_chat_ui
..\..\.venv\Scripts\langgraph.exe dev --no-browser --port 2024
```
Terminal 2:
```powershell
Set-Location .\notebooks\module-3\agent-chat-ui
Copy-Item .env.example .env.local
corepack pnpm dev
```
If dependencies are absent, run `corepack pnpm install` once before starting the frontend.
Open http://localhost:3000. If connection fields appear, use http://localhost:2024, graph `email_assistant`, API key blank. Never paste the Google key in the browser.

## Smoke test

Use dummy login `julie@example.com` / `password123` and ask to read the inbox. Ask to reply to Jane. Confirm an approval card appears and reject it. Save a screenshot of your own UI, not a course page.

## Changes

- Name: Inbox Doorman; envelope/lock logo.
- Restored empty helper files; corrected upload block types; no online font fetch.
- Async model-call filter; no explicit checkpointer (server supplies it).
- Context fallback for the UI; authentication checks inside protected tools.
- Failed-attempt count in conversation state, not a process-global dictionary.

## Verification status

Python syntax and frontend syntax/import paths checked offline. Full Next.js build, LangGraph import and browser conversation require the existing local dependencies and key and have NOT been verified in the sandbox. Earlier CLI attacks remain separate evidence, not proof that this server adaptation ran.

## Limitations

Demo credentials are intentionally public. The thread-level lock is not account-wide and not a production rate limiter. Parallel authentication calls are not hardened. Human approval is enforced by middleware in the graph, not by direct Python tool invocation.

## Outside tester feedback - pending

Let someone outside the cohort use the app without narrating. Record who tested (role only if preferred), what they tried, what surprised you, and what failed. Post actual observations to the Community. Do not mark this task complete before this happens.
