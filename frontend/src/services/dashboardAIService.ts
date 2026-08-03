import api from "./api";

export interface AISummaryResponse {
  summary: string;
}

export async function getAISummary(): Promise<AISummaryResponse> {
  const response = await api.get<AISummaryResponse>(
    "/dashboard/ai-summary"
  );

  return response.data;
}