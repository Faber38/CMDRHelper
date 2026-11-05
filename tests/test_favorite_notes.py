"""Favorite notes survive editing and SQLite reloads as literal plain text."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.favorites import FavoriteStore
from cmdrhelper.ui.favorites_view import FavoriteDialog


class FavoriteNoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db = CMDRDatabase(Path(temp.name) / 'synthetic.db')
        with self.db._connect() as con:
            con.executemany('INSERT INTO commanders(id,fid) VALUES (?,?)',
                            [(1, 'SYNTHETIC-1'), (2, 'SYNTHETIC-2')])
        self.store = FavoriteStore(self.db)
        self.state = SimpleNamespace(commander_id=1, commander_fid='SYNTHETIC-1')

    def record(self, note):
        return dict(commander_id=1, type='system', system_name='Synthetic Sol',
                    name='Synthetic favorite', category='bio', note=note)

    def dialog(self, record):
        dialog = FavoriteDialog(self.store, self.state, record)
        self.addCleanup(dialog.close)
        return dialog

    def assert_stored(self, record, note):
        with self.db._connect() as con:
            raw = con.execute('SELECT note FROM favorites WHERE id=?',
                              (record['id'],)).fetchone()[0]
        self.assertEqual(raw, note)
        self.assertEqual(self.store.get(1, record['id'])['note'], note)
        self.assertEqual(next(r for r in self.store.list(1)
                              if r['id'] == record['id'])['note'], note)
        self.assertEqual((record['name'], record['category'], record['commander_id']),
                         ('Synthetic favorite', 'bio', 1))
        with self.assertRaises(ValueError):
            self.store.get(2, record['id'])

    def test_repeated_open_edit_save_preserves_whitespace(self):
        cases = ('A\nB', 'A\nB\nC', 'A\n\n\nB', '\n\nA\n\nB\n\n',
                 '\n\n\n', '', '  A  \n\n  B  ')
        for original in cases:
            with self.subTest(note=repr(original)):
                dialog = self.dialog(self.record(original))
                self.assertEqual(dialog.note.toPlainText(), original)
                dialog._save()
                saved = dialog.saved
                expected = original
                self.assert_stored(saved, expected)
                for addition in ('', '\n\nErgänzung\n\n', ''):
                    reopened = self.dialog(self.store.get(1, saved['id']))
                    self.assertEqual(reopened.note.toPlainText(), expected)
                    reopened.note.moveCursor(QTextCursor.End)
                    reopened.note.insertPlainText(addition)
                    expected += addition
                    reopened._save()
                    self.assert_stored(reopened.saved, expected)
                    self.assertEqual(reopened.saved['id'], saved['id'])

    def test_html_like_notes_remain_literal_plain_text(self):
        note = '\n<b>Keine Formatierung</b>\n\n<Hinweis> & Text\n'
        dialog = self.dialog(self.record(note))
        self.assertFalse(dialog.note.acceptRichText())
        self.assertEqual(dialog.note.toPlainText(), note)
        dialog._save()
        self.assert_stored(dialog.saved, note)
        reopened = self.dialog(dialog.saved)
        self.assertEqual(reopened.note.toPlainText(), note)

    def test_return_and_enter_insert_breaks_without_saving(self):
        for key in (Qt.Key_Return, Qt.Key_Enter):
            with self.subTest(key=key):
                dialog = self.dialog(self.record(''))
                dialog.show()
                dialog.note.setFocus()
                self.app.processEvents()
                QTest.keyClicks(dialog.note, 'A')
                for _ in range(3):
                    QTest.keyClick(dialog.note, key)
                QTest.keyClicks(dialog.note, 'B')
                self.assertEqual(dialog.note.toPlainText(), 'A\n\n\nB')
                self.assertIsNone(dialog.saved)
                self.assertTrue(dialog.isVisible())
                dialog._save()
                self.assert_stored(dialog.saved, 'A\n\n\nB')
                self.assertEqual(self.dialog(dialog.saved).note.toPlainText(), 'A\n\n\nB')

    def test_store_preserves_note_but_keeps_name_category_normalization(self):
        note = '\n\n  A\n\n\nB  \n\n'
        values = self.record(note)
        values.update(name='  Synthetic favorite  ', category='  bio  ')
        saved = self.store.save(1, values)
        self.assert_stored(saved, note)
        updated = self.store.save(1, dict(values, commander_id=2), saved['id'])
        self.assert_stored(updated, note)
        omitted = self.store.save(1, {'name': '  Synthetic favorite  '}, saved['id'])
        self.assert_stored(omitted, note)
        fallback = self.store.save(1, dict(values, category='   '))
        self.assertEqual(fallback['category'], 'other')

    def test_new_process_reloads_sqlite_and_opens_note_unchanged(self):
        note = '\n\n  A\nB\n\n\nC <b>literal</b>  \n\n'
        dialog = self.dialog(self.record(note))
        dialog._save()
        script = '''
import json, sys
from types import SimpleNamespace
from PySide6.QtWidgets import QApplication
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.favorites import FavoriteStore
from cmdrhelper.ui.favorites_view import FavoriteDialog
app = QApplication([])
store = FavoriteStore(CMDRDatabase(sys.argv[1]))
record = store.get(1, sys.argv[2])
dialog = FavoriteDialog(store, SimpleNamespace(commander_id=1, commander_fid='SYNTHETIC-1'), record)
text = dialog.note.toPlainText()
dialog._save()
print(json.dumps({'loaded': record, 'displayed': text, 'saved': dialog.saved}))
'''
        result = subprocess.run(
            [sys.executable, '-c', script, str(self.db.path), dialog.saved['id']],
            cwd=Path(__file__).resolve().parents[1],
            env=dict(os.environ, QT_QPA_PLATFORM='offscreen', PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True, check=True, timeout=30)
        reloaded = json.loads(result.stdout)
        self.assertEqual(reloaded['displayed'], note)
        for record in (reloaded['loaded'], reloaded['saved']):
            self.assertEqual(record['note'], note)
            self.assert_stored(record, note)


if __name__ == '__main__':
    unittest.main()
