import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Area,
  AreaChart,
} from "recharts";

const data = [
  { day: "Mon", threats: 2 },
  { day: "Tue", threats: 4 },
  { day: "Wed", threats: 3 },
  { day: "Thu", threats: 7 },
  { day: "Fri", threats: 5 },
  { day: "Sat", threats: 8 },
  { day: "Sun", threats: 6 },
];

export default function ThreatChart() {
  return (
    <div
      className="
      group
      relative
      overflow-hidden

      h-[340px]

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
      {/* Background Glow */}

      <div
        className="
        absolute
        -top-20
        -right-20

        h-60
        w-60

        rounded-full

        bg-cyan-500/10

        blur-[110px]
        "
      />

      <div className="relative h-full">

        <div className="mb-5">

          <p
            className="
            text-xs
            uppercase
            tracking-[0.25em]
            text-slate-400
            "
          >
            Weekly Analysis
          </p>

          <h2
            className="
            mt-2
            text-2xl
            font-bold
            text-white
            "
          >
            Threat Trend
          </h2>

        </div>

        <ResponsiveContainer
          width="100%"
          height="80%"
        >

          <AreaChart data={data}>

            <defs>

              <linearGradient
                id="threatGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >

                <stop
                  offset="5%"
                  stopColor="#22D3EE"
                  stopOpacity={0.45}
                />

                <stop
                  offset="95%"
                  stopColor="#22D3EE"
                  stopOpacity={0}
                />

              </linearGradient>

            </defs>

            <CartesianGrid
              stroke="#1E293B"
              strokeDasharray="4 4"
            />

            <XAxis
              dataKey="day"
              tick={{
                fill: "#94A3B8",
                fontSize: 12,
              }}
              axisLine={false}
              tickLine={false}
            />

            <YAxis
              tick={{
                fill: "#94A3B8",
                fontSize: 12,
              }}
              axisLine={false}
              tickLine={false}
            />

            <Tooltip
              contentStyle={{
                background: "#0F172A",
                border: "1px solid #22D3EE55",
                borderRadius: "12px",
                color: "#fff",
              }}
              labelStyle={{
                color: "#fff",
              }}
            />

            <Area
              type="monotone"
              dataKey="threats"
              stroke="#22D3EE"
              strokeWidth={0}
              fill="url(#threatGradient)"
            />

            <Line
              type="monotone"
              dataKey="threats"
              stroke="#22D3EE"
              strokeWidth={4}
              dot={{
                fill: "#22D3EE",
                stroke: "#0B1628",
                strokeWidth: 3,
                r: 5,
              }}
              activeDot={{
                r: 8,
                fill: "#67E8F9",
              }}
            />

          </AreaChart>

        </ResponsiveContainer>

      </div>

    </div>
  );
}