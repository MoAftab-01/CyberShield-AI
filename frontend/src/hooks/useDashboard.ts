import { useEffect, useState } from "react";
import { getDashboard } from "../services/dashboardService";
import type { DashboardResponse } from "../types/dashboard";

export function useDashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const dashboard = await getDashboard();
        setData(dashboard);
      } catch {
        setError("Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    }

    fetchDashboard();
  }, []);

  return {
    data,
    loading,
    error,
  };
}