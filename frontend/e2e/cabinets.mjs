import { chromium } from "@playwright/test";
const out = process.argv[2] ?? "./test-results/cabinets";
const base = "http://localhost:3000";
const browser = await chromium.launch();
async function login(page, email, password) {
  await page.goto(`${base}/login`, { waitUntil: "networkidle" });
  await page.fill("#email", email); await page.fill("#password", password);
  await Promise.all([page.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 15000 }), page.click("button[type=submit]")]);
  await page.waitForLoadState("networkidle");
}
for (const w of [1440, 360]) {
  const ctx = await browser.newContext({ viewport: { width: w, height: 900 } });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.log("PAGEERROR", w, e.message));
  // клиент
  await login(page, "newclient@example.com", "Secret123");
  console.log(w, "client landed on", page.url());
  await page.screenshot({ path: `${out}/${w}-account-list.png`, fullPage: true });
  await page.click("table a[href^='/account/inquiries/']");
  await page.waitForLoadState("networkidle"); await page.waitForTimeout(500);
  console.log(w, "client detail", page.url());
  await page.screenshot({ path: `${out}/${w}-account-detail.png`, fullPage: true });
  await page.goto(`${base}/account/profile`, { waitUntil: "networkidle" });
  await page.screenshot({ path: `${out}/${w}-account-profile.png`, fullPage: true });
  // выход
  await page.click("text=Выйти"); await page.waitForTimeout(800);
  // менеджер
  await login(page, "manager@dortech-demo.ru", "Dortech2026!");
  console.log(w, "manager landed on", page.url());
  await page.screenshot({ path: `${out}/${w}-manager-list.png`, fullPage: true });
  await page.click("table a[href^='/manager/inquiries/']");
  await page.waitForLoadState("networkidle"); await page.waitForTimeout(500);
  console.log(w, "manager detail", page.url());
  await page.screenshot({ path: `${out}/${w}-manager-detail.png`, fullPage: true });
  const sw = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  console.log(w, "hscroll:", sw[0] > sw[1] ? "YES!" : "no");
  await ctx.close();
}
await browser.close();
