import { useState } from "react";
import {
  Search,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  Calendar,
  Crosshair,
} from "lucide-react";


import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";

import { getThreat } from "@/services/threatService";
import { Threat } from "@/types/threat";

export default function ThreatIntel() {
  const [cve, setCve] = useState("");
  const [loading, setLoading] = useState(false);
  const [threat, setThreat] = useState<Threat | null>(null);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    if (!cve.trim()) return;

    try {
      setLoading(true);
      setError("");

      const result = await getThreat(cve.trim().toUpperCase());

      setThreat(result);
    } catch {
      setThreat(null);
      setError("Unable to fetch vulnerability.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-8">

      <div className="mb-8">
        <h1 className="text-4xl font-bold">
          Threat Intelligence
        </h1>

        <p className="text-slate-500 mt-2">
          AI-powered vulnerability analysis
        </p>
      </div>

      <Card>

        <div className="flex gap-4">

          <Input
            placeholder="CVE-2024-4577"
            value={cve}
            onChange={(e) => setCve(e.target.value)}
          />

          <Button
            leftIcon={<Search size={18} />}
            loading={loading}
            onClick={handleSearch}
          >
            Search
          </Button>

        </div>

      </Card>

      {loading && <Spinner />}

      {error && (
        <p className="mt-6 text-red-500">
          {error}
        </p>
      )}

      {threat && (

        <div className="grid lg:grid-cols-2 gap-6 mt-8">

          {/* Overview */}

          <Card>

            <div className="flex justify-between items-center">

              <h2 className="text-2xl font-bold">
                {threat.cve}
              </h2>

              <Badge severity={threat.severity} />

            </div>

            <div className="mt-6 space-y-3">

              <p><strong>CVSS:</strong> {threat.cvss}</p>

              <p><strong>Risk:</strong> {threat.risk_level}</p>

              <p>
                <strong>Exploitability:</strong>{" "}
                {threat.exploitability_score}
              </p>

              <p>
                <strong>Impact Score:</strong>{" "}
                {threat.impact_score}
              </p>

              <p>
                <strong>Status:</strong>{" "}
                {threat.status}
              </p>

              <p>
                <strong>Known Exploited:</strong>{" "}
                {threat.known_exploited ? "✅ Yes" : "❌ No"}
              </p>

              <p>
                <strong>Product:</strong>{" "}
                {threat.product || "N/A"}
              </p>

            </div>

          </Card>

          {/* AI Summary */}

          <Card>

            <h2 className="flex items-center gap-2 text-xl font-bold mb-4">

              <ShieldCheck size={20} />

              AI Summary

            </h2>

            <p className="leading-7">

              {threat.ai_summary || threat.description}

            </p>

          </Card>

          {/* Recommendations */}

          <Card>

            <h2 className="flex items-center gap-2 text-xl font-bold mb-4">

              <AlertTriangle size={20} />

              Recommendations

            </h2>

            {threat.recommendations.length === 0 ? (

              <p>No recommendations available.</p>

            ) : (

              <ul className="space-y-3 list-disc pl-5">

                {threat.recommendations.map((item, index) => (

                  <li key={index}>{item}</li>

                ))}

              </ul>

            )}

          </Card>

          {/* Threat Correlation */}

<Card>

  <h2 className="text-xl font-bold mb-4">

    Threat Correlation

  </h2>

  <div className="space-y-4">

    <div>

      <p className="font-semibold">

        Priority

      </p>

      <p className="mt-1 text-red-600 font-bold text-lg">

        {threat.priority || "N/A"}

      </p>

    </div>

    <div>

      <p className="font-semibold">

        Assessment

      </p>

      <p className="mt-2 leading-7 text-slate-600">

        {threat.threat_assessment || "No assessment available."}

      </p>

    </div>

  </div>

</Card>


          {/* Timeline */}

          <Card>

            <h2 className="flex items-center gap-2 text-xl font-bold mb-4">

              <Calendar size={20} />

              Timeline

            </h2>

            <div className="space-y-3">

              <p>

                <strong>Published:</strong>{" "}

                {threat.published}

              </p>

              <p>

                <strong>Last Modified:</strong>{" "}

                {threat.last_modified}

              </p>

            </div>

          </Card>

          {/* Weaknesses */}

          <Card>

            <h2 className="text-xl font-bold mb-4">

              Weaknesses (CWE)

            </h2>

            {threat.weaknesses.length === 0 ? (

              <p>No weaknesses available.</p>

            ) : (

              <ul className="list-disc pl-5 space-y-2">

                {threat.weaknesses.map((item, index) => (

                  <li key={index}>{item}</li>

                ))}

              </ul>

            )}

          </Card>

          {/* MITRE ATT&CK */}

<Card>

  <h2 className="flex items-center gap-2 text-xl font-bold mb-4">

    <Crosshair size={20} />

    MITRE ATT&CK

  </h2>

  {threat.mitre_attack.length === 0 ? (

    <p>No ATT&CK techniques found.</p>

  ) : (

    <div className="space-y-4">

      {threat.mitre_attack.map((technique, index) => (

        <div
          key={index}
          className="rounded-lg border border-slate-200 p-4"
        >

          <p className="font-semibold text-blue-600">

            {technique.technique_id}

          </p>

          <p className="font-medium mt-1">

            {technique.name}

          </p>

          <p className="text-sm text-slate-500 mt-2">

            <strong>Tactic:</strong>{" "}

            {technique.tactic || "N/A"}

          </p>

          {technique.description && (

            <p className="text-sm text-slate-600 mt-2 line-clamp-4">

              {technique.description}

            </p>

          )}

        </div>

      ))}

    </div>

  )}

</Card>
{/* Vendor Advisories */}

<Card>

  <h2 className="text-xl font-bold mb-4">

    Vendor Advisories

  </h2>

  {threat.github_advisories.length === 0 ? (

    <p>No vendor advisories found.</p>

  ) : (

    <div className="space-y-4">

      {threat.github_advisories.map((advisory, index) => (

        <div
          key={index}
          className="rounded-lg border border-slate-200 p-4"
        >

          <p className="font-semibold text-blue-600">

            {advisory.ghsa_id}

          </p>

          <p className="mt-2">

            {advisory.summary}

          </p>

          <p className="mt-2">

            <strong>Severity:</strong>{" "}

            {advisory.severity}

          </p>

          <p>

            <strong>Published:</strong>{" "}

            {new Date(advisory.published_at!).toLocaleDateString()}

          </p>

          <a
            href={advisory.url!}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline mt-3 inline-block"
          >
            View Advisory
          </a>

        </div>

      ))}

    </div>

  )}

</Card>

          {/* References */}

          <Card>

            <h2 className="text-xl font-bold mb-4">

              References

            </h2>

            <div className="space-y-3">

              {threat.references.map((link, index) => (

                <a
                  key={index}
                  href={link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex gap-2 items-center text-blue-600 hover:underline break-all"
                >

                  <ExternalLink size={16} />

                  {link}

                </a>

              ))}

            </div>

          </Card>

        </div>

      )}

    </div>
  );
}