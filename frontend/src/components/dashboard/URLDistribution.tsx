interface Props {
  low: number;
  medium: number;
  high: number;
}

function Row({
  label,
  value,
  max,
}: {
  label: string;
  value: number;
  max: number;
}) {
  const width = max === 0 ? 0 : (value / max) * 100;

  const color =
    label === "Low"
      ? "from-emerald-400 to-green-500"
      : label === "Medium"
      ? "from-yellow-400 to-orange-400"
      : "from-red-500 to-rose-500";

  return (
    <div className="space-y-2">

      <div className="flex items-center justify-between">

        <span className="text-sm font-medium text-slate-300">
          {label}
        </span>

        <span className="text-sm font-semibold text-white">
          {value}
        </span>

      </div>

      <div
        className="
        h-3
        overflow-hidden
        rounded-full
        bg-slate-800
        "
      >

        <div
          className={`
          h-full
          rounded-full
          bg-gradient-to-r
          ${color}

          shadow-[0_0_15px_rgba(34,211,238,0.35)]

          transition-all
          duration-700
          `}
          style={{
            width: `${width}%`,
          }}
        />

      </div>

    </div>
  );
}

export default function URLDistribution({
  low,
  medium,
  high,
}: Props) {

  const max = Math.max(
    low,
    medium,
    high,
  );

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
      hover:shadow-[0_0_45px_rgba(34,211,238,0.25)]
      "
    >

      {/* Glow */}

      <div
        className="
        absolute

        -top-20
        -right-20

        h-52
        w-52

        rounded-full

        bg-cyan-500/10

        blur-[90px]
        "
      />

      <div className="relative">

        <h2
          className="
          mb-6

          text-xl

          font-semibold

          text-white
          "
        >
          URL Risk Distribution
        </h2>

        <div className="space-y-6">

          <Row
            label="Low"
            value={low}
            max={max}
          />

          <Row
            label="Medium"
            value={medium}
            max={max}
          />

          <Row
            label="High"
            value={high}
            max={max}
          />

        </div>

      </div>

    </div>

  );
}