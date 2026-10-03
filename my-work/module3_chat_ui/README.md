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

Use dummy login `julie@example.com` / `password123` and ask to read the inbox. Ask to reply to Jane. Confirm an approval card appears and reject it. 

## Changes

- Name: Inbox Doorman; envelope/lock logo.
- Restored empty helper files; corrected upload block types; no online font fetch.
- Async model-call filter; no explicit checkpointer (server supplies it).
- Context fallback for the UI; authentication checks inside protected tools.
- Failed-attempt count in conversation state, not a process-global dictionary.

## Verification status

The backend starts and registers the `email_assistant` graph, and the renamed frontend renders. Browser message submission is unresolved, so no UI conversation, approval card or rejection has been verified through the browser. The CLI attacks in `my-work/module3_email_assistant/` are separate evidence.

## Limitations

Demo credentials are intentionally public. The thread-level lock is not account-wide and not a production rate limiter. Parallel authentication calls are not hardened. Human approval is enforced by middleware in the graph, not by direct Python tool invocation.

## Outside tester feedback

Not yet performed.
