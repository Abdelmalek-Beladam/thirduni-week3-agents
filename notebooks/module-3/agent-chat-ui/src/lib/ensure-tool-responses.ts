import type { Message } from "@langchain/langgraph-sdk";
export const DO_NOT_RENDER_ID_PREFIX = "ui-missing-tool-response-";
export function ensureToolCallsHaveResponses(messages: Message[]): Message[] {
  const answered = new Set(messages.filter(m => m.type === "tool").map(m => (m as { tool_call_id?: string }).tool_call_id));
  const missing: Message[] = [];
  for (const message of messages) {
    if (message.type !== "ai") continue;
    for (const call of message.tool_calls ?? []) {
      if (call.id && !answered.has(call.id)) {
        missing.push({ type: "tool", id: DO_NOT_RENDER_ID_PREFIX + call.id,
          tool_call_id: call.id, content: "This tool call has no recorded result. Do not assume it executed or was approved." });
        answered.add(call.id);
      }
    }
  }
  return missing;
}
