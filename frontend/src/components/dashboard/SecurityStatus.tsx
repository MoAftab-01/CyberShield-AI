import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
} from "lucide-react";

interface Props {
  score: number;
}

export default function SecurityStatus({
  score,
}: Props) {

  let title = "";
  let message = "";
  let glow = "";
  let border = "";
  let text = "";
  let Icon = ShieldCheck;

  if (score >= 90) {

    title = "EXCELLENT";

    message = "Overall security posture is healthy.";

    glow = "from-emerald-500/20 to-green-500/5";

    border = "border-emerald-400/40";

    text = "text-emerald-400";

    Icon = ShieldCheck;

  }

  else if (score >= 75) {

    title = "GOOD";

    message = "Minor improvements are recommended.";

    glow = "from-cyan-500/20 to-blue-500/5";

    border = "border-cyan-400/40";

    text = "text-cyan-400";

    Icon = ShieldCheck;

  }

  else if (score >= 50) {

    title = "WARNING";

    message = "Several security issues should be reviewed.";

    glow = "from-yellow-500/20 to-orange-500/5";

    border = "border-yellow-400/40";

    text = "text-yellow-400";

    Icon = ShieldAlert;

  }

  else {

    title = "CRITICAL";

    message = "Immediate action is required.";

    glow = "from-red-500/20 to-red-700/5";

    border = "border-red-400/40";

    text = "text-red-400";

    Icon = ShieldX;

  }

  return (

    <div
      className={`
      group
      relative
      overflow-hidden

      rounded-3xl

      border

      ${border}

      bg-[#0B1628]/85
      backdrop-blur-2xl

      p-6

      shadow-xl

      transition-all
      duration-500

      hover:shadow-[0_0_35px_rgba(34,211,238,0.25)]
      `}
    >

      {/* Glow */}

      <div
        className={`
        absolute

        -top-20
        -right-20

        h-56
        w-56

        rounded-full

        bg-gradient-to-br

        ${glow}

        blur-[90px]
        `}
      />

      <div className="relative flex items-center gap-5">

        <div
          className={`
          flex

          h-16
          w-16

          items-center
          justify-center

          rounded-2xl

          border

          ${border}

          bg-slate-900/60

          shadow-[0_0_20px_rgba(34,211,238,0.25)]
          `}
        >

          <Icon
            size={34}
            className={text}
          />

        </div>

        <div className="flex-1">

          <p
            className="
            text-xs

            uppercase

            tracking-[0.25em]

            text-slate-400
            "
          >
            Security Status
          </p>

          <h2
            className={`
            mt-2

            text-3xl

            font-bold

            ${text}
            `}
          >
            {title}
          </h2>

          <p className="mt-2 text-slate-300">
            Security Score
            <span className="ml-2 font-semibold text-white">
              {score}/100
            </span>
          </p>

          <p className="mt-1 text-sm text-slate-400">
            {message}
          </p>

        </div>

      </div>

    </div>

  );

}