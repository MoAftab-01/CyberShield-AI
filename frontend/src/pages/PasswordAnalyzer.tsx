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
    <div className="space-y-8">
      {/* Header */}

      <section>
        <h1 className="text-4xl font-bold text-slate-800">
          Password Analyzer
        </h1>

        <p className="mt-2 text-slate-500">
          Analyze password strength using entropy,
          pattern detection, dictionary checks,
          and AI-driven recommendations.
        </p>
      </section>

      {/* Input */}

      <Card>
        <form
          onSubmit={handleAnalyze}
          className="space-y-5"
        >
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            placeholder="Enter password..."
            required
          />

          <Button
            type="submit"
            loading={loading}
          >
            Analyze Password
          </Button>

          {error && (
            <div className="rounded-lg bg-red-100 p-4 text-red-700">
              {error}
            </div>
          )}
        </form>
      </Card>

      {/* Results */}

      {result && (
        <>
          <PasswordSummary
            strength={result.strength}
            score={result.score}
            entropy={result.entropy}
            entropyRating={
              result.entropy_rating
            }
            riskScore={result.risk_score}
            riskLevel={result.risk_level}
          />

          <CharacterChecklist
            uppercase={
              result.has_uppercase
            }
            lowercase={
              result.has_lowercase
            }
            number={result.has_number}
            special={
              result.has_special_character
            }
          />

          <div className="grid gap-6 lg:grid-cols-2">
            <DetectionCard
              title="Dictionary Words"
              detected={
                result.contains_dictionary_word
              }
              values={
                result.detected_dictionary_words
              }
            />

            <DetectionCard
              title="Patterns"
              detected={
                result.contains_pattern
              }
              values={
                result.detected_patterns
              }
            />
          </div>

          <Recommendations
            recommendations={
              result.recommendations
            }
          />
        </>
      )}
    </div>
  );
}