import type { URLReport } from "../../types/report";

interface Props {
  reports: URLReport[];
}

export default function URLTable({ reports }: Props) {
  if (reports.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm">
        <h3 className="text-lg font-semibold text-slate-700">
          No URL Reports
        </h3>

        <p className="mt-2 text-slate-500">
          URL scan history will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">

      <div className="overflow-x-auto">

        <table className="w-full table-fixed">

          <thead className="sticky top-0 bg-slate-50">

            <tr className="border-b border-slate-200">

              <th className="w-[25%] px-6 py-4 text-left text-sm font-semibold text-slate-700">
                Domain
              </th>

              <th className="w-[15%] px-6 py-4 text-center text-sm font-semibold text-slate-700">
                Risk
              </th>

              <th className="w-[10%] px-6 py-4 text-center text-sm font-semibold text-slate-700">
                Score
              </th>

              <th className="w-[15%] px-6 py-4 text-center text-sm font-semibold text-slate-700">
                Confidence
              </th>

              <th className="w-[10%] px-6 py-4 text-center text-sm font-semibold text-slate-700">
                HTTPS
              </th>

              <th className="w-[25%] px-6 py-4 text-center text-sm font-semibold text-slate-700">
                Scan Time
              </th>

            </tr>

          </thead>

          <tbody>

            {reports.map((report) => (

              <tr
                key={report.id}
                className="border-b border-slate-100 transition hover:bg-slate-50"
              >

                <td className="px-6 py-4">

                  <div className="font-medium text-slate-700">
                    {report.domain}
                  </div>

                  <div className="truncate text-xs text-slate-400">
                    {report.url}
                  </div>

                </td>

                <td className="px-6 py-4 text-center">

                  <span
                    className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold
                    ${
                      report.final_risk_level === "Low"
                        ? "bg-green-100 text-green-700"
                        : report.final_risk_level === "Medium"
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {report.final_risk_level}
                  </span>

                </td>

                <td className="px-6 py-4 text-center font-semibold">
                  {report.final_risk_score}
                </td>

                <td className="px-6 py-4 text-center">
                  {report.confidence}%
                </td>

                <td className="px-6 py-4 text-center">

                  <span
                    className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold
                    ${
                      report.uses_https
                        ? "bg-blue-100 text-blue-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {report.uses_https ? "HTTPS" : "HTTP"}
                  </span>

                </td>

                <td className="px-6 py-4 text-center text-slate-500">
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