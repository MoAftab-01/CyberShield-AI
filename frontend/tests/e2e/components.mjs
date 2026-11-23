// Existing tools only. Never installs packages, downloads browsers, or uses a live API.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const artifacts = path.resolve(process.env.CYBERSHIELD_UI_ARTIFACTS ?? "");
assert(process.env.CYBERSHIELD_UI_ARTIFACTS && !artifacts.startsWith(frontend + path.sep), "Supply an external temporary artifact directory.");
const tools = process.env.CYBERSHIELD_BROWSER_TOOLS;
const require = createRequire(tools ? path.join(tools, "package.json") : import.meta.url);
const { chromium } = require("playwright");
const esbuild = require("esbuild");
await mkdir(artifacts, { recursive: true });
await esbuild.build({ entryPoints: [path.join(frontend, "tests/e2e/entry.tsx")], bundle: true, format: "esm",
  jsx: "automatic", define: { "process.env.NODE_ENV": '"production"' },
  nodePaths: tools ? [path.join(tools, "node_modules")] : [],
  alias: { "@": path.join(frontend, "src") }, outdir: path.join(artifacts, "ui"),
  logLevel: "warning" });
const html = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic evidence component checks</title><link rel="stylesheet" href="/entry.css"><style>body{margin:0;background:#06111f;color:#e2e8f0;font-family:system-ui}main{max-width:850px;margin:auto;padding:16px;box-sizing:border-box}.copilot-message-bubble{width:100%;padding:16px;box-sizing:border-box}.copilot-message-bubble>div{min-width:0}button{cursor:pointer}svg{max-width:24px}*{box-sizing:border-box}</style><div id="root"></div><script type="module" src="/entry.js"></script></html>';
const server = createServer(async (req, res) => {
  const url = new URL(req.url, "http://127.0.0.1");
  if (url.pathname === "/entry.js" || url.pathname === "/entry.css") {
    res.setHeader("Content-Type", url.pathname.endsWith(".js") ? "text/javascript" : "text/css");
    res.end(await readFile(path.join(artifacts, "ui", url.pathname.slice(1))));
  } else if (url.pathname === "/") { res.setHeader("Content-Type", "text/html"); res.end(html); }
  else { res.writeHead(404); res.end(); }
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const origin = "http://127.0.0.1:" + server.address().port;
const checks = [];
let browser;
let externalAttempts = 0;
let secretLogged = false;
try {
  browser = await chromium.launch({
    executablePath: process.env.CYBERSHIELD_CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true, args: ["--disable-background-networking", "--disable-component-update", "--disable-sync", "--no-first-run"],
  });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, serviceWorkers: "block" });
  await context.route("**/*", route => {
    if (new URL(route.request().url()).origin === origin) return route.continue();
    externalAttempts++; return route.abort();
  });
  const page = await context.newPage();
  page.on("console", message => { if (message.text().includes("SYNTHETIC_UI#")) secretLogged = true; });
  async function run(name, fn) {
    await fn(); checks.push({ name, passed: true });
  }
  async function fixture(name) {
    await page.goto(origin + "/?fixture=" + name);
    await page.getByRole("heading", { name: "CyberGPT", exact: true }).waitFor();
  }
  await run("Legacy Markdown and PDF references remain available", async () => {
    await fixture("legacy");
    assert.equal(await page.locator("strong").innerText(), "Markdown");
    assert.equal(await page.getByText("legacy-fixture.pdf").count(), 1);
    assert.equal(await page.getByText("Quotation attribution checked").count(), 0);
  });
  await run("Supported response is explicitly quotation attribution only", async () => {
    await fixture("supported");
    await page.getByRole("heading", { name: "Quotation attribution checked" }).waitFor();
    assert.match(await page.locator(".grounded-answer").innerText(), /Factual truth.*not verified/);
    assert.equal(await page.getByText("legacy-fixture.pdf").count(), 0);
  });
  await run("Keyboard source control opens and focuses native disclosure", async () => {
    await page.getByRole("button", { name: "Source 1", exact: true }).focus();
    await page.keyboard.press("Enter");
    await page.waitForFunction(() => document.querySelector(".grounded-answer details")?.open);
    assert.equal(await page.locator("summary").evaluate(node => node === document.activeElement), true);
    assert.equal(await page.getByRole("button", { name: "Source 1", exact: true }).getAttribute("aria-expanded"), "true");
  });
  await run("Canonical HTTPS link, dates and source provenance are displayed", async () => {
    const link = page.getByRole("link", { name: /Open canonical source/ });
    assert.equal(await link.getAttribute("href"), "https://example.com/reference");
    assert.equal(await link.getAttribute("rel"), "noopener noreferrer");
    assert.match(await page.locator(".grounded-source").innerText(), /Jan 2, 2026/);
    assert.match(await page.locator(".grounded-source").innerText(), /Synthetic fixture/);
    await page.screenshot({ path: path.join(artifacts, "evidence-desktop.png"), fullPage: true });
  });
  await run("Multiple citations have independent disclosures", async () => {
    await fixture("multiple");
    await page.getByRole("button", { name: "Source 2", exact: true }).click();
    assert.equal(await page.locator("details[open]").count(), 1);
    assert.equal(await page.locator("details[open] summary").innerText(), "Source 2: Second synthetic source");
  });
  for (const scenario of ["invalid", "missing"]) await run("Fail closed for " + scenario + " metadata", async () => {
    await fixture(scenario);
    await page.getByRole("heading", { name: "Evidence metadata unavailable" }).waitFor();
    assert.equal(await page.getByText("UNSUPPORTED_SYNTHETIC_TEXT").count(), 0);
    assert.equal(await page.locator(".grounded-answer a").count(), 0);
  });
  for (const scenario of ["insufficient_evidence", "conflicting_evidence", "generation_failure", "retrieval_failure"]) {
    await run("Controlled status: " + scenario, async () => {
      await fixture(scenario);
      assert.equal(await page.locator(".grounded-warning").count(), 1);
      assert.equal(await page.locator(".grounded-answer details").count(), 0);
      assert.equal(await page.getByText("Backend display text.").count(), 0);
    });
  }
  await run("Source HTML and instructions remain inert literal text", async () => {
    await fixture("injection");
    await page.getByRole("button", { name: "Source 1", exact: true }).click();
    assert.equal(await page.locator(".grounded-answer img, .grounded-answer script").count(), 0);
    assert.equal(await page.evaluate(() => Boolean(window.__pwned)), false);
    assert.match(await page.locator(".grounded-answer blockquote").first().innerText(), /<img/);
  });
  await run("Unsafe canonical scheme is never clickable", async () => {
    await fixture("unsafe-url");
    await page.getByRole("button", { name: "Source 1", exact: true }).click();
    assert.equal(await page.locator(".grounded-answer a").count(), 0);
  });
  await run("Immediate synthetic password text is not stored or logged", async () => {
    await fixture("password");
    assert.match(await page.locator("main").innerText(), /Generated Password:/);
    const storage = await page.evaluate(() => JSON.stringify([localStorage, sessionStorage]));
    assert.equal(storage.includes("SYNTHETIC_UI#"), false);
    assert.equal(secretLogged, false);
  });
  await run("Mobile evidence fits and controls remain keyboard accessible", async () => {
    await page.setViewportSize({ width: 375, height: 812 });
    await fixture("supported");
    await page.getByRole("button", { name: "Source 1", exact: true }).focus();
    await page.keyboard.press("Enter");
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.equal(await page.locator("summary").evaluate(node => node === document.activeElement), true);
    await page.screenshot({ path: path.join(artifacts, "evidence-mobile.png"), fullPage: true });
  });
  assert.equal(externalAttempts, 0);
  await writeFile(path.join(artifacts, "component-browser-results.json"), JSON.stringify({
    kind: "component browser checks, not full application E2E", browser: browser.version(),
    react: require("react/package.json").version, playwright: require("playwright/package.json").version,
    checks, passed: checks.length, failures: 0, externalAttempts, secretLogged,
    productionViteBuildValidated: false,
  }, null, 2));
  console.log(JSON.stringify({ componentBrowserChecks: checks.length, passed: checks.length, externalAttempts, secretLogged }));
} catch (error) {
  await writeFile(path.join(artifacts, "component-browser-results.json"), JSON.stringify({ checks, failed: true, errorType: error.name }));
  console.error("Component browser validation failed: " + error.name);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
