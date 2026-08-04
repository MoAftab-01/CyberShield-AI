interface URLSummaryProps {
  riskScore: number;
  riskLevel: string;
  finalRiskScore: number;
  finalRiskLevel: string;
  confidence: number;
  domain: string;
}

export default function URLSummary({
  riskScore,
  riskLevel,
  finalRiskScore,
  finalRiskLevel,
  confidence,
  domain,
}: URLSummaryProps) {
  const cards = [
    {
      title: "Risk Score",
      value: riskScore,
      subtitle: riskLevel,
      gradient: "from-orange-500 to-red-500",
      icon: "⚠️",
    },
    {
      title: "Final Risk",
      value: finalRiskScore,
      subtitle: finalRiskLevel,
      gradient: "from-cyan-500 to-blue-600",
      icon: "🛡️",
    },
    {
      title: "Confidence",
      value: `${confidence}%`,
      subtitle: "AI Confidence",
      gradient: "from-violet-500 to-fuchsia-600",
      icon: "🤖",
    },
    {
      title: "Domain",
      value: domain,
      subtitle: "Extracted Domain",
      gradient: "from-emerald-500 to-teal-600",
      icon: "🌐",
    },
    {
      title: "Status",
      value: finalRiskLevel,
      subtitle: "Overall Verdict",
      gradient: "from-cyan-500 to-sky-600",
      icon: "✅",
    },
  ];

  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-5">

      {cards.map((card) => (

        <div
          key={card.title}
          className="
          group

          relative

          overflow-hidden

          rounded-[28px]

          border

          border-cyan-400/20

          bg-slate-900/55

          p-6

          backdrop-blur-2xl

          transition-all

          duration-300

          hover:-translate-y-1

          hover:border-cyan-300/45

          hover:shadow-[0_0_45px_rgba(34,211,238,.18)]
          "
        >

          {/* Glow */}

          <div
            className="
            absolute

            -right-8

            -top-8

            h-28

            w-28

            rounded-full

            bg-cyan-500/10

            blur-3xl

            opacity-0

            transition-all

            duration-500

            group-hover:opacity-100
            "
          />

          <div className="relative">

            <div
              className={`
              mb-5

              flex

              h-12

              w-12

              items-center

              justify-center

              rounded-2xl

              bg-gradient-to-br

              ${card.gradient}
              `}
            >

              <span className="text-xl">

                {card.icon}

              </span>

            </div>

            <p
              className="
              text-sm

              font-medium

              text-slate-400
              "
            >
              {card.title}
            </p>

            <h2
              className="
              mt-3

              truncate

              text-2xl

              font-bold

              text-white
              "
            >
              {card.value}
            </h2>

            <p
              className="
              mt-3

              text-sm

              text-slate-500
              "
            >
              {card.subtitle}
            </p>

          </div>

        </div>

      ))}

    </div>
  );
}