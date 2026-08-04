interface Props {
  summary: string[];
}

export default function AnalysisSummary({
  summary,
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

      p-6

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

        right-0

        top-0

        h-44

        w-44

        rounded-full

        bg-cyan-500/10

        blur-[110px]
        "
      />

      <div className="relative">

        <div className="flex items-center gap-4 mb-6">

          <div
            className="
            flex

            h-12

            w-12

            items-center

            justify-center

            rounded-2xl

            bg-gradient-to-br

            from-cyan-400

            via-cyan-500

            to-blue-600

            shadow-[0_0_25px_rgba(34,211,238,.35)]
            "
          >
            🤖
          </div>

          <div>

            <h2
              className="
              text-2xl

              font-bold

              text-white
              "
            >
              AI Analysis Summary
            </h2>

            <p className="text-sm text-slate-400">
              AI-generated security observations
            </p>

          </div>

        </div>

        <div className="space-y-4">

          {summary.map((item, index) => (

            <div
              key={item}
              className="
              flex

              gap-4

              rounded-2xl

              border

              border-cyan-400/15

              bg-slate-900/45

              p-4

              transition-all

              duration-300

              hover:border-cyan-300/35

              hover:bg-slate-900/60
              "
            >

              <div
                className="
                flex

                h-8

                w-8

                flex-shrink-0

                items-center

                justify-center

                rounded-full

                bg-gradient-to-br

                from-cyan-500

                to-blue-600

                text-sm

                font-bold

                text-white
                "
              >
                {index + 1}
              </div>

              <p
                className="
                leading-7

                text-slate-300
                "
              >
                {item}
              </p>

            </div>

          ))}

        </div>

      </div>

    </div>
  );
}