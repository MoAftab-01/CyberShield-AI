import { useState } from "react";
import {
  Bell,
  Search,
  ChevronDown,
  LogOut,
} from "lucide-react";

import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

export default function Navbar() {
  const [open, setOpen] = useState(false);

  const { user, logout } = useAuth();

  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8">

      {/* Left */}

      <div>
        <h1 className="text-2xl font-bold text-slate-800">
          Dashboard
        </h1>

        <p className="text-slate-500">
          AI Powered Cyber Threat Intelligence
        </p>
      </div>

      {/* Right */}

      <div className="flex items-center gap-6">

        {/* Search */}

        <div className="relative">

          <Search
            size={18}
            className="absolute left-3 top-3 text-slate-400"
          />

          <input
            placeholder="Search..."
            className="w-72 rounded-xl border border-slate-300 py-2 pl-10 pr-4 outline-none focus:border-cyan-500"
          />

        </div>

        {/* Notification */}

        <Bell
          size={22}
          className="cursor-pointer text-slate-600 hover:text-cyan-600"
        />

        {/* User */}

        <div className="relative">

          <button
            onClick={() => setOpen(!open)}
            className="flex items-center gap-3 rounded-xl border bg-white px-3 py-2 hover:bg-slate-50"
          >

            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-600 text-white font-semibold">

              {user?.name?.charAt(0).toUpperCase() ?? "U"}

            </div>

            <div className="text-left">

              <div className="font-semibold text-slate-800">

                {user?.name ?? "User"}

              </div>

              <div className="text-xs text-slate-500">

                {user?.email}

              </div>

            </div>

            <ChevronDown size={18} />

          </button>

          {open && (

            <div className="absolute right-0 mt-3 w-64 overflow-hidden rounded-xl border bg-white shadow-xl z-50">

              <div className="border-b px-4 py-4">

                <div className="font-semibold">

                  {user?.name}

                </div>

                <div className="text-sm text-slate-500">

                  {user?.email}

                </div>

              </div>

              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50"
              >

                <LogOut size={18} />

                Logout

              </button>

            </div>

          )}

        </div>

      </div>

    </header>
  );
}