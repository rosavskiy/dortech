import { expect, type Page } from "@playwright/test";

export const CLIENT = { email: process.env.E2E_CLIENT_EMAIL ?? "client-a@dortech-demo.ru", password: process.env.E2E_PASSWORD ?? "Dortech2026!" };
export const MANAGER = { email: process.env.E2E_MANAGER_EMAIL ?? "manager@dortech-demo.ru", password: process.env.E2E_PASSWORD ?? "Dortech2026!" };

export async function expectNoHorizontalScroll(page: Page) {
  const [sw, iw] = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  expect(sw, "горизонтальная прокрутка основного содержимого").toBeLessThanOrEqual(iw);
}

export async function login(page: Page, who: { email: string; password: string }) {
  await page.goto("/login");
  await page.fill("#email", who.email);
  await page.fill("#password", who.password);
  await Promise.all([page.waitForURL((u) => !u.pathname.startsWith("/login")), page.click("button[type=submit]")]);
}
