# JARVIS Web — Vercel + Gemini + Windows köprüsü

Telefon ve bilgisayar tarayıcısında çalışan Türkçe JARVIS sohbeti. Gemini API çağrısı Vercel sunucu fonksiyonunda yapılır; anahtar tarayıcıya gönderilmez. Yerel geliştirme `http://localhost:3000`, Vercel dağıtımı ise HTTPS adresidir. `localhost` yalnızca çalışan bilgisayarda görünür; telefonda Vercel adresini aç.

## Yerel çalışma

1. Node.js 20+ kur.
2. `web/.env.example` dosyasını `web/.env.local` olarak kopyala. `GEMINI_API_KEY` değerini Google AI Studio'dan al. `JARVIS_ACCESS_CODE` için en az 16 karakterlik rastgele bir kod belirle. `GEMINI_MODEL` varsayılanı `gemini-3.5-flash-lite`; hesabında kullanılmıyorsa erişebildiğin model adıyla değiştir.
3. `cd web && npm run dev` çalıştır. `http://localhost:3000` adresini aç ve erişim kodunu gir.
4. `npm test` ile API güvenlik ve yanıt testlerini çalıştır.

İlk sohbet için Upstash ve Windows köprüsü gerekmez. Sohbet geçmişi o sayfa açıkken bellekte tutulur; erişim kodu oturum depolamasında kalır.

## ElevenLabs sesi

Web sürümünde JARVIS, `IKne3meq5aSn9XLyUdCD` sesini `eleven_multilingual_v2` modeliyle kullanır. ElevenLabs hesabından alınan API anahtarını yerelde `web/.env.local` içine `ELEVENLABS_API_KEY` olarak, Vercel'de **Project Settings → Environment Variables** bölümüne aynı adla ekle ve yeniden dağıt. Ses kimliği tek başına API anahtarı değildir. Anahtar sunucuda kalır; ses dosyası erişim koduyla korunan `/api/voice` üzerinden gelir. ElevenLabs ayarlı değilse veya hizmet hata verirse tarayıcıdaki Türkçe ses kullanılır. iPhone otomatik oynatmayı engellerse **Son yanıtı tekrar oynat** düğmesine dokun.

## Vercel kurulumu

1. GitHub'da `yukselenpel1-ship-it/jarvishan` deposunu Vercel'e **Import** et. **Root Directory** `web`, Framework Preset **Other**.
2. Project Settings → Environment Variables altında `GEMINI_API_KEY`, `GEMINI_MODEL` ve en az 16 karakterli `JARVIS_ACCESS_CODE` ekle. Anahtarları `NEXT_PUBLIC_` adıyla ekleme.
3. Deploy et. Telefonda oluşan HTTPS `*.vercel.app` adresini aç. Erişim kodunu girince sohbet hazır.

## Telefondan Windows işlemleri

1. Upstash Redis veritabanı oluştur. Vercel ortamına `UPSTASH_REDIS_REST_URL` ve `UPSTASH_REDIS_REST_TOKEN` değerlerini ekle.
2. Vercel ortamına **başka** bir güçlü `JARVIS_BRIDGE_TOKEN` ekle. Yeniden deploy et.
3. Windows JARVIS v0.7'ye güncelle. **Ayarlar → Telefon bağlantısı** alanına Vercel HTTPS adresini ve aynı köprü anahtarını gir.
4. Windows uygulaması açıkken telefondaki durum **Windows JARVIS bağlı** olur. Mesajda önerilen işlem kartına dokunup onayla; sonuç sohbet içinde görünür.

Windows uygulaması köprüye yalnızca **dışarı doğru HTTPS isteği** yapar. Modem portu açılmaz. Uzaktan yalnızca uygulama açma, web araması, sistem bilgisi, dosya adı arama, not ve hatırlatma izinlidir. Web arayüzü her işlem için ayrı onay ister; Windows tarafı izin listesini yeniden doğrular. Telefon üzerinden fare, klavye, kabuk komutu ve dosya üzerine yazma bulunmaz.

Köprü anahtarı Windows kullanıcı profilindeki `%LOCALAPPDATA%\Jarvis\remote_bridge.json` dosyasında kalır. Bu dosyayı ve `.env.local` dosyasını GitHub'a gönderme. Erişim kodu veya köprü anahtarı sızarsa Vercel ortam değişkenini değiştir ve Windows ayarını yenile.

## Antigravity ile geliştirme

Depoyu aç; `web/AGENTS.md` ve `web/ANTIGRAVITY_BRIEF.md` dosyalarını çalışma talimatı olarak kullan. Web kodu `web/` altında, Windows uygulaması `app/` altındadır. Güvenlik kısıtlarını koruyarak küçük değişiklikler yap ve her değişiklikte `npm test` ile Python testlerini çalıştır.
