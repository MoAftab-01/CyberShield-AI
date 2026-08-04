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
  <div className="mx-auto max-w-7xl space-y-8">

    {/* Header */}

    <section
      className="
      relative

      overflow-hidden

      rounded-[28px]

      border

      border-cyan-400/20

      bg-slate-900/55

      p-8

      backdrop-blur-2xl

      shadow-[0_0_45px_rgba(34,211,238,.08)]
      "
    >

      <div
        className="
        absolute

        -right-20

        -top-20

        h-64

        w-64

        rounded-full

        bg-cyan-500/10

        blur-[120px]
        "
      />

      <div className="relative flex items-center gap-6">

        <div
          className="
          flex

          h-16

          w-16

          items-center

          justify-center

          rounded-3xl

          bg-gradient-to-br

          from-cyan-400

          via-cyan-500

          to-blue-600

          shadow-[0_0_35px_rgba(34,211,238,.35)]

          text-3xl
          "
        >
          🌐
        </div>

        <div>

          <h1
            className="
            text-4xl

            font-bold

            tracking-tight

            text-white
            "
          >
            URL Security Scanner
          </h1>

          <p
            className="
            mt-2

            max-w-3xl

            text-slate-400
            "
          >
            Scan URLs for phishing, malicious indicators,
            HTTPS usage, VirusTotal intelligence,
            and AI-powered security analysis.
          </p>

        </div>

      </div>

    </section>

    {/* Scanner */}

    <Card className="p-8">

      <form
        onSubmit={handleScan}
        className="space-y-6"
      >

        <Input
          label="URL"
          value={url}
          onChange={(e) =>
            setUrl(e.target.value)
          }
          placeholder="https://example.com"
          required
        />

        <Button
          type="submit"
          loading={loading}
          className="
          w-full

          rounded-2xl

          bg-gradient-to-r

          from-cyan-400

          via-cyan-500

          to-blue-600

          py-3

          font-semibold

          text-white

          transition-all

          hover:shadow-[0_0_35px_rgba(34,211,238,.35)]
          "
        >
          Scan URL
        </Button>

        {error && (

          <div
            className="
            rounded-2xl

            border

            border-red-500/20

            bg-red-500/10

            p-4

            text-red-300
            "
          >
            {error}
          </div>

        )}

      </form>

    </Card>

    {/* Results */}

    {result && (

      <div className="space-y-6">

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

      </div>

    )}

  </div>
);
}