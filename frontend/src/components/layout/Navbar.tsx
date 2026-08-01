import {
  Bell,
  Search,
  ShieldCheck,
} from "lucide-react";

export default function Navbar() {
  return (
    <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8">

      <div>

        <h1 className="text-2xl font-bold text-slate-800">
          Dashboard
        </h1>

        <p className="text-slate-500">
          AI Powered Cyber Threat Intelligence
        </p>

      </div>

      <div className="flex items-center gap-6">

        <div className="relative">

          <Search
            size={18}
            className="absolute left-3 top-3 text-slate-400"
          />

          <input
            className="w-72 rounded-xl border border-slate-300 py-2 pl-10 pr-4 outline-none focus:border-cyan-500"
            placeholder="Search..."
          />

        </div>

        <Bell
          size={22}
          className="cursor-pointer text-slate-600 hover:text-cyan-600"
        />

        <ShieldCheck
          size={24}
          className="text-cyan-600"
        />

      </div>

    </header>
  );
}