# JARVIS v0.5 — daha güvenilir sohbet, işlemler ve ses düzeyi

JARVIS artık bir konuşma motoruna bağlandığında doğal Türkçe sohbet eder ve
izin verilen bilgisayar işlemlerini konuşma içinden yönetir. Ana ekranda
turkuaz/turuncu, hareketli HUD küresi teması, konuşma alanı, hızlı komutlar, notlar,
hatırlatmalar ve ayarlar bulunur.

## v0.2/v0.3'ten güncelleme

JARVIS v0.2'yi aç → Ayarlar → Güncellemeyi denetle → Yeni sürümü yükle.
Bağlı `update_source.txt` dosyası varsa v0.5 görünür. Uygulama kapanır,
ZIP'in SHA-256 özetini doğrular, kaynakları değiştirir, yeni bağımlılıkları
kurar ve yeniden açılır. Notlar `%LOCALAPPDATA%\Jarvis\memory.sqlite3`
içinde kalır. Eski v0.2 kurulumunda güncelleme kaynağı görünmüyorsa
https://raw.githubusercontent.com/yukselenpel1-ship-it/jarvishan/main/app/update_source.txt
dosyasını `JARVIS_v0.2` klasörüne koyup uygulamayı yeniden aç.

İlk kurulum: ZIP'i sabit bir klasöre çıkar, Windows 10/11 ve Python 3.11/3.12
üzerinde `KURULUM.bat` çalıştır. Sonrasında masaüstündeki JARVIS kısayoluyla aç.
WebView2 Runtime gerekir: https://developer.microsoft.com/microsoft-edge/webview2/ .

## Sohbet bağlantısı

Ayarlar'da iki seçenek bulunur:

- **OpenAI API:** Kendi API anahtarını gir. `gpt-4.1-mini` varsayılanı.
  Anahtar yalnızca bu oturum belleğinde tutulur; ChatGPT aboneliğinden ayrı
  API kullanımı ücretlidir. Ekran analizi de bu bağlantıyı gerektirir.
- **Yerel Ollama:** https://ollama.com/download/windows adresinden kur. PowerShell'de
  `ollama pull qwen3:4b` çalıştır (yaklaşık 2,5 GB indirme). Ollama açıkken
  Ayarlar'da Yerel Ollama seç. Konuşma bilgisayarında işlenir; ekran analizi
  bu ilk sürümde yerel modelde sunulmaz.

Sohbet bağlantısı yoksa yalnızca yerel komutlar ve birkaç temel selamlama
çalışır. `nasılsın` gibi sohbet sorularının kapsamlı yanıtı için model gerekir.

## Bilgisayar işlemleri

Model şu araçları önerebilir: Chrome/Not Defteri/Hesap Makinesi/Gezgin açma,
Google araması, sistem bilgileri, dosya adı arama, not, hatırlatma, yeni TXT
belgesi oluşturma, etkin pencereye tek satır metin yazma, izinli tuşlara basma
ve ekrandaki konuma tıklama. Yazma, tıklama, tuş ve dosya oluşturma her seferinde
uygulamada işlem özetiyle onaylanır. Sol üst ekran köşesine fareyi götürmek
PyAutoGUI acil durdurma hareketidir. Keyfi program, terminal komutu veya
silme komutu çalıştırılmaz. Uygulama adına bağlı açma listesi sınırlıdır.

Ekran görüntüsü için konuşma kutusundaki ▣ simgesine tıkla. Hedef pencereyi
önce JARVIS'in arkasında açık bırak. Onay verirsen bir önceki pencerenin
görüntüsü küçültülüp OpenAI'ye gönderilir. Önerilen tıklamayı ayrıca onaylarsın.
Mikrofon tanıma Google servisini, çevrimiçi Türkçe TTS Microsoft Edge servisini
kullanır. Bunlar için uygulama içinde açıklama bulunur.

## Geliştirme

Kaynak kod: https://github.com/yukselenpel1-ship-it/jarvishan/tree/main/app .
`python -m unittest discover -s tests -v` ve
`python -m compileall -q jarvis main.py` ile doğrula. Windows üzerinde yeni
ses, ekran ve canlı güncelleme akışını cihazda sınamak gerekir.

## Görsel referans

Arayüz düzeni kullanıcı tarafından gösterilen [alpunlu12-commits/jarvis](https://github.com/alpunlu12-commits/jarvis) projesinin siyah, turkuaz ve turuncu HUD estetiği esas alınarak bağımsız HTML/CSS/canvas koduyla oluşturuldu. Referans deponun kodu veya varlıkları kullanılmadı.

## Yanıt ve ses ayarları

Yerel komutlar (örneğin “Chrome’u aç”, “not al ...”, “10 dakika sonra hatırlat ...”) AI bağlantısını beklemeden çalışır. Diğer konuşmalar için Ayarlar’da OpenAI anahtarı veya çalışan Ollama modeli gerekir. Bağlantı yoksa ekranda MODEL OFFLINE görünür. Model yanıtı uzarsa JARVIS hata metni döndürür; yeni mesajlar sıraya alınır.

Ayarlar → JARVIS ses düzeyi kaydırıcısı 0–100 arasındadır. 0 sessizdir; değişiklikler bilgisayardaki ayarlara kaydedilir. Windows genel ses düzeyini değiştirmez.
