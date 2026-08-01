import {
  LayoutDashboard,
  KeyRound,
  Globe,
  ShieldAlert,
  FileText,
  Settings,
  ShieldCheck,
  UserCircle,
} from "lucide-react";

import { NavLink } from "react-router-dom";

const menuItems = [
  {
    name: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Password Analyzer",
    path: "/password",
    icon: KeyRound,
  },
  {
    name: "URL Scanner",
    path: "/url-scanner",
    icon: Globe,
  },
  {
    name: "Threat Intelligence",
    path: "/threat-intel",
    icon: ShieldAlert,
  },
  {
    name: "Reports",
    path: "/reports",
    icon: FileText,
  },
  {
    name: "Settings",
    path: "/settings",
    icon: Settings,
  },
];

export default function Sidebar() {
  return (
    <aside className="w-72 bg-slate-950 text-white flex flex-col border-r border-slate-800">

      {/* Logo */}

      <div className="h-20 flex items-center px-6 border-b border-slate-800">

        <ShieldCheck
          className="text-cyan-400 mr-3"
          size={34}
        />

        <div>
          <h1 className="font-bold text-xl">
            CyberShield
          </h1>

          <p className="text-xs text-slate-400">
            AI Security Platform
          </p>
        </div>
      </div>

      {/* Navigation */}

      <nav className="flex-1 px-4 py-6 space-y-2">

        {menuItems.map((item) => {

          const Icon = item.icon;

          return (

            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-4 py-3 transition-all duration-200 ${
                  isActive
                    ? "bg-cyan-600 text-white shadow-lg"
                    : "hover:bg-slate-900 text-slate-300"
                }`
              }
            >
              <Icon size={20} />

              <span>{item.name}</span>

            </NavLink>

          );
        })}

      </nav>

      {/* User */}

      <div className="border-t border-slate-800 p-5">

        <div className="flex items-center gap-3">

          <UserCircle
            size={42}
            className="text-cyan-400"
          />

          <div>

            <h3 className="font-semibold">
              Mohammed
            </h3>

            <p className="text-sm text-green-400">
              ● Online
            </p>

          </div>

        </div>

      </div>

    </aside>
  );
}