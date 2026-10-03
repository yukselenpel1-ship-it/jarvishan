"""Desktop bridge for the bundled web interface. Nothing is served publicly."""
import os
import io
import json
import queue
import re
import threading
import time
import webbrowser
from pathlib import Path
from uuid import uuid4

from . import __version__
from .core import Assistant, normalize
from .storage import data_dir
from .voice import Voice, JARVIS_VOICE_ID
from .updates import UpdateClient
from .agent import Agent
from .computer import describe, perform
from .remote import RemoteBridge


def local_command(text):
    """Reliable built-in tasks should not wait for the network or a model."""
    cmd = normalize(re.sub(r'^jarvis[\s,:]*', '', text.strip(), flags=re.I)).rstrip('.!? ')
    exact = {'yardim','komutlar','ne yapabilirsin','merhaba','selam','saat kac','saat',
             'tarih','bugun hangi gun','notlarim','hafiza','notlari goster',
             'sistem bilgisi','bilgisayar durumu','ram','cpu','ses ac','sesi ac',
             'ses azalt','ses kis','sesi kapat','sessiz'}
    if cmd in exact: return True
    if re.fullmatch(r'not sil \d+|\d+ dakika sonra hatirlat .+',cmd): return True
    if any(cmd.startswith(x) for x in ('not al ','hatirla ','dosya bul ','youtube ara ','google ara ')): return True
    return any(cmd in (f'{name} ac', f'{name}i ac', f'{name} acsana')
               for name in ('squadcraft','youtube','google','not defteri','hesap makinesi','gezgin','chrome'))


def common_app_command(text):
    cmd = normalize(re.sub(r'^jarvis[\s,:]*', '', text.strip(), flags=re.I)).replace('’', "'").rstrip('.!? ')
    aliases = {
        'chrome': ('chrome', "chrome'u"),
        'youtube': ('youtube', "youtube'u"),
        'google': ('google', "google'i", "google'u"),
        'squadcraft': ('squadcraft', "squadcraft'i"),
        'not defteri': ('not defteri', 'not defterini'),
        'hesap makinesi': ('hesap makinesi', 'hesap makinesini'),
        'gezgin': ('gezgin', 'gezgini'),
    }
    for name, forms in aliases.items():
        if cmd in (form + ' ac' for form in forms):
            return name + ' aç'
    return None


