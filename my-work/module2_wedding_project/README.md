# Module 2 Wedding Planner

## Architecture

See [architecture.md](architecture.md). The coordinator owns `WeddingState` and one `InMemorySaver`. It saves the complete brief before delegation, then calls three model-backed specialists through tools:

- Travel: receives explicit route/date/passenger fields and calls only Kiwi `search-flight` over streamable HTTP.
- Venue: receives destination/guest count and performs at most two Tavily searches, preserving exact URLs and unknown fields.
- DJ: receives genre and queries the read-only Chinook database for up to eight actual tracks.

Nested specialists do not inherit the coordinator's custom state automatically. The wrappers pass the required values explicitly.

## Run

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -X utf8 .\my-work\module2_wedding_project\run_wedding_demo.py
```

The runner uses the existing root `.env` without printing its values. It saves:

- `wedding_demo_output.txt`
- `wedding_demo_failed_unicode_error.txt`
- `wedding_demo_failed_missing_checkpointer.txt`
- `wedding_demo_failed_nested_state.txt`
- `wedding_demo_attempt2_output.txt`
- `kiwi_tool_discovery.json`
- `wedding_state_snapshots.json`
- `traces/wedding_demo_trace.json`
- `traces/wedding_demo_trace_timeline.txt`

Open [demo.ipynb](demo.ipynb) to display the saved output, snapshots, and trace timeline. It does not launch MCP subprocesses from Jupyter.

## Verified Kiwi Safety Boundary

Kiwi discovery returned `search-flight` and `feedback-to-devs`. Only `search-flight` is exposed to the travel specialist. The implementation never invokes `feedback-to-devs`, follows booking URLs, submits passenger details, books, reserves, or purchases anything.

## Observed Failures and Corrections

1. The first PowerShell attempt failed while printing Kiwi's Unicode arrow with Windows `cp1252` output: `UnicodeEncodeError`. The runner now reconfigures stdout/stderr for UTF-8 and is launched with `-X utf8`.
2. The next attempt failed at `coordinator.get_state` because the coordinator had no checkpointer. A single `InMemorySaver` is now attached to the coordinator and reused for both turns.
3. The following attempt failed with `KeyError: 'origin'` because nested specialists do not automatically inherit custom coordinator state. The corrective rule is now explicit field passing: travel receives route/dates/passenger count, venue receives destination/guest count, and DJ receives genre.
4. After the correction, the initial and Rock follow-up completed successfully. Underlying travel and venue search counters remained unchanged on follow-up, while the genre changed from Jazz to Rock and the playlist specialist ran again.

The successful run also exposed a remaining coordinator behavior: on the follow-up, Gemini reissued `update_brief` and called the travel/venue wrapper tools, but their checkpoint guards returned saved results without repeating Kiwi or Tavily. Only the playlist specialist performed new database work. Thus the external-search requirement was met, but the coordinator message sequence was not minimal.

Venue results are candidate search evidence only. Price, capacity, and availability remain unknown unless explicitly supported by returned evidence. Playlist rows come from the read-only database; `Track.UnitPrice` is not treated as a DJ fee or licensing cost.
