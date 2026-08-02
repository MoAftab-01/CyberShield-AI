import { Outlet } from "react-router-dom";

import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function CopilotLayout() {
  return (
    <div className="h-screen flex bg-slate-100 overflow-hidden">

      <Sidebar />

      <div className="flex flex-col flex-1 overflow-hidden">

        <Navbar />

        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>

      </div>

    </div>
  );
}