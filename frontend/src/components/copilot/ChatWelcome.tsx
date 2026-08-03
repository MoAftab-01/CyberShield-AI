interface Props {
  onSuggestion: (text: string) => void;
}

export default function ChatWelcome({
  onSuggestion,
}: Props) {
  return (
    <div className="max-w-4xl mx-auto mt-12">

      <h2 className="text-4xl font-bold text-slate-800 mb-4">
        Welcome to CyberGPT 👋
      </h2>

      <p className="text-slate-500 text-lg mb-10">
        Your enterprise AI assistant for cybersecurity.
      </p>

      <div className="grid grid-cols-2 gap-5">

        <button
          onClick={() =>
            onSuggestion("Analyze CVE-2024-4577")
          }
          className="rounded-xl bg-white border p-6 hover:border-cyan-500 transition text-left"
        >
          🛡 Analyze CVE-2024-4577
        </button>

        <button
          onClick={() =>
            onSuggestion("Explain SQL Injection")
          }
          className="rounded-xl bg-white border p-6 hover:border-cyan-500 transition text-left"
        >
          🔐 Explain SQL Injection
        </button>

        <button
          onClick={() =>
            onSuggestion("Explain OWASP Top 10")
          }
          className="rounded-xl bg-white border p-6 hover:border-cyan-500 transition text-left"
        >
          📚 Explain OWASP Top 10
        </button>

        <button
          onClick={() =>
            onSuggestion("Explain MITRE ATT&CK")
          }
          className="rounded-xl bg-white border p-6 hover:border-cyan-500 transition text-left"
        >
          🎯 Explain MITRE ATT&CK
        </button>

      </div>

    </div>
  );
}