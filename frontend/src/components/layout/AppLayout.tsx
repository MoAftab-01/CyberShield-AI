import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
import AnimatedBackground from "./AnimatedBackground";

export default function AppLayout() {
  const location = useLocation();

  const [collapsed, setCollapsed] = useState(false);

  const pages: Record<
    string,
    {
      title: string;
      subtitle: string;
    }
  > = {
    "/dashboard": {
      title: "Dashboard",
      subtitle: "AI Powered Cyber Threat Intelligence",
    },

    "/copilot": {
      title: "CyberGPT",
      subtitle: "Enterprise AI Security Assistant",
    },

    "/password": {
      title: "Password Analyzer",
      subtitle: "Analyze password strength and entropy",
    },

    "/url-scanner": {
      title: "URL Scanner",
      subtitle: "Detect phishing and malicious URLs",
    },

    "/threat-intel": {
      title: "Threat Intelligence",
      subtitle: "Enterprise Cyber Threat Intelligence",
    },

    "/reports": {
      title: "Reports",
      subtitle: "Security Reports and Analytics",
    },

    "/settings": {
      title: "Settings",
      subtitle: "Manage your CyberShield Platform",
    },
  };

  const page =
    pages[location.pathname] ?? {
      title: "CyberShield",
      subtitle: "AI Security Platform",
    };

  return (
    <div
      className="
      relative
      flex
      h-screen
      overflow-visible
      bg-[#06111F]
      "
    >
      <AnimatedBackground />

      <div
  className="
  relative

  z-50

  overflow-visible

  flex-shrink-0
  "
>

        <Sidebar
          collapsed={collapsed}
          onToggle={() =>
            setCollapsed(!collapsed)
          }
        />

      </div>

      <div
        className="
        relative
        z-

        flex
        min-w-0
        flex-1
        flex-col

        transition-all
        duration-300
        "
      >
        <Navbar
          title={page.title}
          subtitle={page.subtitle}
        />

        <main
          className="
          flex-1
          overflow-auto
          p-8
          "
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}