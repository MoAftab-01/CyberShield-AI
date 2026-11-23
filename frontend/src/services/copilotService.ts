import api from "./api";
import type { CopilotRequest, CopilotResponse } from "@/types/copilot";
import { readCopilotResponse } from "@/lib/grounding";

export const askCopilot = async (
  data: CopilotRequest,
  signal?: AbortSignal,
): Promise<CopilotResponse> => {
  const response = await api.post<unknown>("/copilot/ask", {
    question: data.question,
    conversation_id: data.conversation_id,
  }, { signal });
  return readCopilotResponse(response.data);
};
