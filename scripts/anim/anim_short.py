#!/usr/bin/env python3
"""Günlük hatların tek giriş noktası: senaryo → izometrik animasyonlu Short (public/social/short-<slug>.mp4 + meta).

    python3 scripts/anim/anim_short.py --scenario public/social/scenarios/<slug>.json [--convert-only]
    python3 scripts/anim/anim_short.py --blog <slug> [--convert-only]

--convert-only: yalnız sahne planını üretir (gece hazırlıkta, LLM burada harcanır) → <...>.anim.json
Plan yoksa render sırasında üretilir (yedek). Çıkış kodu ≠ 0 → çağıran kabuk eski motora düşer.
Blog modunda sayı kapısının kaynağı yazının kendi metnidir (yazıda geçmeyen rakam ekrana çıkmaz).
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PY = sys.executable
SCN_DIR = os.path.join(ROOT, "public", "social", "scenarios")


def blog_scenario(slug):
    """Blog yazısının frontmatter `shorts:` listesini senaryo biçimine çevirir."""
    p = os.path.join(ROOT, "src", "content", "blog", f"{slug}.md")
    raw = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise SystemExit("frontmatter yok")
    import yaml
    fm, body = yaml.safe_load(m.group(1)) or {}, m.group(2)
    lines = fm.get("shorts") or []
    if len(lines) < 3:
        raise SystemExit("shorts: senaryosu yok")
    segs = [{"kind": "hook" if i == 0 else ("cta" if i == len(lines) - 1 else "point"), "spoken": str(t)}
            for i, t in enumerate(lines)]
    return {"slug": slug, "title": fm.get("title", slug), "category": "REHBER",
            "description": fm.get("description", ""), "tags": (fm.get("tags") or [])[:8],
            "format": "blog", "link": f"/blog/{slug}/", "segments": segs,
            "number_source": {}}   # ekrandaki rakam o an konuşulan cümlede geçmeli (yazıdan rakam çekilmez)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scenario")
    g.add_argument("--blog")
    ap.add_argument("--convert-only", action="store_true")
    a = ap.parse_args()
    if a.blog:
        scn_path = os.path.join(SCN_DIR, f"blog-{a.blog}.json")
        json.dump(blog_scenario(a.blog), open(scn_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    else:
        scn_path = os.path.abspath(a.scenario)
    slug = json.load(open(scn_path, encoding="utf-8"))["slug"]
    piece = os.path.join(os.path.dirname(scn_path), f"{slug}.anim.json")
    if not os.path.exists(piece) or a.convert_only:
        r = subprocess.run([PY, os.path.join(HERE, "anim_from_scenario.py"), scn_path], capture_output=True, text=True)
        sys.stderr.write(r.stderr)
        if r.returncode != 0 or not os.path.exists(piece):
            print("[anim-short] sahne planı üretilemedi", file=sys.stderr)
            return 2
    if a.convert_only:
        print(piece)
        return 0
    r = subprocess.run([PY, os.path.join(HERE, "anim_build.py"), piece])
    if r.returncode != 0:
        return 2
    out = os.path.join(ROOT, "public", "social", f"short-{slug}.mp4")
    if not os.path.exists(out) or os.path.getsize(out) < 100_000:
        print("[anim-short] çıktı yok/eksik", file=sys.stderr)
        return 2
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
