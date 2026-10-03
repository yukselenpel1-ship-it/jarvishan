"""Release manifest checker and checked update staging. Publishing is external."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


MAX_ARCHIVE = 40 * 1024 * 1024
ALLOWED = {'main.py', 'requirements.txt', 'KURULUM.bat', 'BASLAT.bat',
           'OTOMATIK_BASLAT.ps1', 'KISAYOL.ps1', 'README.md', 'TEST_RAPORU.md',
           'YAYIN_REHBERI.md', 'tests/test_core.py', 'tests/test_voice.py',
           'tests/test_updates.py', 'update_source.txt'}


def version_tuple(value):
    parts = value.split('.')
    if len(parts) != 3 or not all(x.isdigit() for x in parts):
        raise ValueError('Sürüm biçimi hatalı')
    return tuple(int(x) for x in parts)


def archive_files(zipped):
    files = []
    for entry in zipped.infolist():
        if entry.is_dir():
            continue
        parts = Path(entry.filename.replace('\\', '/')).parts
        if not parts or '..' in parts or entry.filename.startswith('/') or ':' in entry.filename:
            raise ValueError('Güvensiz dosya yolu')
        # Publisher's zip may wrap all content in one JARVIS_vX.Y directory.
        if parts[0].lower().startswith('jarvis_v'):
            parts = parts[1:]
        if not parts:
            continue
        rel = Path(*parts)
        if rel.as_posix() not in ALLOWED and not (parts[0] == 'jarvis' and len(parts) > 1
                                                  and '__pycache__' not in parts):
            raise ValueError('Beklenmeyen güncelleme dosyası: ' + rel.as_posix())
        if entry.file_size > MAX_ARCHIVE:
            raise ValueError('Dosya çok büyük')
        files.append((entry, rel))
    if not files or not {'main.py', 'requirements.txt'}.issubset({str(rel) for _, rel in files}):
        raise ValueError('Güncelleme paketi eksik')
    if sum(entry.file_size for entry, _ in files) > MAX_ARCHIVE:
        raise ValueError('Paket çok büyük')
    return files


class UpdateClient:
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        source_file = Path(__file__).resolve().parent.parent / 'update_source.txt'
        self.source = os.environ.get('JARVIS_UPDATE_URL') or (
            source_file.read_text(encoding='utf-8').strip() if source_file.exists() else '')
        self.latest = None

    @staticmethod
    def _get(url, limit):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.username or parsed.password or not parsed.hostname:
            raise ValueError('Güncelleme için HTTPS adresi gerekir')
        request = urllib.request.Request(url, headers={'User-Agent': 'Jarvis-Windows-Update/0.2'})
        with urllib.request.urlopen(request, timeout=20) as response:
            if urllib.parse.urlsplit(response.url).scheme != 'https':
                raise ValueError('Güvenli olmayan yönlendirme')
            result = response.read(limit + 1)
        if len(result) > limit:
            raise ValueError('Güncelleme boyut sınırı aşıldı')
        return result

    def check(self, current):
        if not self.source:
            return {'available': False, 'message': 'Güncelleme yayını henüz bağlanmadı. Şu an otomatik güncelleme kullanılamıyor.'}
        try:
            manifest = json.loads(self._get(self.source, 16 * 1024))
            version = manifest['version']
            url = manifest['url']
            digest = manifest['sha256']
            if not isinstance(version, str) or not isinstance(url, str) or not isinstance(digest, str) or len(digest) != 64:
                raise ValueError('Güncelleme bilgisi geçersiz')
            if not all(x in '0123456789abcdef' for x in digest.lower()):
                raise ValueError('Özet hatalı')
            if urllib.parse.urlsplit(url).scheme != 'https':
                raise ValueError('Güvenli indirme adresi gerekir')
            available = version_tuple(version) > version_tuple(current)
            self.latest = manifest if available else None
            return {'available': available, 'message': f'Yeni sürüm v{version} hazır.' if available else 'JARVIS güncel.'}
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            self.latest = None
            return {'available': False, 'message': 'Güncelleme kontrol edilemedi. Yayın adresini ve internet bağlantını kontrol et.'}

    def prepare(self, current):
        check = self.check(current)
        if not check['available']:
            return {'ok': False, 'message': check['message']}
        stage = Path(tempfile.mkdtemp(prefix='jarvis-update-', dir=self.data_path))
        try:
            data = self._get(self.latest['url'], MAX_ARCHIVE)
            digest = hashlib.sha256(data).hexdigest()
            if digest.lower() != self.latest['sha256'].lower():
                raise ValueError('Paket doğrulaması başarısız')
            archive = stage / 'release.zip'
            archive.write_bytes(data)
            with zipfile.ZipFile(archive) as zipped:
                archive_files(zipped)
                if zipped.testzip() is not None:
                    raise ValueError('Bozuk paket')
            shutil.copy2(Path(__file__).resolve().parent / 'update_worker.py', stage / 'worker.py')
            return {'ok': True, 'message': 'Güncelleme hazır.', 'stage': str(stage)}
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            return {'ok': False, 'message': 'Güncelleme indirilemedi veya doğrulanamadı.'}

    @staticmethod
    def launch_installer(stage, pid):
        project = Path(__file__).resolve().parent.parent
        kwargs = {'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {}
        subprocess.Popen([sys.executable, str(Path(stage) / 'worker.py'), str(project),
                          str(pid), str(stage)], cwd=str(project),
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, **kwargs)
