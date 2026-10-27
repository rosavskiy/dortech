"""Генератор тестового CSV для приёмки: uv run python -m scripts.gen_import_csv --rows 1000 --duplicates 50 --invalid 20 > import.csv"""

import argparse
import random
import sys

CATS = ["ekskavatory", "pogruzchiki", "avtokrany", "samosvaly", "buldozery", "katki", "avtogreydery", "manipulyatory"]
MANS = ["Komatsu", "Hitachi", "Caterpillar", "JCB", "Volvo", "Liebherr", "XCMG", "SANY", "КАМАЗ", "Hyundai"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=1000)
    ap.add_argument("--duplicates", type=int, default=0)
    ap.add_argument("--invalid", type=int, default=0)
    ap.add_argument("--prefix", default="IMP")
    a = ap.parse_args()
    random.seed(1)
    out = sys.stdout
    out.write("﻿")
    out.write(
        "external_id;name;category;manufacturer;model;year;status;short_description;price_per_shift;price_per_day;price_hidden;is_published;attr:weight;attr:engine_power;attr:drive;attr:with_operator\n"
    )
    rows = []
    for i in range(1, a.rows + 1):
        man = random.choice(MANS)
        model = f"{random.choice(['PC', 'ZX', 'EC', 'R', 'D'])}{random.randint(100, 999)}"
        rows.append(
            [
                f"{a.prefix}-{i:05d}",
                f"Техника {man} {model}",
                random.choice(CATS),
                man,
                model,
                str(random.randint(2010, 2025)),
                random.choice(["available", "busy", "on_request"]),
                "Импортированная карточка",
                str(random.randrange(5000, 60000, 500)),
                str(random.randrange(12000, 140000, 500)),
                "0",
                "1",
                str(round(random.uniform(2, 50), 1)),
                str(random.randint(60, 500)),
                random.choice(["Гусеничная", "Колёсная"]),
                random.choice(["1", "0"]),
            ]
        )
    for _ in range(a.duplicates):
        rows.append(list(random.choice(rows)))
    for k in range(a.invalid):
        bad = list(random.choice(rows))
        bad[0] = f"{a.prefix}-BAD-{k:03d}"
        bad[random.choice([2, 5, 8])] = random.choice(["nope", "abc", ""])
        if bad[2] == "":
            bad[2] = "no-such-category"
        rows.append(bad)
    random.shuffle(rows)
    for r in rows:
        out.write(";".join(r) + "\n")


if __name__ == "__main__":
    main()
