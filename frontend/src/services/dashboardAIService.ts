import axios from "axios";

const API = "http://localhost:8000";

export interface AISummaryResponse {
    summary: string;
}

export async function getAISummary(): Promise<AISummaryResponse> {

    const response = await axios.get<AISummaryResponse>(
        `${API}/dashboard/ai-summary`
    );

    return response.data;
}