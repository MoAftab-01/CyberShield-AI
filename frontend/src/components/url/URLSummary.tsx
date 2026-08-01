interface URLSummaryProps {
  riskScore: number;
  riskLevel: string;
  finalRiskScore: number;
  finalRiskLevel: string;
  confidence: number;
  domain: string;
}

export default function URLSummary({
  riskScore,
  riskLevel,
  finalRiskScore,
  finalRiskLevel,
  confidence,
  domain,
}: URLSummaryProps) {
  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-5">
      <Card title="Risk Score" value={riskScore} subtitle={riskLevel} />
      <Card
        title="Final Risk"
        value={finalRiskScore}
        subtitle={finalRiskLevel}
      />
      <Card title="Confidence" value={`${confidence}%`} subtitle="AI Confidence" />
      <Card title="Domain" value={domain} subtitle="Extracted Domain" />
      <Card title="Status" value={finalRiskLevel} subtitle="Overall Verdict" />
    </div>
  );
}

function Card({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string | number;
  subtitle: string;
}) {
  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <p className="text-sm text-slate-500">{title}</p>

      <h2 className="mt-2 text-2xl font-bold text-slate-800">
        {value}
      </h2>

      <p className="mt-2 text-sm text-slate-500">
        {subtitle}
      </p>
    </div>
  );
}