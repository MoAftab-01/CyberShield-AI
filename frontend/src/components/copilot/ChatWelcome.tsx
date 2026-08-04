import {
  Shield,
  Search,
  FileSearch,
  Bug,
} from "lucide-react";

import type { LucideIcon } from "lucide-react";

interface Props {
  onSuggestion: (text: string) => void;
}

interface Suggestion {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  prompt: string;

  border: string;
  gradient: string;
  glow: string;
  orb: string;
  iconShadow: string;
}

const suggestions: Suggestion[] = [
  {
    title: "Analyze CVE",
    subtitle: "Investigate vulnerabilities",
    icon: Shield,
    prompt: "Analyze CVE-2024-4577",

    border:
      "border-cyan-400/35 hover:border-cyan-300/80",

    gradient:
      "from-cyan-500 via-sky-500 to-blue-600",

    glow:
      "hover:shadow-[0_0_45px_rgba(34,211,238,.28)]",

    orb:
      "bg-cyan-500/25",

    iconShadow:
      "shadow-[0_0_28px_rgba(34,211,238,.55)]",
  },

  {
    title: "Threat Hunting",
    subtitle: "Search attack patterns",
    icon: Search,
    prompt:
      "Find indicators of compromise for ransomware",

    border:
      "border-violet-400/35 hover:border-violet-300/80",

    gradient:
      "from-violet-500 via-fuchsia-500 to-purple-600",

    glow:
      "hover:shadow-[0_0_45px_rgba(168,85,247,.28)]",

    orb:
      "bg-violet-500/25",

    iconShadow:
      "shadow-[0_0_28px_rgba(168,85,247,.55)]",
  },

  {
    title: "Analyze Report",
    subtitle: "Summarize uploaded reports",
    icon: FileSearch,
    prompt:
      "Summarize the uploaded security report",

    border:
      "border-orange-400/35 hover:border-orange-300/80",

    gradient:
      "from-orange-500 via-amber-500 to-yellow-500",

    glow:
      "hover:shadow-[0_0_45px_rgba(251,146,60,.28)]",

    orb:
      "bg-orange-500/25",

    iconShadow:
      "shadow-[0_0_28px_rgba(251,146,60,.55)]",
  },

  {
    title: "MITRE ATT&CK",
    subtitle: "Explain attack techniques",
    icon: Bug,
    prompt:
      "Explain MITRE ATT&CK T1059",

    border:
      "border-emerald-400/35 hover:border-emerald-300/80",

    gradient:
      "from-emerald-500 via-teal-500 to-green-600",

    glow:
      "hover:shadow-[0_0_45px_rgba(16,185,129,.28)]",

    orb:
      "bg-emerald-500/25",

    iconShadow:
      "shadow-[0_0_28px_rgba(16,185,129,.55)]",
  },
];

export default function ChatWelcome({
  onSuggestion,
}: Props) {
  return (
  <div className="mx-auto max-w-4xl">

    {/* Hero */}

    <div className="mb-6 text-center">

      <div
        className="
        relative
        mx-auto
        mb-4
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
        shadow-[0_0_45px_rgba(34,211,238,.55)]
        "
      >

        <div
          className="
          absolute
          inset-0
          rounded-2xl
          bg-cyan-400/20
          blur-xl
          "
        />

        <Shield
          size={32}
          className="relative text-white"
        />

      </div>

      <h1 className="text-3xl font-bold tracking-tight text-white">
        CyberGPT
      </h1>

      <p className="mt-2 text-base text-slate-400">
        How can I help you today?
      </p>

    </div>

    {/* Quick Actions */}

    <div
      className="
      grid
      gap-4
      md:grid-cols-2
      "
    >

      {suggestions.map((item) => {

        const Icon = item.icon;

        return (

          <button
            key={item.title}
            onClick={() => onSuggestion(item.prompt)}
            className={`
            group
            relative
            overflow-hidden

            min-h-[115px]

            rounded-[24px]

            border

            ${item.border}

            bg-slate-900/75

            backdrop-blur-2xl

            p-5

            text-left

            transition-all

            duration-500

            hover:-translate-y-1

            hover:scale-[1.015]

            ${item.glow}
            `}
          >

            {/* Ambient Orb */}

            <div
              className={`
              absolute
              -right-12
              -top-12

              h-44
              w-44

              rounded-full

              ${item.orb}

              opacity-40

              blur-[90px]

              transition-all

              duration-700

              group-hover:scale-125

              group-hover:opacity-70
              `}
            />

            <div className="relative flex items-start justify-between">

              <div className="flex gap-3">

                <div
                  className={`
                  flex
                  h-12
                  w-12
                  flex-shrink-0
                  items-center
                  justify-center
                  rounded-xl
                  bg-gradient-to-br
                  ${item.gradient}
                  ${item.iconShadow}
                  `}
                >

                  <Icon
                    size={22}
                    className="text-white"
                  />

                </div>

                <div>

                  <h3
                    className="
                    text-lg
                    font-semibold
                    text-white
                    "
                  >
                    {item.title}
                  </h3>

                  <p
                    className="
                    mt-1
                    text-sm
                    leading-5
                    text-slate-400
                    "
                  >
                    {item.subtitle}
                  </p>

                </div>

              </div>

              <div
                className="
                translate-x-2

                opacity-0

                text-xl

                text-white

                transition-all

                duration-300

                group-hover:translate-x-0

                group-hover:opacity-100
                "
              >
                →
              </div>

            </div>

          </button>

        );

      })}

    </div>

  </div>
);
}