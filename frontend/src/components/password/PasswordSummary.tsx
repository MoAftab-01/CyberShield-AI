interface PasswordSummaryProps {
  strength: string;
  score: number;
  entropy: number;
  entropyRating: string;
  riskScore: number;
  riskLevel: string;
}

export default function PasswordSummary({
  strength,
  score,
  entropy,
  entropyRating,
  riskScore,
  riskLevel,
}: PasswordSummaryProps) {
  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
      <div className="rounded-2xl border bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Strength</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-800">
          {strength}
        </h2>
      </div>

      <div className="rounded-2xl border bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Score</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-800">
          {score}/100
        </h2>
      </div>

      <div className="rounded-2xl border bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Entropy</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-800">
          {entropy.toFixed(2)}
        </h2>

        <p className="mt-2 text-sm text-slate-500">
          {entropyRating}
        </p>
      </div>

      <div className="rounded-2xl border bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">Risk</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-800">
          {riskScore}
        </h2>

        <p className="mt-2 text-sm text-slate-500">
          {riskLevel}
        </p>
      </div>
    </div>
  );
}