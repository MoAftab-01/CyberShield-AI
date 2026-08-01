import { useEffect, useState } from "react";
import {
  getPasswordReports,
  getURLReports,
} from "../services/reportService";

export function useReports() {
  const [passwordReports, setPasswordReports] = useState<any>(null);
  const [urlReports, setURLReports] = useState<any>(null);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const passwords = await getPasswordReports();

        const urls = await getURLReports();

        setPasswordReports(passwords);

        setURLReports(urls);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return {
    passwordReports,
    urlReports,
    loading,
  };
}