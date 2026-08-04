import { useState } from "react";
import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";
import AnimatedBackground from "./AnimatedBackground";

export default function CopilotLayout() {

  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      className="
      relative
      flex
      h-screen
      overflow-hidden
      bg-[#06111F]
      "
    >
      {/* Galaxy Background */}

      <AnimatedBackground />

      {/* Sidebar */}

      <div className="relative z-20">

        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed((prev) => !prev)}
        />

      </div>

      {/* Main Content */}

      <main
        className="
        relative
        z-10

        flex-1

        overflow-hidden

        px-8

        pt-6
        "
      >

        <Outlet />

      </main>

    </div>
  );
}