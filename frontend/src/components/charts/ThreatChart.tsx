import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
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
    <div className="h-[320px] rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-6 text-xl font-bold text-slate-800">
        Threat Trend
      </h2>

      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="day" />

          <YAxis />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="threats"
            stroke="#06b6d4"
            strokeWidth={3}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}