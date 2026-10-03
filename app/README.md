# JARVIS v0.2 — masaüstü sürümü

Türkçe kişisel asistan. Modern masaüstü penceresi, konuşma alanı, hızlı komutlar,
yerel notlar, hatırlatmalar, isteğe bağlı mikrofon ve AI sohbeti.

## İlk kurulum ve eski sürümden geçiş

Windows 10/11, WebView2 Runtime ve Python 3.11 ya da 3.12 gerekir. Python: https://www.python.org/downloads/ .
ZIP'i bilgisayarda kalıcı bir klasöre çıkar. `KURULUM.bat` dosyasını bir kez aç.
Bağımlılıklar ve masaüstü kısayolu kurulur. Sonraki açılışlarda masaüstündeki
**JARVIS** kısayolunu kullan. Hata çıktısını görmek için `BASLAT.bat` kullanılabilir.

v0.1 kullandıysan yeni paketi eski `JARVIS_v0.1` klasörünün bulunduğu üst klasöre
çıkar. Yeni `JARVIS_v0.2` klasöründe `KURULUM.bat` çalıştır. Notlar
`%LOCALAPPDATA%\Jarvis\memory.sqlite3` içinde tutulduğu için yeni sürümde görünür.
Yeni sürüm çalıştıktan sonra eski proje klasörünü silebilirsin; veri klasörüne dokunma.
Pencere hiç açılmazsa `BASLAT.bat` çıktısını kontrol et; WebView2 gerekiyorsa
Microsoft'un https://developer.microsoft.com/microsoft-edge/webview2/ adresinden kur.

## Kullanım

- Ana merkezde yaz veya mikrofona bas: `saat kaç`, `Chrome aç`, `SquadCraft aç`,
  `YouTube ara KPSS`, `dosya bul CV`, `sistem bilgisi`, `ses aç`.
- Hafıza bölümünde notları ekle, görüntüle ve sil. `not al ...` komutu da çalışır.
- Hatırlatmalar bölümünde süre ve metin gir. Bekleyenleri gör ve iptal et.
- Ayarlardan sesi, sürekli “Jarvis” modunu ve isteğe bağlı AI anahtarını yönet.
- Türkçe yerel ses varsa kullanılır; yoksa yanıt metni çevrimiçi Türkçe ses
  servisine gönderilir. Mikrofon konuşması Google tanıma servisine gönderilir;
  dinleme başlamadan açıklama ve onay gösterilir.
- AI sohbeti OpenAI API anahtarı gerektirir ve ayrı ücretlendirilir. Anahtar
  bellekte tutulur; notlar AI'ye otomatik gönderilmez.

## Güncellemeler

v0.2 içinde güncelleme denetleme ve kurma akışı hazırdır. Sabit HTTPS yayın
adresi `update_source.txt` dosyasında JARVISHAN deposuna bağlanmıştır. Yeni sürüm
yayımlandığında uygulama sürümü ve SHA-256 özetini doğrular, kapanır, eski
kaynakları yedekleyerek günceller ve tekrar açılır. Not veritabanına dokunulmaz.
v0.1'den v0.2'ye geçiş için bir kez ZIP gerekir. Sonraki sürüm yayın akışı
`YAYIN_REHBERI.md` dosyasındadır. Güncellemenin Windows'ta canlı testi gerekir.

`main.py` → `jarvis/desktop.py` → `jarvis/web/index.html` görsel arayüz.
Komut motoru `jarvis/core.py`, ses `jarvis/voice.py`, kalıcı veri
`jarvis/storage.py`, güncelleme `jarvis/updates.py` ve `jarvis/update_worker.py`.
Kaynak kod ayrı bir Windows EXE değildir; Python kurulumu bir kez gerekir.

Geliştirici kontrolü:

```bash
python -m unittest discover -s tests -v
python -m compileall -q jarvis main.py
```
