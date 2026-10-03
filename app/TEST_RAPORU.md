# JARVIS v0.7 doğrulama raporu

03.10.2026 — Linux/Python 3.12.14 ortamı. 24 otomatik test PASS.
AI sohbet yanıtı ve model araç çağrısı mock yanıtlarla sınandı. Modelin
teklif ettiği yazma işlemi kullanıcı onayı olmadan çalışmıyor; onay bir kez
kullanılabiliyor. Komut motoru, notlar, hatırlatmalar, ses seçimi ve güncelleme
geri alma testleri geçti. Python kaynakları derlendi; HTML ayrıştırıldı ve
JavaScript sözdizimi Node ile doğrulandı.

Yeni WebView2 arayüzü, gerçek OpenAI/Ollama bağlantısı, Windows ekran/tuş
kontrolü, Türkçe ses ve uygulama içi v0.3→v0.7 güncellemesi bu Linux ortamında
uçtan uca test edilemedi. İlk Windows kurulumunda bunların cihazda kontrolü
gerekir. Kullanıcının önceki ekran görüntüsü yalnızca v0.1 arayüzünün açılıp
`saat kaç` komutuna yanıt verdiğini doğrular.
