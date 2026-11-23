import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("CVE follows CyberGPT; only the old Threat Intelligence menu item is removed", () => {
  const sidebar = readFileSync(new URL("../src/components/layout/Sidebar.tsx", import.meta.url), "utf8");
  const menu = sidebar.slice(sidebar.indexOf("const menuItems"), sidebar.indexOf("export default"));
  const names = [...menu.matchAll(/name:\s*"([^"]+)"/g)].map(match => match[1]);
  assert.equal(names[names.indexOf("CyberGPT") + 1], "CVE Investigation");
  assert(!names.includes("Threat Intelligence"));
  for (const name of ["Dashboard", "Password Analyzer", "URL Scanner", "Reports", "Settings"]) assert(names.includes(name));
});
test("investigation and CyberGPT keep the protected layout and legacy routes remain", () => {
  const router = readFileSync(new URL("../src/router/AppRouter.tsx", import.meta.url), "utf8");
  const protectedChat = router.slice(router.lastIndexOf("<ProtectedRoute>"));
  assert(protectedChat.includes('path="/copilot"') && protectedChat.includes('path="/investigate"'));
  assert(router.includes('path="/threat-intel"'));
  for (const path of ["/dashboard", "/password", "/url-scanner", "/reports", "/settings"]) assert(router.includes('path="' + path + '"'));
});
