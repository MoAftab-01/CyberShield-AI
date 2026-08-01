import { useState } from "react";

import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";

import URLSummary from "../components/url/URLSummary";
import URLChecks from "../components/url/URLChecks";
import VirusTotalCard from "../components/url/VirusTotalCard";
import AnalysisSummary from "../components/url/AnalysisSummary";
import Recommendations from "../components/password/Recommendations";

import {
  analyzeURL,
  URLResponse,
} from "../services/urlService";

export default function UrlScanner() {
  const [url, setUrl] = useState("");

  const [result, setResult] =
    useState<URLResponse | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function handleScan(
    e: React.FormEvent
  ) {
    e.preventDefault();

    if (!url.trim()) return;

    setLoading(true);
    setError("");

    try {
      const response = await analyzeURL(url);
      setResult(response);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ??
          "Unable to analyze URL."
      );
    }

    setLoading(false);
  }

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-4xl font-bold text-slate-800">
          URL Security Scanner
        </h1>

        <p className="mt-2 text-slate-500">
          Scan URLs for phishing, malicious indicators, HTTPS usage,
          VirusTotal intelligence, and AI-driven risk analysis.
        </p>
      </section>

      <Card>
        <form onSubmit={handleScan} className="space-y-5">
          <Input
            label="URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            required
          />

          <Button type="submit" loading={loading}>
            Scan URL
          </Button>

          {error && (
            <div className="rounded-lg bg-red-100 p-4 text-red-700">
              {error}
            </div>
          )}
        </form>
      </Card>

      {result && (
        <>
          <URLSummary
            riskScore={result.risk_score}
            riskLevel={result.risk_level}
            finalRiskScore={result.final_risk_score}
            finalRiskLevel={result.final_risk_level}
            confidence={result.confidence}
            domain={result.domain}
          />

          <URLChecks
            valid={result.is_valid_url}
            https={result.uses_https}
            containsIP={result.contains_ip_address}
            length={result.url_length}
            subdomains={result.subdomain_count}
          />

          <VirusTotalCard
            found={result.virustotal_found}
            harmless={result.virustotal_harmless}
            suspicious={result.virustotal_suspicious}
            malicious={result.virustotal_malicious}
          />

          <AnalysisSummary
            summary={result.analysis_summary}
          />

          <Recommendations
            recommendations={result.recommendations}
          />
        </>
      )}
    </div>
  );
}