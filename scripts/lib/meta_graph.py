"""Meta Graph API sürümü TEK yerde (denetim sosyal-6, 2026-11-18).

v21.0, Meta takvimine göre 2027-01-21'de kapanıyor; sürüm 16 betikte ayrı ayrı yazılıydı. Yükseltme: önce
META_GRAPH_VERSION=v2X.0 ile her betiği --dry / --no-publish koştur, sonra buradaki varsayılanı değiştir.
Bu dosyayı kullananlar: instagram-reel.py, facebook-reel.py, instagram-carousel.py, anim/kuyruk.py, token-health.py.
"""
import os

GRAPH_VERSION = os.environ.get("META_GRAPH_VERSION") or "v21.0"
API = f"https://graph.facebook.com/{GRAPH_VERSION}"
RUPLOAD = f"https://rupload.facebook.com/video-upload/{GRAPH_VERSION}"
