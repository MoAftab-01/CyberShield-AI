import { useRef, useState } from "react";
import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";
import AnimatedBackground from "./AnimatedBackground";

export default function CopilotLayout() {

  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);

  return (
    <div
      className="
      copilot-shell
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

      <button type="button" ref={toggle} className="copilot-navigation-toggle" aria-controls="copilot-navigation"
        onKeyDown={event => { if (event.key === "Escape") setMobileOpen(false); }}
        aria-expanded={mobileOpen} onClick={() => setMobileOpen(value => !value)}>Navigation</button>
      <div id="copilot-navigation" className="copilot-navigation relative z-20" data-open={mobileOpen}
        onKeyDown={event => { if (event.key === "Escape") { setMobileOpen(false); toggle.current?.focus(); } }}>

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