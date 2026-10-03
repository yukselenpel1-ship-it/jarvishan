# Güncelleme yayınına bağlama

Yayın deposu: https://github.com/yukselenpel1-ship-it/jarvishan .
Uygulama sabit `update.json` dosyasına bağlıdır. v0.2 arşivi `downloads/` içindedir.

1. `app/` içindeki kaynakları güncelle. API anahtarlarını, `.venv` ve
   `%LOCALAPPDATA%` verilerini repoya koyma.
2. Yeni sürüm ZIP'ini `downloads/` içine yükle. ZIP içinde `main.py`,
   `requirements.txt`, `jarvis/` ve kurulum dosyaları bulunmalı.
3. ZIP'in özetini Windows PowerShell'de hesapla:
   `Get-FileHash .\jarvis-v0.4.zip -Algorithm SHA256`.
4. `update.json` dosyasını ZIP yayına çıktıktan sonra güncelle:
   `{"version":"0.4.0","url":"https://raw.githubusercontent.com/yukselenpel1-ship-it/jarvishan/main/downloads/JARVIS_v0.4_Windows.zip","sha256":"GERCEK_64_KARAKTERLIK_OZET"}`
6. Windows'ta denetleme, indirme, kurulum, geri alma ve yeniden açılmayı dene.

v0.1'den ilk geçiş bir kez ZIP çıkarmayı gerektirir.
