"""Optional voice I/O. Cloud recognition is opt-in; speech runs on one thread."""
import queue
import threading
import asyncio
import ctypes
import os
import tempfile
import json
import urllib.request
import urllib.error


JARVIS_VOICE_ID = 'IKne3meq5aSn9XLyUdCD'


def turkish_voice(voices):
    for voice in voices:
        details = ' '.join(str(x) for x in (
            getattr(voice, 'id', ''), getattr(voice, 'name', ''), getattr(voice, 'languages', ''))).lower()
        if any(tag in details for tag in ('tr-tr', 'turkish', 'türk', '041f', 'ahmet', 'emel', 'tolga')):
            return voice
    return None


def play_mp3_windows(path, volume=100):
    """Use Windows MCI so online Turkish speech needs no second audio package."""
    mci = ctypes.windll.winmm.mciSendStringW
    alias = 'jarvis_voice'
    def send(command):
        code = mci(command, None, 0, None)
        if code:
            raise OSError(f'Windows audio error {code}')
    send(f'open "{path}" type mpegvideo alias {alias}')
    try:
        send(f'setaudio {alias} volume to {max(0, min(100, int(volume))) * 10}')
        send(f'play {alias} wait')
    finally:
        mci(f'close {alias}', None, 0, None)


class Voice:
    def __init__(self, events):
        self.events = events
        self.speaking = threading.Event()
        self.enabled = True
        self.volume = 100
        self.elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY', '').strip()
        self.voice_id = JARVIS_VOICE_ID
        self.stop = threading.Event()
        self.closed = threading.Event()
        self.jobs = queue.Queue()
        self.capture_lock = threading.Lock()
        self.listener = None
        threading.Thread(target=self._speaker, daemon=True).start()

    def say(self, text):
        if self.enabled:
            self.jobs.put(text[:1600])

    def _speaker(self):
        engine = None
        try:
            import pyttsx3
            candidate = pyttsx3.init()
            voice = turkish_voice(candidate.getProperty('voices'))
            if voice:
                candidate.setProperty('voice', voice.id)
                candidate.setProperty('rate', 175)
                engine = candidate
        except Exception:
            pass
        if engine is None:
            self.events.put(('notice', 'Yerel Türkçe ses bulunamadı. Türkçe çevrimiçi ses kullanılacak.'))
        while not self.closed.is_set():
            try:
                text = self.jobs.get(timeout=0.5)
            except queue.Empty:
                continue
            if not self.enabled:
                continue
            self.speaking.set()
            try:
                if self.volume == 0:
                    continue
                if self.elevenlabs_key:
                    try:
                        self._speak_elevenlabs(text)
                        continue
                    except (OSError, ValueError, urllib.error.HTTPError):
                        self.events.put(('notice', 'Seçilen ElevenLabs sesi çalışmadı; varsayılan Türkçe sese geçildi. API anahtarını ve kullanım hakkını kontrol et.'))
                if engine:
                    engine.setProperty('volume', self.volume / 100)
                    engine.say(text)
                    engine.runAndWait()
                else:
                    self._speak_online(text)
            except Exception:
                self.events.put(('notice', 'Türkçe çevrimiçi ses oynatılamadı. İnterneti veya Windows Türkçe ses paketini kontrol et.'))
            finally:
                self.speaking.clear()

    def _speak_online(self, text):
        import edge_tts
        fd, path = tempfile.mkstemp(suffix='.mp3', prefix='jarvis-')
        os.close(fd)
        try:
            asyncio.run(edge_tts.Communicate(text, 'tr-TR-AhmetNeural').save(path))
            play_mp3_windows(path, self.volume)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _speak_elevenlabs(self, text):
        """Send only the spoken answer to the selected ElevenLabs voice."""
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}?output_format=mp3_44100_128'
        request = urllib.request.Request(url, data=json.dumps({
            'text':text,'model_id':'eleven_multilingual_v2'}).encode('utf-8'),
            headers={'xi-api-key':self.elevenlabs_key,'Content-Type':'application/json',
                     'Accept':'audio/mpeg'}, method='POST')
        with urllib.request.urlopen(request,timeout=25) as response:
            audio = response.read(6 * 1024 * 1024 + 1)
        if not audio or len(audio)>6*1024*1024:
            raise ValueError('Ses dosyası boş veya çok büyük')
        fd,path=tempfile.mkstemp(suffix='.mp3',prefix='jarvis-eleven-')
        try:
            with os.fdopen(fd,'wb') as handle:
                handle.write(audio)
            play_mp3_windows(path,self.volume)
        finally:
            try: os.unlink(path)
            except OSError: pass

    def listen(self, continuous=False):
        if self.listener and self.listener.is_alive():
            self.events.put(('notice', 'Mikrofon zaten dinleniyor.'))
            return
        self.stop.clear()
        self.listener = threading.Thread(target=self._listen, args=(continuous,), daemon=True)
        self.listener.start()

    def _listen(self, continuous):
        if not self.capture_lock.acquire(blocking=False):
            return
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            recognizer.operation_timeout = 10
            with sr.Microphone() as mic:
                self.events.put(('status', 'Mikrofon hazırlanıyor…'))
                recognizer.adjust_for_ambient_noise(mic, duration=0.5)
                armed = False
                while not self.stop.is_set():
                    if self.speaking.is_set():
                        self.stop.wait(0.2)
                        continue
                    self.events.put(('status', 'Jarvis komutunu bekliyor' if continuous else 'Dinliyorum…'))
                    try:
                        audio = recognizer.listen(mic, timeout=2, phrase_time_limit=8)
                    except sr.WaitTimeoutError:
                        if continuous:
                            continue
                        self.events.put(('notice', 'Ses duyulmadı. Mikrofonu tekrar deneyebilirsin.'))
                        break
                    if self.stop.is_set() or self.speaking.is_set():
                        continue
                    try:
                        spoken = recognizer.recognize_google(audio, language='tr-TR')
                    except sr.UnknownValueError:
                        if not continuous:
                            self.events.put(('notice', 'Söylediğini anlayamadım.'))
                        if continuous:
                            continue
                        break
                    except sr.RequestError:
                        self.events.put(('notice', 'Ses tanıma servisine erişilemiyor. Yazılı komut kullanabilirsin.'))
                        break
                    if self.stop.is_set():
                        break
                    if not continuous or armed:
                        self.events.put(('command', spoken))
                        armed = False
                    else:
                        import re
                        match = re.search(r'\bjarvis\b', spoken, re.I)
                        if match:
                            remainder = spoken[match.end():].strip(' ,:.')
                            if remainder:
                                self.events.put(('command', remainder))
                            else:
                                armed = True
                                self.events.put(('notice', 'Dinliyorum. Sonraki cümlede komutunu söyle.'))
                    if not continuous:
                        break
        except ImportError:
            self.events.put(('notice', 'Mikrofon için KURULUM.bat ile ses bileşenlerini kur.'))
        except Exception:
            self.events.put(('notice', 'Mikrofon açılamadı. Windows mikrofon iznini ve varsayılan giriş aygıtını kontrol et.'))
        finally:
            self.capture_lock.release()
            self.events.put(('status', 'Hazır'))

    def stop_listening(self):
        self.stop.set()

    def close(self):
        self.enabled = False
        self.closed.set()
        self.stop.set()
