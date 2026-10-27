import { test, expect } from "@playwright/test";
import { expectNoHorizontalScroll, login, CLIENT, MANAGER } from "./helpers";

test("гость создаёт заявку и получает номер", async ({ page }) => {
  await page.goto("/catalog");
  await page.getByRole("button", { name: "В заявку" }).first().click();
  await page.goto("/request");
  await expect(page.getByText("Предварительный расчёт")).toBeVisible();
  await page.fill("#from", "2026-11-10");
  await page.fill("#to", "2026-11-12");
  await page.fill("#contact_name", "Тест Playwright");
  await page.fill("#contact_phone", "+7 900 000-00-00");
  await page.fill("#contact_email", "pw@example.com");
  await page.getByRole("checkbox", { name: /Согласен/ }).check();
  await expectNoHorizontalScroll(page);
  await page.getByRole("button", { name: "Отправить заявку" }).click();
  await expect(page).toHaveURL(/\/request\/success/);
  await expect(page.locator("h1")).toContainText(/Заявка DT-\d{6} принята/);
});

test("клиент видит свои заявки, менеджер — все; чужой id → не найдено", async ({ page, context }) => {
  await login(page, CLIENT);
  await expect(page).toHaveURL(/\/account\/inquiries/);
  await expect(page.locator("h1")).toHaveText("Мои заявки");
  const first = page.locator("table a[href^='/account/inquiries/']").first();
  await expect(first).toBeVisible();
  await first.click();
  await expect(page.locator("h1")).toContainText("Заявка DT-");
  await expectNoHorizontalScroll(page);
  const own = page.url().split("/").pop()!;
  await page.getByRole("button", { name: "Выйти" }).click();
  await context.clearCookies();

  await login(page, MANAGER);
  await expect(page).toHaveURL(/\/manager\/inquiries/);
  await expect(page.locator("h1")).toHaveText("Заявки");
  const foreign = page.locator("table a[href^='/manager/inquiries/']").filter({ hasNotText: "DT-000000" }).first();
  await foreign.click();
  await expect(page.locator("h1")).toContainText("Заявка DT-");
  await expect(page.getByText("Изменить статус")).toBeVisible();
  const foreignId = page.url().split("/").pop()!;
  await page.getByRole("button", { name: "Выйти" }).click();
  await context.clearCookies();

  await login(page, CLIENT);
  if (foreignId !== own) {
    await page.goto(`/account/inquiries/${foreignId}`);
    await expect(page.getByText(/не найдена|Заявка не найдена/)).toBeVisible();
  }
});
