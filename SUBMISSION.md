# Thirduni project-page draft

## Title

Week 3 - Building and Testing Agents with Gemini

## Description

I implemented Week 3 experiments covering model calls, tools, memory, multimodal messages, MCP, runtime context/state, multi-agent delegation, middleware, human-in-the-loop and dynamic agents. I adapted the wedding workflow into a conference preparation team and built a dummy email assistant with authentication and approval before sending.

The repository includes my implementations, saved terminal outputs, notebooks, state snapshots and local execution traces, including failures and limitations. My email attacks exposed an unauthorized inbox read despite tool hiding. Adding authentication checks inside the protected tools blocked that attack on retest. A two-failure limit also blocked the tested password-guessing sequence. Human approval prevented an email send despite claimed advance approval.

A renamed Agent Chat UI (Inbox Doorman) and RAG lesson notes are included. UI browser verification and outside-tester feedback are pending; I am not claiming these tasks completed yet.

Repository URL: https://github.com/Djawad-mdallahmari/thirduni-week3-agents

## RAG Community answer

If retrieval silently returned wrong documents, I would detect it using a fixed evaluation set with known relevant documents, recall at k, retrieved document IDs/scores, embedding model/version compatibility checks, and checks that cited chunks support the answer. Fluent answers and absence of exceptions are not evidence of correct retrieval.

## Chat UI Community report - fill after actual testing

Tester: [person outside cohort / role]
What they did without my narration: [observed actions]
What they tried that I had not anticipated: [actual observation]
What failed or held: [actual observation]
Change I would make: [based on feedback]

## Remaining tasks requiring user action before claiming complete

- Browser message submission via the Inbox Doorman UI (unresolved).
- Outside-tester session for the Chat UI Community task (no fabricated feedback).
- Deliberate long-conversation and different-user probes on last week's agent (pending).
- RAG from-memory drawing (not evidenced).
- Email and Chat UI Community posts: a draft does not constitute publication — confirm actual posting.
- Storytelling and any other remaining lessons not audited in the supplied materials.

