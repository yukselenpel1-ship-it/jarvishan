import json
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from jarvis.core import Assistant, normalize
from jarvis.storage import Memory


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'memory.sqlite3'
        self.memory = Memory(self.path)
        self.urls = []
        self.app = Assistant(self.memory, self.urls.append)
        self.app.api_key = ''

    def tearDown(self):
        self.temp.cleanup()

    def test_turkish_note_persists(self):
        self.app.execute('Jarvis not al Çarşamba görüşmeye git')
        self.assertEqual(Memory(self.path).notes()[0][1], 'Çarşamba görüşmeye git')
        self.assertIn('Çarşamba', self.app.execute('notlarım').text)

    def test_search_encoding(self):
        self.app.execute('YouTube ara Türkçe KPSS & tarih')
        self.assertEqual(self.urls[0], 'https://www.youtube.com/results?search_query=T%C3%BCrk%C3%A7e%20KPSS%20%26%20tarih')

    def test_sql_input_is_literal(self):
        self.app.execute("not al '); DROP TABLE notes; --")
        self.assertEqual(len(self.memory.notes()), 1)
        self.assertIn('silindi', self.app.execute('not sil 1').text)
        self.assertEqual(self.memory.notes(), [])

    def test_reminder_delivered_once(self):
        now = datetime.now()
        self.memory.remind('mola', now - timedelta(minutes=1))
        self.memory.remind('sonra', now + timedelta(minutes=1))
        self.assertEqual(self.memory.due(now)[0][1], 'mola')
        self.assertEqual(self.memory.due(now), [])

    def test_reminder_preserves_turkish(self):
        self.app.execute('10 dakika sonra hatırlat Çay iç')
        rows = self.memory.due(datetime.now() + timedelta(minutes=11))
        self.assertEqual(rows[0][1], 'Çay iç')

    def test_no_arbitrary_shell(self):
        with patch('jarvis.core.subprocess.Popen') as process:
            self.app.execute('cmd /c del *')
            process.assert_not_called()

    def test_missing_ai_key(self):
        self.assertIn('API', self.app.execute('Bana şiir yaz').text)

    def test_ai_payload_and_memory_privacy(self):
        self.app.api_key = 'test-key'
        self.memory.add_note('özel not')
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'choices': [{'message': {'content': 'Merhaba dünya'}}]}).encode()
        with patch('jarvis.core.urllib.request.urlopen', return_value=Response()) as request:
            self.assertEqual(self.app.chat('Bir fikir ver'), 'Merhaba dünya')
            payload = json.loads(request.call_args.args[0].data)
            self.assertNotIn('özel not', json.dumps(payload, ensure_ascii=False))
        self.assertEqual(len(self.app.history), 2)

    def test_ai_auth_error(self):
        self.app.api_key = 'invalid'
        error = urllib.error.HTTPError('https://api.openai.com', 401, 'unauthorized', {}, None)
        with patch('jarvis.core.urllib.request.urlopen', side_effect=error):
            self.assertIn('geçersiz', self.app.chat('Test'))

    def test_system_fallback(self):
        with patch.dict('sys.modules', {'psutil': None}):
            self.assertIn('mantıksal', self.app.system_info())

    def test_known_site(self):
        self.app.execute('SquadCraft aç')
        self.assertEqual(self.urls, ['https://squadcraft.vercel.app/'])

    def test_normalize(self):
        self.assertEqual(normalize('İŞLEM ÇĞÜÖ'), 'islem cguo')


if __name__ == '__main__':
    unittest.main()
