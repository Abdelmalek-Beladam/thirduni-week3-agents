# Module 2 Conference Preparation Team

## Architecture

The coordinator owns `ConferenceState` and one `InMemorySaver`. It saves the eight-minute brief before delegation and passes relevant fields explicitly into three model-backed specialists:

- **Evidence-review specialist:** uses Tavily with a hard two-search limit. It preserves URLs, snippets, retrieved excerpts, access status, support status, and date limitations.
- **Presentation-structure specialist:** receives topic, audience, time limit, and evidence report; it produces an outline whose section times must total eight minutes.
- **Rehearsal-question specialist:** receives topic, audience, time limit, outline, and evidence; it produces five questions without assuming experimental results.

Specialists do not inherit coordinator custom state automatically. Wrapper tools read coordinator state and pass explicit values to each specialist.

## Run

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\my-work\module2_conference_team\run_conference_demo.py
```

The runner uses the existing root `.env` without printing credentials. It saves `conference_demo_output.txt`, `conference_state_snapshots.json`, and local callback traces under `traces/`.

The display-only [demo.ipynb](demo.ipynb) reads those files and does not repeat model or Tavily calls.

## Observed Results

The initial run saved the Abdelmalek brief, ran the evidence, structure, and question specialists, and preserved the eight-minute/mixed-audience context. Evidence used exactly two Tavily searches. The follow-up changed only the audience-facing question request: evidence searches stayed at 2, the outline run count stayed at 1, and question runs increased to 2.

The final trace contains the coordinator, all specialist calls, and the two evidence-search tool calls with parent/child run IDs. Cloud tracing was not enabled.

## Limitations and Prompt Rule

The evidence specialist returned a mixture of accessible and blocked source candidates, so support/access/date status must remain visible. The model-generated evidence prose may be more confident than individual source records; the coordinator prompt explicitly requires preserving the records and forbids invented experimental results or external-validation claims.

A factual-grounding rule was added after observing invented project details and was retested. The retest improved handling of missing information, but citation preservation and scientific wording remain incomplete in this run. The existing targeted rule is: preserve every source's support/access/date limitation and never claim the user's model passed validation when no results were supplied. This is a prompt rule, not a code fix. A stronger future improvement would validate final citations against the exact returned source records before allowing the coordinator to respond.
