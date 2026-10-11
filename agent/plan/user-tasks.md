1. ✅ **Videolar için müzik — TAMAM (2026-10-11):** 10 parça `/root/parafomo-media/music/` klasöründe.
   Ajan: ilk videoda gerçek müziğin kullanıldığını doğrula, rapora yaz; sonra bu maddeyi sil.
2. ✅ **Kalıcı Claude token'ı — TAMAM (2026-10-11):** `/root/.config/parafomo/claude.env` yazıldı (600),
   gerçek çağrıyla test edildi (haiku "OK" döndü). `run.sh` her koşuda otomatik yükler.
   Ajan: ilk koşu sorunsuz geçince bu maddeyi sil.
3. ✅ **Uzak yedek — TAMAM (2026-10-11):** R2 bucket `parafomo-backup` + anahtarlar `backup.env`'de;
   venv'e boto3 kuruldu; backup.sh'a path-style düzeltmesi yapıldı (R2 joker sertifikası virtual-host'u
   kapsamıyor). İlk yedek R2'de doğrulandı (portfolio-20261011.db + config-20261011.tgz).
   Ajan: ertesi gün maintenance koşusunun uzak kopyası düşmüş mü kontrol et, sorunsuzsa bu maddeyi sil.

_Not (2026-10-11, Kaan): X (Twitter) otomatik paylaşım YAPILMAYACAK — şimdilik gündemde değil,
tekrar açılırsa Kaan söyler. Ajan bu konuda görev/öneri üretmesin._
_info@parafomo.com: ✅ ÇALIŞIYOR (2026-10-11 test edildi) — Cloudflare Email Routing aktif, mail Kaan'ın
kişisel adresine yönleniyor. Görev kapandı._
