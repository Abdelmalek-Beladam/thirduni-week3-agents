export function getApiKey(): string | null {
  if (typeof window === "undefined") return null;
  try { return window.localStorage.getItem("lg:chat:apiKey") || null; } catch { return null; }
}
