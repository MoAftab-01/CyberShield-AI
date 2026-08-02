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
  let bg = "";
  let border = "";
  let text = "";
  let Icon = ShieldCheck;

  if (score >= 90) {

    title = "EXCELLENT";

    message = "Overall security posture is healthy.";

    bg = "bg-green-500/15";

    border = "border-green-500/30";

    text = "text-green-400";

    Icon = ShieldCheck;

  }

  else if (score >= 75) {

    title = "GOOD";

    message = "Minor improvements are recommended.";

    bg = "bg-cyan-500/15";

    border = "border-cyan-500/30";

    text = "text-cyan-400";

    Icon = ShieldCheck;

  }

  else if (score >= 50) {

    title = "WARNING";

    message = "Several security issues should be reviewed.";

    bg = "bg-yellow-500/15";

    border = "border-yellow-500/30";

    text = "text-yellow-400";

    Icon = ShieldAlert;

  }

  else {

    title = "CRITICAL";

    message = "Immediate action is required.";

    bg = "bg-red-500/15";

    border = "border-red-500/30";

    text = "text-red-400";

    Icon = ShieldX;

  }

  return (

    <div
      className={`
        ${bg}
        ${border}
        border
        rounded-2xl
        p-6
        mb-8
      `}
    >

      <div className="flex items-center gap-4">

        <Icon
          className={text}
          size={34}
        />

        <div>

          <p className="text-slate-400 text-sm uppercase tracking-wider">

            Security Status

          </p>

          <h2 className={`text-3xl font-bold ${text}`}>

            {title}

          </h2>

          <p className="text-slate-300 mt-2">

            Security Score: {score}/100

          </p>

          <p className="text-slate-400 mt-1">

            {message}

          </p>

        </div>

      </div>

    </div>

  );

}