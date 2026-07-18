#!/usr/bin/env python3
"""
ParaFOMO — winners.json sorgu aracı (üreticiler/shell için).

Kullanım:
  winner.py <yol>            → kararlaştırılmış seçimi bas (yoksa BOŞ)
  winner.py <yol> --field X  → seçim yerine başka bir alanı bas (ör. recommended_slots)

Yol örnekleri: viral.format · viral.slot · shorts.voice · shorts.engine

BOŞ çıktı = "yeterli veri yok / karar yok" → çağıran MEVCUT davranışını sürdürsün.
Bu sözleşme sayesinde öğrenme katmanı yalnızca güven oluşunca devreye girer;
winners.json yoksa/bozuksa üretim asla durmaz.
"""
import os
import sys
import json

WINNERS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "learning", "winners.json")


def main():
    if len(sys.argv) < 2:
        return 0
    path = sys.argv[1]
    field = "next_pick"
    if "--field" in sys.argv:
        field = sys.argv[sys.argv.index("--field") + 1]
    try:
        w = json.load(open(WINNERS))
        node = w
        for part in path.split("."):
            node = node[part]
        val = node.get(field)
        if val:
            print(",".join(map(str, val)) if isinstance(val, list) else val)
    except (OSError, KeyError, ValueError, TypeError):
        pass  # sessiz: yoksa boş → çağıran fallback yapar
    return 0


if __name__ == "__main__":
    sys.exit(main())
