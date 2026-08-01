import { useState } from "react";

interface Props {
  onSearch: (cve: string) => void;
  loading: boolean;
}

export default function SearchBar({ onSearch, loading }: Props) {
  const [value, setValue] = useState("");

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow p-6">
      <h2 className="text-xl font-semibold mb-4">
        Search CVE
      </h2>

      <div className="flex gap-3">
        <input
          className="flex-1 border rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none"
          placeholder="Example: CVE-2024-4577"
          value={value}
          onChange={(e) => setValue(e.target.value.toUpperCase())}
        />

        <button
          onClick={() => onSearch(value)}
          disabled={loading}
          className="bg-blue-600 text-white px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>
    </div>
  );
}