import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  Bot,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import SecurityStatus from "./SecurityStatus";
import InsightChips from "./InsightChips";

interface Props {

  summary: string;

  score: number;

  lastUpdated: Date | null;

  refreshing: boolean;

  onRefresh: () => void;

}

export default function AISummaryCard({

  summary,

  score,

  lastUpdated,

  refreshing,

  onRefresh,

}: Props) {

 return (

  <div
    className="
    group
    relative
    overflow-hidden

    rounded-[28px]

    border
    border-cyan-400/20

    bg-slate-900/55

    backdrop-blur-2xl

    shadow-[0_0_45px_rgba(34,211,238,.10)]

    transition-all
    duration-500

    hover:border-cyan-300/40

    hover:shadow-[0_0_60px_rgba(34,211,238,.20)]
    "
  >

    {/* Ambient Glow */}

    <div
      className="
      absolute

      -right-20

      -top-20

      h-64

      w-64

      rounded-full

      bg-cyan-500/10

      blur-[120px]
      "
    />

    <div
      className="
      absolute

      bottom-0

      left-0

      h-56

      w-56

      rounded-full

      bg-blue-500/10

      blur-[100px]
      "
    />

    {/* Header */}

    <div
      className="
      relative

      flex

      items-center

      justify-between

      border-b

      border-cyan-400/10

      px-6

      py-4
      "
    >

      <div className="flex items-center gap-4">

        <div
          className="
          flex

          h-14

          w-14

          items-center

          justify-center

          rounded-2xl

          bg-gradient-to-br

          from-cyan-400

          via-cyan-500

          to-blue-600

          shadow-[0_0_30px_rgba(34,211,238,.35)]
          "
        >

          <Bot
            size={28}
            className="text-white"
          />

        </div>

        <div>

          <h2
            className="
            text-xl

            font-bold

            text-white
            "
          >

            CyberGPT Executive Overview

          </h2>

          <p className="text-sm text-slate-400">

            AI-powered enterprise security intelligence

          </p>

        </div>

      </div>

      <button
        disabled={refreshing}
        onClick={onRefresh}
        className="
        flex

        items-center

        gap-2

        rounded-2xl

        border

        border-cyan-400/20

        bg-cyan-500/10

        px-4

        py-2

        text-cyan-300

        transition-all

        duration-300

        hover:border-cyan-300/40

        hover:bg-cyan-500/20

        hover:shadow-[0_0_20px_rgba(34,211,238,.25)]

        disabled:opacity-60
        "
      >

        <RefreshCw
          size={18}
          className={
            refreshing
              ? "animate-spin"
              : ""
          }
        />

        {refreshing
          ? "Refreshing..."
          : "Refresh"}

      </button>

    </div>

    {/* Body */}

    <div className="p-6">

      <SecurityStatus
        score={score}
      />

      <InsightChips
        score={score}
      />

      <div
        className="
        mt-5

        rounded-2xl

        border

        border-cyan-400/15

        bg-slate-950/45

        p-5
        "
      >

        <div className="mb-4 flex items-center gap-3">

          <ShieldCheck
            size={20}
            className="text-cyan-400"
          />

          <h3
            className="
            text-lg

            font-semibold

            text-white
            "
          >

            AI Executive Summary

          </h3>

        </div>

        {/* Markdown starts here */}

        <div
  className="
  text-slate-200

  [&_h1]:mb-3
  [&_h1]:text-xl
  [&_h1]:font-bold
  [&_h1]:text-white

  [&_h2]:mb-3
  [&_h2]:text-lg
  [&_h2]:font-semibold
  [&_h2]:text-white

  [&_h3]:mb-2
  [&_h3]:font-semibold
  [&_h3]:text-white

  [&_p]:mb-2
  [&_p]:leading-7
  [&_p]:text-slate-300

  [&_strong]:font-semibold
  [&_strong]:text-cyan-300

  [&_ul]:ml-5
  [&_ul]:list-disc

  [&_ol]:ml-5
  [&_ol]:list-decimal

  [&_li]:mb-1
  [&_li]:leading-7
  [&_li]:text-slate-300

  [&_code]:rounded
  [&_code]:bg-cyan-500/10
  [&_code]:px-1
  [&_code]:text-cyan-300

  [&_pre]:overflow-x-auto
  [&_pre]:rounded-xl
  [&_pre]:border
  [&_pre]:border-cyan-400/15
  [&_pre]:bg-slate-950
  [&_pre]:p-4
  "
>

  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
  >
    {summary}
  </ReactMarkdown>

</div>

      </div>

    </div>

    {/* Footer */}

    <div
      className="
      flex

      items-center

      justify-between

      border-t

      border-cyan-400/10

      px-6

      py-3
      "
    >

      <div
        className="
        flex

        items-center

        gap-2

        text-sm

        font-medium

        text-emerald-300
        "
      >

        <div
          className="
          h-2.5

          w-2.5

          rounded-full

          bg-emerald-400

          shadow-[0_0_10px_rgba(74,222,128,.9)]
          "
        />

        Powered by CyberGPT

      </div>

      <div
        className="
        text-sm

        text-slate-400
        "
      >

        {lastUpdated
          ? `Updated ${lastUpdated.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}`
          : "Not Updated"}

      </div>

    </div>

  </div>

);
}