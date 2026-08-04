import type { PasswordReport } from "../../types/report";

interface Props {
  reports: PasswordReport[];
}

export default function PasswordTable({ reports }: Props) {
  if (reports.length === 0) {
    return (
      <div
        className="
        rounded-[28px]

        border

        border-cyan-400/20

        bg-slate-900/55

        p-12

        text-center

        backdrop-blur-2xl

        shadow-[0_0_45px_rgba(34,211,238,.08)]
        "
      >
        <h3 className="text-xl font-bold text-white">
          No Password Reports
        </h3>

        <p className="mt-3 text-slate-400">
          Password scan history will appear here.
        </p>
      </div>
    );
  }

  return (
    <div
      className="
      overflow-hidden

      rounded-[28px]

      border

      border-cyan-400/20

      bg-slate-900/55

      backdrop-blur-2xl

      shadow-[0_0_45px_rgba(34,211,238,.08)]
      "
    >
      <div className="overflow-x-auto">

        <table className="w-full">

          <thead
            className="
            sticky

            top-0

            border-b

            border-cyan-400/15

            bg-slate-950/90

            backdrop-blur-xl
            "
          >
            <tr>

              <th className="px-6 py-5 text-left text-sm font-semibold text-cyan-300">
                Strength
              </th>

              <th className="px-6 py-5 text-center text-sm font-semibold text-cyan-300">
                Score
              </th>

              <th className="px-6 py-5 text-center text-sm font-semibold text-cyan-300">
                Entropy
              </th>

              <th className="px-6 py-5 text-center text-sm font-semibold text-cyan-300">
                Scan Time
              </th>

            </tr>

          </thead>

          <tbody>

            {reports.map((report) => (

              <tr
                key={report.id}
                className="
                border-b

                border-cyan-400/10

                transition-all

                duration-300

                hover:bg-cyan-500/5
                "
              >

                <td className="px-6 py-5">

                  <span
                    className={`
                    inline-flex

                    rounded-full

                    px-3

                    py-1

                    text-xs

                    font-semibold

                    ${
                      report.password_strength === "Strong"
                        ? `
                        border
                        border-emerald-500/20

                        bg-emerald-500/10

                        text-emerald-300
                        `
                        : report.password_strength === "Medium"
                        ? `
                        border
                        border-amber-500/20

                        bg-amber-500/10

                        text-amber-300
                        `
                        : `
                        border
                        border-red-500/20

                        bg-red-500/10

                        text-red-300
                        `
                    }
                    `}
                  >
                    {report.password_strength}
                  </span>

                </td>

                <td className="px-6 py-5 text-center font-semibold text-white">
                  {report.score}
                </td>

                <td className="px-6 py-5 text-center text-slate-300">
                  {report.entropy}
                </td>

                <td className="px-6 py-5 text-center text-slate-400">
                  {new Date(report.created_at).toLocaleString()}
                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </div>
  );
}