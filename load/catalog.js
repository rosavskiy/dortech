// Нагрузочный сценарий (ТЗ 6 «Нагрузка»): 50 виртуальных пользователей, 10 минут чтения каталога.
// Запуск: k6 run -e BASE_URL=https://test.example.com load/catalog.js --summary-export load/results/summary.json
import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.BASE_URL || "http://localhost:8000";
const VUS = Number(__ENV.VUS || 50);
const DURATION = __ENV.DURATION || "10m";

export const options = {
  scenarios: {
    catalog_read: { executor: "ramping-vus", startVUs: 5, stages: [{ duration: "1m", target: VUS }, { duration: DURATION, target: VUS }, { duration: "30s", target: 0 }] },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],          // ошибок сервера менее 1 %
    "http_req_duration{api:true}": ["p(95)<2000"], // p95 ответа API до 2 с
  },
};

let slugs = [];
let categories = [];

export function setup() {
  const cats = http.get(`${BASE}/api/v1/catalog/categories`).json();
  const list = http.get(`${BASE}/api/v1/catalog/equipment?page_size=60`).json();
  return { categories: cats.map((c) => c.slug), slugs: list.items.map((i) => i.slug) };
}

const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

export default function (data) {
  slugs = data.slugs; categories = data.categories;
  const tags = { api: true };
  const q = ["экскаватор", "каток", "кран", "komatsu", "jcb", "220"];
  const r1 = http.get(`${BASE}/api/v1/catalog/equipment?page=${1 + Math.floor(Math.random() * 3)}`, { tags });
  check(r1, { "list 200": (r) => r.status === 200 });
  sleep(1 + Math.random() * 2);
  const r2 = http.get(`${BASE}/api/v1/catalog/equipment?q=${encodeURIComponent(pick(q))}`, { tags });
  check(r2, { "search 200": (r) => r.status === 200 });
  sleep(1 + Math.random() * 2);
  const cat = pick(categories);
  const r3 = http.batch([
    ["GET", `${BASE}/api/v1/catalog/equipment?category=${cat}&ordering=price`, null, { tags }],
    ["GET", `${BASE}/api/v1/catalog/facets?category=${cat}`, null, { tags }],
  ]);
  check(r3[0], { "filter 200": (r) => r.status === 200 });
  check(r3[1], { "facets 200": (r) => r.status === 200 });
  sleep(1 + Math.random() * 2);
  const r4 = http.get(`${BASE}/api/v1/catalog/equipment/${pick(slugs)}`, { tags });
  check(r4, { "detail 200": (r) => r.status === 200 });
  sleep(1 + Math.random() * 2);
  const r5 = http.get(`${BASE}/api/v1/content/home`, { tags });
  check(r5, { "home 200": (r) => r.status === 200 });
  sleep(1 + Math.random() * 2);
}
