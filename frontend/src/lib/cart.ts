"use client";
/** Корзина заявки и список сравнения в localStorage (ТЗ 3.1: до 10 позиций; 2.3: сравнение до 4). */
import { useSyncExternalStore } from "react";
import type { RateUnit } from "./types";

export type CartItem = { equipment_id: number; slug: string; name: string; model: string | null; image: string | null; quantity: number; unit: RateUnit; units: number | null };
const CART_KEY = "dt_cart";
const COMPARE_KEY = "dt_compare";
export const CART_LIMIT = 10;
export const COMPARE_LIMIT = 4;

type State = { items: CartItem[]; compare: number[]; hydrated: boolean };
let state: State = { items: [], compare: [], hydrated: false };
const listeners = new Set<() => void>();

function read<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? (JSON.parse(raw) as T) : fallback; } catch { return fallback; }
}
function write(key: string, value: unknown) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* ignore */ } }
function emit() { listeners.forEach((l) => l()); }
function hydrate() {
  if (state.hydrated || typeof window === "undefined") return;
  state = { items: read(CART_KEY, []), compare: read(COMPARE_KEY, []), hydrated: true };
}
function set(patch: Partial<State>) {
  state = { ...state, ...patch };
  if (patch.items) write(CART_KEY, state.items);
  if (patch.compare) write(COMPARE_KEY, state.compare);
  emit();
}

export const cart = {
  add(item: Omit<CartItem, "quantity" | "unit" | "units"> & Partial<Pick<CartItem, "quantity" | "unit" | "units">>): "ok" | "exists" | "limit" {
    hydrate();
    if (state.items.some((i) => i.equipment_id === item.equipment_id)) return "exists";
    if (state.items.length >= CART_LIMIT) return "limit";
    set({ items: [...state.items, { quantity: 1, unit: "shift", units: null, ...item }] });
    return "ok";
  },
  update(id: number, patch: Partial<CartItem>) { hydrate(); set({ items: state.items.map((i) => (i.equipment_id === id ? { ...i, ...patch } : i)) }); },
  remove(id: number) { hydrate(); set({ items: state.items.filter((i) => i.equipment_id !== id) }); },
  clear() { hydrate(); set({ items: [] }); },
  replace(items: CartItem[]) { hydrate(); set({ items: items.slice(0, CART_LIMIT) }); },
  toggleCompare(id: number): "added" | "removed" | "limit" {
    hydrate();
    if (state.compare.includes(id)) { set({ compare: state.compare.filter((c) => c !== id) }); return "removed"; }
    if (state.compare.length >= COMPARE_LIMIT) return "limit";
    set({ compare: [...state.compare, id] });
    return "added";
  },
  clearCompare() { hydrate(); set({ compare: [] }); },
};

const serverSnapshot: State = { items: [], compare: [], hydrated: false };
export function useCart(): State {
  return useSyncExternalStore(
    (cb) => { listeners.add(cb); hydrate(); queueMicrotask(emit); return () => listeners.delete(cb); },
    () => { hydrate(); return state; },
    () => serverSnapshot,
  );
}
