import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle: string;
  icon: LucideIcon;
  suffix?: string;
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  suffix = "",
}: StatCardProps) {
  return (
    <div
      className="
      group
      relative
      overflow-hidden

      rounded-3xl

      border
      border-cyan-500/30

      bg-[#0B1628]/85
      backdrop-blur-2xl

      p-6

      shadow-2xl
      shadow-cyan-950/30

      transition-all
      duration-500

      hover:-translate-y-1
      hover:border-cyan-300/90
      hover:shadow-[0_0_45px_rgba(34,211,238,0.35)]
      "
    >
      {/* Animated Glow Border */}

      <div
        className="
        absolute
        inset-0
        rounded-3xl
        opacity-0
        transition-all
        duration-500
        group-hover:opacity-100
        "
      >
        <div
          className="
          absolute
          inset-0
          rounded-3xl

          ring-2
          ring-cyan-300/60

          shadow-[0_0_15px_rgba(34,211,238,0.45),0_0_35px_rgba(34,211,238,0.35),0_0_70px_rgba(59,130,246,0.30)]
          "
        />
      </div>

      {/* Top Right Glow */}

      <div
        className="
        absolute
        -top-16
        -right-16

        h-44
        w-44

        rounded-full

        bg-cyan-400/15

        blur-[80px]
        "
      />

      {/* Bottom Left Glow */}

      <div
        className="
        absolute
        -bottom-10
        -left-10

        h-32
        w-32

        rounded-full

        bg-blue-500/10

        blur-[70px]
        "
      />

      <div className="relative flex items-start justify-between">

        <div>

          <p
            className="
            text-xs
            uppercase
            tracking-[0.22em]
            text-slate-400
            "
          >
            {title}
          </p>

          <h2
            className="
            mt-4
            text-4xl
            font-bold
            text-white
            "
          >
            {value}
            {suffix}
          </h2>

          <p
            className="
            mt-2
            text-sm
            text-slate-400
            "
          >
            {subtitle}
          </p>

        </div>

        <div
          className="
          flex
          h-14
          w-14
          items-center
          justify-center

          rounded-2xl

          bg-gradient-to-br
          from-cyan-400
          via-sky-500
          to-blue-600

          shadow-[0_0_30px_rgba(34,211,238,0.45)]

          transition-all
          duration-500

          group-hover:scale-110
          group-hover:rotate-6
          "
        >
          <Icon
            className="
            h-7
            w-7
            text-white
            "
          />
        </div>

      </div>

      {/* Accent Line */}

      <div
        className="
        mt-6
        h-1
        w-16
        rounded-full

        bg-gradient-to-r

        from-cyan-400

        via-sky-400

        to-blue-500

        shadow-[0_0_15px_rgba(34,211,238,0.7)]
        "
      />

    </div>
  );
}