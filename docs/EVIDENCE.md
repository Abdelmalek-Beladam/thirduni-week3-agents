# Execution Evidence Index

Each entry lists implementation files and saved output artifacts that demonstrate execution. Notebook cells with populated outputs count as evidence where cells are present. The existence of a source file alone is not execution proof.

All links below are valid relative paths from this document to the repository root.

---

## Module 1 Experiments

**Implementation & Notebooks:**
- [`my-work/foundational_models_experiment.ipynb`](../my-work/foundational_models_experiment.ipynb)
- [`my-work/tools_experiment.ipynb`](../my-work/tools_experiment.ipynb)
- [`my-work/short_term_memory_experiment.ipynb`](../my-work/short_term_memory_experiment.ipynb)
- [`my-work/multimodal_messages_experiment.ipynb`](../my-work/multimodal_messages_experiment.ipynb)

**Evidence:** Populated notebook cells. The two local multimodal test images were excluded from the public export conservatively; those image-dependent cells require local assets to rerun.

---

## Module 1 Final Project

**Implementation:** [`my-work/module1_final_project/`](../my-work/module1_final_project/)
- Chef agent: [`my-work/module1_final_project/chef_agent.py`](../my-work/module1_final_project/chef_agent.py)
- Conference rehearsal agent: [`my-work/module1_final_project/conference_rehearsal_agent.py`](../my-work/module1_final_project/conference_rehearsal_agent.py)

**Evidence:**
- [`my-work/module1_final_project/demo.ipynb`](../my-work/module1_final_project/demo.ipynb)

---

## Module 2 Conference Preparation Team

**Implementation:** [`my-work/module2_conference_team/`](../my-work/module2_conference_team/)
- Team definition: [`my-work/module2_conference_team/conference_team.py`](../my-work/module2_conference_team/conference_team.py)
- Demo runner: [`my-work/module2_conference_team/run_conference_demo.py`](../my-work/module2_conference_team/run_conference_demo.py)

**Evidence:**
- Corrected demo output: [`my-work/module2_conference_team/conference_demo_output.txt`](../my-work/module2_conference_team/conference_demo_output.txt)
- Interactive notebook: [`my-work/module2_conference_team/demo.ipynb`](../my-work/module2_conference_team/demo.ipynb)
- Pre-correction output (preserved failure): [`my-work/module2_conference_team/before_correction_20261003_141427/conference_demo_output.txt`](../my-work/module2_conference_team/before_correction_20261003_141427/conference_demo_output.txt)
- Post-correction execution trace: [`my-work/module2_conference_team/traces/conference_demo_trace.json`](../my-work/module2_conference_team/traces/conference_demo_trace.json)
- Pre-correction execution trace: [`my-work/module2_conference_team/before_correction_20261003_141427/traces/conference_demo_trace.json`](../my-work/module2_conference_team/before_correction_20261003_141427/traces/conference_demo_trace.json)

*Note:* Failure runs are intentionally preserved to document the progression from the unverified initial draft to the grounded version.

---

## Module 2 Context & State

**Implementation:** [`my-work/module2_context_state/`](../my-work/module2_context_state/)

**Evidence:**
- [`my-work/module2_context_state/demo.ipynb`](../my-work/module2_context_state/demo.ipynb)

---

## Module 2 Model Context Protocol (MCP)

**Implementation:** [`my-work/module2_mcp/`](../my-work/module2_mcp/)
- Local timing server: [`my-work/module2_mcp/presentation_timing_server.py`](../my-work/module2_mcp/presentation_timing_server.py)
- Local client demo: [`my-work/module2_mcp/local_mcp_demo.py`](../my-work/module2_mcp/local_mcp_demo.py)
- Public Kiwi client demo: [`my-work/module2_mcp/public_mcp_demo.py`](../my-work/module2_mcp/public_mcp_demo.py)

**Evidence:**
- Interactive notebook: [`my-work/module2_mcp/demo.ipynb`](../my-work/module2_mcp/demo.ipynb)
- Local server terminal output: [`my-work/module2_mcp/local_mcp_terminal_output.txt`](../my-work/module2_mcp/local_mcp_terminal_output.txt)
- Public Kiwi server terminal output: [`my-work/module2_mcp/public_mcp_terminal_output.txt`](../my-work/module2_mcp/public_mcp_terminal_output.txt)

---

## Module 2 Multi-Agent Delegation

**Implementation:** [`my-work/module2_multi_agent/`](../my-work/module2_multi_agent/)
- Runner script: [`my-work/module2_multi_agent/run_demo.py`](../my-work/module2_multi_agent/run_demo.py)
- Trace callback handler: [`my-work/module2_multi_agent/local_trace.py`](../my-work/module2_multi_agent/local_trace.py)

**Evidence:**
- Execution output: [`my-work/module2_multi_agent/demo_output.txt`](../my-work/module2_multi_agent/demo_output.txt)
- Notebook: [`my-work/module2_multi_agent/demo.ipynb`](../my-work/module2_multi_agent/demo.ipynb)
- Stage 1 execution trace: [`my-work/module2_multi_agent/traces/stage1_trace.json`](../my-work/module2_multi_agent/traces/stage1_trace.json)
- Stage 3 execution trace: [`my-work/module2_multi_agent/traces/stage3_trace.json`](../my-work/module2_multi_agent/traces/stage3_trace.json)

---

## Module 2 Wedding Project

