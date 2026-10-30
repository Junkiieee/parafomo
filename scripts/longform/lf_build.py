#!/usr/bin/env python3
"""Uzun-form (16:9) video derleyici: senaryo JSON → mp4 + kapak + bölümler + altyazı (SRT) + meta.

    python3 scripts/longform/lf_build.py public/social/longform/<slug>.script.json [--beats N] [--no-lock]

Akış: her "beat" ayrı seslendirilir (önbellekli; görüntü-ses senkronu kaymaz) → süreler → tek ffmpeg
sürecine PIL kareleri akıtılır (stok video yok) → anlatım + müzik (parçalar arası yumuşak geçiş,
konuşmada kısılır) → loudnorm (-14 LUFS, YouTube) → mux.
Senaryo biçimi: lf_script.py başındaki açıklamaya bak.
"""
import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lf_common import FPS, H, MUSIC_DIR, OUT_DIR, W, WORK, duration, run, tts  # noqa: E402
import lf_scenes as S  # noqa: E402

LEAD = 0.15        # beat başında sesten önce
GAP = 0.40         # beat sonunda nefes
CHAPTER_EXTRA = 0.5
ZOOM = 0.025       # beat boyunca toplam yakınlaşma
MUSIC_VOL = 0.10
LOCK = "/tmp/shorts_frames.lock"   # Shorts hattıyla aynı kilit: aynı anda tek ağır render


def mmss(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60:02d}:{t % 60:02d}"


def srt_ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


def flatten(script):
    beats = []
    for ci, ch in enumerate(script["chapters"]):
        for bi, b in enumerate(ch["beats"]):
            show = b.get("show")
            if not show or not show.get("kind"):
                show = ({"kind": "chapter", "n": ci + 1, "title": ch["title"]} if bi == 0 and ci > 0
                        else {"kind": "title", "headline": ch["title"]})
            if show.get("kind") == "chapter":
                show.setdefault("n", ci + 1)
                show.setdefault("title", ch["title"])
            beats.append({"ci": ci, "bi": bi, "say": b["say"].strip(), "show": show,
                          "chapter": ch["title"]})
    return beats


def chunk_caption(text, maxlen=84):
    """Cümleleri ≤2 satırlık altyazı parçalarına böl."""
    parts = re.split(r"(?<=[.!?…])\s+|(?<=[,;:])\s+(?=\S{4,})", text)
    out, cur = [], ""
    for p in parts:
        if not p:
            continue
        if len(cur) + len(p) + 1 <= maxlen:
            cur = (cur + " " + p).strip()
        else:
            if cur:
                out.append(cur)
            while len(p) > maxlen:
                cut = p.rfind(" ", 0, maxlen)
                cut = cut if cut > 20 else maxlen
                out.append(p[:cut].strip())
                p = p[cut:].strip()
            cur = p
    if cur:
        out.append(cur)
    return out


def music_bed(total, slug, out):
    tracks = sorted(f for f in os.listdir(MUSIC_DIR) if f.lower().endswith((".mp3", ".m4a")))
    if not tracks:
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", f"{total:.2f}", out])
        return out
    start = int(hashlib.sha1(slug.encode()).hexdigest(), 16) % len(tracks)
    order, acc = [], 0.0
    i = 0
    while acc < total + 5 and i < 12:
        p = os.path.join(MUSIC_DIR, tracks[(start + i) % len(tracks)])
        order.append(p)
        acc += duration(p) - 4
        i += 1
    cmd = ["ffmpeg", "-y"]
    for p in order:
        cmd += ["-i", p]
    if len(order) == 1:
        fc = "[0:a]aresample=48000,aformat=channel_layouts=stereo[m]"
    else:
        fc, last = "", "[0:a]"
        for k in range(1, len(order)):
            nxt = f"[x{k}]" if k < len(order) - 1 else "[m0]"
            fc += f"{last}[{k}:a]acrossfade=d=4:c1=tri:c2=tri{nxt};"
            last = nxt
        fc += "[m0]aresample=48000,aformat=channel_layouts=stereo[m]"
    fc += f";[m]atrim=0:{total:.2f},afade=t=in:d=1.5,afade=t=out:st={max(0, total - 4):.2f}:d=4[o]"
    run(cmd + ["-filter_complex", fc, "-map", "[o]", "-ac", "2", out])
    return out


