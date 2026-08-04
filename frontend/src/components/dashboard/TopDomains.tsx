import {
  Globe,
  TrendingUp,
} from "lucide-react";

interface Domain {
  domain: string;
  count: number;
}

interface Props {
  domains: Domain[];
}

export default function TopDomains({
  domains,
}: Props) {
  return (
    <div
      className="
      group
      relative
      overflow-hidden

      rounded-3xl

      border
      border-cyan-500/25

      bg-[#0B1628]/85
      backdrop-blur-2xl

      p-6

      shadow-xl
      shadow-cyan-950/20

      transition-all
      duration-500

      hover:border-cyan-400/70
      hover:shadow-[0_0_45px_rgba(34,211,238,0.25)]
      "
    >

      {/* Glow */}

      <div
        className="
        absolute
        -top-20
        -right-20

        h-52
        w-52

        rounded-full

        bg-cyan-500/10

        blur-[90px]
        "
      />

      <div className="relative">

        {/* Header */}

        <div className="mb-6 flex items-center justify-between">

          <div>

            <h2
              className="
              text-xl
              font-semibold
              text-white
              "
            >
              Top Scanned Domains
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              Most frequently analyzed websites
            </p>

          </div>

          <div
            className="
            flex
            h-12
            w-12
            items-center
            justify-center

            rounded-2xl

            bg-gradient-to-br
            from-cyan-400
            to-blue-600

            shadow-[0_0_25px_rgba(34,211,238,0.35)]
            "
          >
            <Globe
              size={22}
              className="text-white"
            />
          </div>

        </div>

        {/* Empty State */}

        {domains.length === 0 ? (

          <div
            className="
            rounded-2xl

            border

            border-dashed

            border-slate-700

            py-10

            text-center

            text-slate-400
            "
          >
            No domains scanned yet.
          </div>

        ) : (

          <div className="space-y-4">

            {domains.map((domain, index) => (

              <div
                key={domain.domain}
                className="
                flex
                items-center
                justify-between

                rounded-2xl

                border

                border-slate-800

                bg-slate-900/50

                px-4
                py-3

                transition-all
                duration-300

                hover:border-cyan-500/40
                hover:bg-slate-900
                "
              >

                <div className="flex items-center gap-3">

                  <div
                    className="
                    flex

                    h-9
                    w-9

                    items-center
                    justify-center

                    rounded-xl

                    bg-cyan-500/10
                    "
                  >
                    <Globe
                      size={18}
                      className="text-cyan-400"
                    />
                  </div>

                  <div>

                    <p className="font-medium text-white">
                      {domain.domain}
                    </p>

                    <p className="text-xs text-slate-500">
                      Rank #{index + 1}
                    </p>

                  </div>

                </div>

                <div
                  className="
                  flex
                  items-center
                  gap-2

                  rounded-full

                  bg-cyan-500/10

                  px-3
                  py-1.5

                  text-cyan-300
                  "
                >

                  <TrendingUp size={14} />

                  <span className="font-semibold">
                    {domain.count}
                  </span>

                </div>

              </div>

            ))}

          </div>

        )}

      </div>

    </div>
  );
}