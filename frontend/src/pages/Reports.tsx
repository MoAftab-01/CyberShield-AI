import { useState } from "react";
import { FileText, Shield, Globe } from "lucide-react";

import { useReports } from "../hooks/useReports";

import PasswordTable from "../components/reports/PasswordTable";
import URLTable from "../components/reports/URLTable";

export default function Reports() {
  const { passwordReports, urlReports, loading } = useReports();

  const [tab, setTab] = useState<"passwords" | "urls">("passwords");

  if (loading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <p className="text-lg text-slate-500">
          Loading reports...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">

      {/* Header */}

      <div>
        <h1 className="flex items-center gap-3 text-4xl font-bold text-slate-800">
          <FileText size={36} />
          Reports
        </h1>

        <p className="mt-2 text-slate-500">
          Review historical password and URL scans.
        </p>
      </div>

      {/* Tabs */}

      <div className="flex gap-4">

        <button
          onClick={() => setTab("passwords")}
          className={`flex items-center gap-2 rounded-xl px-5 py-3 transition
          ${
            tab === "passwords"
              ? "bg-blue-600 text-white"
              : "bg-white border"
          }`}
        >
          <Shield size={18} />
          Password Reports
        </button>

        <button
          onClick={() => setTab("urls")}
          className={`flex items-center gap-2 rounded-xl px-5 py-3 transition
          ${
            tab === "urls"
              ? "bg-blue-600 text-white"
              : "bg-white border"
          }`}
        >
          <Globe size={18} />
          URL Reports
        </button>

      </div>

      {/* Content */}

      {tab === "passwords" ? (
        <PasswordTable
          reports={passwordReports?.items ?? []}
        />
      ) : (
        <URLTable
          reports={urlReports?.items ?? []}
        />
      )}

    </div>
  );
}