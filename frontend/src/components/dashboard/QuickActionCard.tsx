import { ArrowRight, type LucideIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface QuickActionCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  route: string;
}

export default function QuickActionCard({
  title,
  description,
  icon: Icon,
  route,
}: QuickActionCardProps) {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate(route)}
      className="
      group
      relative
      w-full
      overflow-hidden

      rounded-[28px]

      border
      border-cyan-400/20

      bg-slate-900/55

      p-7

      text-left

      backdrop-blur-2xl

      shadow-[0_0_35px_rgba(34,211,238,.08)]

      transition-all
      duration-500

      hover:-translate-y-2

      hover:border-cyan-300/50

      hover:shadow-[0_0_50px_rgba(34,211,238,.18)]
      "
    >
      {/* Ambient Glow */}

      <div
        className="
        absolute

        -right-12

        -top-12

        h-44

        w-44

        rounded-full

        bg-cyan-500/10

        blur-[90px]

        transition-all

        duration-700

        group-hover:scale-125

        group-hover:bg-cyan-500/20
        "
      />

      <div className="relative">

        {/* Icon */}

        <div
          className="
          mb-6

          flex

          h-16
          w-16

          items-center
          justify-center

          rounded-2xl

          bg-gradient-to-br

          from-cyan-400

          via-cyan-500

          to-blue-600

          shadow-[0_0_30px_rgba(34,211,238,.35)]

          transition-all

          duration-300

          group-hover:scale-110
          "
        >
          <Icon
            size={30}
            className="text-white"
          />
        </div>

        {/* Title */}

        <h3
          className="
          text-xl

          font-bold

          tracking-tight

          text-white
          "
        >
          {title}
        </h3>

        {/* Description */}

        <p
          className="
          mt-3

          leading-7

          text-slate-400
          "
        >
          {description}
        </p>

        {/* Footer */}

        <div
          className="
          mt-8

          flex

          items-center

          justify-between
          "
        >
          <span
            className="
            rounded-full

            border
            border-cyan-400/20

            bg-cyan-500/10

            px-4

            py-2

            text-sm

            font-semibold

            text-cyan-300
            "
          >
            Launch
          </span>

          <ArrowRight
            size={22}
            className="
            text-cyan-300

            transition-all

            duration-300

            group-hover:translate-x-2

            group-hover:text-cyan-200
            "
          />
        </div>

      </div>

    </button>
  );
}