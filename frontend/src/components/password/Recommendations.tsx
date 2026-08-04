interface Props {
  recommendations: string[];
}

export default function Recommendations({
  recommendations,
}: Props) {
  return (
    <div
      className="
      relative

      overflow-hidden

      rounded-3xl

      border

      border-cyan-500/10

      bg-slate-900/40

      p-6

      backdrop-blur-2xl

      shadow-[0_0_35px_rgba(34,211,238,.08)]
      "
    >

      {/* Glow */}

      <div
        className="
        absolute

        right-0

        top-0

        h-40

        w-40

        rounded-full

        bg-cyan-500/10

        blur-[100px]
        "
      />

      <div className="relative">

        <h2
          className="
          mb-6

          text-2xl

          font-bold

          text-white
          "
        >
          AI Recommendations
        </h2>

        <div className="space-y-4">

          {recommendations.map((item, index) => (

            <div
              key={item}
              className="
              flex

              gap-4

              rounded-2xl

              border

              border-cyan-500/10

              bg-slate-900/50

              p-4

              transition-all

              duration-300

              hover:border-cyan-400/25
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