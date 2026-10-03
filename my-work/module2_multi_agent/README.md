# Week 3 Multi-Agent Systems

## Architecture

`run_demo.py` builds two supervisors using `gemini-3.1-flash-lite`:

- Stage 1 delegates to separate model-backed analogy and definition specialists through `analogy_specialist` and `definition_specialist` LangChain tools.
- Stage 3 delegates external evidence requests to a model-backed evidence researcher. That specialist uses Tavily, attempts bounded HTTPS retrieval of returned URLs, and reports exact URLs, excerpts, access/date limits, and conservative support status. The conference supervisor is instructed not to invent results or claim external validation for the user's model.

Both stages use the installed LangChain callback API locally. Callback `run_id` and `parent_run_id` values are saved with a shared `trace_id`, so the saved trace represents actual execution events. No LangSmith cloud tracing is enabled.

## Run

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe .\my-work\module2_multi_agent\run_demo.py
```

The script uses the existing repository `.env` without printing values. It writes `demo_output.txt` and creates `traces/stage1_trace.json`, `traces/stage1_trace_timeline.txt`, `traces/stage3_trace.json`, and `traces/stage3_trace_timeline.txt`.

The LangSmith UI shown in the course requires a LangSmith account/API key and `LANGSMITH_TRACING=true` in `.env`. Enabling it would send prompts and outputs to LangSmith; it was not enabled here. The local callback trace is a private alternative, not the exact course UI.

## Trace vs. Message List

The supervisor's message list shows the visible human prompt, AI delegation tool calls, tool results, and final answer. The callback trace additionally shows nested specialist agent runs and Gemini model calls with run and parent-run IDs, grouped by the same local trace ID.

## Observed Run

Stage 1 invoked both specialists. The supervisor combined their outputs into two sentences.

Stage 3 called Tavily and returned several candidate sources. The final supervisor cited two URLs that were both present in the returned source set: an Applied AI Course page and a Medium article. The Applied AI Course page was retrieved and supplied an excerpt about cross-validation and generalizability, so the evidence was marked **partially supported**; its publication date was not supplied and it is an educational page rather than a peer-reviewed source. The Medium page returned HTTP 403, so that source remained **unverified** and had no confirmed publication date. The citations matched returned URLs, but the response overstated confidence by presenting the sources together without preserving their different statuses. It did not claim that the user's own model had passed external validation. No model performance values were supplied by the user.

The first run's broad numeric-claim detector printed `True` because it matched the word “accuracy” in the answer's disclaimer (“not independently verified for accuracy”). The detector in `run_demo.py` was narrowed to numeric metrics/percentages after that run; it was not rerun to avoid extra model calls.

## Limitations and Next Improvement

Direct page retrieval is bounded and some publishers block automated access; those records remain unverified rather than being promoted based on snippets. A next improvement is to make the supervisor preserve each returned source's support status and access/date limitation verbatim in its final response.