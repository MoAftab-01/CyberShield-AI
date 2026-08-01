interface Props {
  valid: boolean;
  https: boolean;
  containsIP: boolean;
  length: number;
  subdomains: number;
}

function Check({
  label,
  ok,
}: {
  label: string;
  ok: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border p-4">
      <span>{label}</span>

      <span
        className={`font-bold ${
          ok ? "text-green-600" : "text-red-600"
        }`}
      >
        {ok ? "✓" : "✗"}
      </span>
    </div>
  );
}

export default function URLChecks({
  valid,
  https,
  containsIP,
  length,
  subdomains,
}: Props) {
  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <h2 className="mb-5 text-xl font-bold">
        URL Properties
      </h2>

      <div className="grid gap-4 md:grid-cols-2">
        <Check label="Valid URL" ok={valid} />
        <Check label="Uses HTTPS" ok={https} />
        <Check label="Contains IP Address" ok={!containsIP} />

        <div className="rounded-lg border p-4">
          <p className="font-semibold">Length</p>
          <p>{length}</p>
        </div>

        <div className="rounded-lg border p-4">
          <p className="font-semibold">Subdomains</p>
          <p>{subdomains}</p>
        </div>
      </div>
    </div>
  );
}