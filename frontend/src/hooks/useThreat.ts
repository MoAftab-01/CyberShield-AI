import { useState } from "react";

import { getThreat } from "../services/threatService";

import { Threat } from "../types/threat";

export const useThreat = () => {

    const [loading, setLoading] = useState(false);

    const [data, setData] = useState<Threat | null>(null);

    const [error, setError] = useState("");

    const search = async (cve: string) => {

        setLoading(true);

        setError("");

        try {

            const response = await getThreat(cve);

            setData(response);

        } catch {

            setError("Threat not found");

        } finally {

            setLoading(false);

        }
    };

    return {
        loading,
        error,
        data,
        search
    };
};