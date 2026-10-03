# JARVIS v0.2 doğrulama raporu

03.10.2026 — Linux ortamı, Python 3.12.14.

- 20 otomatik test: PASS. Komutlar, Türkçe notlar, bekleyen hatırlatmalar,
  API anahtarı hatası, gizlilik, ses seçimi, güvenli güncelleme paketi ve
  güncelleme geri alması denetlendi.
- Python derleme/sözdizimi: PASS. HTML ayrıştırıldı; JavaScript `node --check`
  ile PASS.
- Kullanıcının Windows ekran görüntüsü, v0.1 penceresinin açıldığını ve
  `saat kaç` komutunun cevap verdiğini gösterdi.

v0.2'nin WebView2 penceresi, Türkçe çevrimiçi ses, Windows masaüstü kısayolu ve
canlı güncelleme bu Linux ortamında uçtan uca denenemedi. İlk Windows çalıştırmasında ana merkez, not ekleme,
hatırlatma oluşturma ve ses yanıtı kontrol edilmeli. Canlı güncelleme, yayın
kaynağı bağlandıktan sonra ayrıca denenmeli.
