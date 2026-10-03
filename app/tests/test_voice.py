import queue
import threading
import types
import json
import unittest
from unittest.mock import patch

from jarvis.voice import Voice, turkish_voice


class VoiceTests(unittest.TestCase):
    def test_stopping_microphone_keeps_speech_available(self):
        spoken = []
        completed = threading.Event()
        class Engine:
            def getProperty(self, name): return [types.SimpleNamespace(id='HKEY_LOCAL_MACHINE\\tr-TR-Tolga', name='Tolga', languages=[])]
            def setProperty(self, *args): pass
            def say(self, text): spoken.append(text)
            def runAndWait(self): completed.set()
        fake = types.SimpleNamespace(init=lambda: Engine())
        with patch.dict('sys.modules', {'pyttsx3': fake}):
            voice = Voice(queue.Queue())
            try:
                voice.stop_listening()
                voice.say('Mikrofon kapalıyken yanıt ver')
                self.assertTrue(completed.wait(2))
                self.assertEqual(spoken, ['Mikrofon kapalıyken yanıt ver'])
            finally:
                voice.close()

    def test_turkish_voice_selection_avoids_english_default(self):
        english = types.SimpleNamespace(id='en-US-David', name='David', languages=[])
        turkish = types.SimpleNamespace(id='tr-TR-Tolga', name='Tolga', languages=[])
        self.assertIs(turkish_voice([english, turkish]), turkish)
        self.assertIsNone(turkish_voice([english]))

    def test_local_speech_uses_selected_volume(self):
        volumes=[]
        completed=threading.Event()
        class Engine:
            def getProperty(self, name): return [types.SimpleNamespace(id='tr-TR-Test',name='Turkish',languages=[])]
            def setProperty(self, key, value):
                if key=='volume': volumes.append(value)
            def say(self, text): pass
            def runAndWait(self): completed.set()
        with patch.dict('sys.modules', {'pyttsx3':types.SimpleNamespace(init=lambda:Engine())}):
            voice=Voice(queue.Queue())
            try:
                voice.volume=25
                voice.say('Test')
                self.assertTrue(completed.wait(2))
                self.assertIn(0.25,volumes)
            finally:
                voice.close()

    def test_selected_elevenlabs_voice_and_volume(self):
        voice=Voice.__new__(Voice)
        voice.elevenlabs_key='test-key'
        voice.voice_id='IKne3meq5aSn9XLyUdCD'
        voice.volume=35
        class Audio:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return b'ID3sample'
        with patch('jarvis.voice.urllib.request.urlopen',return_value=Audio()) as send, \
             patch('jarvis.voice.play_mp3_windows') as play:
            voice._speak_elevenlabs('Merhaba Oğuzhan')
        request=send.call_args.args[0]
        self.assertIn('/IKne3meq5aSn9XLyUdCD?',request.full_url)
        self.assertEqual(json.loads(request.data)['text'],'Merhaba Oğuzhan')
        self.assertEqual(request.headers['Xi-api-key'],'test-key')
        self.assertEqual(play.call_args.args[1],35)


if __name__ == '__main__':
    unittest.main()