class DesktopAPI:
    def __init__(self):
        self.events = queue.Queue()
        self.assistant = Assistant()
        self.agent = Agent()
        self.agent.key = self.assistant.api_key
        self.agent.openai_model = self.assistant.model
        self.config_path = data_dir() / 'settings.json'
        config = {}
        if self.config_path.is_file():
            try:
                config = json.loads(self.config_path.read_text(encoding='utf-8'))
                if not isinstance(config, dict): config = {}
                self.agent.provider = config.get('provider', 'auto')
                self.agent.local_model = config.get('local_model', 'qwen3:4b')
                self.agent.openai_model = config.get('openai_model', self.assistant.model)
            except (ValueError, OSError):
                pass
        self.voice = Voice(self.events)
        value = config.get('voice_volume', 100)
        self.voice.volume = value if type(value) is int and 0 <= value <= 100 else 100
        self.update_client = UpdateClient(data_dir())
        self.speech_permission = False
        self.wake = False
        self.window = None
        self._lock = threading.Lock()
        self.pending = {}
        self._running = True
        self._timer = threading.Thread(target=self._reminders, daemon=True)
        self._timer.start()
        self.remote = None
        self.remote_config_path = data_dir() / 'remote_bridge.json'
        if self.remote_config_path.is_file():
            try:
                saved=json.loads(self.remote_config_path.read_text(encoding='utf-8'))
                self.remote=RemoteBridge(saved['url'],saved['token'],self.events)
                self.remote.start()
            except (OSError, ValueError, KeyError, TypeError):
                self.remote=None

    def initial(self):
        return {'version': __version__, 'notes': self.notes(), 'reminders': self.reminders(),
                'voice_enabled': self.voice.enabled, 'wake': self.wake,
                'voice_volume': self.voice.volume,
                'elevenlabs_configured': bool(self.voice.elevenlabs_key),
                'voice_id': JARVIS_VOICE_ID,
                'remote_configured': self.remote is not None,
                'remote_url': self.remote.url if self.remote else '',
                'model': self.agent.openai_model, 'local_model': self.agent.local_model,
                'provider': self.agent.provider, 'api_configured': bool(self.agent.key),
                'chat_ready': bool(self.agent.selected_provider()),
                'update_source': self.update_client.source or ''}

    def command(self, text):
        if not isinstance(text, str) or len(text) > 3000 or not text.strip():
            return {'ok': False, 'text': 'Kısa bir komut yaz.'}
        if not self._lock.acquire(blocking=False):
            return {'ok': False, 'text': 'Önceki komut işleniyor.'}
        try:
            common = common_app_command(text)
            if common or local_command(text):
                result = self.assistant.execute(common or text).text
                self.voice.say(result)
                return {'ok': True, 'text': result}
            if self.agent.selected_provider():
                result = self.agent.ask(text)
                return self._apply_proposals(result)
            normalized = normalize(text).rstrip('.!? ')
            if normalized in ('nasilsin', 'jarvis nasilsin', 'iyi misin', 'jarvis iyi misin'):
                result = 'İyiyim, teşekkür ederim. Sen nasılsın? Geniş sohbet için Ayarlar’dan OpenAI veya yerel Ollama bağlantısını açabilirsin.'
            else:
                result = self.assistant.execute(text).text
                if result.startswith('Bu komutu tanımadım.'):
                    result = self.agent.ask(text)['text']
            self.voice.say(result)
            return {'ok': True, 'text': result}
        except Exception:
            return {'ok': False, 'text': 'Komut tamamlanamadı. Tekrar deneyebilirsin.'}
        finally:
            self._lock.release()

    def _apply_proposals(self, result):
        outcomes, protected = [], []
        for action in result['actions']:
            if action['name'] in {'type_text','press_keys','click_screen','write_document'}:
                protected.append(action)
            else:
                try:
                    outcomes.append(describe(action) + ': ' + perform(action, self.assistant))
                except Exception:
                    outcomes.append(describe(action) + ': İşlem tamamlanamadı.')
        answer = result['text'] or ('İşlem önerdim.' if protected else 'İşlemler tamamlandı.')
        if outcomes: answer += '\n' + '\n'.join(outcomes)
        if outcomes:
            self.agent.history.append({'role':'assistant','content':'Gerçek işlem sonuçları: '+ '\n'.join(outcomes)})
        response = {'ok': True, 'text': answer}
        if protected:
            token = uuid4().hex
            self.pending.clear()
            self.pending[token] = (time.monotonic() + 180, protected)
            response['proposal'] = {'id':token, 'items':[describe(x) for x in protected]}
        self.voice.say(answer)
        return response

    def execute_pending(self, token):
        saved = self.pending.pop(token, None)
        if not saved or saved[0] < time.monotonic():
            return {'ok':False,'text':'İşlem onayı süresi doldu.'}
        outputs=[]
        for action in saved[1]:
            try:
                outputs.append(describe(action) + ': ' + perform(action, self.assistant))
            except Exception:
                outputs.append(describe(action) + ': Uygulanamadı.')
        answer='\n'.join(outputs)
        self.agent.history.append({'role':'assistant','content':'Onaylanan işlem sonuçları: '+answer})
        self.voice.say(answer)
        return {'ok':True,'text':answer}

    def cancel_pending(self, token):
        self.pending.pop(token, None)
        return {'ok':True}

    def inspect_screen(self, prompt, accepted):
        if accepted is not True or not isinstance(prompt,str) or len(prompt)>1000:
            return {'ok':False,'text':'Ekran analizi iptal edildi.'}
        if self.agent.selected_provider()!='openai':
            return {'ok':False,'text':'Ekran analizi için Ayarlar’dan OpenAI bağlantısını seç.'}
        try:
            import pyautogui
            pyautogui.FAILSAFE=True
            switched=False
            try:
                if os.name=='nt':
                    pyautogui.hotkey('alt','tab')
                    switched=True
                    time.sleep(0.35)
                picture=pyautogui.screenshot()
                size=picture.size
            finally:
                if switched:
                    pyautogui.hotkey('alt','tab')
            picture.thumbnail((1280,900))
            stream=io.BytesIO()
            picture.convert('RGB').save(stream,format='JPEG',quality=75)
            result=self.agent.ask(prompt,stream.getvalue(),size)
            return self._apply_proposals(result)
        except Exception:
            return {'ok':False,'text':'Ekran görüntüsü alınamadı. Windows ekran iznini kontrol et.'}

    def notes(self):
        return [{'id': i, 'body': body} for i, body in self.assistant.memory.notes()]

    def remove_note(self, note_id):
        try:
            return {'removed': bool(self.assistant.memory.delete_note(int(note_id))), 'notes': self.notes()}
        except (ValueError, TypeError):
            return {'removed': False, 'notes': self.notes()}

    def reminders(self):
        return [{'id': i, 'body': body, 'due': due} for i, body, due in self.assistant.memory.pending_reminders()]

    def cancel_reminder(self, reminder_id):
        try:
            removed = bool(self.assistant.memory.cancel_reminder(int(reminder_id)))
        except (ValueError, TypeError):
            removed = False
        return {'removed': removed, 'reminders': self.reminders()}

    def set_voice(self, enabled):
        self.voice.enabled = enabled is True
        return {'enabled': self.voice.enabled}

    def set_voice_volume(self, value):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
            return {'ok': False, 'volume': self.voice.volume}
        self.voice.volume = value
        self._save_settings()
        return {'ok': True, 'volume': value}

    def set_elevenlabs_key(self, key):
        if not isinstance(key, str) or not 8 <= len(key.strip()) <= 256:
            return {'ok': False, 'message': 'Geçerli ElevenLabs API anahtarını gir.'}
        self.voice.elevenlabs_key = key.strip()
        return {'ok': True, 'message': 'Seçilen JARVIS sesi bu oturum için etkin.'}

    def clear_elevenlabs_key(self):
        self.voice.elevenlabs_key = ''
        return {'ok': True, 'message': 'Varsayılan Türkçe sese dönüldü.'}

    def connect_remote(self, url, token):
        try:
            if not isinstance(url,str) or not isinstance(token,str): raise ValueError()
            token=token.strip() or (self.remote.token if self.remote else '')
            bridge=RemoteBridge(url.strip(),token,self.events)
            self.remote_config_path.write_text(json.dumps({'url':bridge.url,'token':token}),encoding='utf-8')
            if self.remote:self.remote.close()
            self.remote=bridge
            self.remote.start()
            return {'ok':True,'message':'Mobil bağlantı başlatıldı. Web arayüzünden bilgisayar durumunu kontrol et.'}
        except (OSError,ValueError):
            return {'ok':False,'message':'HTTPS web adresini ve en az 16 karakterlik köprü anahtarını gir.'}

    def disconnect_remote(self):
        if self.remote:self.remote.close()
        self.remote=None
        self.remote_config_path.unlink(missing_ok=True)
        return {'ok':True,'message':'Mobil bağlantı kapatıldı.'}

    def _save_settings(self):
        self.config_path.write_text(json.dumps({'provider':self.agent.provider,
            'openai_model':self.agent.openai_model,'local_model':self.agent.local_model,
            'voice_volume':self.voice.volume}),encoding='utf-8')

    def listen(self, accepted):
        if accepted is not True:
            return {'ok': False}
        self.speech_permission = True
        self.voice.listen()
        return {'ok': True}

    def set_wake(self, enabled, accepted):
        if enabled is True:
            if accepted is not True:
                return {'ok': False, 'wake': False}
            if self.voice.listener and self.voice.listener.is_alive():
                return {'ok': False, 'wake': self.wake, 'message': 'Mikrofonun mevcut dinlemesi bitince tekrar dene.'}
            self.speech_permission = True
            self.wake = True
            self.voice.listen(continuous=True)
        else:
            self.wake = False
            self.voice.stop_listening()
        return {'ok': True, 'wake': self.wake}

    def settings(self, key, model, provider='auto', local_model='qwen3:4b'):
        if not isinstance(key, str) or not isinstance(model, str) or not isinstance(local_model,str):
            return {'ok': False}
        if len(key) > 512 or len(model) > 100 or len(local_model)>100 or provider not in ('auto','openai','ollama'):
            return {'ok': False}
        self.assistant.api_key = key.strip() or self.assistant.api_key
        self.assistant.model = model.strip() or 'gpt-4.1-mini'
        self.assistant.history.clear()
        self.agent.key = self.assistant.api_key
        self.agent.openai_model = self.assistant.model
        self.agent.local_model = local_model.strip() or 'qwen3:4b'
        self.agent.provider = provider
        self.agent.history.clear()
        self._save_settings()
        selected = self.agent.selected_provider()
        return {'ok': True, 'api_configured': bool(self.agent.key), 'model': self.agent.openai_model,
                'provider':provider, 'selected_provider':selected, 'chat_ready':bool(selected)}

    def events_since_last_poll(self):
        events = []
        while len(events) < 40:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'status' and value == 'Hazır' and self.wake:
                self.wake = False
                events.append({'kind': 'wake', 'value': False})
            events.append({'kind': kind, 'value': value})
        return events

    def system_info(self):
        return self.assistant.system_info()

    def check_update(self):
        return self.update_client.check(__version__)

    def install_update(self):
        result = self.update_client.prepare(__version__)
        if result['ok']:
            self.voice.close()
            self.update_client.launch_installer(result['stage'], os.getpid())
            if self.window:
                self.window.destroy()
        return {k: v for k, v in result.items() if k != 'stage'}

    def open_url(self, url):
        if url in ('https://squadcraft.vercel.app/', 'https://www.youtube.com/'):
            webbrowser.open(url)

    def _reminders(self):
        while self._running:
            try:
                for _, body in self.assistant.memory.due():
                    self.events.put(('reminder', body))
                    self.voice.say('Hatırlatma: ' + body)
            except Exception:
                self.events.put(('notice', 'Hatırlatmalar okunamadı.'))
            threading.Event().wait(1)

    def close(self):
        self._running = False
        if self.remote:self.remote.close()
        self.voice.close()


def main():
    try:
        import webview
    except ImportError:
        raise SystemExit('Yeni arayüz için KURULUM.bat dosyasını tekrar çalıştır.')
    api = DesktopAPI()
    html = Path(__file__).parent / 'web' / 'index.html'
    window = webview.create_window('JARVIS · Windows Edition', str(html), js_api=api,
                                   width=1280, height=810, min_size=(880, 620),
                                   background_color='#020b0c')
    api.window = window
    window.events.closed += lambda *args: api.close()
    webview.start(debug=False)
