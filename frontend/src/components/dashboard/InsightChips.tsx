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

    <div className="flex flex-wrap gap-3 mb-8">

      {

        chips.map(

          (

            chip,

            index,

          ) => (

            <span

              key={index}

              className="
                rounded-full
                bg-slate-800
                border
                border-slate-700
                px-4
                py-2
                text-sm
                text-slate-200
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