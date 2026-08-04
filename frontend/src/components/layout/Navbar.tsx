import { useEffect, useRef, useState } from "react";import {
  Bell,
  Search,
  ChevronDown,
  LogOut,
} from "lucide-react";

import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

interface NavbarProps {
  title: string;
  subtitle: string;
}

export default function Navbar({
  title,
  subtitle,
}: NavbarProps) {
  const [open, setOpen] = useState(false);
const [notificationsOpen, setNotificationsOpen] = useState(false);

const [notifications, setNotifications] = useState([
  {
    title: "Dashboard Loaded",
    description: "System initialized successfully.",
    success: false,
  },
  {
    title: "CyberGPT Online",
    description: "AI assistant is ready.",
    success: false,
  },
  {
    title: "Threat Intelligence",
    description: "Latest vulnerability feeds synced.",
    success: false,
  },
  {
    title: "No Critical Alerts",
    description: "Everything looks secure.",
    success: true,
  },
]);

const notificationRef = useRef<HTMLDivElement>(null);

  const { user, logout } = useAuth();

  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  useEffect(() => {
  function handleClickOutside(event: MouseEvent) {
    if (
      notificationRef.current &&
      !notificationRef.current.contains(
        event.target as Node
      )
    ) {
      setNotificationsOpen(false);
    }
  }

  function handleEsc(event: KeyboardEvent) {
    if (event.key === "Escape") {
      setNotificationsOpen(false);
    }
  }

  document.addEventListener(
    "mousedown",
    handleClickOutside
  );

  document.addEventListener(
    "keydown",
    handleEsc
  );

  return () => {
    document.removeEventListener(
      "mousedown",
      handleClickOutside
    );

    document.removeEventListener(
      "keydown",
      handleEsc
    );
  };
}, []);

const [search, setSearch] = useState("");


const pages = [
  {
    title: "Dashboard",
    keyword: "dashboard",
    route: "/dashboard",
  },
  {
    title: "CyberGPT",
    keyword: "copilot",
    route: "/copilot",
  },
  {
    title: "Password Analyzer",
    keyword: "password",
    route: "/password",
  },
  {
    title: "URL Scanner",
    keyword: "url",
    route: "/url-scanner",
  },
  {
    title: "Threat Intelligence",
    keyword: "threat",
    route: "/threat-intel",
  },
  {
    title: "Reports",
    keyword: "report",
    route: "/reports",
  },
  {
    title: "Settings",
    keyword: "settings",
    route: "/settings",
  },
];



function handleSearch() {
  const query = search.trim().toLowerCase();

  if (!query) return;

  const page = pages.find(
    (p) =>
      p.title.toLowerCase().includes(query) ||
      p.keyword.includes(query)
  );

  if (page) {
    navigate(page.route);
    setSearch("");
  } else {
    alert("No matching feature found.");
  }
}




  return (
    <header
  className="
  relative

  z-[100]

  overflow-visible

  px-8

  pt-6
  "
>

      <div
        className="
        flex
        items-center
        justify-between

        rounded-3xl

        border
        border-cyan-500/20

        bg-[#0B1628]/70

        backdrop-blur-2xl

        px-8
        py-5

        shadow-xl
        shadow-cyan-950/20
        "
      >

        {/* Left */}

        <div>

          <h1 className="text-3xl font-bold text-white">
            {title}
          </h1>

          <p className="mt-1 text-slate-400">
            {subtitle}
          </p>

        </div>

        {/* Right */}

        <div className="flex items-center gap-5">

          <div className="relative">

            <button
  onClick={handleSearch}
  className="
  absolute
  left-4
  top-1/2
  -translate-y-1/2
  text-slate-400
  transition
  hover:text-cyan-300
  "
>
  <Search size={18} />
</button>

            <input
  value={search}
  onChange={(e) => setSearch(e.target.value)}
  onKeyDown={(e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  }}
  placeholder="Search features..."
  className="
  w-72
  rounded-2xl
  border
  border-slate-700
  bg-slate-900/70
  py-3
  pl-11
  pr-4
  text-white
  placeholder:text-slate-500
  outline-none
  transition-all
  focus:border-cyan-400
  focus:ring-2
  focus:ring-cyan-500/20
  "
/>

          </div>

          <div className="relative"
          >


  <button
    onClick={() =>
      setNotificationsOpen(!notificationsOpen)
    }
    className="
    relative

    flex

    h-11
    w-11

    items-center
    justify-center

    rounded-2xl

    border
    border-slate-700

    bg-slate-900/70

    text-slate-300

    transition-all

    hover:border-cyan-400

    hover:text-cyan-300
    "
  >

    <Bell size={20} />

    {/* Notification Dot */}

    {notifications.length > 0 && (

<span
  className="
  absolute

  -right-1

  -top-1

  flex

  h-5

  w-5

  items-center

  justify-center

  rounded-full

  bg-cyan-500

  text-[10px]

  font-bold

  text-white

  shadow-[0_0_12px_rgba(34,211,238,.8)]
  "
>

  {notifications.length}

</span>

)}

  </button>

  {notificationsOpen && (

    <div
  ref={notificationRef}
      className="
      absolute

      right-0

      mt-3

      w-80

      overflow-hidden

      rounded-3xl

      border

      border-cyan-400/20

      bg-[#07111F]/95

      backdrop-blur-2xl

      shadow-[0_20px_60px_rgba(0,0,0,.45)]

      z-[9999]
      "
    >

      {/* Header */}

      <div
  className="
  flex

  items-center

  justify-between

  border-b

  border-cyan-400/10

  px-5

  py-4
  "
>

<div>

<h3 className="font-semibold text-white">

Notifications

</h3>

<p className="text-xs text-slate-400">

CyberGPT Activity

</p>

</div>

<button

onClick={() => {

setNotifications([]);

}}

className="
rounded-lg

px-3

py-1

text-xs

text-red-400

transition

hover:bg-red-500/10
"

>

✕

</button>

</div>

      {/* Items */}

      <div className="divide-y divide-slate-800">

        {notifications.length === 0 ? (

<div
className="
py-10

text-center

text-slate-400
"
>

No notifications 🎉

</div>

) : (

notifications.map((item) => (

<NotificationItem

key={item.title}

title={item.title}

description={item.description}

success={item.success}

/>

))

)}

      </div>

    </div>

  )}

</div>

          <div
  className="
  relative

  z-[999]
  "
>

            <button
              onClick={() => setOpen(!open)}
              className="
              flex
              items-center
              gap-3

              rounded-2xl

              border
              border-slate-700

              bg-slate-900/70

              px-4
              py-2

              transition-all

              hover:border-cyan-400
              "
            >

              <div
                className="
                flex

                h-11
                w-11

                items-center
                justify-center

                rounded-full

                bg-gradient-to-br
                from-cyan-400
                to-blue-600

                text-white

                font-bold
                "
              >

                {user?.name?.charAt(0).toUpperCase() ?? "U"}

              </div>

              <div className="text-left">

                <div className="font-semibold text-white">

                  {user?.name ?? "User"}

                </div>

                <div
  className="
  max-w-[180px]

  truncate

  text-xs

  text-slate-400
  "
  title={user?.email}
>

  {user?.email}

</div>

              </div>

              <ChevronDown
                size={18}
                className="text-slate-400"
              />

            </button>

            {open && (

              <div
  className="
  absolute

  right-0

  top-full

  mt-3

animate-in

fade-in

zoom-in-95

duration-200

  w-64

  overflow-hidden

  rounded-2xl

  border

  border-cyan-400/20

  bg-[#07111F]/95

  backdrop-blur-2xl

  shadow-[0_25px_80px_rgba(0,0,0,.55)]

  z-[9999]
  "
>

                <div className="border-b border-slate-700 px-5 py-4">

                  <div className="font-semibold text-white">

                    {user?.name}

                  </div>

                  <div
  className="
  truncate

  text-sm

  text-slate-400
  "
  title={user?.email}
>

  {user?.email}

</div>

                </div>

                <button
                  onClick={handleLogout}
                  className="
                  flex

                  w-full

                  items-center

                  gap-3

                  px-5
                  py-4

                  text-red-400

                  transition

                  hover:bg-red-500/10
                  "
                >

                  <LogOut size={18} />

                  Logout

                </button>

              </div>

            )}

          </div>

        </div>

      </div>

    </header>
  );
}

function NotificationItem({
  title,
  description,
  success = false,
}: {
  title: string;
  description: string;
  success?: boolean;
}) {
  return (
    <div
      className="
      flex

      items-start

      gap-3

      px-5

      py-4

      transition

      hover:bg-cyan-500/5
      "
    >

      <div
        className={`
        mt-2

        h-2.5

        w-2.5

        rounded-full

        ${
          success
            ? "bg-emerald-400 shadow-[0_0_10px_rgba(74,222,128,.8)]"
            : "bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,.8)]"
        }
        `}
      />

      <div>

        <p className="font-medium text-white">

          {title}

        </p>

        <p className="mt-1 text-sm text-slate-400">

          {description}

        </p>

      </div>

    </div>
  );
}