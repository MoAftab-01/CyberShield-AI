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
    if (score >= 80) return "#22c55e";
    if (score >= 60) return "#f59e0b";
    return "#ef4444";
  };

  return (
    <div className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm h-[320px]">

      <h2 className="text-xl font-bold text-slate-800 mb-6">
        Security Score
      </h2>

      <div className="h-52">

        <ResponsiveContainer width="100%" height="100%">

          <PieChart>

            <Pie
              data={data}
              startAngle={90}
              endAngle={-270}
              innerRadius={70}
              outerRadius={90}
              dataKey="value"
              stroke="none"
            >

              <Cell fill={getColor()} />
              <Cell fill="#E2E8F0" />

            </Pie>

          </PieChart>

        </ResponsiveContainer>

      </div>

      <div className="-mt-36 text-center">

        <h1 className="text-5xl font-bold">
          {score}%
        </h1>

        <p className="text-slate-500 mt-2">
          Excellent
        </p>

      </div>

    </div>
  );
}