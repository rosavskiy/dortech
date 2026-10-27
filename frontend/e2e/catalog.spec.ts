import { test, expect } from "@playwright/test";
import { expectNoHorizontalScroll } from "./helpers";

test("поиск, фильтр по производителю и сравнение четырёх карточек", async ({ page, viewport }) => {
  await page.goto("/catalog");
  await page.getByRole("searchbox", { name: "Поиск" }).fill("экскаватор");
  await page.getByRole("button", { name: "Найти" }).click();
  await expect(page).toHaveURL(/q=/);
  await expect(page.locator("article").first()).toBeVisible();

  // фильтр внутри категории: фасеты считаются по категории, поэтому первый вариант гарантированно даёт результаты
  await page.goto("/catalog/ekskavatory");
  const narrow = (viewport?.width ?? 0) < 1024;
  if (narrow) await page.getByRole("button", { name: /Фильтры/ }).click();
  const box = page.getByRole(narrow ? "dialog" : "complementary").getByRole("checkbox").first();
  await box.click();
  await expect(page).toHaveURL(/manufacturer=|status=|attr_/);
  if (narrow) await page.getByRole("button", { name: "Показать" }).click();
  await expect(page.locator("article").first()).toBeVisible();
  await expectNoHorizontalScroll(page);

  await page.goto("/catalog");
  const buttons = page.getByRole("button", { name: /^Сравнить$/ });
  for (let i = 0; i < 4; i++) await buttons.nth(i).click();
  await buttons.nth(4).click();
  await expect(page.getByText("Сравнивать можно не более 4 карточек")).toBeVisible();
  await page.goto("/compare");
  await expect(page.locator("table")).toBeVisible();
  await expect(page.locator("thead th")).toHaveCount(5);
  await expectNoHorizontalScroll(page);
});

test("пустой и мусорный запросы не ломают каталог", async ({ page }) => {
  for (const qs of ["?q=", "?page=abc", "?attr_weight_min=xx&ordering=zzz", "?q=%D1%84%D1%8B%D0%B2%D0%B0%D0%BF%D1%80%D0%BE%D0%BB"]) {
    const res = await page.goto("/catalog" + qs);
    expect(res?.status()).toBe(200);
    await expect(page.locator("h1")).toBeVisible();
  }
});
