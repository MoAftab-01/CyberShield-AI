import { useState } from "react";
import { FileText, Shield, Globe } from "lucide-react";

import { useReports } from "../hooks/useReports";

import PasswordTable from "../components/reports/PasswordTable";
import URLTable from "../components/reports/URLTable";

import ExecutiveSummaryCard from "../components/reports/ExecutiveSummaryCard";
import { useAISummary } from "../hooks/useAISummary";

import { Download } from "lucide-react";

import {
  generateExecutiveReport,
} from "../services/pdfReportService";


export default function Reports() {
  const { passwordReports, urlReports, loading } = useReports();

  const [tab, setTab] = useState<"passwords" | "urls">("passwords");
  const {
  summary,
  loading: aiLoading,
  refresh,
} = useAISummary();
  

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
  <div className="mx-auto max-w-7xl space-y-8">

    {/* Header */}

    <section
      className="
      relative

      overflow-hidden

      rounded-[28px]

      border

      border-cyan-400/20

      bg-slate-900/55

      p-8

      backdrop-blur-2xl

      shadow-[0_0_45px_rgba(34,211,238,.08)]
      "
    >

      <div
        className="
        absolute

        -right-24

        -top-24

        h-72

        w-72

        rounded-full

        bg-cyan-500/10

        blur-[140px]
        "
      />

      <div className="relative flex items-center justify-between">

        <div className="flex items-center gap-6">

          <div
            className="
            flex

            h-16

            w-16

            items-center

            justify-center

            rounded-3xl

            bg-gradient-to-br

            from-cyan-400

            via-cyan-500

            to-blue-600

            shadow-[0_0_35px_rgba(34,211,238,.35)]
            "
          >

            <FileText
              size={32}
              className="text-white"
            />

          </div>

          <div>

            <h1
              className="
              text-4xl

              font-bold

              tracking-tight

              text-white
              "
            >
              Security Reports
            </h1>

            <p
              className="
              mt-2

              text-slate-400
              "
            >
              Review historical scans, executive summaries,
              and export security reports.
            </p>

          </div>

        </div>

        <button
          onClick={() =>
            generateExecutiveReport(
              summary?.summary ?? "",
              passwordReports?.items.length ?? 0,
              urlReports?.items.length ?? 0,
            )
          }
          className="
          flex

          items-center

          gap-3

          rounded-2xl

          bg-gradient-to-r

          from-cyan-400

          via-cyan-500

          to-blue-600

          px-6

          py-3

          font-semibold

          text-white

          transition-all

          duration-300

          hover:shadow-[0_0_35px_rgba(34,211,238,.35)]
          "
        >

          <Download size={18} />

          Export Report

        </button>

      </div>

    </section>

    {/* Executive Summary */}

    <ExecutiveSummaryCard
      summary={summary?.summary ?? ""}
      loading={aiLoading}
      onRefresh={refresh}
    />

    {/* Tabs */}

    <div className="flex gap-4">

      <button
        onClick={() =>
          setTab("passwords")
        }
        className={`
        flex

        items-center

        gap-3

        rounded-2xl

        px-6

        py-3

        transition-all

        duration-300

        ${
          tab === "passwords"
            ? `
            border
            border-cyan-300/40

            bg-cyan-500/15

            text-cyan-300

            shadow-[0_0_25px_rgba(34,211,238,.15)]
            `
            : `
            border
            border-cyan-400/15

            bg-slate-900/45

            text-slate-400

            hover:border-cyan-300/30
            `
        }
        `}
      >

        <Shield size={18} />

        Password Reports

      </button>

      <button
        onClick={() =>
          setTab("urls")
        }
        className={`
        flex

        items-center

        gap-3

        rounded-2xl

        px-6

        py-3

        transition-all

        duration-300

        ${
          tab === "urls"
            ? `
            border
            border-cyan-300/40

            bg-cyan-500/15

            text-cyan-300

            shadow-[0_0_25px_rgba(34,211,238,.15)]
            `
            : `
            border
            border-cyan-400/15

            bg-slate-900/45

            text-slate-400

            hover:border-cyan-300/30
            `
        }
        `}
      >

        <Globe size={18} />

        URL Reports

      </button>

    </div>

    {/* Content */}

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