import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from "recharts";

interface SecurityGaugeProps {
  score: number;
}

export default function SecurityGauge({
  score,
}: SecurityGaugeProps) {

  const data = [
    { value: score },
    { value: 100 - score },
  ];

  const getColor = () => {
    if (score >= 90) return "#22d3ee";
    if (score >= 75) return "#38bdf8";
    if (score >= 50) return "#facc15";
    return "#ef4444";
  };

  const getStatus = () => {
    if (score >= 90) return "Excellent";
    if (score >= 75) return "Good";
    if (score >= 50) return "Warning";
    return "Critical";
  };

  return (

    <div
      className="
      group
      relative
      overflow-hidden

      rounded-3xl

      border
      border-cyan-500/25

      bg-[#0B1628]/85
      backdrop-blur-2xl

      p-6

      shadow-xl
      shadow-cyan-950/20

      transition-all
      duration-500

      hover:border-cyan-400/70
      hover:shadow-[0_0_50px_rgba(34,211,238,0.30)]
      "
    >

      {/* Glow */}

      <div
        className="
        absolute
        -top-24
        -right-20

        h-64
        w-64

        rounded-full

        bg-cyan-500/10

        blur-[120px]
        "
      />

      <div className="relative">

        <div className="mb-6">

          <p
            className="
            text-xs
            uppercase
            tracking-[0.25em]
            text-slate-400
            "
          >
            Security Overview
          </p>

          <h2
            className="
            mt-2
            text-2xl
            font-bold
            text-white
            "
          >
            Security Score
          </h2>

        </div>

        <div className="relative h-64">

          <ResponsiveContainer
            width="100%"
            height="100%"
          >

            <PieChart>

              <Pie
                data={data}
                startAngle={90}
                endAngle={-270}
                innerRadius={78}
                outerRadius={96}
                dataKey="value"
                stroke="none"
              >

                <Cell fill={getColor()} />

                <Cell fill="#1E293B" />

              </Pie>

            </PieChart>

          </ResponsiveContainer>

          {/* Center */}

          <div
            className="
            absolute
            inset-0

            flex
            flex-col
            items-center
            justify-center
            "
          >

            <h1
              className="
              text-5xl
              font-bold
              text-white
              "
            >
              {score}%
            </h1>

            <p
              className="
              mt-2
              text-sm
              text-slate-400
              "
            >
              {getStatus()}
            </p>

          </div>

        </div>

      </div>

    </div>

  );
}