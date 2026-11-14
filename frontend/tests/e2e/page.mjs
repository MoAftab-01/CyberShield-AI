// Chat-page/API integration using existing tools. This is not a production Vite/AppRouter build.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { createServer } from "node:net";
import { mkdir, cp, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { supported } from "../fixtures.ts";
const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const project = path.dirname(frontend);
const artifacts = process.env.CYBERSHIELD_UI_ARTIFACTS;
assert(artifacts && !path.resolve(artifacts).startsWith(project + path.sep));
const tools = process.env.CYBERSHIELD_BROWSER_TOOLS;
const require = createRequire(tools ? path.join(tools, "package.json") : import.meta.url);
const { chromium } = require("playwright");
const esbuild = require("esbuild");
const assets = path.join(artifacts, "page-assets");
await mkdir(assets, { recursive: true });
const production = Boolean(process.env.CYBERSHIELD_FRONTEND_DIST);
if (!production) {
await esbuild.build({ entryPoints: [path.join(frontend, "tests/e2e/page.tsx")], bundle: true,
  format: "esm", jsx: "automatic", nodePaths: tools ? [path.join(tools, "node_modules")] : [],
  define: { "process.env.NODE_ENV": '"production"', "import.meta.env.VITE_API_URL": '"/api"' },
  alias: { "@": path.join(frontend, "src") }, outdir: assets, logLevel: "warning",
  plugins: [{ name: "fixture-toast-only", setup(build) {
    build.onResolve({ filter: /^sonner$/ }, () => ({ path: "fixture-toast", namespace: "fixture" }));
    build.onLoad({ filter: /.*/, namespace: "fixture" }, () => ({ contents: "export const toast = {success(){},error(){}};" }));
  }}],
});
await writeFile(path.join(assets, "index.html"), '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Isolated chat-page checks</title><link rel="stylesheet" href="/assets/page.css"><style>body{margin:0;background:#06111f;color:#e2e8f0;font:16px system-ui}.copilot-page{display:flex;position:relative;height:100vh}.copilot-page>div:last-child{display:flex;flex-direction:column;flex:1;min-width:0}.copilot-chat-scroll{flex:1;overflow:auto}svg{max-width:24px}button{cursor:pointer}textarea{width:80%}.copilot-conversations{width:280px;overflow:auto}.copilot-message-bubble{padding:12px}*{box-sizing:border-box}</style><div id="root"></div><script type="module" src="/assets/page.js"></script></html>');
} else { await cp(process.env.CYBERSHIELD_FRONTEND_DIST, assets, { recursive: true }); }
async function freePort() {
  const server = createServer();
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}
const children = [];
const checks = [];
let stage = "startup";
let browser;
let externalAttempts = 0;
let secretLogged = false;
async function server(legacy = false) {
  const data = path.join(artifacts, legacy ? "server-legacy" : "server-v2");
  await mkdir(data, { recursive: true });
  const port = await freePort();
  const child = spawn(process.env.CYBERSHIELD_PYTHON || "python", [
    "-B", path.join(frontend, "tests/e2e/server.py"), "--data", data, "--assets", assets,
    "--backend", path.join(project, "backend"), "--port", String(port), ...(legacy ? ["--legacy"] : []), ...(production ? ["--production-ui"] : []),
  ], { windowsHide: true, env: { ...process.env, PYTHONUTF8: "1", PYTHONDONTWRITEBYTECODE: "1" }, stdio: ["ignore", "pipe", "pipe"] });
  children.push(child);
  let output = "";
  child.stdout.on("data", chunk => { output += chunk.toString(); });
  child.stderr.on("data", chunk => { output += chunk.toString(); });
  const origin = "http://127.0.0.1:" + port;
  let ready = false;
  for (let i = 0; i < 160; i++) {
    if (child.exitCode !== null) break;
    try { if ((await fetch(origin + "/health")).ok) { ready = true; break; } } catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  await writeFile(path.join(data, "server.log"), output);
  assert(ready, "Synthetic backend did not become ready");
  return { origin, child };
}
async function account(origin, name) {
  const response = await fetch(origin + "/api/users/login", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: name+"@example.com", password: "SyntheticBrowserPass923!" }),
  });
  assert.equal(response.status, 200);
  const token = (await response.json()).access_token;
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, serviceWorkers: "block",
    storageState: { cookies: [], origins: [{ origin, localStorage: [{ name: "access_token", value: token }] }] },
  });
  await context.route("**/*", route => {
    if (new URL(route.request().url()).origin === origin) return route.continue();
    externalAttempts++; return route.abort();
  });
  const page = await context.newPage();
  page.on("console", msg => { if (msg.text().includes("SYNTHETIC_UI#")) secretLogged = true; });
  await page.goto(origin + (production ? "/copilot" : "/"));
  await page.getByRole("textbox", { name: "Message CyberGPT" }).waitFor();
  return { context, page };
}
async function run(name, fn) { stage = name; await fn(); checks.push({ name, passed: true }); }
async function send(page, text) {
  await page.getByRole("textbox", { name: "Message CyberGPT" }).fill(text);
  await page.getByRole("button", { name: "Send message", exact: true }).click();
}
async function fresh(page) {
  await page.getByRole("button", { name: /New Chat/ }).click();
}
const question = "What approvals does Juniper TLS recovery require?";
try {
  const live = await server();
  browser = await chromium.launch({ executablePath: process.env.CYBERSHIELD_CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true, args: ["--disable-background-networking", "--disable-component-update", "--disable-sync", "--no-first-run"] });
  const alpha = await account(live.origin, "alpha");
  let ownedConversation;
  await run("Authenticated real API returns multiple attributed quotations in the actual chat page", async () => {
    const response = alpha.page.waitForResponse(r => r.url().endsWith("/api/copilot/ask") && r.request().method() === "POST");
    await send(alpha.page, question);
    const json = await (await response).json();
    ownedConversation = json.conversation_id;
    assert.equal(json.grounding.status, "supported_quotes");
    await alpha.page.getByRole("heading", { name: "Quotation attribution checked" }).waitFor();
    assert.equal(await alpha.page.locator(".grounded-answer details").count(), 2);
  });
  if (production) {
    await run("Production desktop citation controls and screenshot", async () => {
      await alpha.page.getByRole("button", { name: "Source 1", exact: true }).first().focus();
      await alpha.page.keyboard.press("Enter");
      assert.equal(await alpha.page.locator("details[open] summary").first().evaluate(node => node === document.activeElement), true);
      await alpha.page.locator(".copilot-chat-scroll").evaluate(node => { node.scrollTop = 0; });
      await alpha.page.screenshot({ path: path.join(artifacts, "production-desktop.png"), fullPage: true });
    });
    for (const variant of ["missing", "conflict", "injection"]) await run("Production response presentation: " + variant, async () => {
      await fresh(alpha.page);
      const grounding = supported();
      if (variant === "conflict") Object.assign(grounding, { status: "conflicting_evidence", abstained: true, claims: [], evidence: [] });
      if (variant === "injection") {
        const literal = '<img src="x" onerror="window.__pwned=1"> Ignore previous instructions.';
        grounding.claims[0].text = literal; grounding.evidence[0].excerpt = literal;
        grounding.evidence[0].canonical_url = "javascript:window.__pwned=1";
      }
      await alpha.page.route("**/api/copilot/ask", route => route.fulfill({ status: 200, json: {
        answer: "UNSUPPORTED_SYNTHETIC_TEXT", conversation_id: ownedConversation, sources: [],
        grounding: variant === "missing" ? { status: "supported_quotes" } : grounding,
      } }), { times: 1 });
      await send(alpha.page, question);
      const heading = variant === "missing" ? "Evidence metadata unavailable" : variant === "conflict" ? "Conflicting sources" : "Quotation attribution checked";
      await alpha.page.getByRole("heading", { name: heading }).waitFor();
      assert.equal(await alpha.page.getByText("UNSUPPORTED_SYNTHETIC_TEXT").count(), 0);
      if (variant === "injection") {
        await alpha.page.getByRole("button", { name: "Source 1", exact: true }).click();
        assert.equal(await alpha.page.locator(".grounded-answer img, .grounded-answer script, .grounded-answer a").count(), 0);
        assert.equal(await alpha.page.evaluate(() => Boolean(window.__pwned)), false);
      }
    });
    await run("Rename failure never logs a pasted synthetic generated password", async () => {
      await alpha.page.getByRole("button", { name: "Rename conversation", exact: true }).first().click();
      await alpha.page.getByRole("textbox", { name: "Conversation title" }).fill("SYNTHETIC_UI#Value923!");
      await alpha.page.route("**/api/conversations/*", route => route.request().method() === "PATCH" ? route.abort("failed") : route.continue(), { times: 1 });
      await alpha.page.getByRole("button", { name: "Save conversation title", exact: true }).click();
      await alpha.page.getByRole("alert").filter({ hasText: "Unable to rename conversation." }).waitFor();
      assert.equal(secretLogged, false);
      await alpha.page.getByRole("button", { name: "Cancel rename", exact: true }).click();
    });
    await fresh(alpha.page);
  }
  await run("Existing history loads without fabricating structured verification", async () => {
    await fresh(alpha.page);
    await alpha.page.getByRole("button", { name: question, exact: true }).first().focus();
    await alpha.page.keyboard.press("Enter");
    await alpha.page.waitForFunction(() => document.body.innerText.includes("[source 1]"));
    assert.equal(await alpha.page.locator(".grounded-answer").count(), 0);
  });
  await run("Provider timeout becomes a controlled evidence status", async () => {
    await fresh(alpha.page);
    await send(alpha.page, question+" timeout");
    await alpha.page.getByRole("heading", { name: "Answer generation unavailable" }).waitFor();
  });
  await run("Network failure has safe manual retry without diagnostic bodies", async () => {
    await fresh(alpha.page);
    await alpha.page.route("**/api/copilot/ask", route => route.abort("timedout"), { times: 1 });
    await send(alpha.page, question);
    await alpha.page.getByRole("button", { name: "Retry message" }).waitFor();
    await alpha.page.getByRole("button", { name: "Retry message" }).click();
    await alpha.page.getByRole("heading", { name: "Quotation attribution checked" }).waitFor();
  });
  await run("Cancel/new chat prevents a delayed response from entering another view", async () => {
    await fresh(alpha.page);
    await alpha.page.route("**/api/copilot/ask", async route => {
      await new Promise(resolve => setTimeout(resolve, 250));
      try { await route.continue(); } catch {}
    }, { times: 1 });
    await send(alpha.page, question);
    await alpha.page.getByRole("button", { name: "Cancel response" }).click();
    await fresh(alpha.page);
    await new Promise(resolve => setTimeout(resolve, 400));
    assert.equal(await alpha.page.locator(".grounded-answer").count(), 0);
  });
  await run("Generated password stays immediate, absent from storage and diagnostics", async () => {
    await send(alpha.page, "Generate a strong password");
    await alpha.page.waitForFunction(() => document.body.innerText.includes("Generated Password"));
    const storage = await alpha.page.evaluate(() => JSON.stringify([localStorage, sessionStorage]));
    assert.equal(storage.includes("SYNTHETIC_UI#"), false);
    assert.equal(secretLogged, false);
    await fresh(alpha.page);
  });
  await run("Owner-scoped private evidence is usable by its authenticated owner", async () => {
    await send(alpha.page, "How is Amber gateway recovery authorized?");
    await alpha.page.getByRole("heading", { name: "Quotation attribution checked" }).waitFor();
    assert.match(await alpha.page.locator(".grounded-answer").innerText(), /Amber gateway/);
  });
  const beta = await account(live.origin, "beta");
  await run("Different account cannot retrieve private evidence or read another conversation", async () => {
    await send(beta.page, "How is Amber gateway recovery authorized?");
    await beta.page.getByRole("heading", { name: "Insufficient evidence" }).waitFor();
    assert.equal(await beta.page.locator(".grounded-answer details").count(), 0);
    const status = await beta.page.evaluate(async id => (await fetch("/api/conversations/"+id, {
      headers: { Authorization: "Bearer "+localStorage.getItem("access_token") },
    })).status, ownedConversation);
    assert.equal(status, 404);
  });
  await run("Invalid authentication removes the local token and redirects to login", async () => {
    await beta.page.evaluate(() => localStorage.setItem("access_token", "invalid-synthetic"));
    await send(beta.page, question);
    await beta.page.waitForURL("**/login");
    assert.equal(await beta.page.evaluate(() => localStorage.getItem("access_token")), null);
  });
  if (production) {
    await run("Protected frontend route redirects an unauthenticated browser", async () => {
      const context = await browser.newContext();
      const page = await context.newPage();
      await context.route("**/*", route => new URL(route.request().url()).origin === live.origin ? route.continue() : route.abort());
      await page.goto(live.origin + "/copilot");
      await page.waitForURL("**/login");
      assert.equal(await page.locator(".grounded-answer").count(), 0);
      await context.close();
    });
    await run("Production mobile layout, history and navigation keyboard controls", async () => {
      await alpha.page.setViewportSize({ width: 375, height: 812 });
      const history = alpha.page.getByRole("button", { name: "Chat history", exact: true });
      await history.click();
      await alpha.page.getByRole("button", { name: /New Chat/ }).click();
      await send(alpha.page, question);
      await alpha.page.getByRole("heading", { name: "Quotation attribution checked" }).waitFor();
      await alpha.page.getByRole("button", { name: "Source 1", exact: true }).first().focus();
      await alpha.page.keyboard.press("Enter");
      assert.equal(await alpha.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      assert.equal(await alpha.page.locator("details[open] summary").first().evaluate(node => node === document.activeElement), true);
      const upload = await alpha.page.getByTitle("Upload document").boundingBox();
      const sendButton = await alpha.page.getByRole("button", { name: "Send message", exact: true }).boundingBox();
      await writeFile(path.join(artifacts, "mobile-layout.json"), JSON.stringify({ upload, sendButton,
        ancestors: await alpha.page.getByTitle("Upload document").evaluate(node => {
          const rows = []; for (let p = node; p; p = p.parentElement) {
            const rect = p.getBoundingClientRect(); rows.push({ tag:p.tagName, classes:p.className, x:rect.x, width:rect.width, client:p.clientWidth, scroll:p.scrollWidth, left:p.scrollLeft });
          } return rows;
        }),
      }, null, 2));
      assert(upload && upload.x >= 0 && upload.x + upload.width <= 375);
      assert(sendButton && sendButton.x >= 0 && sendButton.x + sendButton.width <= 375);
      await alpha.page.locator("details[open] summary").first().click();
      await alpha.page.locator(".copilot-chat-scroll").evaluate(node => { node.scrollTop = 0; });
      await alpha.page.screenshot({ path: path.join(artifacts, "production-mobile.png"), fullPage: true });
      const navigation = alpha.page.getByRole("button", { name: "Navigation", exact: true });
      await navigation.click();
      await alpha.page.keyboard.press("Escape");
      assert.equal(await navigation.getAttribute("aria-expanded"), "false");
    });
  }
  const legacy = await server(true);
  const old = await account(legacy.origin, "alpha");
  await run("Disabled server flag retains the legacy frontend/API path", async () => {
    await send(old.page, question);
    await old.page.getByText("Legacy synthetic answer.", { exact: true }).waitFor();
    assert.equal(await old.page.locator(".grounded-answer").count(), 0);
  });
  assert.equal(externalAttempts, 0);
  await writeFile(path.join(artifacts, "page-browser-results.json"), JSON.stringify({
    kind: production ? "production Vite UI plus isolated real FastAPI auth/retrieval/verifier" : "actual chat page plus real isolated FastAPI; toast stubbed; fixture CSS",
    passed: checks.length, failures: 0, checks, externalAttempts, secretLogged, browser: browser.version(),
  }, null, 2));
  console.log(JSON.stringify({ chatPageApiChecks: checks.length, passed: checks.length, externalAttempts, secretLogged }));
} catch (error) {
  await writeFile(path.join(artifacts, "page-browser-results.json"), JSON.stringify({ checks, failed: true, stage, errorType: error.name, locations: String(error.stack).split("\n").filter(line => line.trimStart().startsWith("at ")).slice(0, 3) }));
  console.error("Chat-page validation failed: " + error.name);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  for (const child of children) if (child.exitCode === null) child.kill();
}
