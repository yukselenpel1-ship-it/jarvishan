"""Separate process applies a verified update after the UI exits."""
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path


def wait_for_exit(pid, timeout=25):
    if os.name != 'nt':
        return
    import ctypes
    kernel = ctypes.windll.kernel32
    handle = kernel.OpenProcess(0x00100000, False, pid)
    if handle:
        try:
            result = kernel.WaitForSingleObject(handle, timeout * 1000)
            if result == 0x102:
                raise TimeoutError('JARVIS kapanmadı; güncelleme ertelendi')
        finally:
            kernel.CloseHandle(handle)


def apply(archive, project, stage):
    # This copy lives in the stage directory so replacing jarvis/ is safe.
    from zipfile import ZipFile
    from pathlib import Path
    project, stage = Path(project), Path(stage)
    backup = stage / 'backup'
    backup.mkdir()
    with ZipFile(archive) as zipped:
        # Same file allowlist as the staging checker.
        allowed = {'main.py', 'requirements.txt', 'KURULUM.bat', 'BASLAT.bat',
                   'OTOMATIK_BASLAT.ps1', 'KISAYOL.ps1', 'README.md', 'TEST_RAPORU.md',
                   'YAYIN_REHBERI.md', 'tests/test_core.py', 'tests/test_voice.py',
                   'tests/test_updates.py', 'tests/test_agent.py', 'update_source.txt'}
        files = []
        for entry in zipped.infolist():
            if entry.is_dir(): continue
            parts = Path(entry.filename.replace('\\', '/')).parts
            if parts and parts[0].lower().startswith('jarvis_v'): parts = parts[1:]
            if not parts or '..' in parts or entry.filename.startswith('/') or ':' in entry.filename: raise ValueError('Path')
            rel = Path(*parts)
            if rel.as_posix() not in allowed and not (parts[0] == 'jarvis' and len(parts) > 1 and '__pycache__' not in parts): raise ValueError('File')
            files.append((entry, rel))
        touched = []
        try:
            for entry, rel in files:
                dest = project / rel
                previous = backup / rel
                if dest.exists():
                    previous.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dest, previous)
                dest.parent.mkdir(parents=True, exist_ok=True)
                temp = dest.with_name(dest.name + '.jarvis-new')
                with zipped.open(entry) as source, temp.open('wb') as out:
                    shutil.copyfileobj(source, out)
                os.replace(temp, dest)
                touched.append((dest, previous))
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(project / 'requirements.txt')],
                           check=True, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            for dest, previous in reversed(touched):
                if previous.exists(): shutil.copy2(previous, dest)
                else: dest.unlink(missing_ok=True)
            raise


if __name__ == '__main__':
    project, pid, stage = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    try:
        wait_for_exit(pid)
        apply(stage / 'release.zip', project, stage)
    except Exception as exc:
        (stage / 'update-error.txt').write_text(str(exc), encoding='utf-8')
    finally:
        # The app is restarted whether the update succeeded or was rolled back.
        subprocess.Popen([sys.executable, str(project / 'main.py')], cwd=str(project))
