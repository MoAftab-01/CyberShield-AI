import {
  LayoutDashboard,
  Bot,
  KeyRound,
  Globe,
  ShieldAlert,
  FileText,
  Settings,
  ShieldCheck,
  UserCircle,
  PanelLeftClose,
  PanelLeftOpen,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import { NavLink } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const menuItems = [
  {
    name: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "CyberGPT",
    path: "/copilot",
    icon: Bot,
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

export default function Sidebar({
  collapsed,
  onToggle,
}: SidebarProps) {

  const { user } = useAuth();

  return (

    <aside
      className={`
      relative
z-40

      h-screen

      ${
        collapsed
          ? "w-24 min-w-[96px]"
          : "w-72 min-w-[288px]"
      }

      flex
      flex-col

      flex-shrink-0

      overflow-hidden

      transition-all
      duration-500
      ease-in-out

      border-r
      border-cyan-400/20

      bg-[rgba(7,16,30,0.72)]

      backdrop-blur-3xl

      shadow-[0_0_60px_rgba(34,211,238,0.08)]
      `}
    >

      {/* Background */}

      <div className="absolute inset-0 pointer-events-none">

        <div
          className="
          absolute
          -top-32
          left-1/2

          h-80
          w-80

          -translate-x-1/2

          rounded-full

          bg-cyan-500/12

          blur-[140px]
          "
        />

        <div
          className="
          absolute
          bottom-[-180px]
          left-[-120px]

          h-96
          w-96

          rounded-full

          bg-blue-500/10

          blur-[170px]
          "
        />

      </div>

      {/* Header */}

      <div
  className="
  relative

  z-20

  overflow-visible

  flex
        items-center

        h-24

        px-5

        border-b
        border-cyan-500/10
        "
      >

        <button
  onClick={onToggle}
  className="
  absolute

  right-2

  top-1/2

  z-[9999]

  flex

  h-10
  w-10

  -translate-y-1/2

  items-center
  justify-center

  rounded-full

  border
  border-cyan-400/20

  bg-[#07111F]

  text-cyan-300

  shadow-[0_10px_30px_rgba(0,0,0,.45)]

  transition-all
  duration-300

  hover:scale-105
  hover:border-cyan-300
  hover:bg-cyan-500/10
  hover:shadow-[0_0_25px_rgba(34,211,238,.35)]
  "
>
  {collapsed ? (
    <ChevronRight size={18} />
  ) : (
    <ChevronLeft size={18} />
  )}
</button>

        <div className="flex items-center gap-4">

          <div
            className="
            flex

            h-12
            w-12

            items-center
            justify-center

            rounded-2xl

            bg-gradient-to-br

            from-cyan-400

            to-blue-600

            shadow-[0_0_30px_rgba(34,211,238,0.40)]
            "
          >

            <ShieldCheck
              size={28}
              className="text-white"
            />

          </div>

          {

            !collapsed && (

              <div>

                <h2
                  className="
                  text-2xl

                  font-bold

                  tracking-tight

                  text-white
                  "
                >

                  CyberShield

                </h2>

                <p
                  className="
                  text-xs

                  text-slate-400
                  "
                >

                  AI Security Platform

                </p>

              </div>

            )

          }

        </div>

      </div>

      {/* Navigation */}

      <nav
        className="
        relative
        z-10

        mt-6

        flex-1

        space-y-3

        px-3
        "
      >

        {

          menuItems.map((item) => {

            const Icon = item.icon;

            return (

              <NavLink key={item.path} to={item.path}>

                {

                  ({ isActive }) => (

                    <div
                      className={`
                      group

                      relative

                      flex

                      items-center

                      ${
                        collapsed
                          ? "justify-center"
                          : "gap-4"
                      }

                      rounded-2xl

                      px-4
                      py-4

                      transition-all
                      duration-300

                      overflow-hidden

                      border

                      ${
                        isActive

                          ? `
                          border-cyan-400/40

                          bg-gradient-to-r

                          from-cyan-500/20

                          via-cyan-400/10

                          to-transparent

                          shadow-[0_0_30px_rgba(34,211,238,0.20)]
                          `

                          : `
                          border-transparent

                          hover:border-cyan-400/20

                          hover:bg-white/[0.03]
                          `
                      }
                      `}
                    >

                      {

                        isActive && (

                          <div
                            className="
                            absolute

                            left-0
                            top-3
                            bottom-3

                            w-1

                            rounded-r-full

                            bg-cyan-400

                            shadow-[0_0_15px_rgba(34,211,238,1)]
                            "
                          />

                        )

                      }

                      <Icon
                        size={20}
                        className={`
                        flex-shrink-0

                        transition-all

                        duration-300

                        ${
                          isActive

                            ? "text-cyan-300 drop-shadow-[0_0_8px_rgba(34,211,238,0.9)]"

                            : "text-slate-400 group-hover:text-cyan-300 group-hover:scale-110"
                        }
                        `}
                      />

                      {

                        !collapsed && (

                          <span
                            className={`
                            font-medium

                            transition-all

                            ${
                              isActive

                                ? "text-white"

                                : "text-slate-300"
                            }
                            `}
                          >

                            {item.name}

                          </span>

                        )

                      }

                    </div>

                  )

                }

              </NavLink>

            );

          })

        }

      </nav>

            {/* User Section */}

      <div
        className="
        relative
        z-10

        border-t
        border-cyan-500/10

        p-4
        "
      >

        <div
          className={`
          group

          flex

          ${
            collapsed
              ? "justify-center"
              : "items-center gap-3"
          }

          rounded-2xl

          border

          border-cyan-500/15

          bg-white/[0.03]

          backdrop-blur-xl

          p-3

          transition-all
          duration-300

          hover:border-cyan-400/30

          hover:shadow-[0_0_25px_rgba(34,211,238,0.12)]
          `}
        >

          {/* Avatar */}

          <div
            className="
            relative

            flex

            h-12
            w-12

            items-center
            justify-center

            rounded-full

            bg-gradient-to-br

            from-cyan-400

            to-blue-600

            shadow-[0_0_25px_rgba(34,211,238,0.35)]
            "
          >

            <UserCircle
              size={28}
              className="text-white"
            />

            <span
              className="
              absolute

              bottom-0
              right-0

              h-3
              w-3

              rounded-full

              border-2
              border-[#07101E]

              bg-emerald-400
              "
            />

          </div>

          {/* User Info */}

          {

            !collapsed && (

              <div className="min-w-0 flex-1">

                <h3
                  className="
                  truncate

                  font-semibold

                  text-white
                  "
                >

                  {user?.name ?? "Cyber User"}

                </h3>

                <p
                  className="
                  truncate

                  text-xs

                  text-slate-400
                  "
                >

                  {user?.email}

                </p>

                <p
                  className="
                  mt-1

                  text-xs

                  font-medium

                  text-emerald-400
                  "
                >

                  ● Online

                </p>

              </div>

            )

          }

        </div>

      </div>

    </aside>

  );

}