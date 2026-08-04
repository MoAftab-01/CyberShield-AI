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

import AISummaryCard from "../components/dashboard/AISummaryCard";
import LoadingAISummary from "../components/dashboard/LoadingAISummary";

import { useDashboard } from "../hooks/useDashboard";
import { useAISummary } from "../hooks/useAISummary";

export default function Dashboard() {

  const {
    data,
    loading,
    error,
  } = useDashboard();

  const {
    summary,
    loading: aiLoading,
    refreshing,
    error: aiError,
    lastUpdated,
    refresh,
  } = useAISummary();

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

    <div className="mx-auto max-w-[1700px] space-y-10 px-2">

      {/* Welcome */}

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

        <h1
  className="
    text-5xl
    font-bold
    tracking-tight
    text-white
  "
>

          Welcome Back 👋

        </h1>

        <p
  className="
    mt-3
    max-w-3xl
    text-lg
    leading-8
    text-slate-400
  "
>

          Monitor your cyber security posture and analyze threats in real time.

        </p>

      </section>

      {/* AI Summary */}

      <section>

        {

          aiLoading && !summary

            ?

            <LoadingAISummary />

            :

            aiError

              ?

              <div
  className="
  rounded-[24px]

  border

  border-red-500/20

  bg-red-500/10

  p-6

  text-red-300
  "
>

                {aiError}

              </div>

              :

              <AISummaryCard

                summary={summary?.summary ?? ""}

                score={data.stats.securityScore}

                lastUpdated={lastUpdated}

                refreshing={refreshing}

                onRefresh={refresh}

              />

        }

      </section>

      {/* Charts */}

      <section className="grid gap-6 lg:grid-cols-2">

        <SecurityGauge
          score={data.stats.securityScore}
        />

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

        <h2 className="mb-5 text-2xl font-bold text-white">

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

        <h2 className="mb-5 text-2xl font-bold text-white">

          Recent Activity

        </h2>

        <div className="space-y-4">

          {

            data.activities.length === 0

              ?

              <div
  className="
  rounded-[24px]

  border

  border-cyan-400/20

  bg-slate-900/55

  p-6

  text-center

  text-slate-400
  "
>

                No recent activity found.

              </div>

              :

              data.activities.map(

                (activity) => (

                  <ActivityCard

                    key={activity.id}

                    title={activity.title}

                    time={activity.time}

                    status={activity.status}

                  />

                ),

              )

          }

        </div>

      </section>

    </div>

  );

}