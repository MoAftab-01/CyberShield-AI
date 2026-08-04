interface Props {

  score: number;

}

export default function InsightChips({

  score,

}: Props) {

  let chips: string[] = [];

  if (score >= 90) {

    chips = [

      "✅ Excellent Security",

      "🛡 Strong Overall Posture",

      "🔍 Continue Monitoring",

      "🚀 Low Risk Environment",

    ];

  }

  else if (score >= 75) {

    chips = [

      "✅ Good Security",

      "⚠ Minor Improvements",

      "🔍 Review Recent Activity",

      "🛡 Monitor Threats",

    ];

  }

  else if (score >= 50) {

    chips = [

      "⚠ Security Needs Attention",

      "🔐 Improve Password Hygiene",

      "🌐 Review URL Activity",

      "📈 Monitor CVEs",

    ];

  }

  else {

    chips = [

      "🔥 Critical Security Issues",

      "⚠ Immediate Action Required",

      "🛑 High Risk Environment",

      "🚨 Review Threat Intelligence",

    ];

  }

  return (

    <div
  className="
  mt-5

  flex

  flex-wrap

  gap-3
  "
>

      {

        chips.map(

          (

            chip,

            index,

          ) => (

            <span

              key={index}

              className="
inline-flex

items-center

rounded-full

border

border-slate-700

bg-slate-800/70

px-5

py-3

text-sm

font-medium

text-slate-300

transition-all

hover:border-cyan-400/40

hover:bg-cyan-500/10
"

            >

              {chip}

            </span>

          ),

        )

      }

    </div>

  );

}