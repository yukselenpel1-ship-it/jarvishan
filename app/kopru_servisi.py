"""
J.A.R.V.I.S. Windows Köprü Servisi
Web / Mobil arayüzden gelen bilgisayar işlemlerini dinler ve güvenli şekilde çalıştırır.
"""
import sys
import os
import json
import time
import queue
from pathlib import Path

# jarvis paketini tanıt
sys.path.insert(0, str(Path(__file__).parent))

from jarvis.remote import RemoteBridge
from jarvis.storage import data_dir

def main():
    print("=" * 64)
    print("       J.A.R.V.I.S. WINDOWS KÖPRÜ SERVİSİ (PC KONTROL)")
    print("=" * 64)
    
    config_file = data_dir() / 'remote_bridge.json'
    url = ""
    token = ""
    
    if config_file.is_file():
        try:
            cfg = json.loads(config_file.read_text(encoding='utf-8'))
            url = cfg.get('url', '').strip()
            token = cfg.get('token', '').strip()
        except Exception:
            pass
            
    # Komut satırı argümanları ile de geçilebilir: python kopru_servisi.py <url> <token>
    if len(sys.argv) >= 3:
        url = sys.argv[1].strip()
        token = sys.argv[2].strip()
        config_file.write_text(json.dumps({'url': url, 'token': token}, ensure_ascii=False), encoding='utf-8')
        
    if not url or len(token) < 16:
        print("\n[İLK KURULUM - KÖPRÜ AYARLARI]")
        print("Vercel web sitenizin adresini ve köprü anahtarınızı girin.")
        print("Örnek URL: https://jarvishan.vercel.app  (veya http://localhost:3000)")
        entered_url = input("\nWeb Adresi: ").strip()
        entered_token = input("JARVIS_BRIDGE_TOKEN (en az 16 karakter): ").strip()
        
        if not entered_url:
            print("Hata: Web adresi boş bırakılamaz.")
            input("\nÇıkmak için Enter'a basın...")
            return
            
        if len(entered_token) < 16:
            print("Hata: Köprü anahtarı (JARVIS_BRIDGE_TOKEN) en az 16 karakter olmalı.")
            input("\nÇıkmak için Enter'a basın...")
            return
            
        url = entered_url.rstrip('/')
        token = entered_token
        config_file.write_text(json.dumps({'url': url, 'token': token}, ensure_ascii=False), encoding='utf-8')
        print(f"Ayarlar kaydedildi -> {config_file}\n")
        
    print(f"Hedef Sunucu : {url}")
    print(f"Köprü Anahtarı: {token[:4]}...{token[-4:]} ({len(token)} karakter)")
    print("-" * 64)
    print("Köprü bağlantısı başlatılıyor...")
    
    events = queue.Queue()
    try:
        bridge = RemoteBridge(url, token, events)
        bridge.start()
    except Exception as e:
        print(f"[BAĞLANTI HATASI] {e}")
        input("\nÇıkmak için Enter'a basın...")
        return

    print("[KÖPRÜ AKTİF] Telefondan ve web'den gelecek komutlar bekleniyor...")
    print("Çıkmak için pencereyi kapatabilir veya Ctrl+C tuşlayabilirsiniz.\n")

    try:
        while True:
            try:
                kind, msg = events.get(timeout=1.0)
                ts = time.strftime('%H:%M:%S')
                if 'Mobil istek' in msg:
                    print(f"[{ts}] ⚡ [İŞLEM GERÇEKLEŞTİRİLDİ] {msg}")
                elif 'hata' in msg.lower() or 'reddedildi' in msg.lower() or 'erişilemedi' in msg.lower():
                    print(f"[{ts}] ⚠️ [{kind.upper()}] {msg}")
                else:
                    print(f"[{ts}] ℹ️ [{kind.upper()}] {msg}")
            except queue.Empty:
                pass
    except KeyboardInterrupt:
        print("\nKöprü durduruluyor...")
        bridge.close()
        print("Köprü sonlandırıldı.")

if __name__ == '__main__':
    main()
