import api from "./api";

import {
    CopilotRequest,
    CopilotResponse,
} from "@/types/copilot";


export const askCopilot = async (

    data: CopilotRequest,

): Promise<CopilotResponse> => {

    const response = await api.post(

        "/copilot/ask",

        data,

    );

    return response.data;
};