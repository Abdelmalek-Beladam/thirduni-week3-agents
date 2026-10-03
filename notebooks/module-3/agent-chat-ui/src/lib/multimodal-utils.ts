import type { ContentBlock } from "@langchain/core/messages";
export function isBase64ContentBlock(block: unknown): block is ContentBlock.Multimodal.Data {
  if (!block || typeof block !== "object") return false;
  const b = block as Record<string, unknown>;
  return (b.type === "image" || b.type === "file") && typeof b.data === "string" && typeof b.mimeType === "string";
}
export function fileToContentBlock(file: File): Promise<ContentBlock.Multimodal.Data> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result);
      const block = { type: file.type === "application/pdf" ? "file" : "image",
        mimeType: file.type, data: result.substring(result.indexOf(",") + 1),
        metadata: { name: file.name, filename: file.name } };
      resolve(block as ContentBlock.Multimodal.Data);
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}
