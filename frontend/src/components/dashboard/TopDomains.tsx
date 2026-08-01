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
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <h2 className="mb-6 text-xl font-bold">
        Top Scanned Domains
      </h2>

      {domains.length === 0 ? (
        <p className="text-slate-500">
          No domains scanned yet.
        </p>
      ) : (
        <div className="space-y-4">
          {domains.map((domain) => (
            <div
              key={domain.domain}
              className="flex items-center justify-between border-b pb-2"
            >
              <span className="font-medium">
                {domain.domain}
              </span>

              <span className="rounded-full bg-slate-100 px-3 py-1 text-sm">
                {domain.count}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}