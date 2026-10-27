import { test, expect } from "@playwright/test";
import { expectNoHorizontalScroll } from "./helpers";

const PAGES = ["/", "/catalog", "/services", "/projects", "/publications", "/contacts", "/about", "/privacy", "/compare", "/request", "/login", "/register"];

for (const path of PAGES) {
  test(`страница ${path} открывается без горизонтальной прокрутки`, async ({ page }) => {
    const res = await page.goto(path);
    expect(res?.status()).toBe(200);
    await expect(page.locator("h1").first()).toBeVisible();
    await expectNoHorizontalScroll(page);
  });
}

test("карточка техники из sitemap", async ({ page, request }) => {
  const xml = await (await request.get("/sitemap.xml")).text();
  const m = xml.match(/<loc>([^<]*\/equipment\/[^<]+)<\/loc>/);
  expect(m, "в sitemap есть карточки техники").toBeTruthy();
  const url = new URL(m![1]);
  const res = await page.goto(url.pathname);
  expect(res?.status()).toBe(200);
  await expect(page.locator("h1")).toBeVisible();
  await expect(page.getByRole("button", { name: /В заявку|Недоступно/ })).toBeVisible();
  await expectNoHorizontalScroll(page);
});

test("мобильное меню открывается и закрывается", async ({ page, viewport }) => {
  test.skip((viewport?.width ?? 0) >= 1024, "только для узких экранов");
  await page.goto("/");
  await page.getByRole("button", { name: "Открыть меню" }).click();
  await expect(page.getByRole("dialog", { name: "Меню" })).toBeVisible();
  await page.getByRole("dialog").getByRole("link", { name: "Услуги" }).click();
  await expect(page).toHaveURL(/\/services/);
});

test("контент правится из панели — заголовок страницы приходит из API", async ({ page, request }) => {
  const api = await (await request.get("/api/v1/content/pages/about")).json();
  await page.goto("/about");
  await expect(page.locator("h1")).toHaveText(api.title);
});

test("robots.txt и sitemap.xml", async ({ request }) => {
  expect((await request.get("/robots.txt")).status()).toBe(200);
  const sm = await request.get("/sitemap.xml");
  expect(sm.status()).toBe(200);
  expect(await sm.text()).toContain("<urlset");
});