**Implementation:** [`my-work/module2_wedding_project/`](../my-work/module2_wedding_project/)
- Wedding team graph: [`my-work/module2_wedding_project/wedding_team.py`](../my-work/module2_wedding_project/wedding_team.py)
- Demo runner: [`my-work/module2_wedding_project/run_wedding_demo.py`](../my-work/module2_wedding_project/run_wedding_demo.py)

**Evidence:**
- Successful run output: [`my-work/module2_wedding_project/wedding_demo_output.txt`](../my-work/module2_wedding_project/wedding_demo_output.txt)
- Second attempt output: [`my-work/module2_wedding_project/wedding_demo_attempt2_output.txt`](../my-work/module2_wedding_project/wedding_demo_attempt2_output.txt)
- Failure log (missing checkpointer): [`my-work/module2_wedding_project/wedding_demo_failed_missing_checkpointer.txt`](../my-work/module2_wedding_project/wedding_demo_failed_missing_checkpointer.txt)
- Failure log (nested state error): [`my-work/module2_wedding_project/wedding_demo_failed_nested_state.txt`](../my-work/module2_wedding_project/wedding_demo_failed_nested_state.txt)
- Failure log (Windows Unicode error): [`my-work/module2_wedding_project/wedding_demo_failed_unicode_error.txt`](../my-work/module2_wedding_project/wedding_demo_failed_unicode_error.txt)
- Checkpointed state snapshots: [`my-work/module2_wedding_project/wedding_state_snapshots.json`](../my-work/module2_wedding_project/wedding_state_snapshots.json)
- Execution trace: [`my-work/module2_wedding_project/traces/wedding_demo_trace.json`](../my-work/module2_wedding_project/traces/wedding_demo_trace.json)
- Notebook: [`my-work/module2_wedding_project/demo.ipynb`](../my-work/module2_wedding_project/demo.ipynb)

---

## Module 3 Agent Chat UI (Inbox Doorman)

**Implementation:** [`my-work/module3_chat_ui/`](../my-work/module3_chat_ui/)
- Server agent: [`my-work/module3_chat_ui/server_agent.py`](../my-work/module3_chat_ui/server_agent.py)
- Graph configuration: [`my-work/module3_chat_ui/langgraph.json`](../my-work/module3_chat_ui/langgraph.json)
- Shared utilities: [`my-work/module3_chat_ui/common.py`](../my-work/module3_chat_ui/common.py)
- UI documentation: [`my-work/module3_chat_ui/README.md`](../my-work/module3_chat_ui/README.md)

**Evidence & Status:** The backend server starts and the frontend renders. Browser message submission from the UI remains unresolved. No outside-tester session has been recorded.

---

## Module 3 Email Assistant

**Implementation:** [`my-work/module3_email_assistant/`](../my-work/module3_email_assistant/)
- Assistant implementation: [`my-work/module3_email_assistant/email_assistant.py`](../my-work/module3_email_assistant/email_assistant.py)
- Security attack script: [`my-work/module3_email_assistant/attack_email_assistant.py`](../my-work/module3_email_assistant/attack_email_assistant.py)
- Hardened retest script: [`my-work/module3_email_assistant/retest_hardened.py`](../my-work/module3_email_assistant/retest_hardened.py)
- Documentation: [`my-work/module3_email_assistant/README.md`](../my-work/module3_email_assistant/README.md)

**Evidence:**
- Prompt-injection attack output: [`my-work/module3_email_assistant/attack_output.txt`](../my-work/module3_email_assistant/attack_output.txt)
- Hardened defense retest output: [`my-work/module3_email_assistant/retest_hardened_output.txt`](../my-work/module3_email_assistant/retest_hardened_output.txt)

---

## Module 3 Middleware

**Implementation:** [`my-work/module3_middleware/`](../my-work/module3_middleware/)
- Long conversations: [`my-work/module3_middleware/long_conversations.py`](../my-work/module3_middleware/long_conversations.py)
- Human-in-the-loop: [`my-work/module3_middleware/hitl.py`](../my-work/module3_middleware/hitl.py)
- Dynamic agents: [`my-work/module3_middleware/dynamic_agents.py`](../my-work/module3_middleware/dynamic_agents.py)
- Documentation: [`my-work/module3_middleware/README.md`](../my-work/module3_middleware/README.md)

**Evidence:**
- Long conversations output: [`my-work/module3_middleware/long_conversations_output.txt`](../my-work/module3_middleware/long_conversations_output.txt)
- Human-in-the-loop output: [`my-work/module3_middleware/hitl_output.txt`](../my-work/module3_middleware/hitl_output.txt)
- Dynamic agents output: [`my-work/module3_middleware/dynamic_agents_output.txt`](../my-work/module3_middleware/dynamic_agents_output.txt)
- Dynamic agents parts A & B output: [`my-work/module3_middleware/dynamic_agents_output_parts_AB.txt`](../my-work/module3_middleware/dynamic_agents_output_parts_AB.txt)

---

## Module 3 RAG Analysis

**Implementation / Artifacts:** [`my-work/module3_rag/`](../my-work/module3_rag/)
- Pipeline diagram: [`my-work/module3_rag/rag_pipelines.png`](../my-work/module3_rag/rag_pipelines.png)
- RAG evaluation & notes: [`my-work/module3_rag/README.md`](../my-work/module3_rag/README.md)

**Evidence:** Architectural diagram and written answers. No code retrieval pipeline was implemented or executed.
