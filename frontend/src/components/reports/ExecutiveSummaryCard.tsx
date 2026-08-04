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
    <div
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

      transition-all

      duration-300

      hover:border-cyan-300/40

      hover:shadow-[0_0_55px_rgba(34,211,238,.15)]
      "
    >

      {/* Ambient Glow */}

      <div
        className="
        absolute

        -right-16

        -top-16

        h-60

        w-60

        rounded-full

        bg-cyan-500/10

        blur-[120px]
        "
      />

      <div className="relative">

        <div className="flex items-center justify-between">

          <div className="flex items-center gap-5">

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

              shadow-[0_0_30px_rgba(34,211,238,.35)]
              "
            >

              <Brain
                size={30}
                className="text-white"
              />

            </div>

            <div>

              <h2
                className="
                text-2xl

                font-bold

                text-white
                "
              >
                AI Executive Summary
              </h2>

              <p className="text-slate-400">
                Enterprise Security Overview
              </p>

            </div>

          </div>

          <button
            onClick={onRefresh}
            className="
            flex

            h-12

            w-12

            items-center

            justify-center

            rounded-2xl

            border

            border-cyan-400/20

            bg-slate-900/50

            text-cyan-300

            transition-all

            duration-300

            hover:border-cyan-300/40

            hover:bg-cyan-500/10

            hover:shadow-[0_0_25px_rgba(34,211,238,.20)]
            "
          >

            <RefreshCw
              size={20}
              className={loading ? "animate-spin" : ""}
            />

          </button>

        </div>

        <div
          className="
          mt-8

          rounded-2xl

          border

          border-cyan-400/15

          bg-slate-900/45

          p-6
          "
        >

          <p
            className="
            whitespace-pre-wrap

            leading-8

            text-slate-300
            "
          >
            {loading
              ? "Generating AI executive summary..."
              : summary}
          </p>

        </div>

      </div>

    </div>
  );
}