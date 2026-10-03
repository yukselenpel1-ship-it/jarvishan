import ctypes
import json
import os
import platform
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .storage import Memory


def normalize(text):
    return text.translate(str.maketrans('İI', 'ii')).lower().translate(
        str.maketrans('çğıöşü', 'cgiosu')).strip()


HELP = ('Komutlar: Chrome aç • hesap makinesi aç • not defteri aç • SquadCraft aç • '
        'YouTube ara lo-fi • Google ara KPSS • saat kaç • sistem bilgisi • '
        'ses aç / ses azalt / sesi kapat • dosya bul özgeçmiş • '
        'not al yarın CV hazırla • notlarım • not sil 1 • '
        '10 dakika sonra hatırlat mola ver. Serbest sohbet için Ayarlar’dan API anahtarı gir.')


@dataclass
class Result:
    text: str


class Assistant:
    def __init__(self, memory=None, opener=None):
        self.memory = memory or Memory()
        self.open_url = opener or webbrowser.open
        self.api_key = os.environ.get('OPENAI_API_KEY', '')
        self.model = os.environ.get('JARVIS_MODEL', 'gpt-4.1-mini')
        self.history = []
        self.processes = {}

    def execute(self, raw):
        raw = raw.strip()
        raw = re.sub(r'^jarvis[\s,:]*', '', raw, flags=re.I)
        cmd = normalize(raw).rstrip('.!?')
        if not cmd:
            return Result('Dinliyorum. Komutunu söyle.')
        if cmd in ('yardim', 'komutlar', 'ne yapabilirsin'):
            return Result(HELP)
        if cmd in ('merhaba', 'selam'):
            return Result('Merhaba. Hazırım. Nasıl yardımcı olayım?')
        if cmd in ('saat kac', 'saat'):
            return Result(datetime.now().strftime('Saat %H:%M.'))
        if cmd in ('tarih', 'bugun hangi gun'):
            return Result(datetime.now().strftime('Bugün %d.%m.%Y.'))
        if cmd in ('notlarim', 'hafiza', 'notlari goster'):
            notes = self.memory.notes()
            return Result('\n'.join(f'{i}. {t}' for i, t in notes) or 'Henüz kayıtlı not yok.')
        match = re.fullmatch(r'not sil (\d+)', cmd)
        if match:
            deleted = self.memory.delete_note(int(match[1]))
            return Result('Not silindi.' if deleted else 'Bu numarada not yok.')
        match = re.match(r'^(not al|hatirla)\s+(.+)$', cmd)
        if match:
            body = raw[len(match[1]):].strip()
            self.memory.add_note(body)
            return Result('Yerel hafızama kaydettim: ' + body)
        match = re.fullmatch(r'(\d+) dakika sonra hatirlat (.+)', cmd)
        if match:
            minutes = int(match[1])
            if not 1 <= minutes <= 525600:
                return Result('Süre 1–525600 dakika arasında olmalı.')
            body = raw[match.start(2):].strip()
            self.memory.remind(body, datetime.now() + timedelta(minutes=minutes))
            return Result(f'{minutes} dakika sonra hatırlatacağım: {body}. Uygulama açık kalmalı.')
        for provider, base in [('youtube', 'https://www.youtube.com/results?search_query='),
                               ('google', 'https://www.google.com/search?q=')]:
            prefix = provider + ' ara '
            if cmd.startswith(prefix):
                query = raw[len(prefix):].strip()
                self.open_url(base + urllib.parse.quote(query))
                return Result(f'{provider.title()} araması açıldı: {query}')
        sites = {'squadcraft': 'https://squadcraft.vercel.app/',
                 'youtube': 'https://www.youtube.com/', 'google': 'https://www.google.com/'}
        for name, url in sites.items():
            if cmd in (f'{name} ac', f'{name}i ac', f'{name} acsana'):
                self.open_url(url)
                return Result(name.title() + ' açıldı.')
        if cmd in ('sistem bilgisi', 'bilgisayar durumu', 'ram', 'cpu'):
            return Result(self.system_info())
        if cmd in ('ses ac', 'sesi ac', 'ses azalt', 'ses kis', 'sesi kapat', 'sessiz'):
            if platform.system() != 'Windows':
                return Result('Ses kontrolü Windows üzerinde çalışır.')
            key = 0xAF if cmd in ('ses ac', 'sesi ac') else 0xAE
            if cmd in ('sesi kapat', 'sessiz'):
                key = 0xAD
            for _ in range(1 if key == 0xAD else 5):
                ctypes.windll.user32.keybd_event(key, 0, 0, 0)
                ctypes.windll.user32.keybd_event(key, 0, 2, 0)
            return Result('Sessiz modu değiştirildi.' if key == 0xAD else 'Ses seviyesi değiştirildi.')
        if cmd.startswith('dosya bul '):
            return Result(self.find_files(raw[10:].strip()))
        apps = {'not defteri': 'notepad.exe', 'hesap makinesi': 'calc.exe',
                'gezgin': 'explorer.exe', 'chrome': 'chrome'}
        for name, executable in apps.items():
            if cmd == name + ' ac':
                return Result(self.launch(name, executable))
            if cmd == name + ' kapat':
                process = self.processes.get(name)
                if process and process.poll() is None:
                    # Ask the launched window to close, allowing native unsaved-work prompts.
                    return Result(self.close_window(process.pid))
                return Result('Bu oturumda başlattığım, kapanabilir bir pencere bulunamadı.')
        return Result(self.chat(raw))

    def launch(self, name, executable):
        if platform.system() != 'Windows':
            return 'Uygulama açma Windows üzerinde çalışır.'
        if name == 'chrome':
            roots = [os.environ.get('PROGRAMFILES', ''), os.environ.get('PROGRAMFILES(X86)', ''),
                     os.environ.get('LOCALAPPDATA', '')]
            found = next((Path(p) / 'Google/Chrome/Application/chrome.exe' for p in roots
                          if p and (Path(p) / 'Google/Chrome/Application/chrome.exe').is_file()), None)
            if found is None:
                return 'Chrome bulunamadı. “Google aç” ile varsayılan tarayıcıyı kullanabilirsin.'
            executable = str(found)
        try:
            self.processes[name] = subprocess.Popen([executable], shell=False)
            return name.title() + ' açıldı.'
        except OSError:
            return 'Uygulama başlatılamadı. Kurulu olduğunu kontrol et.'

    @staticmethod
    def close_window(pid):
        user32 = ctypes.windll.user32
        count = []
        callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @callback_type
        def callback(hwnd, _):
            process_id = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd), ctypes.byref(process_id))
            if process_id.value == pid and user32.IsWindowVisible(ctypes.c_void_p(hwnd)):
                user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0010, 0, 0)
                count.append(hwnd)
            return True
        user32.EnumWindows(callback, 0)
        return 'Pencereye kapatma isteği gönderildi.' if count else 'Kapanabilir pencere bulunamadı.'

    @staticmethod
    def system_info():
        base = f'{platform.system()} {platform.release()} · {os.cpu_count()} mantıksal işlemci'
        try:
            import psutil
            ram = psutil.virtual_memory()
            return f'{base}\nCPU: %{psutil.cpu_percent(interval=0.2):.0f} · RAM: %{ram.percent:.0f} · {ram.total / 2**30:.1f} GB'
        except ImportError:
            return base + '\nAyrıntılı CPU/RAM için KURULUM.bat dosyasını çalıştır.'

    @staticmethod
    def find_files(query):
        if not query or '/' in query or '\\' in query:
            return 'Yalnızca dosya adını yaz: dosya bul CV'
        folders = [Path.home() / x for x in ('Desktop', 'Documents', 'Downloads',
                                           'OneDrive/Desktop', 'OneDrive/Documents')]
        found, deadline = [], time.monotonic() + 5
        truncated = False
        for folder in folders:
            for root, dirs, files in os.walk(folder, followlinks=False):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'venv')]
                for filename in files:
                    if normalize(query) in normalize(filename):
                        found.append(str(Path(root) / filename))
                    if len(found) >= 20:
                        break
                if len(found) >= 20 or time.monotonic() > deadline:
                    truncated = True
                    break
            if truncated:
                break
        text = '\n'.join(found) or 'Masaüstü, Belgeler ve İndirilenler içinde eşleşme bulunamadı.'
        return text + ('\nArama sınırına ulaşıldı; daha belirgin bir ad kullan.' if truncated else '')

    def chat(self, prompt):
        if not self.api_key:
            return 'Bu komutu tanımadım. “Yardım” yazabilirsin. Serbest AI sohbeti için Ayarlar’dan API anahtarı gir.'
        messages = [{'role': 'system', 'content': 'Sen Jarvis isimli Türkçe kişisel asistansın. Kısa ve doğru cevap ver. '
                     'Bilgisayarda işlem yapma aracın yok. Uyguladığını iddia etme. Yerel notlara erişimin yok.'}]
        messages += self.history[-12:] + [{'role': 'user', 'content': prompt}]
        payload = json.dumps({'model': self.model, 'messages': messages}).encode()
        request = urllib.request.Request('https://api.openai.com/v1/chat/completions', data=payload,
            headers={'Authorization': 'Bearer ' + self.api_key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=35) as response:
                answer = json.load(response)['choices'][0]['message']['content']
            if not isinstance(answer, str) or not answer:
                return 'AI metin yanıtı döndürmedi.'
            self.history.extend([{'role': 'user', 'content': prompt}, {'role': 'assistant', 'content': answer}])
            return answer
        except urllib.error.HTTPError as exc:
            return {401: 'API anahtarı geçersiz.', 429: 'API kotası veya hız sınırına ulaşıldı.',
                    404: 'Model bulunamadı; Ayarlar’dan erişebildiğin modeli seç.'}.get(exc.code,
                    f'AI servisi HTTP {exc.code} hatası verdi.')
        except (OSError, ValueError, KeyError, IndexError):
            return 'AI servisine erişilemedi veya yanıt okunamadı. İnternetini ve model ayarını kontrol et.'
