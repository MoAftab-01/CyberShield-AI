import { useState } from "react";

import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";

import PasswordSummary from "../components/password/PasswordSummary";
import CharacterChecklist from "../components/password/CharacterChecklist";
import DetectionCard from "../components/password/DetectionCard";
import Recommendations from "../components/password/Recommendations";

import {
  analyzePassword,
  PasswordResponse,
} from "../services/passwordService";

export default function PasswordAnalyzer() {
  const [password, setPassword] = useState("");

  const [result, setResult] =
    useState<PasswordResponse | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function handleAnalyze(
    e: React.FormEvent
  ) {
    e.preventDefault();

    if (!password.trim()) return;

    setLoading(true);
    setError("");

    try {
      const response = await analyzePassword(
        password
      );

      setResult(response);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ??
          "Unable to analyze password."
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

      rounded-3xl

      border

      border-cyan-500/10

      bg-slate-900/40

      p-8

      backdrop-blur-2xl
      "
    >

      {/* Glow */}

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

      <div className="relative">

        <div className="flex items-center gap-5">

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

            🔐

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
              Password Analyzer
            </h1>

            <p
              className="
              mt-2

              max-w-2xl

              text-slate-400
              "
            >
              Analyze password strength using entropy,
              dictionary detection, pattern recognition,
              and AI-powered recommendations.
            </p>

          </div>

        </div>

      </div>

    </section>

    {/* Analyzer */}

    <Card
      className="
      relative

      overflow-hidden

      rounded-3xl

      border

      border-cyan-500/10

      bg-slate-900/40

      backdrop-blur-2xl

      shadow-[0_0_40px_rgba(34,211,238,.08)]
      "
    >

      <div
        className="
        absolute

        right-0

        top-0

        h-40

        w-40

        rounded-full

        bg-cyan-500/10

        blur-[90px]
        "
      />

      <form
        onSubmit={handleAnalyze}
        className="relative space-y-6"
      >

        <Input
          label="Password"
          type="password"
          value={password}
          onChange={(e) =>
            setPassword(e.target.value)
          }
          placeholder="Enter a password..."
          required
        />

        <Button
          type="submit"
          loading={loading}
          className="
          w-full

          rounded-2xl

          bg-gradient-to-r

          from-cyan-500

          to-blue-600

          py-3

          font-semibold

          text-white

          transition-all

          hover:shadow-[0_0_30px_rgba(34,211,238,.35)]
          "
        >
          Analyze Password
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

        <PasswordSummary
          strength={result.strength}
          score={result.score}
          entropy={result.entropy}
          entropyRating={result.entropy_rating}
          riskScore={result.risk_score}
          riskLevel={result.risk_level}
        />

        <CharacterChecklist
          uppercase={result.has_uppercase}
          lowercase={result.has_lowercase}
          number={result.has_number}
          special={result.has_special_character}
        />

        <div className="grid gap-6 lg:grid-cols-2">

          <DetectionCard
            title="Dictionary Words"
            detected={result.contains_dictionary_word}
            values={result.detected_dictionary_words}
          />

          <DetectionCard
            title="Patterns"
            detected={result.contains_pattern}
            values={result.detected_patterns}
          />

        </div>

        <Recommendations
          recommendations={result.recommendations}
        />

      </div>

    )}

  </div>
);
}