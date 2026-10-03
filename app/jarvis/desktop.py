"""Desktop bridge for the bundled web interface. Nothing is served publicly."""
import os
import queue
import threading
import webbrowser
from pathlib import Path

from . import __version__
from .core import Assistant
from .storage import data_dir
from .voice import Voice
from .updates import UpdateClient


class DesktopAPI:
    def __init__(self):
        self.events = queue.Queue()
        self.assistant = Assistant()
        self.voice = Voice(self.events)
        self.update_client = UpdateClient(data_dir())
        self.speech_permission = False
        self.wake = False
        self.window = None
        self._lock = threading.Lock()
        self._running = True
        self._timer = threading.Thread(target=self._reminders, daemon=True)
        self._timer.start()

    def initial(self):
        return {'version': __version__, 'notes': self.notes(), 'reminders': self.reminders(),
                'voice_enabled': self.voice.enabled, 'wake': self.wake,
                'model': self.assistant.model, 'api_configured': bool(self.assistant.api_key),
                'update_source': self.update_client.source or ''}

    def command(self, text):
        if not isinstance(text, str) or len(text) > 3000 or not text.strip():
            return {'ok': False, 'text': 'Kısa bir komut yaz.'}
        if not self._lock.acquire(blocking=False):
            return {'ok': False, 'text': 'Önceki komut işleniyor.'}
        try:
            result = self.assistant.execute(text).text
            self.voice.say(result)
            return {'ok': True, 'text': result}
        except Exception:
            return {'ok': False, 'text': 'Komut tamamlanamadı. Tekrar deneyebilirsin.'}
        finally:
            self._lock.release()

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

    def settings(self, key, model):
        if not isinstance(key, str) or not isinstance(model, str):
            return {'ok': False}
        if len(key) > 512 or len(model) > 100:
            return {'ok': False}
        self.assistant.api_key = key.strip()
        self.assistant.model = model.strip() or 'gpt-4.1-mini'
        self.assistant.history.clear()
        return {'ok': True, 'api_configured': bool(self.assistant.api_key), 'model': self.assistant.model}

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
        self.voice.close()


def main():
    try:
        import webview
    except ImportError:
        raise SystemExit('Yeni arayüz için KURULUM.bat dosyasını tekrar çalıştır.')
    api = DesktopAPI()
    html = Path(__file__).parent / 'web' / 'index.html'
    window = webview.create_window('JARVIS • Komut Merkezi', str(html), js_api=api,
                                   width=1280, height=810, min_size=(880, 620),
                                   background_color='#090e1b')
    api.window = window
    window.events.closed += lambda *args: api.close()
    webview.start(debug=False)
