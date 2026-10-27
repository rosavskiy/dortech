"use client";
import { cart, useCart } from "@/lib/cart";
import { toast } from "@/components/ui/Toast";
import type { EquipmentCard } from "@/lib/types";

export function CardActions({ item, big = false }: { item: EquipmentCard; big?: boolean }) {
  const { items, compare } = useCart();
  const inCart = items.some((i) => i.equipment_id === item.id);
  const inCompare = compare.includes(item.id);
  const canRequest = item.status?.allow_request ?? true;
  const add = () => {
    const r = cart.add({ equipment_id: item.id, slug: item.slug, name: item.name, model: item.model, image: item.image?.url ?? null });
    if (r === "ok") toast(`${item.name} добавлен в заявку`, "success");
    else if (r === "exists") toast("Эта техника уже в заявке", "info");
    else toast("В заявке не больше 10 позиций", "error");
  };
  const cmp = () => {
    const r = cart.toggleCompare(item.id);
    if (r === "limit") toast("Сравнивать можно не более 4 карточек", "error");
    else toast(r === "added" ? "Добавлено к сравнению" : "Убрано из сравнения", "info");
  };
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      <button type="button" className={`btn ${inCart ? "btn--outline" : "btn--primary"} ${big ? "" : "btn--sm"}`} onClick={add} disabled={!canRequest || inCart} style={{ flex: 1 }}>
        {inCart ? "В заявке" : canRequest ? "В заявку" : "Недоступно"}
      </button>
      <button type="button" className={`btn btn--ghost ${big ? "" : "btn--sm"}`} onClick={cmp} aria-pressed={inCompare} title="Сравнить">
        {inCompare ? "✓ Сравнить" : "Сравнить"}
      </button>
    </div>
  );
}
