import { Brain, RefreshCw } from "lucide-react";

interface Props {
  summary: string;
  loading: boolean;
  onRefresh: () => void;
}

export default function ExecutiveSummaryCard({
  summary,
  loading,
  onRefresh,
}: Props) {
  return (
    <div className="rounded-2xl bg-gradient-to-r from-cyan-600 to-blue-700 p-6 text-white shadow-lg">
      <div className="flex items-center justify-between">

        <div className="flex items-center gap-3">
          <Brain size={30} />

          <div>
            <h2 className="text-2xl font-bold">
              AI Executive Summary
            </h2>

            <p className="text-cyan-100">
              Enterprise Security Overview
            </p>
          </div>
        </div>

        <button
          onClick={onRefresh}
          className="rounded-lg bg-white/20 p-2 hover:bg-white/30 transition"
        >
          <RefreshCw
            size={18}
            className={loading ? "animate-spin" : ""}
          />
        </button>

      </div>

      <p className="mt-6 leading-7 whitespace-pre-wrap">
        {loading
          ? "Generating AI summary..."
          : summary}
      </p>
    </div>
  );
}