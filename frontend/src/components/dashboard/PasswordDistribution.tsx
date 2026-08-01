interface Props {
  weak: number;
  medium: number;
  strong: number;
}

function Row({
  label,
  value,
  max,
}: {
  label: string;
  value: number;
  max: number;
}) {
  const width = max === 0 ? 0 : (value / max) * 100;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        <span>{value}</span>
      </div>

      <div className="h-3 w-full rounded-full bg-slate-200">
        <div
          className="h-3 rounded-full bg-blue-600 transition-all duration-500"
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

export default function PasswordDistribution({
  weak,
  medium,
  strong,
}: Props) {
  const max = Math.max(weak, medium, strong);

  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <h2 className="mb-6 text-xl font-bold">
        Password Strength Distribution
      </h2>

      <div className="space-y-5">
        <Row label="Weak" value={weak} max={max} />
        <Row label="Medium" value={medium} max={max} />
        <Row label="Strong" value={strong} max={max} />
      </div>
    </div>
  );
}