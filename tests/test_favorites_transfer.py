import json
import os
from io import BytesIO
from pathlib import Path, PureWindowsPath, PurePosixPath
import sqlite3
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
import warnings
from unittest.mock import patch, Mock
from zipfile import ZipFile, ZipInfo

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PIL import Image
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QDialog, QComboBox
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.favorites import FavoriteStore
from cmdrhelper.favorites_transfer import (
    FIELDS, serialize_favorites, deserialize_favorites, favorite_identity,
    export_package, read_package, prepare_import, apply_import, TransferError)
from cmdrhelper.ui.favorites_view import FavoritesView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.i18n import _TRANSLATIONS, set_language


class FavoritesTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = CMDRDatabase(self.root / 'app.db')
        with self.db._connect() as con:
            con.executemany('INSERT INTO commanders(id,fid) VALUES (?,?)', [(1, 'F1'), (2, 'F2')])
        self.store = FavoriteStore(self.db)
        self.state = SimpleNamespace(database=self.db, commander_id=1, system='Sol', system_address=0,
            settings=SimpleNamespace(value=lambda k, d=None: d, setValue=Mock()))

    def save(self, kind='surface_location', image=None, **changes):
        values = dict(type=kind, name='Ä crater 星', system_name='Sol', system_address=10477373803,
                      body_name='Sol 1', body_id=0, latitude=12.123456789012345,
                      longitude=-179.99999999999997, category='geo', note='Line 1\nLine 2')
        values.update(changes)
        return self.store.save(1, values, image_source=image)

    def image(self):
        path = self.root / 'original.png'
        Image.new('RGB', (12, 12), 'red').save(path)
        return path

    def archive(self, manifest, entries=None):
        output = self.root / 'input.zip'
        with ZipFile(output, 'w') as archive:
            archive.writestr('favorites.json', manifest if isinstance(manifest, str) else json.dumps(manifest))
            for name, data in (entries or {}).items():
                archive.writestr(name, data)
        return output

    def plan(self, path, commander=2):
        records, images, missing = read_package(path)
        return prepare_import(self.store, commander, records, images, missing)

    def exported(self):
        data, counts = export_package(self.store, 1)
        path = self.root / 'export.zip'
        path.write_bytes(data)
        return path, counts

    def view(self):
        view = FavoritesView(self.state, Mock(), Mock())
        self.addCleanup(view.close)
        return view

    def test_empty_export(self):
        path, counts = self.exported()
        self.assertEqual(counts, dict(count=0, images=0, missing=0))
        plan = self.plan(path)
        self.assertEqual(apply_import(self.store, plan), dict(added=0, updated=0, skipped=0))

    def test_all_types_round_trip_exact_values_and_private_fields(self):
        for kind in ('system', 'body', 'surface_location'):
            self.save(kind)
        path, counts = self.exported()
        with ZipFile(path) as archive:
            raw = archive.read('favorites.json').decode('utf-8')
            data = json.loads(raw)
        self.assertIn('Ä crater 星', raw)
        self.assertEqual(data['format'], 'CMDRHelperFavorites')
        self.assertEqual(data['format_version'], 1)
        self.assertEqual(data['favorite_count'], 3)
        self.assertTrue(data['created_at']); self.assertTrue(data['cmdrhelper_version'])
        self.assertEqual(set(data['favorites'][0]), set(FIELDS))
        self.assertNotIn('commander_id', raw)
        self.assertNotIn('"id"', raw)
        self.assertNotIn('F1', raw)
        original = sorted(self.store.list(1), key=lambda r: r['type'])
        apply_import(self.store, self.plan(path))
        imported = sorted(self.store.list(2), key=lambda r: r['type'])
        self.assertEqual([{k: r[k] for k in FIELDS} for r in original],
                         [{k: r[k] for k in FIELDS} for r in imported])
        self.assertTrue(set(r['id'] for r in original).isdisjoint(r['id'] for r in imported))

    def test_image_round_trip_deduplicated_and_portable(self):
        source = self.image(); original = source.read_bytes()
        self.save(image=source)
        self.save('body', image=source)
        path, counts = self.exported()
        self.assertEqual(counts, dict(count=2, images=1, missing=0))
        with ZipFile(path) as archive:
            names = archive.namelist()
            self.assertEqual(len(names), 2)
            reference = names[1]
            self.assertFalse(PureWindowsPath(reference).is_absolute())
            self.assertFalse(PurePosixPath(reference).is_absolute())
            self.assertNotIn('\\', reference)
            self.assertEqual(archive.read(reference), original)
        apply_import(self.store, self.plan(path))
        rows = self.store.list(2)
        self.assertEqual(len(set(r['image_path'] for r in rows)), 1)
        for row in rows:
            self.assertEqual(self.store.image_file(row['image_path']).read_bytes(), original)
            self.assertNotIn(row['image_path'], [r['image_path'] for r in self.store.list(1)])
        self.assertEqual(source.read_bytes(), original)
        # Imported images can themselves be exported again without data loss.
        second, result = export_package(self.store, 2)
        with ZipFile(BytesIO(second)) as archive:
            self.assertEqual(archive.read(reference), original)
        self.assertEqual(result['images'], 1)

    def test_missing_and_broken_export_images(self):
        row = self.save(image=self.image())
        self.store.image_file(row['image_path']).unlink()
        path, counts = self.exported()
        self.assertEqual(counts['missing'], 1)
        apply_import(self.store, self.plan(path))
        self.assertEqual(self.store.list(2)[0]['image_path'], '')
        row = self.save('body', image=self.image())
        self.store.image_file(row['image_path']).write_bytes(b'broken')
        self.assertEqual(self.exported()[1]['missing'], 2)

    def test_missing_and_broken_import_images(self):
        row = self.save()
        for content in (None, b'not an image'):
            with self.subTest(content=content):
                data = json.loads(serialize_favorites([row]))
                data['favorites'][0]['image_path'] = 'images/missing.png'
                entries = {} if content is None else {'images/missing.png': content}
                plan = self.plan(self.archive(data, entries))
                self.assertEqual(plan.missing_images, 1)
                apply_import(self.store, plan, 'new')
                self.assertTrue(all(r['image_path'] == '' for r in self.store.list(2)))

    def test_invalid_json_format_version_and_fields_leave_db_unchanged(self):
        row = self.save()
        valid = json.loads(serialize_favorites([row]))
        bad = ['{', '[]', '{"format":NaN}', '{"format":1,"format":2}']
        for change in ({'format': 'foreign'}, {'format_version': 2}, {'format_version': True},
                       {'favorites': None}, {'favorite_count': 22}):
            bad.append(dict(valid, **change))
        for change in ({'name': ''}, {'latitude': '1,2'}, {'longitude': 181}, {'body_id': True},
                       {'system_address': 2**63}, {'created_at': 'yesterday'}, {'note': []}):
            bad.append(dict(valid, favorites=[dict(valid['favorites'][0], **change)]))
        for value in bad:
            with self.subTest(value=value), self.assertRaises(TransferError):
                self.plan(self.archive(value))
            self.assertEqual(self.store.list(1), [row])
            self.assertEqual(self.store.list(2), [])
        with self.assertRaisesRegex(TransferError, 'unsupported_version'):
            deserialize_favorites(json.dumps(dict(valid, format_version=999)))
        # One invalid row invalidates the whole file.
        with self.assertRaises(TransferError):
            self.plan(self.archive(dict(valid, favorite_count=2, favorites=[valid['favorites'][0], {}])))
        self.assertEqual(self.store.list(2), [])

    def test_unknown_extra_fields_are_ignored(self):
        row = self.save()
        data = json.loads(serialize_favorites([row]))
        data['future'] = {'anything': [1, 2]}
        data['favorites'][0]['future'] = 'ignored'
        apply_import(self.store, self.plan(self.archive(data)))
        self.assertEqual(self.store.list(2)[0]['note'], row['note'])

    def test_duplicate_policies(self):
        row = self.save()
        incoming = dict(row, note='updated note', updated_at='2026-09-14T12:00:00+00:00')
        for policy, counts in [('skip', (0, 0, 1)), ('replace', (0, 1, 0)), ('new', (1, 0, 0))]:
            plan = prepare_import(self.store, 1, [incoming])
            self.assertEqual((plan.new_count, plan.duplicate_count), (0, 1))
            result = apply_import(self.store, plan, policy)
            self.assertEqual(tuple(result.values()), counts)
            if policy == 'skip':
                self.assertEqual(self.store.get(1, row['id']), row)
            elif policy == 'replace':
                self.assertEqual(self.store.get(1, row['id'])['note'], 'updated note')
                self.assertEqual(self.store.get(1, row['id'])['updated_at'], incoming['updated_at'])
        self.assertEqual(len(self.store.list(1)), 2)

    def test_identity_uses_location_type_category_and_name(self):
        row = self.save()
        identity = favorite_identity(row)
        for key, value in [('system_address', 4), ('body_id', 1), ('latitude', 0),
                           ('longitude', 0), ('category', 'bio'), ('name', 'Else')]:
            self.assertNotEqual(identity, favorite_identity(dict(row, **{key: value})))
        self.assertEqual(identity, favorite_identity(dict(row, system_name='translated', body_name='changed')))
        fallback = dict(row, system_address=None, body_id=None)
        self.assertNotEqual(favorite_identity(fallback), favorite_identity(dict(fallback, system_name='Other')))
        self.assertNotEqual(favorite_identity(fallback), favorite_identity(dict(fallback, body_name='Other')))
        self.assertNotEqual(favorite_identity(self.save('system')), favorite_identity(self.save('body')))

    def test_duplicates_inside_package(self):
        row = self.save()
        plan = prepare_import(self.store, 2, [row, row])
        self.assertEqual((plan.new_count, plan.duplicate_count), (1, 1))
        self.assertEqual(apply_import(self.store, plan), dict(added=1, updated=0, skipped=1))

    def test_zip_rejects_paths_symlinks_duplicates_and_external_references(self):
        manifest = serialize_favorites([self.save()])
        for name in ('../escape', '/absolute', 'C:/temp/image.png', 'images/../escape',
                     'images\\escape', '//server/share', './image', 'images//file'):
            with self.subTest(name=name), self.assertRaises(TransferError):
                self.plan(self.archive(manifest, {name: b'bad'}))
        data = json.loads(manifest)
        for reference in ('../x', 'C:\\Users\\x.png', '/home/user/x.png', 'https://example.com/x.png'):
            data['favorites'][0]['image_path'] = reference
            with self.subTest(reference=reference), self.assertRaises(TransferError):
                self.plan(self.archive(data))
        path = self.archive(manifest)
        with ZipFile(path, 'a') as archive:
            symlink = ZipInfo('images/link')
            symlink.create_system = 3
            symlink.external_attr = 0o120777 << 16
            archive.writestr(symlink, '/etc/passwd')
        with self.assertRaises(TransferError):
            self.plan(path)
        path = self.archive(manifest)
        with ZipFile(path, 'a') as archive, warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            archive.writestr('favorites.json', manifest)
        with self.assertRaises(TransferError):
            self.plan(path)
        with patch('cmdrhelper.favorites_transfer.MAX_MEMBER_SIZE', 10), self.assertRaises(TransferError):
            self.plan(self.archive(manifest))
        self.assertEqual(self.store.list(2), [])

    def test_skipping_duplicates_does_not_copy_images(self):
        row = self.save(image=self.image())
        path, _ = self.exported()
        before = sorted(self.store.images.iterdir())
        with patch.object(self.store, '_copy_image', side_effect=AssertionError('unexpected copy')):
            result = apply_import(self.store, self.plan(path, 1))
        self.assertEqual(result['skipped'], 1)
        self.assertEqual(self.store.get(1, row['id']), row)
        self.assertEqual(sorted(self.store.images.iterdir()), before)

    def test_copy_failure_rolls_back_rows_and_images(self):
        self.save(image=self.image())
        second = self.root / 'second.png'
        Image.new('RGB', (12, 12), 'blue').save(second)
        self.save('body', image=second, name='ZZ last')
        path, _ = self.exported()
        before = sorted(self.store.images.iterdir())
        copy = self.store._copy_image
        calls = []
        def fail_second(*args):
            calls.append(args)
            if len(calls) == 2:
                raise OSError('disk full')
            return copy(*args)
        with patch.object(self.store, '_copy_image', side_effect=fail_second), self.assertRaises(OSError):
            apply_import(self.store, self.plan(path))
        self.assertEqual(self.store.list(2), [])
        self.assertEqual(sorted(self.store.images.iterdir()), before)

    def test_rollback_removes_copied_images_and_restores_replacements(self):
        self.save(image=self.image())
        self.save('body', image=self.image(), name='ZZ failure')
        path, _ = self.exported()
        # A real SQL error after the first successful INSERT.
        with self.db._connect() as con:
            con.execute("""CREATE TRIGGER fail_import BEFORE INSERT ON favorites
                WHEN NEW.commander_id=2 AND NEW.name='ZZ failure'
                BEGIN SELECT RAISE(ABORT, 'forced failure'); END""")
        before_images = sorted(self.store.images.iterdir())
        before_rows = self.store.list(1)
        with self.assertRaises(sqlite3.IntegrityError):
            apply_import(self.store, self.plan(path))
        self.assertEqual(self.store.list(2), [])
        self.assertEqual(self.store.list(1), before_rows)
        self.assertEqual(sorted(self.store.images.iterdir()), before_images)
        with self.db._connect() as con:
            con.execute("""CREATE TRIGGER fail_update BEFORE UPDATE ON favorites
                WHEN NEW.name='ZZ failure' BEGIN SELECT RAISE(ABORT, 'forced failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            apply_import(self.store, self.plan(path, 1), 'replace')
        self.assertEqual(self.store.list(1), before_rows)
        self.assertEqual(sorted(self.store.images.iterdir()), before_images)

    def test_stale_plan_rejected(self):
        row = self.save()
        plan = prepare_import(self.store, 1, [row])
        self.store.save(1, dict(note='concurrent edit'), row['id'])
        before = self.store.list(1)
        with self.assertRaisesRegex(TransferError, 'changed'):
            apply_import(self.store, plan, 'replace')
        self.assertEqual(self.store.list(1), before)

    def test_ui_export_ignores_filters_and_reports_counts(self):
        self.save(); self.save('body')
        view = self.view()
        view.search.setText('no matches')
        view.kind.setCurrentIndex(1)
        view.distance_filter.setChecked(True)
        destination = self.root / 'result.zip'
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(destination), '')) as dialog, \
                patch.object(QMessageBox, 'information') as message:
            view.export_favorites()
        self.assertTrue(dialog.call_args.args[2].startswith('CMDRHelper_Favoriten_'))
        self.assertTrue(dialog.call_args.args[2].endswith('.zip'))
        self.assertNotIn('options', dialog.call_args.kwargs)  # Default overwrite confirmation.
        self.assertEqual(len(read_package(destination)[0]), 2)
        message.assert_called_once()
        self.assertEqual(view.search.text(), 'no matches')
        self.assertTrue(view.distance_filter.isChecked())

    def test_ui_cancel_and_commander_switch(self):
        self.save(); path, _ = self.exported(); view = self.view()
        before = self.store.list(1)
        with patch.object(QFileDialog, 'getSaveFileName', return_value=('', '')), \
                patch('cmdrhelper.ui.favorites_view.export_package') as export:
            view.export_favorites(); export.assert_not_called()
        with patch.object(QFileDialog, 'getOpenFileName', return_value=('', '')), \
                patch.object(view, '_confirm_import') as confirm:
            view.import_favorites(); confirm.assert_not_called()
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(path), '')), \
                patch.object(view, '_confirm_import', return_value=None):
            view.import_favorites()
        self.assertEqual(before, self.store.list(1))
        def switch(_):
            self.state.commander_id = 2
            return 'new'
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(path), '')), \
                patch.object(view, '_confirm_import', side_effect=switch), \
                patch.object(QMessageBox, 'warning') as message:
            view.import_favorites()
        message.assert_called_once()
        self.assertEqual(self.store.list(2), [])

    def test_ui_import_success_and_validation_error(self):
        self.save(); path, _ = self.exported(); view = self.view()
        self.state.commander_id = 2
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(path), '')), \
                patch.object(view, '_confirm_import', return_value='skip'), \
                patch.object(QMessageBox, 'information') as message:
            view.import_favorites()
        self.assertEqual(view.list.count(), 1); message.assert_called_once()
        path.write_bytes(b'bad zip')
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(path), '')), \
                patch.object(view, '_confirm_import') as confirm, \
                patch.object(QMessageBox, 'warning') as message:
            view.import_favorites()
        confirm.assert_not_called(); message.assert_called_once()
        self.assertEqual(len(self.store.list(2)), 1)

    def test_dialog_options_themes_and_twelve_languages(self):
        row = self.save(); plan = prepare_import(self.store, 1, [row])
        view = self.view()
        self.addCleanup(set_language, 'de')
        for language, table in _TRANSLATIONS.items():
            set_language(language)
            self.assertEqual(len([k for k in table if k.startswith('favorites.transfer.')]), 18)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                view.setStyleSheet(theme)
                view.resize(1100, 800); view.show(); self.app.processEvents()
                self.assertTrue(view.export_button.isVisible())
                self.assertTrue(view.import_button.isVisible())
                self.assertFalse(view.grab().isNull())
                def inspect(dialog):
                    dialog.show(); self.app.processEvents()
                    combo = dialog.findChild(QComboBox)
                    self.assertEqual([combo.itemData(i) for i in range(combo.count())], ['skip', 'replace', 'new'])
                    self.assertEqual(combo.currentData(), 'skip')
                    self.assertFalse(dialog.grab().isNull())
                    dialog.close()
                    return QDialog.Rejected
                with patch.object(QDialog, 'exec', inspect):
                    self.assertIsNone(view._confirm_import(plan))


if __name__ == '__main__':
    unittest.main()
