interface Props {
  found: boolean;
  harmless: number;
  suspicious: number;
  malicious: number;
}

export default function VirusTotalCard({
  found,
  harmless,
  suspicious,
  malicious,
}: Props) {
  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-bold">
        VirusTotal
      </h2>

      {!found ? (
        <p>No VirusTotal data available.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          <Metric title="Harmless" value={harmless} />
          <Metric title="Suspicious" value={suspicious} />
          <Metric title="Malicious" value={malicious} />
        </div>
      )}
    </div>
  );
}

function Metric({
  title,
  value,
}: {
  title: string;
  value: number;
}) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm text-slate-500">{title}</p>
      <h3 className="mt-2 text-2xl font-bold">{value}</h3>
    </div>
  );
}