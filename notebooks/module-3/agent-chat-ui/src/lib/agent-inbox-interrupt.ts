import type { Interrupt } from "@langchain/langgraph-sdk";
import type { HITLRequest } from "@/components/thread/agent-inbox/types";
function valid(item: unknown): boolean {
  if (!item || typeof item !== "object" || !("value" in item)) return false;
  const value = (item as { value: unknown }).value;
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return Array.isArray(v.action_requests) && Array.isArray(v.review_configs);
}
export function isAgentInboxInterruptSchema(value: unknown): value is Interrupt<HITLRequest> | Interrupt<HITLRequest>[] {
  return Array.isArray(value) ? value.length > 0 && value.every(valid) : valid(value);
}
