    export interface Source {

        filename: string;

        page: number;

        folder?: string | null;
    }

    export interface CopilotRequest {

        question: string;

        conversation_id?: number;
    }

    export interface CopilotResponse {

        conversation_id: number;

        answer: string;

        sources: Source[];

        related_sources?: Source[];
    }