import queue
import threading
import types
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


if __name__ == '__main__':
    unittest.main()
