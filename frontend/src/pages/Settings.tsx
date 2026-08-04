import Card from "../components/ui/Card";

export default function Settings() {
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

            text-3xl
            "
          >

            ⚙️

          </div>

          <div>

            <h1 className="text-4xl font-bold tracking-tight text-white">

              Settings

            </h1>

            <p className="mt-2 text-slate-400">

              Manage your CyberGPT workspace and AI preferences.

            </p>

          </div>

        </div>

      </section>

      {/* Settings */}

      <div className="grid gap-6 lg:grid-cols-2">

        <Card>

          <h2 className="mb-6 text-2xl font-bold text-white">

            🎨 Appearance

          </h2>

          <div className="space-y-4">

            <SettingRow title="Dark Theme" value="Enabled" />

            <SettingRow title="Glass Effects" value="Enabled" />

            <SettingRow title="Animations" value="Enabled" />

            <SettingRow title="Accent Color" value="Cyber Cyan" />

          </div>

        </Card>

        <Card>

          <h2 className="mb-6 text-2xl font-bold text-white">

            🤖 AI Preferences

          </h2>

          <div className="space-y-4">

            <SettingRow title="Model" value="GPT-4.1" />

            <SettingRow title="Response Style" value="Detailed" />

            <SettingRow title="Threat Confidence" value="High" />

            <SettingRow title="Memory" value="Enabled" />

          </div>

        </Card>

        <Card>

          <h2 className="mb-6 text-2xl font-bold text-white">

            🛡 Security

          </h2>

          <div className="space-y-4">

            <SettingRow title="Conversation History" value="Enabled" />

            <SettingRow title="Upload Protection" value="Enabled" />

            <SettingRow title="Auto Delete Uploads" value="Enabled" />

            <SettingRow title="Session Timeout" value="30 Minutes" />

          </div>

        </Card>

        <Card>

          <h2 className="mb-6 text-2xl font-bold text-white">

            📄 Reports

          </h2>

          <div className="space-y-4">

            <SettingRow title="Default Export" value="PDF" />

            <SettingRow title="Executive Summary" value="Enabled" />

            <SettingRow title="Threat Reports" value="Enabled" />

            <SettingRow title="Retention" value="90 Days" />

          </div>

        </Card>

        <Card>

          <h2 className="mb-6 text-2xl font-bold text-white">

            ℹ️ About CyberGPT

          </h2>

          <div className="space-y-4">

            <SettingRow title="Version" value="1.0.0" />

            <SettingRow title="Framework" value="React + FastAPI" />

            <SettingRow title="AI Engine" value="LangGraph + OpenAI" />

            <SettingRow title="Threat Sources" value="NVD • CISA • MITRE" />

            <SettingRow title="Database" value="PostgreSQL" />

            <SettingRow title="Retrieval" value="Hybrid RAG" />

          </div>

        </Card>

        <Card>

          <h2 className="mb-6 text-2xl font-bold text-white">

            🟢 System Status

          </h2>

          <div className="space-y-5">

            <StatusRow title="AI Backend" />

            <StatusRow title="Threat Intelligence" />

            <StatusRow title="Vector Database" />

            <StatusRow title="VirusTotal API" />

            <StatusRow title="Executive Reports" />

          </div>

        </Card>

      </div>

      <div className="flex justify-center">

        <button
          className="
          rounded-2xl

          bg-gradient-to-r

          from-cyan-400

          via-cyan-500

          to-blue-600

          px-10

          py-4

          text-lg

          font-semibold

          text-white

          shadow-[0_0_35px_rgba(34,211,238,.35)]

          transition-all

          duration-300

          hover:scale-[1.02]

          hover:shadow-[0_0_55px_rgba(34,211,238,.45)]
          "
        >

          Save Settings

        </button>

      </div>

    </div>
  );
}

function SettingRow({
  title,
  value,
}: {
  title: string;
  value: string;
}) {
  return (
    <div
      className="
      flex

      items-center

      justify-between

      rounded-2xl

      border

      border-cyan-400/15

      bg-slate-900/45

      px-5

      py-4
      "
    >
      <span className="text-slate-300">

        {title}

      </span>

      <span
        className="
        rounded-full

        border

        border-cyan-400/20

        bg-cyan-500/10

        px-3

        py-1

        text-sm

        font-medium

        text-cyan-300
        "
      >

        {value}

      </span>

    </div>
  );
}

function StatusRow({
  title,
}: {
  title: string;
}) {
  return (
    <div className="flex items-center justify-between">

      <span className="text-slate-300">

        {title}

      </span>

      <div className="flex items-center gap-2">

        <div
          className="
          h-3

          w-3

          rounded-full

          bg-emerald-400

          shadow-[0_0_12px_rgba(74,222,128,.9)]
          "
        />

        <span className="text-emerald-300">

          Online

        </span>

      </div>

    </div>
  );
}