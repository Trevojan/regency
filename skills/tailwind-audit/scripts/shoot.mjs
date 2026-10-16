#!/usr/bin/env node
// Headless render check over the DevTools protocol: local Edge/Chrome + Node >= 22 (built-in WebSocket), no installs.
//
//   node shoot.mjs page.html [more.html] --widths 360,768,1280 --themes light,dark --out shots
//   node shoot.mjs page.html --probe        # layout facts per width, no screenshots
//   node shoot.mjs page.html --before "document.querySelector('dialog').showModal()" --viewport
//                                            # act first (open a menu/dialog), capture the viewport
//
// Waits until the Tailwind browser build has written its CSS before capturing (fixed delays and
// --virtual-time-budget are unreliable with it). Probe loads references/layout/debug.js and reports page
// overflow, overflow culprits and `truncate` elements that are not clipping. Console errors are printed.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, basename, extname, dirname } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

const SKILL = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv.splice(i, 2)[1] : d; };
const flag = (k) => { const i = argv.indexOf(k); return i >= 0 ? (argv.splice(i, 1), true) : false; };
const widths = opt("--widths", "360,768,1280").split(",").map(Number);
const themes = opt("--themes", "light").split(",");
const out = opt("--out", "shots");
const exeArg = opt("--browser", null);
const before = opt("--before", null); // JS run after load, before capture: open a menu, a dialog, hover state…
const viewportOnly = flag("--viewport"); // capture the 900px-tall viewport only (top-layer UI is viewport-bound)
const probe = flag("--probe");
const pages = argv;
if (!pages.length) { console.error("usage: node shoot.mjs page.html [--widths ..] [--themes light,dark] [--out dir] [--probe]"); process.exit(2); }

const env = process.env;
const candidates = [exeArg,
  `${env["ProgramFiles(x86)"]}\\Microsoft\\Edge\\Application\\msedge.exe`, `${env.ProgramFiles}\\Microsoft\\Edge\\Application\\msedge.exe`,
  `${env.ProgramFiles}\\Google\\Chrome\\Application\\chrome.exe`, `${env.LOCALAPPDATA}\\Google\\Chrome\\Application\\chrome.exe`,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/microsoft-edge"];
const exe = candidates.find((c) => c && existsSync(c));
if (!exe) { console.error("no Edge/Chrome found; pass --browser PATH"); process.exit(2); }

const profile = mkdtempSync(join(tmpdir(), "tw-audit-"));
const proc = spawn(exe, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
  "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"], { stdio: ["ignore", "ignore", "pipe"] });
// The browser writes "<port>\n<path>" to DevToolsActivePort in the profile (stderr is silent on Windows Edge).
let stderr = ""; proc.stderr.on("data", (d) => { stderr += d; });
const wsUrl = await (async () => {
  const f = join(profile, "DevToolsActivePort");
  for (let i = 0; i < 200; i++) {
    if (existsSync(f)) {
      const [port, path] = readFileSync(f, "utf8").trim().split(/\r?\n/);
      if (port && path) return `ws://127.0.0.1:${port}${path}`;
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("browser did not start: " + stderr.slice(-300));
})();

const ws = new WebSocket(wsUrl);
await new Promise((ok) => ws.addEventListener("open", ok, { once: true }));
let seq = 0; const waiting = new Map(); const listeners = [];
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && waiting.has(m.id)) { const { ok, fail } = waiting.get(m.id); waiting.delete(m.id); m.error ? fail(new Error(m.error.message)) : ok(m.result); }
  else listeners.forEach((l) => l(m));
});
const send = (method, params = {}, sessionId) => new Promise((ok, fail) => {
  const id = ++seq; waiting.set(id, { ok, fail }); ws.send(JSON.stringify({ id, method, params, sessionId }));
});

const { targetId } = await send("Target.createTarget", { url: "about:blank" });
const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
const s = (method, params) => send(method, params, sessionId);
const errors = [];
listeners.push((m) => {
  if (m.sessionId !== sessionId) return;
  if (m.method === "Runtime.exceptionThrown") errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
  if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") errors.push(m.params.args.map((a) => a.value ?? a.description).join(" "));
});
await s("Page.enable"); await s("Runtime.enable");
const evaluate = async (expression) => (await s("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true })).result.value;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function load(url, width) {
  await s("Emulation.setDeviceMetricsOverride", { width, height: 900, deviceScaleFactor: 1, mobile: width < 768 });
  const loaded = new Promise((ok) => listeners.push(function l(m) { if (m.sessionId === sessionId && m.method === "Page.loadEventFired") { listeners.splice(listeners.indexOf(l), 1); ok(); } }));
  await s("Page.navigate", { url });
  await loaded;
  // Tailwind browser build: wait for its generated <style> (no type attribute, contains "tailwindcss")
  for (let i = 0; i < 50; i++) {
    const ready = await evaluate(`!document.querySelector('script[src*="tailwindcss"]') || [...document.querySelectorAll('style:not([type])')].some(s => s.textContent.includes('tailwindcss'))`);
    if (ready) break;
    await sleep(100);
  }
  await sleep(300);
}

if (!probe) mkdirSync(out, { recursive: true });
const debugJs = readFileSync(join(SKILL, "references", "layout", "debug.js"), "utf8");
for (const page of pages) {
  const base = pathToFileURL(resolve(page)).href;
  const name = basename(page, extname(page));
  for (const theme of probe ? ["light"] : themes) {
    for (const w of widths) {
      await load(base + (theme === "dark" ? "?theme=dark" : ""), w);
      if (before) { await evaluate(before); await sleep(300); }
      if (probe) {
        await evaluate(debugJs + ";window.__dbg={overflowCulprits};1");
        const r = await evaluate(`(() => {
          const o = window.__dbg.overflowCulprits();
          // a .truncate that shows no ellipsis yet sticks out of an ancestor: some wrapper grew instead (F02)
          const bad = [...document.querySelectorAll('.truncate')].filter(e => {
            if (e.scrollWidth > e.clientWidth + 1) return false; // it is clipping: fine
            const r = e.getBoundingClientRect();
            for (let n = e.parentElement, i = 0; n && i < 6; n = n.parentElement, i++)
              if (r.right > n.getBoundingClientRect().right + 1) return true;
            return false;
          }).map(e => e.outerHTML.slice(0, 120));
          return { pageScrolls: o.pageScrolls, culprits: o.culprits.slice(0, 8), truncateNotClipping: bad.slice(0, 8) };
        })()`);
        console.log(`${name} @${w}px`, JSON.stringify(r));
        continue;
      }
      const { cssContentSize } = await s("Page.getLayoutMetrics");
      const { data } = await s("Page.captureScreenshot", viewportOnly ? { format: "png" } : { format: "png", captureBeyondViewport: true,
        clip: { x: 0, y: 0, width: w, height: Math.ceil(cssContentSize.height), scale: 1 } });
      const file = join(out, `${name}-${w}-${theme}${before ? "-before" : ""}.png`);
      writeFileSync(file, Buffer.from(data, "base64"));
      console.log(file);
    }
  }
}
if (errors.length) console.log("console errors:\n  " + [...new Set(errors)].join("\n  "));
await send("Browser.close").catch(() => {});
proc.kill();
await sleep(300);
try { rmSync(profile, { recursive: true, force: true }); } catch {}
