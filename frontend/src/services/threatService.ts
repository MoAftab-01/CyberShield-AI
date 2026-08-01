import api from "./api";

export const getThreat = async (cve: string) => {
    const response = await api.get(`/threats/${cve}`);
    return response.data;
};