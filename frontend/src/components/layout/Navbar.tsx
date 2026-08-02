import {
  Bell,
  Search,
  ShieldCheck,
} from "lucide-react";

import { useLocation } from "react-router-dom";

export default function Navbar() {

  const location = useLocation();

  const getTitle = () => {

    switch (location.pathname) {

      case "/":
      case "/dashboard":
        return {
          title: "Dashboard",
          subtitle:
            "AI Powered Cyber Threat Intelligence",
        };

      case "/copilot":
        return {
          title: "CyberGPT",
          subtitle:
            "Enterprise AI Security Assistant",
        };

      case "/password":
        return {
          title: "Password Analyzer",
          subtitle:
            "Analyze password strength and security",
        };

      case "/url-scanner":
        return {
          title: "URL Scanner",
          subtitle:
            "Detect phishing and malicious websites",
        };

      case "/threat-intel":
        return {
          title: "Threat Intelligence",
          subtitle:
            "Analyze CVEs and security threats",
        };

      case "/reports":
        return {
          title: "Reports",
          subtitle:
            "View reports and analytics",
        };

      default:
        return {
          title: "CyberShield AI",
          subtitle:
            "Enterprise Cybersecurity Platform",
        };

    }

  };

  const page = getTitle();

  return (

    <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8">

      <div>

        <h1 className="text-2xl font-bold text-slate-800">
          {page.title}
        </h1>

        <p className="text-slate-500">
          {page.subtitle}
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