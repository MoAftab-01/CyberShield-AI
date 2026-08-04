interface Props {
  valid: boolean;
  https: boolean;
  containsIP: boolean;
  length: number;
  subdomains: number;
}

function StatusCard({
  label,
  ok,
}: {
  label: string;
  ok: boolean;
}) {
  return (
    <div
      className="
      flex

      items-center

      justify-between

      rounded-2xl

      border

      border-cyan-400/20

      bg-slate-900/45

      px-5

      py-4

      backdrop-blur-xl

      transition-all

      duration-300

      hover:border-cyan-300/40

      hover:shadow-[0_0_30px_rgba(34,211,238,.12)]
      "
    >
      <span className="font-medium text-slate-200">
        {label}
      </span>

      <span
        className={`
        rounded-full

        px-3

        py-1

        text-xs

        font-semibold

        ${
          ok
            ? `
            border
            border-emerald-500/20

            bg-emerald-500/10

            text-emerald-300
            `
            : `
            border
            border-red-500/20

            bg-red-500/10

            text-red-300
            `
        }
        `}
      >
        {ok ? "✓ Pass" : "✕ Fail"}
      </span>
    </div>
  );
}

function MetricCard({
  title,
  value,
}: {
  title: string;
  value: number;
}) {
  return (
    <div
      className="
      rounded-2xl

      border

      border-cyan-400/20

      bg-slate-900/45

      p-5

      backdrop-blur-xl

      transition-all

      duration-300

      hover:border-cyan-300/40

      hover:shadow-[0_0_30px_rgba(34,211,238,.12)]
      "
    >
      <p className="text-sm text-slate-400">
        {title}
      </p>

      <h3
        className="
        mt-3

        text-3xl

        font-bold

        text-white
        "
      >
        {value}
      </h3>
    </div>
  );
}

export default function URLChecks({
  valid,
  https,
  containsIP,
  length,
  subdomains,
}: Props) {
  return (
    <div
      className="
      rounded-[28px]

      border

      border-cyan-400/20

      bg-slate-900/55

      p-6

      backdrop-blur-2xl

      shadow-[0_0_45px_rgba(34,211,238,.08)]
      "
    >
      <h2
        className="
        mb-6

        text-2xl

        font-bold

        text-white
        "
      >
        URL Properties
      </h2>

      <div className="grid gap-4 md:grid-cols-2">

        <StatusCard
          label="Valid URL"
          ok={valid}
        />

        <StatusCard
          label="HTTPS Enabled"
          ok={https}
        />

        <StatusCard
          label="No IP Address"
          ok={!containsIP}
        />

        <MetricCard
          title="URL Length"
          value={length}
        />

        <MetricCard
          title="Subdomains"
          value={subdomains}
        />

      </div>

    </div>
  );
}