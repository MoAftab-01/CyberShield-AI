import { Routes, Route, Navigate } from "react-router-dom";

import AppLayout from "../components/layout/AppLayout";
import ProtectedRoute from "./ProtectedRoute";

import Dashboard from "../pages/Dashboard";
import Login from "../pages/Login";
import Register from "../pages/Register";
import PasswordAnalyzer from "../pages/PasswordAnalyzer";
import UrlScanner from "../pages/UrlScanner";
import ThreatIntel from "../pages/ThreatIntel";
import Reports from "../pages/Reports";
import Settings from "../pages/Settings";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected Routes */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/password" element={<PasswordAnalyzer />} />
        <Route path="/url-scanner" element={<UrlScanner />} />
        <Route path="/threat-intel" element={<ThreatIntel />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}