def build(script_path, max_beats=0, use_lock=True):
    script = json.load(open(script_path, encoding="utf-8"))
    slug = script["slug"]
    beats = flatten(script)
    if max_beats:
        beats = beats[:max_beats]
    work = os.path.join(WORK, slug)
    os.makedirs(work, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1) seslendirme + süreler
    t = 0.0
    for b in beats:
        b["mp3"] = tts(b["say"])
        b["adur"] = duration(b["mp3"])
        extra = CHAPTER_EXTRA if b["show"].get("kind") == "chapter" else 0
        frames = int(round((LEAD + b["adur"] + GAP + extra) * FPS))
        b["frames"] = frames
        b["dur"] = frames / FPS
        b["start"] = t
        t += b["dur"]
    total = t
    print(f"[lf] {len(beats)} beat, {mmss(total)} ({total:.1f} sn)")

    chap_ranges, chapters = [], []
    for b in beats:
        if not chapters or chapters[-1]["ci"] != b["ci"]:
            chapters.append({"ci": b["ci"], "title": b["chapter"], "start": b["start"]})
    for i, c in enumerate(chapters):
        end = chapters[i + 1]["start"] if i + 1 < len(chapters) else total
        chap_ranges.append((c["start"], end))

    lock_fh = None
    if use_lock:
        lock_fh = open(LOCK, "w")
        t0 = time.time()
        while True:
            try:
                fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.time() - t0 > 3600:
                    print("[lf] kilit 60 dk'dır meşgul — kilitsiz devam")
                    break
                time.sleep(15)

    # 2) anlatım izi (beat başına tam süreli wav → birleştir)
    lst = os.path.join(work, "narr.txt")
    with open(lst, "w") as f:
        for i, b in enumerate(beats):
            wav = os.path.join(work, f"n{i:03d}.wav")
            run(["ffmpeg", "-y", "-i", b["mp3"], "-af",
                 f"aresample=48000,adelay={int(LEAD * 1000)}:all=1,apad=whole_dur={b['dur']:.4f},"
                 f"atrim=0:{b['dur']:.4f}", "-ac", "1", wav])
            f.write(f"file '{wav}'\n")
    narr = os.path.join(work, "narr.wav")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", narr])

    # 3) görüntü: tek ffmpeg sürecine ham kareler
    vid = os.path.join(work, "video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                            "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-threads", "2",
                            vid], stdin=subprocess.PIPE)
    t_render = time.time()
    for i, b in enumerate(beats):
        sp, dur = b["show"], b["dur"]
        a_end = S.anim_end(sp, dur)
        cached = None
        label = f"Bölüm {b['ci'] + 1} · {b['chapter']}" if b["ci"] > 0 else ""
        for fi in range(b["frames"]):
            tt = fi / FPS
            if tt >= a_end:
                if cached is None:
                    cached = S.draw_content(sp, a_end, dur)
                content = cached
            else:
                content = S.draw_content(sp, tt, dur)
            frame = S.zoom(content, 1 + ZOOM * (tt / dur))
            if frame is content:
                frame = content.copy()
            S.draw_hud(frame, label, b["start"] + tt, total, chap_ranges)
            enc.stdin.write(frame.tobytes())
        if i % 5 == 0:
            el = time.time() - t_render
            print(f"[lf] kare {i + 1}/{len(beats)} beat — {el:.0f} sn")
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("ffmpeg video kodlama başarısız")

    # 4) müzik + karışım + loudnorm + mux
    bed = music_bed(total, slug, os.path.join(work, "music.wav"))
    out_mp4 = os.path.join(OUT_DIR, f"{slug}.mp4")
    fc = (f"[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[n1][n2];"
          f"[2:a]volume={MUSIC_VOL}[m];"
          f"[m][n1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];"
          f"[n2][md]amix=inputs=2:normalize=0:duration=first,"
          f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
    run(["ffmpeg", "-y", "-i", vid, "-i", narr, "-i", bed, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out_mp4])
    if lock_fh:
        lock_fh.close()

    # 5) altyazı (SRT) — beat içinde karakter oranıyla zamanlanır
    srt, n = [], 1
    for b in beats:
        parts = chunk_caption(b["say"])
        tot_chars = sum(len(p) for p in parts) or 1
        t0 = b["start"] + LEAD
        for p in parts:
            d = b["adur"] * len(p) / tot_chars
            srt.append(f"{n}\n{srt_ts(t0)} --> {srt_ts(t0 + d - 0.05)}\n{p}\n")
            n += 1
            t0 += d
    srt_path = os.path.join(OUT_DIR, f"{slug}.srt")
    open(srt_path, "w", encoding="utf-8").write("\n".join(srt))

    # 6) kapak + meta
    thumb = S.thumbnail(script.get("thumbnail", {}), os.path.join(OUT_DIR, f"{slug}-thumb.jpg"))
    chap_lines = [f"{mmss(c['start'])} {c['title']}" for c in chapters]
    meta = {"slug": slug, "title": script["title"], "description": script.get("description", ""),
            "tags": script.get("tags", []), "link": script.get("link", ""), "file": out_mp4,
            "thumbnail": thumb, "srt": srt_path, "duration": round(total, 2),
            "chapters": chap_lines, "chapters_valid": chapters_ok(chapters, total),
            "beats": [{"start": round(b["start"], 2), "dur": round(b["dur"], 2), "kind": b["show"]["kind"],
                       "chapter": b["chapter"], "say": b["say"]} for b in beats],
            "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": script.get("source", "")}
    meta_path = os.path.join(OUT_DIR, f"{slug}.meta.json")
    json.dump(meta, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[lf] ✅ {out_mp4} ({mmss(total)}) · kapak {thumb} · meta {meta_path}")
    print(f"[lf] render süresi {time.time() - t_render:.0f} sn")
    return meta


def chapters_ok(chapters, total):
    """YouTube kuralları: 00:00 ile başlar, ≥3 bölüm, her biri ≥10 sn."""
    if len(chapters) < 3 or chapters[0]["start"] > 0.01:
        return False
    for i, c in enumerate(chapters):
        end = chapters[i + 1]["start"] if i + 1 < len(chapters) else total
        if end - c["start"] < 10:
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--beats", type=int, default=0, help="yalnız ilk N beat (hızlı deneme)")
    ap.add_argument("--no-lock", action="store_true")
    a = ap.parse_args()
    build(a.script, a.beats, not a.no_lock)


if __name__ == "__main__":
    main()
