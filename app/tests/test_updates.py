import io
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from jarvis.storage import Memory
from jarvis.updates import UpdateClient, archive_files, version_tuple
from jarvis.update_worker import apply


def archive(names):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as zipped:
        for name in names:
            zipped.writestr(name, 'data')
    output.seek(0)
    return zipfile.ZipFile(output)


class UpdateTests(unittest.TestCase):
    def test_version_comparison(self):
        self.assertGreater(version_tuple('0.2.0'), version_tuple('0.1.9'))
        with self.assertRaises(ValueError): version_tuple('v0.2')

    def test_reject_traversal_and_surprises(self):
        for names in (['../main.py', 'requirements.txt'],
                      ['jarvis_v0.3/main.py', 'jarvis_v0.3/requirements.txt', 'jarvis_v0.3/setup.exe'],
                      ['jarvis_v0.3/main.py', 'jarvis_v0.3/requirements.txt', 'jarvis_v0.3/jarvis/../bad.py']):
            with self.subTest(names=names), archive(names) as zipped:
                with self.assertRaises(ValueError): archive_files(zipped)

    def test_release_accepted(self):
        with archive(['JARVIS_v0.3/main.py','JARVIS_v0.3/requirements.txt',
                      'JARVIS_v0.3/jarvis/core.py', 'JARVIS_v0.3/jarvis/web/index.html']) as zipped:
            self.assertEqual(len(archive_files(zipped)), 4)

    def test_no_source_is_honest(self):
        with tempfile.TemporaryDirectory() as folder:
            client = UpdateClient(folder)
            client.source = ''
            result = client.check('0.2.0')
            self.assertFalse(result['available'])
            self.assertIn('henüz', result['message'])

    def test_notes_survive_new_client(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'memory.sqlite3'
            Memory(path).add_note('SquadCraft üzerinde çalış')
            self.assertEqual(Memory(path).notes()[0][1], 'SquadCraft üzerinde çalış')

    def test_apply_rollback_on_dependency_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = root / 'project'
            stage = root / 'stage'
            project.mkdir()
            stage.mkdir()
            (project / 'main.py').write_text('old')
            (project / 'requirements.txt').write_text('old deps')
            archive_path = stage / 'release.zip'
            with zipfile.ZipFile(archive_path, 'w') as zipped:
                zipped.writestr('main.py', 'new')
                zipped.writestr('requirements.txt', 'new deps')
            with patch('jarvis.update_worker.subprocess.run', side_effect=subprocess.CalledProcessError(1, 'pip')):
                with self.assertRaises(subprocess.CalledProcessError):
                    apply(archive_path, project, stage)
            self.assertEqual((project / 'main.py').read_text(), 'old')
            self.assertEqual((project / 'requirements.txt').read_text(), 'old deps')


if __name__ == '__main__':
    unittest.main()
