interface Props {
  title: string;
  detected: boolean;
  values: string[];
}

export default function DetectionCard({
  title,
  detected,
  values,
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

      transition-all

      duration-300

      hover:border-cyan-400/30

      hover:shadow-[0_0_35px_rgba(34,211,238,.08)]
      "
    >

      {/* Glow */}

      <div
        className="
        absolute

        -right-10

        -top-10

        h-32

        w-32

        rounded-full

        bg-cyan-500/10

        blur-3xl
        "
      />

      <div className="relative">

        <div className="flex items-center justify-between">

          <h2
            className="
            text-xl

            font-bold

            text-white
            "
          >
            {title}
          </h2>

          <span
            className={`
            rounded-full

            px-3

            py-1

            text-xs

            font-semibold

            ${
              detected
                ? `
                border
                border-red-500/20

                bg-red-500/10

                text-red-300
                `
                : `
                border
                border-emerald-500/20

                bg-emerald-500/10

                text-emerald-300
                `
            }
            `}
          >
            {detected ? "Detected" : "Clean"}
          </span>

        </div>

        {!detected ? (

          <div
            className="
            mt-6

            rounded-2xl

            border

            border-emerald-500/10

            bg-emerald-500/5

            p-4

            text-emerald-300
            "
          >
            ✅ No issues detected
          </div>

        ) : (

          <div className="mt-5 space-y-3">

            {values.map((item) => (

              <div
                key={item}
                className="
                rounded-xl

                border

                border-red-500/10

                bg-red-500/5

                px-4

                py-3

                text-sm

                text-red-200
                "
              >
                {item}
              </div>

            ))}

          </div>

        )}

      </div>

    </div>
  );
}