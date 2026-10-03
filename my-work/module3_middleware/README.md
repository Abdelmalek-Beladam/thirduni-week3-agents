# Module 3 - Middleware exercises

Practical exercises for the Thirduni Week 3 Module 3 lessons: Managing Long Conversations, Human-in-the-Loop and Dynamic Agents. The APIs follow the course notebooks in `notebooks/module-3/`, adapted to Gemini (`gemini-3.1-flash-lite`).

## Files

| File | Lesson | What it demonstrates |
| --- | --- | --- |
| `common.py` | - | Shared model, logging and token helpers |
| `long_conversations.py` | Managing Long Conversations | Summarisation middleware on a long conversation; a `before_agent` hook that removes a sensor tool result; token usage before and after |
| `hitl.py` | Human-in-the-Loop | A dummy feedback-sending tool gated for approval; approve, reject with a reason, and edit |
| `dynamic_agents.py` | Dynamic Agents | Prompt by language; Chinook SQL tool hidden from external users; model switch after 10 messages |

Each script writes its terminal output to a matching `*_output.txt` file in this folder.

## Run

From the repository root, in PowerShell:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\my-work\module3_middleware\long_conversations.py
.\.venv\Scripts\python.exe -X utf8 .\my-work\module3_middleware\hitl.py
.\.venv\Scripts\python.exe -X utf8 .\my-work\module3_middleware\dynamic_agents.py
```

The larger model in the model-switch exercise defaults to `gemini-3.8-flash`. If the key cannot use it, the script says so and skips that part. To choose another model, set `MODULE3_LARGE_MODEL` in `.env`.

## Design decisions

- The `before_agent` hook removes the sensor `ToolMessage` together with the AI message that requested it. Gemini expects every function call to be followed by its result, so removing only the tool result could break the request.
- The gated tool is a dummy that only appends to an in-memory list. Nothing is sent externally. It stands in for the Kiwi `feedback-to-devs` tool, which was excluded from the wedding project.
- The database is opened read-only (`mode=ro`).
- Tavily is limited to two results per search, and every search is counted.

## Observed results

- Summarisation reduced the state from 12 to 3 messages. In this short conversation it did not save tokens: the main call used 284 input tokens compared with 167 without summarisation, because the summary was longer than the original messages. The summary also distorted one fact, changing "night deliveries" into "24/7 delivery service".
- The before_agent hook removed the sensor tool call and its result. Without the hook, the agent answered 41 C. With the hook, it said it did not have the reading. Input tokens fell from 129 to 116. The agent called the sensor tool again and received "offline"; the removed value never appeared.
- Human-in-the-loop: approve sent the draft; reject sent nothing and produced a revised draft; edit sent exactly the edited text. Reading flight options stayed automatic. All sends were dummy.
- The dynamic prompt answered in English, French and Arabic.
- The SQL tool was offered only to internal users. The external user still found the public answer (275 artists) using 5 web searches and suggested an SQL check it could not run. Hiding a tool restricts capability, not information that is publicly available.
- Model switch: gemini-2.5-flash was unavailable for this key (404), so gemini-3.8-flash was used. The 1-message conversation used gemini-3.1-flash-lite (23 input / 21 output tokens). The 11-message conversation switched to gemini-3.8-flash (111 input / 273 output tokens) for a one-sentence answer, so the larger model cost far more per answer. The model-switch output is in dynamic_agents_output.txt; the earlier parts are in dynamic_agents_output_parts_AB.txt.

## Written tasks

- **Where the agent needs a door (before):** sending anything externally or booking. In the wedding project, Kiwi offered a feedback-sending tool. It was excluded, but approval gating is the alternative that keeps the tool available.
- **What to check after it answers:** unsupported claims. The first conference-team answer invented sensors, findings and benefits that were never supplied.
- **Try to break last week's agent:** to be completed by testing a long conversation, a different kind of user, and a request close to an action that should not run automatically.

## Breaking last week's agent

These observations come from the Module 2 runs, not from a dedicated break test.

- **Missing information:** the first version of the conference team invented sensors, findings and benefits that were never supplied. After the correction it marked missing details as "Not supplied", but then treated them as unfinished work.
- **Long output:** in the corrected run, the final answer dropped the evidence URLs, access status and dates collected earlier, overclaimed that the model would "prove learned physics", and treated validation as if it were training.
- **Close to an action:** the Kiwi flight server exposed a tool that sends feedback to its developers. It was excluded from the wedding project because nothing should be sent externally without a human decision.
- **Not tested:** asking as a different kind of user.

## What should be gated in my agents

Rule: gate anything that spends money, sends something to another person, or cannot be undone.

| Agent | Action | Decision |
| --- | --- | --- |
| Wedding planner | Kiwi feedback-to-devs (sends a message externally) | Gate, or exclude as done in Module 2 |
| Wedding planner | Booking or paying for flights or venues (not implemented) | Gate if ever added |
| Wedding planner | Flight search, venue search, Chinook music queries (read-only) | Automatic |
| Conference team | Evidence review, outline, rehearsal questions (internal drafts) | Automatic; a human checks the final answer for unsupported claims |
| Email assistant | send_email | Gated, tested |
| Email assistant | check_inbox | Not gated, but must check login inside the tool |
| Email assistant | authenticate | Not gated, but limited to 2 failed attempts |

Note: `max_results=2` limits results per Tavily call, not the number of calls. The external-user run made five calls. Model-switch token totals do not establish pricing or model superiority because both the model and the input differ.
