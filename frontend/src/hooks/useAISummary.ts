import { useEffect, useState } from "react";

import {
  getAISummary,
  AISummaryResponse,
} from "../services/dashboardAIService";

export function useAISummary() {

  const [summary, setSummary] =
    useState<AISummaryResponse | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] =
    useState("");

  const [lastUpdated, setLastUpdated] =
    useState<Date | null>(null);

  const loadSummary = async (
    showLoader = false,
  ) => {

    if (showLoader) {

      setLoading(true);

    } else {

      setRefreshing(true);

    }

    setError("");

    try {

      const data =
        await getAISummary();

      setSummary(data);

      setLastUpdated(new Date());

    }

    catch {

      setError(
        "Unable to load AI Summary."
      );

    }

    finally {

      setLoading(false);

      setRefreshing(false);

    }

  };

  useEffect(() => {

    loadSummary(true);

  }, []);

  return {

    summary,

    loading,

    refreshing,

    error,

    lastUpdated,

    refresh: () => loadSummary(false),

  };

}