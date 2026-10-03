# Testing, Verification and Limitations

This document records the actual executed tests, static syntax checks, known failures, and operational limitations of the implementations in this repository. Unverified behaviors are explicitly identified and are not claimed as tested.

---

## 1. Static Checks and Syntax Verification

- **Python AST Syntax Parse**:
  - 22 custom and adapted Python implementation files in `my-work/` parsed with zero syntax errors via Python's `ast` parser.
  - *Limitation*: This is a static syntax check only. It does not test package imports, runtime environment dependencies, or live model execution.
- **Frontend Syntax Parse**:
  - 52 TypeScript and TSX files in `notebooks/module-3/agent-chat-ui/` parsed with zero syntax errors via Prettier's TypeScript syntax parser.
  - *Limitation*: This is a static syntax parse only. It is not a TypeScript compiler type-check (`tsc`) or Next.js production build (`next build`).
- **Credential Pattern Scan**:
  - Regular expression pattern scan (Google `AIza*`, OpenAI `sk-*`, Tavily `tvly-*`, and key assignment patterns) performed across all tracked text files.
  - Zero live credentials detected. Only template placeholders (`example.env`) and documentation examples (`COURSE_README.md`) are present.
  - *Limitation*: This was a bounded pattern scan, not a full security audit.

---

## 2. Executed Tests and Saved Evidence

All tests below reflect actual executions with saved outputs retained in the repository.

### Middleware & Conversation Management (`my-work/module3_middleware/`)
- **Long Conversations (`long_conversations.py`)**:
  - *Executed*: Message summarisation and a `before_agent` hook to strip sensor readings.
  - *Observed finding*: Conversation state compressed from 12 to 3 messages, but input token count rose on this short prompt (284 vs 167 tokens) due to summary overhead. Summarisation also altered specific facts (shortening "night deliveries" to "24/7 delivery service").
  - *Output file*: [`my-work/module3_middleware/long_conversations_output.txt`](../my-work/module3_middleware/long_conversations_output.txt).
- **Human-in-the-Loop Gating (`hitl.py`)**:
  - *Executed*: Interrupt-and-review lifecycle for tool calls covering approve, reject-with-reason, and input modification.
  - *Observed finding*: Simulated advance approval in the user prompt failed to bypass the gate; unapproved email send actions were successfully caught and rejected.
  - *Output file*: [`my-work/module3_middleware/hitl_output.txt`](../my-work/module3_middleware/hitl_output.txt).
- **Dynamic Agents (`dynamic_agents.py`)**:
  - *Executed*: Dynamic model switching from `gemini-3.1-flash-lite` to `gemini-3.8-flash` based on conversation depth, along with dynamic role and language prompt injection.
  - *Output file*: [`my-work/module3_middleware/dynamic_agents_output.txt`](../my-work/module3_middleware/dynamic_agents_output.txt).

### Security Attacks & Hardened Retests (`my-work/module3_email_assistant/`)
- **Prompt-Injection Vulnerability Test (`attack_email_assistant.py`)**:
  - *Executed*: Tested whether hiding sensitive tools (`check_inbox`) from the agent's visible tool list prevents unauthorized invocation via prompt injection.
  - *Observed finding*: Tool hiding failed. An attacker prompt tricked the agent into invoking the hidden tool, exposing the inbox.
  - *Output file*: [`my-work/module3_email_assistant/attack_output.txt`](../my-work/module3_email_assistant/attack_output.txt).
- **Hardened Defense Retest (`retest_hardened.py`)**:
  - *Executed*: Retested against tool-level authentication checks and retry limits.
  - *Observed finding*: Adding internal session verification inside the protected tool blocked the prompt-injection exploit. Enforcing a 2-failure password attempt limit blocked brute-force password guessing.
  - *Output file*: [`my-work/module3_email_assistant/retest_hardened_output.txt`](../my-work/module3_email_assistant/retest_hardened_output.txt).

### Multi-Agent Coordination (`my-work/module2_multi_agent/`)
- **Task Delegation (`run_demo.py`)**:
  - *Executed*: Delegating agent assigning sub-tasks with structured callback tracing.
  - *Output file*: [`my-work/module2_multi_agent/demo_output.txt`](../my-work/module2_multi_agent/demo_output.txt), [`traces/stage1_trace.json`](../my-work/module2_multi_agent/traces/stage1_trace.json), [`traces/stage3_trace.json`](../my-work/module2_multi_agent/traces/stage3_trace.json).

### Complex Agent Teams & Real Failures (`my-work/module2_wedding_project/`, `my-work/module2_conference_team/`)
- **Wedding Planner Team (`run_wedding_demo.py`)**:
  - *Executed*: Multi-agent workflow coordinating specialized agents (music via SQLite Chinook DB, flights via Kiwi MCP, and web research via Tavily).
  - *Documented failure runs*: Preserved records of real execution failures prior to success, including missing checkpointer configuration, nested state schema mismatches, and Windows console Unicode encoding errors.
  - *Output file*: [`my-work/module2_wedding_project/wedding_demo_output.txt`](../my-work/module2_wedding_project/wedding_demo_output.txt) alongside preserved failure logs (`wedding_demo_failed_*.txt`).
- **Conference Preparation Adaptation (`run_conference_demo.py`)**:
  - *Executed*: Adaptation of the wedding workflow to academic conference preparation.
  - *Observed finding*: Both pre-correction and post-correction outputs are preserved. The pre-correction run produced unverified claims; even after factual grounding prompts, multi-agent synthesis dropped citations and conflated model validation with training.
  - *Output file*: [`my-work/module2_conference_team/conference_demo_output.txt`](../my-work/module2_conference_team/conference_demo_output.txt).

### Model Context Protocol (MCP) Integration (`my-work/module2_mcp/`)
- **Local & Public MCP Servers**:
  - *Executed*: Local FastMCP timing server (`local_mcp_demo.py`) and public Kiwi server (`public_mcp_demo.py`).
  - *Output file*: [`my-work/module2_mcp/local_mcp_terminal_output.txt`](../my-work/module2_mcp/local_mcp_terminal_output.txt), [`my-work/module2_mcp/public_mcp_terminal_output.txt`](../my-work/module2_mcp/public_mcp_terminal_output.txt).

---

## 3. Known Failures, Limitations and Unverified Areas

The following items are explicitly not verified or have documented limitations:

1. **Agent Chat UI (Inbox Doorman UI)**:
   - The Next.js frontend renders and the local backend server runs.
   - However, browser message submission from the UI is unresolved.
   - **No successful UI conversation is claimed.**
2. **Outside Tester Feedback**:
   - No external user testing or cohort peer evaluations were performed on the chat interface.
3. **Simulated Email Environment**:
   - The email assistant uses an in-memory dictionary test fixture (`julie@example.com` / `password123`). It does not connect to live SMTP/IMAP mailboxes.
4. **RAG Pipeline Scope**:
   - The RAG module consists of architectural pipeline diagrams and written analyses. No RAG retrieval pipeline was implemented or executed in code.
5. **Prior Agent Break Probes**:
   - Extended multi-turn degradation testing and cross-user context leakage tests on the prior week's agent were pending and not executed.
6. **Local Image Dependencies**:
   - Multimodal notebook cells requiring local image assets cannot be rerun without those local files.
7. **Environment Reproducibility**:
   - `uv.lock` and `requirements.txt` are provided for dependency tracking, but individual package versions were not independently re-verified via a clean environment reinstall.
