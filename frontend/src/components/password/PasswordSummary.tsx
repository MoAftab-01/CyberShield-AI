interface PasswordSummaryProps {
  strength: string;
  score: number;
  entropy: number;
  entropyRating: string;
  riskScore: number;
  riskLevel: string;
}

export default function PasswordSummary({
  strength,
  score,
  entropy,
  entropyRating,
  riskScore,
  riskLevel,
}: PasswordSummaryProps) {
  const cards = [
    {
      title: "Strength",
      value: strength,
      subtitle: "Overall Rating",
      color: "from-cyan-500 to-blue-600",
    },
    {
      title: "Score",
      value: `${score}/100`,
      subtitle: "Security Score",
      color: "from-violet-500 to-fuchsia-600",
    },
    {
      title: "Entropy",
      value: entropy.toFixed(2),
      subtitle: entropyRating,
      color: "from-emerald-500 to-teal-600",
    },
    {
      title: "Risk",
      value: riskScore,
      subtitle: riskLevel,
      color: "from-orange-500 to-amber-500",
    },
  ];

  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">

      {cards.map((card) => (

        <div
          key={card.title}
          className="
          group

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

          hover:-translate-y-1

          hover:border-cyan-400/30

          hover:shadow-[0_0_35px_rgba(34,211,238,.12)]
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

              ${card.color}
              `}
            >
              <span className="text-xl">🔐</span>
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

              text-3xl

              font-bold

              tracking-tight

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