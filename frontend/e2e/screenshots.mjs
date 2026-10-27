import { chromium } from "@playwright/test";
const out = process.argv[2] ?? "./test-results/shots";
const pages = ["/", "/catalog/ekskavatory", "/equipment/ekskavator-sany-3cx-1", "/request", "/contacts"];
const widths = [360, 768, 1440];
const browser = await chromium.launch();
for (const w of widths) {
  const ctx = await browser.newContext({ viewport: { width: w, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  for (const p of pages) {
    await page.goto("http://localhost:3000" + p, { waitUntil: "networkidle" });
    if (p === "/request") {
      // положим две позиции в корзину заявки
      await page.evaluate(() => localStorage.setItem("dt_cart", JSON.stringify([
        { equipment_id: 1, slug: "ekskavator-sany-3cx-1", name: "Экскаватор SANY 3CX", model: "3CX", image: "/media/public/equipment/ekskavator-sany-3cx-1-1.jpg", quantity: 1, unit: "shift", units: null },
        { equipment_id: 10, slug: "x", name: "Погрузчик Hyundai R220", model: "R220", image: null, quantity: 2, unit: "day", units: 3 },
      ])));
      await page.reload({ waitUntil: "networkidle" });
      await page.waitForTimeout(800);
    }
    const sw = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
    const name = (p === "/" ? "home" : p.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, ""));
    await page.screenshot({ path: `${out}/${w}-${name}.png`, fullPage: p !== "/catalog/ekskavatory" });
    console.log(w, p, "scrollWidth/innerWidth:", sw.join("/"), sw[0] > sw[1] ? "HSCROLL!" : "ok");
  }
  await ctx.close();
}
await browser.close();
