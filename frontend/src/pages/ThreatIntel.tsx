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

function Metric({
  title,
  value,
}: {
  title: string;
  value: string | number;
}) {
  return (
    <div
      className="
      rounded-2xl

      border

      border-cyan-400/15

      bg-slate-900/45

      p-4
      "
    >
      <p className="text-xs text-slate-400">
        {title}
      </p>

      <p className="mt-2 text-xl font-bold text-white">
        {value}
      </p>
    </div>
  );
}
  
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

        -right-24

        -top-24

        h-72

        w-72

        rounded-full

        bg-cyan-500/10

        blur-[140px]
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
          "
        >

          <ShieldCheck
            size={32}
            className="text-white"
          />

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
            Threat Intelligence
          </h1>

          <p
            className="
            mt-2

            max-w-3xl

            text-slate-400
            "
          >
            Search CVEs and receive AI-powered vulnerability analysis,
            exploit intelligence, MITRE ATT&CK mapping,
            GitHub advisories and remediation guidance.
          </p>

        </div>

      </div>

    </section>

    {/* Search */}

    <Card className="p-8">

      <div className="flex gap-4">

        <Input
          placeholder="Enter CVE ID (e.g. CVE-2024-4577)"
          value={cve}
          onChange={(e) =>
            setCve(e.target.value)
          }
        />

        <Button
          leftIcon={<Search size={18} />}
          loading={loading}
          onClick={handleSearch}
          className="
          rounded-2xl

          bg-gradient-to-r

          from-cyan-400

          via-cyan-500

          to-blue-600

          px-8

          font-semibold

          text-white

          hover:shadow-[0_0_35px_rgba(34,211,238,.35)]
          "
        >
          Search
        </Button>

      </div>

    </Card>

    {/* Loading */}

    {loading && (

      <div className="flex justify-center py-10">

        <Spinner />

      </div>

    )}

    {/* Error */}

    {error && (

      <div
        className="
        rounded-2xl

        border

        border-red-500/20

        bg-red-500/10

        p-5

        text-red-300
        "
      >
        {error}
      </div>

    )}

    {/* Results */}

    {threat && (

      <div className="grid gap-6 lg:grid-cols-2">

            {/* Overview */}

      <Card>

        <div className="flex items-center justify-between">

          <div>

            <p className="text-sm text-slate-400">
              Vulnerability
            </p>

            <h2 className="mt-2 text-3xl font-bold text-white">
              {threat.cve}
            </h2>

          </div>

          <Badge severity={threat.severity} />

        </div>

        <div className="mt-8 grid grid-cols-2 gap-5">

          <Metric
            title="CVSS"
            value={threat.cvss}
          />

          <Metric
            title="Risk"
            value={threat.risk_level}
          />

          <Metric
            title="Exploitability"
            value={threat.exploitability_score}
          />

          <Metric
            title="Impact"
            value={threat.impact_score}
          />

          <Metric
            title="Status"
            value={threat.status}
          />

          <Metric
            title="Known Exploited"
            value={
              threat.known_exploited
                ? "Yes"
                : "No"
            }
          />

        </div>

        <div
          className="
          mt-6

          rounded-2xl

          border

          border-cyan-400/15

          bg-slate-900/45

          p-4
          "
        >

          <p className="text-sm text-slate-400">
            Product
          </p>

          <p className="mt-2 text-white font-medium">
            {threat.product || "N/A"}
          </p>

        </div>

      </Card>

      {/* AI Summary */}

      <Card>

        <div className="flex items-center gap-3 mb-5">

          <div
            className="
            flex

            h-11

            w-11

            items-center

            justify-center

            rounded-2xl

            bg-gradient-to-br

            from-cyan-400

            to-blue-600
            "
          >

            <ShieldCheck
              size={20}
              className="text-white"
            />

          </div>

          <div>

            <h2 className="text-2xl font-bold text-white">
              AI Summary
            </h2>

            <p className="text-sm text-slate-400">
              Generated threat overview
            </p>

          </div>

        </div>

        <div
          className="
          rounded-2xl

          border

          border-cyan-400/15

          bg-slate-900/45

          p-5
          "
        >

          <p className="leading-8 text-slate-300">

            {threat.ai_summary ||
              threat.description}

          </p>

        </div>

      </Card>

      {/* Recommendations */}

      <Card>

        <div className="flex items-center gap-3 mb-6">

          <div
            className="
            flex

            h-11

            w-11

            items-center

            justify-center

            rounded-2xl

            bg-gradient-to-br

            from-orange-500

            to-red-500
            "
          >

            <AlertTriangle
              size={20}
              className="text-white"
            />

          </div>

          <h2 className="text-2xl font-bold text-white">

            Recommendations

          </h2>

        </div>

        {threat.recommendations.length === 0 ? (

          <div
            className="
            rounded-2xl

            border

            border-cyan-400/15

            bg-slate-900/45

            p-5

            text-slate-400
            "
          >
            No recommendations available.
          </div>

        ) : (

          <div className="space-y-4">

            {threat.recommendations.map(
              (item, index) => (

                <div
                  key={index}
                  className="
                  flex

                  gap-4

                  rounded-2xl

                  border

                  border-cyan-400/15

                  bg-slate-900/45

                  p-4
                  "
                >

                  <div
                    className="
                    flex

                    h-8

                    w-8

                    items-center

                    justify-center

                    rounded-full

                    bg-gradient-to-br

                    from-cyan-500

                    to-blue-600

                    text-sm

                    font-bold

                    text-white
                    "
                  >

                    {index + 1}

                  </div>

                  <p className="text-slate-300 leading-7">

                    {item}

                  </p>

                </div>

              ),
            )}

          </div>

        )}

      </Card>

      {/* Threat Correlation */}

      <Card>

        <h2 className="text-2xl font-bold text-white mb-6">

          Threat Correlation

        </h2>

        <div className="space-y-5">

          <div
            className="
            rounded-2xl

            border

            border-red-500/20

            bg-red-500/10

            p-5
            "
          >

            <p className="text-sm text-slate-400">

              Priority

            </p>

            <p className="mt-2 text-3xl font-bold text-red-300">

              {threat.priority || "N/A"}

            </p>

          </div>

          <div
            className="
            rounded-2xl

            border

            border-cyan-400/15

            bg-slate-900/45

            p-5
            "
          >

            <p className="text-sm text-slate-400">

              Assessment

            </p>

            <p className="mt-3 leading-8 text-slate-300">

              {threat.threat_assessment ||
                "No assessment available."}

            </p>

          </div>

        </div>

      </Card>

                {/* Timeline */}

      <Card>

        <div className="flex items-center gap-3 mb-6">

          <div
            className="
            flex

            h-11

            w-11

            items-center

            justify-center

            rounded-2xl

            bg-gradient-to-br

            from-cyan-400

            to-blue-600
            "
          >
            <Calendar
              size={20}
              className="text-white"
            />
          </div>

          <h2 className="text-2xl font-bold text-white">

            Timeline

          </h2>

        </div>

        <div className="space-y-4">

          <Metric
            title="Published"
            value={threat.published}
          />

          <Metric
            title="Last Modified"
            value={threat.last_modified}
          />

        </div>

      </Card>

      {/* Weaknesses */}

      <Card>

        <h2 className="text-2xl font-bold text-white mb-6">

          Weaknesses (CWE)

        </h2>

        {threat.weaknesses.length === 0 ? (

          <div
            className="
            rounded-2xl

            border

            border-cyan-400/15

            bg-slate-900/45

            p-5

            text-slate-400
            "
          >
            No weaknesses available.
          </div>

        ) : (

          <div className="space-y-3">

            {threat.weaknesses.map((item, index) => (

              <div
                key={index}
                className="
                rounded-2xl

                border

                border-cyan-400/15

                bg-slate-900/45

                p-4

                text-slate-300
                "
              >

                {item}

              </div>

            ))}

          </div>

        )}

      </Card>

      {/* MITRE ATT&CK */}

      <Card>

        <div className="flex items-center gap-3 mb-6">

          <div
            className="
            flex

            h-11

            w-11

            items-center

            justify-center

            rounded-2xl

            bg-gradient-to-br

            from-violet-500

            to-fuchsia-600
            "
          >

            <Crosshair
              size={20}
              className="text-white"
            />

          </div>

          <h2 className="text-2xl font-bold text-white">

            MITRE ATT&CK

          </h2>

        </div>

        {threat.mitre_attack.length === 0 ? (

          <div
            className="
            rounded-2xl

            border

            border-cyan-400/15

            bg-slate-900/45

            p-5

            text-slate-400
            "
          >

            No ATT&CK techniques found.

          </div>

        ) : (

          <div className="space-y-4">

            {threat.mitre_attack.map(
              (technique, index) => (

                <div
                  key={index}
                  className="
                  rounded-2xl

                  border

                  border-cyan-400/15

                  bg-slate-900/45

                  p-5

                  transition-all

                  duration-300

                  hover:border-cyan-300/35
                  "
                >

                  <div className="flex items-center justify-between">

                    <span className="font-bold text-cyan-300">

                      {technique.technique_id}

                    </span>

                    <span className="text-xs text-slate-500">

                      {technique.tactic || "N/A"}

                    </span>

                  </div>

                  <h3 className="mt-3 text-lg font-semibold text-white">

                    {technique.name}

                  </h3>

                  {technique.description && (

                    <p className="mt-3 text-sm leading-7 text-slate-400">

                      {technique.description}

                    </p>

                  )}

                </div>

              ),
            )}

          </div>

        )}

      </Card>

      {/* Vendor Advisories */}

      <Card>

        <h2 className="text-2xl font-bold text-white mb-6">

          Vendor Advisories

        </h2>

        {threat.github_advisories.length === 0 ? (

          <div
            className="
            rounded-2xl

            border

            border-cyan-400/15

            bg-slate-900/45

            p-5

            text-slate-400
            "
          >

            No vendor advisories found.

          </div>

        ) : (

          <div className="space-y-5">

            {threat.github_advisories.map(
              (advisory, index) => (

                <div
                  key={index}
                  className="
                  rounded-2xl

                  border

                  border-cyan-400/15

                  bg-slate-900/45

                  p-5
                  "
                >

                  <h3 className="font-bold text-cyan-300">

                    {advisory.ghsa_id}

                  </h3>

                  <p className="mt-3 text-slate-300 leading-7">

                    {advisory.summary}

                  </p>

                  <div className="mt-4 flex flex-wrap gap-4 text-sm text-slate-400">

                    <span>

                      Severity:
                      <strong className="ml-1 text-white">

                        {advisory.severity}

                      </strong>

                    </span>

                    <span>

                      Published:
                      <strong className="ml-1 text-white">

                        {new Date(
                          advisory.published_at!,
                        ).toLocaleDateString()}

                      </strong>

                    </span>

                  </div>

                  <a
                    href={advisory.url!}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="
                    mt-5

                    inline-flex

                    items-center

                    gap-2

                    text-cyan-300

                    hover:text-cyan-200
                    "
                  >

                    <ExternalLink size={16} />

                    View Advisory

                  </a>

                </div>

              ),
            )}

          </div>

        )}

      </Card>

      {/* References */}

      <Card>

        <h2 className="text-2xl font-bold text-white mb-6">

          References

        </h2>

        <div className="space-y-3">

          {threat.references.map((link, index) => (

            <a
              key={index}
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="
              flex

              items-center

              gap-3

              rounded-2xl

              border

              border-cyan-400/15

              bg-slate-900/45

              px-4

              py-3

              text-cyan-300

              transition-all

              duration-300

              hover:border-cyan-300/35

              hover:bg-slate-900/60
              "
            >

              <ExternalLink size={16} />

              <span className="truncate">

                {link}

              </span>

            </a>

          ))}

        </div>

      </Card>

    </div>

  )}

</div>

  );
}
