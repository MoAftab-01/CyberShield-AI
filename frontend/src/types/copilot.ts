export interface Source {

    filename: string;

    page: number;

    folder: string;
}

export interface CopilotRequest {

    question: string;

    conversation_id?: number;
}

export interface CopilotResponse {

    conversation_id: number;

    answer: string;

    sources: Source[];
}