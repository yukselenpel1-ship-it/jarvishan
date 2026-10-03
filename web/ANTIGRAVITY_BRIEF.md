# Antigravity için JARVIS çalışma özeti

Hedef: Türkçe kişisel asistanın Vercel üzerinde mobil uyumlu web arayüzü ve Gemini sohbeti; Windows masaüstü köprüsü üzerinden kullanıcı onaylı bilgisayar işlemleri.

## Mevcut kod

- `index.html`, `client.js`: telefon ve masaüstü HUD sohbeti; erişim kodu; önerilen işlem için ayrı onay.
- `api/chat.js`: sunucu tarafında Gemini `generateContent`, konuşma geçmişi ve izinli araç önerileri.
- `api/jobs.js`, `api/bridge.js`, `api/status.js`: Upstash Redis üzerinden kısa ömürlü işlem kuyruğu ve Windows durum sinyali.
- `../app/jarvis/remote.py`: Windows uygulamasının HTTPS üzerinden dışarı doğru bağlanan köprüsü.

## Çalışma ilkeleri

Arayüz Türkçe ve koyu turkuaz/turuncu görünümde kalsın. Mobil ekranda konuşma kutusu ve işlem onayı kolay dokunulsun. API anahtarları ve Redis token'ı tarayıcıya geçmesin. Modelin işlem önerisi gerçek işlem olarak gösterilmesin. Uzak işlemler için `lib/server.js` ve Windows `remote.py` içindeki iki ayrı izin listesi geçerli olsun.

## İlk geliştirme işleri

1. Mobil web sayfasını gerçek iPhone ve masaüstünde kontrol et; ekran görüntülerine göre düzeni iyileştir.
2. Gemini hesabındaki model erişimini canlı istekle sınayıp `GEMINI_MODEL` değerini doğrula.
3. Windows köprüsünde kopma ve tekrar bağlanma testleri yap. İşlem kuyruğu kaybına karşı tekrar deneme ve gözlemlenebilir durum ekle.
4. Kişisel kullanım için güçlü kimlik doğrulama ve kötüye kullanım sınırı eklemeden web adresini herkese duyurma.

## Doğrulama

`cd web && npm test`; masaüstü için `cd app && python -m unittest discover -s tests -v`. Vercel'de Root Directory `web`; gizli değerler Vercel Environment Variables içindedir.
