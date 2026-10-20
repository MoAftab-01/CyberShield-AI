interface Props {
  found: boolean;
  harmless: number;
  suspicious: number;
  malicious: number;
  threatStatus?: string;
}

export default function VirusTotalCard({
  found,
  harmless,
  suspicious,
  malicious,
  threatStatus,
}: Props) {
  const isUnavailable = threatStatus === "unavailable";
  const isInconclusive = threatStatus === "inconclusive" || (!found && !isUnavailable);
  const isMalicious = threatStatus === "malicious" || malicious > 0;
  const isSuspicious = threatStatus === "suspicious" || (suspicious > 0 && !isMalicious);

  const getBadge = () => {
    if (isUnavailable) {
      return {
        label: "Unavailable",
        className: "border-orange-500/20 bg-orange-500/10 text-orange-300",
      };
    }
    if (isInconclusive) {
      return {
        label: "Inconclusive / Unrated",
        className: "border-cyan-500/20 bg-cyan-500/10 text-cyan-300",
      };
    }
    if (isMalicious) {
      return {
        label: "Malicious Detections",
        className: "border-red-500/20 bg-red-500/10 text-red-300",
      };
    }
    if (isSuspicious) {
      return {
        label: "Suspicious Detections",
        className: "border-amber-500/20 bg-amber-500/10 text-amber-300",
      };
    }
    return {
      label: "Clean / Verified",
      className: "border-emerald-500/20 bg-emerald-500/10 text-emerald-300",
    };
  };

  const badge = getBadge();

  return (
    <div
      className="
      relative
      overflow-hidden
      rounded-[28px]
      border
      border-cyan-400/20
      bg-slate-900/55
      p-6
      backdrop-blur-2xl
      shadow-[0_0_45px_rgba(34,211,238,.08)]
      transition-all
      duration-300
      hover:border-cyan-300/40
      hover:shadow-[0_0_55px_rgba(34,211,238,.15)]
      "
    >
      {/* Glow */}
      <div
        className="
        absolute
        -right-10
        -top-10
        h-40
        w-40
        rounded-full
        bg-cyan-500/10
        blur-[100px]
        "
      />

      <div className="relative">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">
            VirusTotal Intelligence
          </h2>

          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold border ${badge.className}`}
          >
            {badge.label}
          </span>
        </div>

        {!found ? (
          <div
            className={`
            rounded-2xl
            border
            p-5
            text-center
            ${
              isUnavailable
                ? "border-orange-500/20 bg-orange-500/10 text-orange-300"
                : "border-cyan-500/20 bg-cyan-500/10 text-cyan-300"
            }
            `}
          >
            {isUnavailable
              ? "VirusTotal intelligence service is currently unavailable or unconfigured."
              : "No prior scan records found in VirusTotal for this URL (inconclusive / unrated)."}
          </div>
        ) : (


          <div className="grid gap-5 md:grid-cols-3">

            <Metric
              title="Harmless"
              value={harmless}
              color="emerald"
              emoji="✅"
            />

            <Metric
              title="Suspicious"
              value={suspicious}
              color="amber"
              emoji="⚠️"
            />

            <Metric
              title="Malicious"
              value={malicious}
              color="red"
              emoji="🚨"
            />

          </div>

        )}

      </div>

    </div>
  );
}

function Metric({
  title,
  value,
  color,
  emoji,
}: {
  title: string;
  value: number;
  color: "emerald" | "amber" | "red";
  emoji: string;
}) {
  const styles = {
    emerald: {
      border: "border-emerald-500/20",
      bg: "bg-emerald-500/10",
      text: "text-emerald-300",
    },
    amber: {
      border: "border-amber-500/20",
      bg: "bg-amber-500/10",
      text: "text-amber-300",
    },
    red: {
      border: "border-red-500/20",
      bg: "bg-red-500/10",
      text: "text-red-300",
    },
  };

  const theme = styles[color];

  return (
    <div
      className={`
      rounded-2xl

      border

      ${theme.border}

      ${theme.bg}

      p-5

      transition-all

      duration-300

      hover:scale-[1.02]
      `}
    >

      <div className="text-2xl">

        {emoji}

      </div>

      <p
        className="
        mt-3

        text-sm

        text-slate-400
        "
      >
        {title}
      </p>

      <h3
        className={`
        mt-2

        text-3xl

        font-bold

        ${theme.text}
        `}
      >
        {value}
      </h3>

    </div>
  );
}