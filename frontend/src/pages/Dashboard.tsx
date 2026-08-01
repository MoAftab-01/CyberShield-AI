import {
  ShieldCheck,
  KeyRound,
  Globe,
  ShieldAlert,
  Lock,
  Search,
  Brain,
  FileText,
} from "lucide-react";

import SecurityGauge from "../components/charts/SecurityGauge";
import ThreatChart from "../components/charts/ThreatChart";

import StatCard from "../components/dashboard/StatCard";
import QuickActionCard from "../components/dashboard/QuickActionCard";
import ActivityCard from "../components/dashboard/ActivityCard";

import PasswordDistribution from "../components/dashboard/PasswordDistribution";
import URLDistribution from "../components/dashboard/URLDistribution";
import TopDomains from "../components/dashboard/TopDomains";

import { useDashboard } from "../hooks/useDashboard";

export default function Dashboard() {
  const { data, loading, error } = useDashboard();

  if (loading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <p className="text-lg text-slate-500">
          Loading dashboard...
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <p className="text-lg text-red-500">
          {error || "Unable to load dashboard."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">

      {/* Welcome */}

      <section>
        <h1 className="text-4xl font-bold text-slate-800">
          Welcome Back 👋
        </h1>

        <p className="mt-2 text-slate-500">
          Monitor your cyber security posture and analyze threats in real time.
        </p>
      </section>

      {/* Charts */}

      <section className="grid gap-6 lg:grid-cols-2">
        <SecurityGauge score={data.stats.securityScore} />

        <ThreatChart />
      </section>

      {/* Statistics */}

      <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Security Score"
          value={data.stats.securityScore}
          suffix="%"
          subtitle="Excellent"
          icon={ShieldCheck}
        />

        <StatCard
          title="Passwords Checked"
          value={data.stats.passwordsChecked}
          subtitle="Total scans"
          icon={KeyRound}
        />

        <StatCard
          title="URLs Scanned"
          value={data.stats.urlsScanned}
          subtitle="Total scans"
          icon={Globe}
        />

        <StatCard
          title="Threats Detected"
          value={data.stats.threatsDetected}
          subtitle="Requires attention"
          icon={ShieldAlert}
        />
      </section>

      {/* Analytics */}

      <section className="grid gap-6 lg:grid-cols-3">

        <PasswordDistribution
          weak={data.passwordDistribution.Weak}
          medium={data.passwordDistribution.Medium}
          strong={data.passwordDistribution.Strong}
        />

        <URLDistribution
          low={data.urlDistribution.Low}
          medium={data.urlDistribution.Medium}
          high={data.urlDistribution.High}
        />

        <TopDomains
          domains={data.topDomains}
        />

      </section>

      {/* Quick Actions */}

      <section>
        <h2 className="mb-5 text-2xl font-bold text-slate-800">
          Quick Actions
        </h2>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">

          <QuickActionCard
            title="Password Analyzer"
            description="Evaluate password strength and entropy."
            icon={Lock}
            route="/password"
          />

          <QuickActionCard
            title="URL Scanner"
            description="Detect phishing and malicious websites."
            icon={Search}
            route="/url-scanner"
          />

          <QuickActionCard
            title="Threat Intelligence"
            description="View CVEs, MITRE ATT&CK and AI insights."
            icon={Brain}
            route="/threat-intel"
          />

          <QuickActionCard
            title="Reports"
            description="Review scan history and analytics."
            icon={FileText}
            route="/reports"
          />

        </div>
      </section>

      {/* Recent Activity */}

      <section>
        <h2 className="mb-5 text-2xl font-bold text-slate-800">
          Recent Activity
        </h2>

        <div className="space-y-4">

          {data.activities.length === 0 ? (
            <div className="rounded-xl border bg-white p-6 text-center text-slate-500 shadow-sm">
              No recent activity found.
            </div>
          ) : (
            data.activities.map((activity) => (
              <ActivityCard
                key={activity.id}
                title={activity.title}
                time={activity.time}
                status={activity.status}
              />
            ))
          )}

        </div>
      </section>

    </div>
  );
}