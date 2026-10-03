"""Optional voice I/O. Cloud recognition is opt-in; speech runs on one thread."""
import queue
import threading
import asyncio
import ctypes
import os
import tempfile


def turkish_voice(voices):
    for voice in voices:
        details = ' '.join(str(x) for x in (
            getattr(voice, 'id', ''), getattr(voice, 'name', ''), getattr(voice, 'languages', ''))).lower()
        if any(tag in details for tag in ('tr-tr', 'turkish', 'türk', '041f', 'ahmet', 'emel', 'tolga')):
            return voice
    return None


def play_mp3_windows(path):
    """Use Windows MCI so online Turkish speech needs no second audio package."""
    mci = ctypes.windll.winmm.mciSendStringW
    alias = 'jarvis_voice'
    def send(command):
        code = mci(command, None, 0, None)
        if code:
            raise OSError(f'Windows audio error {code}')
    send(f'open "{path}" type mpegvideo alias {alias}')
    try:
        send(f'play {alias} wait')
    finally:
        mci(f'close {alias}', None, 0, None)


class Voice:
    def __init__(self, events):
        self.events = events
        self.speaking = threading.Event()
        self.enabled = True
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
                if engine:
                    engine.say(text)
                    engine.runAndWait()
                else:
                    self._speak_online(text)
            except Exception:
                self.events.put(('notice', 'Türkçe çevrimiçi ses oynatılamadı. İnterneti veya Windows Türkçe ses paketini kontrol et.'))
            finally:
                self.speaking.clear()

    @staticmethod
    def _speak_online(text):
        import edge_tts
        fd, path = tempfile.mkstemp(suffix='.mp3', prefix='jarvis-')
        os.close(fd)
        try:
            asyncio.run(edge_tts.Communicate(text, 'tr-TR-AhmetNeural').save(path))
            play_mp3_windows(path)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

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
