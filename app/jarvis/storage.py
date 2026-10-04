"""Local persistent memory; no conversation or credential logging."""
import os
import sqlite3
from datetime import datetime
from pathlib import Path


from contextlib import contextmanager


def data_dir():
    root = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share')) / 'Jarvis'
    root.mkdir(parents=True, exist_ok=True)
    return root


class Memory:
    def __init__(self, path=None):
        self.path = str(path or data_dir() / 'memory.sqlite3')
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY, body TEXT NOT NULL,
                    due TEXT NOT NULL, delivered INTEGER NOT NULL DEFAULT 0);
            ''')

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def add_note(self, text):
        with self.connect() as db:
            db.execute('INSERT INTO notes(body) VALUES (?)', (text,))

    def notes(self):
        with self.connect() as db:
            return db.execute('SELECT id, body FROM notes ORDER BY id DESC LIMIT 100').fetchall()

    def delete_note(self, note_id):
        with self.connect() as db:
            return db.execute('DELETE FROM notes WHERE id=?', (note_id,)).rowcount

    def remind(self, text, due):
        with self.connect() as db:
            db.execute('INSERT INTO reminders(body,due) VALUES (?,?)', (text, due.isoformat()))

    def pending_reminders(self):
        with self.connect() as db:
            return db.execute('SELECT id,body,due FROM reminders WHERE delivered=0 ORDER BY due LIMIT 100').fetchall()

    def cancel_reminder(self, reminder_id):
        with self.connect() as db:
            return db.execute('DELETE FROM reminders WHERE id=? AND delivered=0', (reminder_id,)).rowcount

    def due(self, now=None):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute('SELECT id,body FROM reminders WHERE delivered=0 AND due<=?',
                              ((now or datetime.now()).isoformat(),)).fetchall()
            db.executemany('UPDATE reminders SET delivered=1 WHERE id=?', [(r[0],) for r in rows])
        return rows
