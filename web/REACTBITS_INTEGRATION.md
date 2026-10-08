# JARVIS React Bits arayüzü

## Mevcut mimari

Depo React/Next.js uygulaması değildi: `web/index.html` ve `web/client.js` mobil web arayüzünü, `web/api/` Vercel fonksiyonlarını, `web/lib/server.js` erişim kodu / güvenli araç listesi / Redis köprüsünü içerir. `app/` ayrı Windows uygulamasıdır; SQLite hafıza, bilgisayar işlemleri, ses ve güncelleme sistemi burada kalır. `downloads/` ve `update.json` masaüstü yayınlarını yönetir.

## Uygulanan entegrasyon

React 19 ve esbuild ile mevcut HTML üzerinde aşamalı React entegrasyonu. Eski formlar, DOM kimlikleri ve istemci handler'ları korunur. Kartların sabit HTML'i React Bits SpotlightCard içine **bir kez**, `client.js` bağlanmadan önce yerleştirilir. Mesaj ve işlem önerilerini hâlâ mevcut istemci yönetir. Bu HTML yalnızca uygulamanın kendi statik şablonudur; kullanıcı/model metni `textContent` ile eklenir.

Gerçek kaynak bileşenleri: Aurora, Particles, Orb, DecryptedText, BlurText, SpotlightCard, Magnet, StarBorder ve AnimatedContent. Kaynak commit ve lisans `src/reactbits/` içindedir. Orb enerji efekti olduğundan Lightning, DecryptedText/BlurText yeterli olduğundan SplitText zorla eklenmedi.

`jarvis:state`: idle, listening, thinking, speaking, error. `jarvis:audio`: Web Audio AnalyserNode ile gerçek RMS + frekans dilimleri. Yüksek frekanslı veriler React state yerine ref/CSS değişkeni üzerinden iletilir. Mikrofon ölçümü izin verilirse çalışır; izin reddi ses tanımayı engellemez. ElevenLabs `<audio>` çıktısı ölçülür. Tarayıcı speechSynthesis PCM erişimi sağlamadığından bu yedekte yalnızca SPEAKING durumu gösterilir, sahte ses dalgası üretilmez. Bitiş/iptalde mikrofon track'leri ve bağlamlar temizlenir. Yeniden oynatma mevcut MediaElementAudioSourceNode'u kullanır.

Mobil parçacık sayısı 28, masaüstünde 110. DPR üst sınırı 1.5; mobil Orb 30 FPS, masaüstünde 60 FPS üst sınırı. Düşük FPS ölçülürse Aurora kaldırılıp parçacık sayısı azaltılır. Gizli sekmede render yapılmaz. WebGL yoksa CSS çekirdek, Reduced Motion etkinse sabit çekirdek gösterilir. Ayarlarda animasyon, parçacık ve yoğunluk tercihi saklanır.

Sohbet / Gemini / ElevenLabs API sözleşmeleri, erişim kodu, Redis kuyruğu ve her bilgisayar işlemi için ayrı onay korunmuştur. Anahtarlar build'e eklenmez. Mevcut isteğe bağlı kişisel ElevenLabs anahtarı ayarı önceki davranışını sürdürür. Windows kaynakları ve güncelleme arşivleri değiştirilmez. Kök dizinden dağıtımda mevcut ses API'sine erişmek için `api/voice.js` yeniden dışa aktarımı eklendi.

## Çalıştırma ve kontroller

Kök dizinde `npm install`, ardından `npm run build`, `npm run typecheck`, `npm run lint`, `npm test`.

Yerel önizleme: `npm --prefix web run dev`. Önce mevcut ortam değişkenlerini `web/.env.local` üzerinden sağla; `web/.env.example` adları gösterir. Mevcut API anahtarları veya erişim kodları değiştirilmez.

Tarayıcı regresyonları: `cd web`, `npx playwright install chromium`, `npm run test:ui`. Sistem Chromium'u için `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/path/to/chrome` kullanılabilir. Testlerde erişim kodu yalnızca yerel fixture'dır. Gerçek status/401 endpoint'i sınanır; Gemini ve ElevenLabs cevapları tarayıcı testlerinde fixture ile sağlanır. Bu testler canlı sağlayıcı doğrulaması değildir.

## Bu çalışma alanındaki doğrulama

- TypeScript, ESLint, production build ve `git diff --check`: başarılı.
- Mevcut web API testleri: 8/8 başarılı.
- Mevcut Python / Windows uygulaması birim testleri: 29/29 başarılı. Windows donanımı üzerindeki ses ve bilgisayar kontrolü bu Linux ortamında çalıştırılmadı.
- Chromium masaüstü + iPhone boyutu regresyonları: 8/8 başarılı. Sohbet geçmişi, ayrı bilgisayar işlemi onayı, ElevenLabs ses yolu için gerçek WAV RMS ölçümü ve tekrar oynatma, ERROR durumu, mikrofon yaşam döngüsü, ayar kalıcılığı, Reduced Motion ve WebGL fallback doğrulandı.
- Masaüstü ve mobil ekran görüntüleri incelendi. Daralan panellerde gizlenen hızlı komutlar ve genişleyen menünün içerik üzerine binmesi düzeltildi.
- Tarayıcı testlerinde sağlayıcı yanıtları fixture kullanır; canlı Gemini/ElevenLabs bağlantısı doğrulanmadı. Gerçek mikrofon donanım seviyesi ve cihaz GPU FPS değeri kullanıcı cihazında ölçülmelidir.
- Kullanıcının canlı siteye yansıtma talimatıyla GitHub dalı, PR ve Vercel Git dağıtımı yayın akışı kullanılır.
