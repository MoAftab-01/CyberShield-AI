interface ActivityCardProps {
  title: string;
  time: string;
  status: "success" | "warning" | "danger";
}

const statusColors = {
  success: "bg-emerald-400",
  warning: "bg-amber-400",
  danger: "bg-red-400",
};

const badgeStyles = {
  success:
    "border border-emerald-500/20 bg-emerald-500/10 text-emerald-300",

  warning:
    "border border-amber-500/20 bg-amber-500/10 text-amber-300",

  danger:
    "border border-red-500/20 bg-red-500/10 text-red-300",
};

export default function ActivityCard({
  title,
  time,
  status,
}: ActivityCardProps) {
  return (
    <div
      className="
      group

      flex

      items-center

      justify-between

      rounded-[24px]

      border

      border-cyan-400/20

      bg-slate-900/55

      p-6

      backdrop-blur-2xl

      shadow-[0_0_35px_rgba(34,211,238,.08)]

      transition-all

      duration-300

      hover:-translate-y-1

      hover:border-cyan-300/40

      hover:shadow-[0_0_45px_rgba(34,211,238,.18)]
      "
    >

      <div className="flex items-center gap-5">

        <div
          className={`
          h-3
          w-3

          rounded-full

          shadow-[0_0_12px_rgba(255,255,255,.35)]

          ${statusColors[status]}
          `}
        />

        <div>

          <h4
            className="
            text-lg

            font-semibold

            text-white
            "
          >
            {title}
          </h4>

          <p
            className="
            mt-1

            text-sm

            text-slate-400
            "
          >
            {time}
          </p>

        </div>

      </div>

      <span
        className={`
        rounded-full

        px-4

        py-2

        text-xs

        font-semibold

        uppercase

        tracking-wide

        ${badgeStyles[status]}
        `}
      >
        {status}
      </span>

    </div>
  );
}