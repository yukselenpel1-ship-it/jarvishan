"""Explicit, bounded desktop actions. No arbitrary command or script execution."""
import platform
import re
import urllib.parse
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

from .storage import data_dir


KEYS = {'ctrl', 'alt', 'shift', 'win', 'tab', 'enter', 'esc', 'space', 'backspace',
        'up', 'down', 'left', 'right', 'home', 'end', 'f2', 'f5', 'a', 'c', 'v', 'x', 'z'}
APPS = {'chrome', 'not defteri', 'hesap makinesi', 'gezgin'}


def valid_action(name, args):
    if not isinstance(args, dict):
        raise ValueError('Araç parametreleri hatalı')
    if name == 'open_app':
        if args.get('name') not in APPS: raise ValueError('Uygulama izin listesinde yok')
    elif name == 'search_web':
        if not isinstance(args.get('query'), str) or not 1 <= len(args['query']) <= 200: raise ValueError('Arama metni hatalı')
    elif name == 'system_info':
        pass
    elif name == 'find_file':
        if not isinstance(args.get('name'), str) or not 1 <= len(args['name']) <= 100: raise ValueError('Dosya adı hatalı')
    elif name == 'add_note':
        if not isinstance(args.get('text'), str) or not 1 <= len(args['text']) <= 1000: raise ValueError('Not çok uzun')
    elif name == 'remind_me':
        if not isinstance(args.get('text'), str) or not 1 <= len(args['text']) <= 500: raise ValueError('Hatırlatma hatalı')
        if not isinstance(args.get('minutes'), int) or not 1 <= args['minutes'] <= 525600: raise ValueError('Süre hatalı')
    elif name == 'type_text':
        text = args.get('text')
        if not isinstance(text, str) or not 1 <= len(text) <= 1000 or '\n' in text or '\r' in text: raise ValueError('Tek satırlık metin gerekli')
    elif name == 'press_keys':
        keys = args.get('keys')
        if not isinstance(keys, list) or not 1 <= len(keys) <= 3 or not all(k in KEYS for k in keys): raise ValueError('Kısayol izin listesinde yok')
    elif name == 'click_screen':
        if not all(isinstance(args.get(k), int) and 0 <= args[k] <= 10000 for k in ('x','y')): raise ValueError('Ekran konumu hatalı')
    elif name == 'write_document':
        title, text = args.get('title'), args.get('text')
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 80 or not re.fullmatch(r'[\w\s-]+', title, re.UNICODE): raise ValueError('Dosya adı geçersiz')
        if title.strip().upper() in {'CON','PRN','AUX','NUL','COM1','COM2','LPT1','LPT2'}: raise ValueError('Windows ayrılmış dosya adı')
        if not isinstance(text, str) or not 1 <= len(text) <= 10000: raise ValueError('Dosya içeriği geçersiz')
    else:
        raise ValueError('Bilinmeyen araç')
    return {'name': name, 'args': args}


def describe(action):
    name, args = action['name'], action['args']
    return {
        'open_app': lambda: f"{args['name']} uygulamasını aç",
        'search_web': lambda: f"Web'de ara: {args['query']}",
        'system_info': lambda: 'Sistem bilgilerini oku',
        'find_file': lambda: f"Dosya bul: {args['name']}",
        'add_note': lambda: f"Not kaydet: {args['text']}",
        'remind_me': lambda: f"{args['minutes']} dakika sonra hatırlat: {args['text']}",
        'type_text': lambda: f"Etkin pencereye yaz: {args['text'][:80]}",
        'press_keys': lambda: 'Tuşlara bas: ' + ' + '.join(args['keys']),
        'click_screen': lambda: f"Ekranda ({args['x']}, {args['y']}) konumuna tıkla",
        'write_document': lambda: f"Belgeler/Jarvis içine {args['title']}.txt dosyasını oluştur",
    }[name]()


def perform(action, assistant):
    action = valid_action(action['name'], action['args'])
    name, args = action['name'], action['args']
    if name == 'open_app':
        return assistant.launch(args['name'], {'chrome':'chrome', 'not defteri':'notepad.exe',
                   'hesap makinesi':'calc.exe', 'gezgin':'explorer.exe'}[args['name']])
    if name == 'search_web':
        url='https://www.google.com/search?q='+urllib.parse.quote(args['query'])
        webbrowser.open(url)
        return 'Arama açıldı.'
    if name == 'system_info': return assistant.system_info()
    if name == 'find_file': return assistant.find_files(args['name'])
    if name == 'add_note':
        assistant.memory.add_note(args['text'])
        return 'Not kaydedildi.'
    if name == 'remind_me':
        assistant.memory.remind(args['text'], datetime.now()+timedelta(minutes=args['minutes']))
        return 'Hatırlatma kaydedildi.'
    if name == 'write_document':
        base=Path.home()/'OneDrive'/'Documents'
        if not base.is_dir(): base=Path.home()/'Documents'
        folder=base/'Jarvis'
        folder.mkdir(parents=True,exist_ok=True)
        dest=folder/(args['title'].strip()+'.txt')
        if dest.exists(): return 'Bu dosya zaten var; üzerine yazılmadı.'
        dest.write_text(args['text'],encoding='utf-8')
        return 'Dosya oluşturuldu: '+str(dest)
    if platform.system() != 'Windows': return 'Ekran kontrolü Windows üzerinde çalışır.'
    import pyautogui
    pyautogui.FAILSAFE=True
    if name == 'press_keys':
        import time
        pyautogui.hotkey('alt','tab')
        time.sleep(0.25)
        pyautogui.hotkey(*args['keys'],interval=0.12)
        return 'Tuş kısayolu uygulandı.'
    if name == 'click_screen':
        width,height=pyautogui.size()
        if args['x']>=width or args['y']>=height: return 'Konum ekran dışında.'
        import time
        pyautogui.hotkey('alt','tab')
        time.sleep(0.25)
        pyautogui.click(args['x'],args['y'])
        return 'Tıklama uygulandı.'
    if name == 'type_text':
        # The foreground window must be chosen by the user before confirmation.
        # Clipboard roundtrip preserves Turkish characters; no newline is accepted.
        import time
        import tkinter as tk
        clipboard=tk.Tk(); clipboard.withdraw()
        try:
            try: original=clipboard.clipboard_get()
            except tk.TclError: original=None
            clipboard.clipboard_clear(); clipboard.clipboard_append(args['text']); clipboard.update()
            pyautogui.hotkey('alt','tab')
            time.sleep(0.25)
            pyautogui.hotkey('ctrl','v')
            time.sleep(0.25)
            if original is not None:
                clipboard.clipboard_clear(); clipboard.clipboard_append(original); clipboard.update()
        finally:
            clipboard.destroy()
        return 'Metin önceki pencereye yazıldı.'
    return 'İşlem uygulanamadı.'
