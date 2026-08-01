interface Props {
  summary: string[];
}

export default function AnalysisSummary({
  summary,
}: Props) {
  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-bold">
        AI Analysis Summary
      </h2>

      <ul className="list-disc space-y-2 pl-6">
        {summary.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}