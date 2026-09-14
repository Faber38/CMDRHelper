import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from PySide6.QtCore import QObject, Signal, QSettings, Qt
from PySide6.QtWidgets import QApplication

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.favorites import FavoriteStore
from cmdrhelper.ui.favorites_view import FavoritesView, stored_coordinates
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class State(QObject):
    changed = Signal()
    positionChanged = Signal(str, object, str)
    commanderIdentityChanged = Signal(object, str, str)


class FavoritesDistanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.state = State()
        self.state.database = CMDRDatabase(root / 'app.db')
        self.state.settings = QSettings(str(root / 'settings.ini'), QSettings.IniFormat)
        self.state.commander_id = 1
        self.state.system = 'Origin'
        self.state.system_address = 0
        with self.state.database._connect() as con:
            con.execute("INSERT INTO commanders(id,fid) VALUES (1,'F1')")
            con.executemany('INSERT INTO systems(system_address,name,x,y,z) VALUES (?,?,?,?,?)', [
                (0, 'Origin', 0, 0, 0), (1, 'Near', 100, 0, 0),
                (2, 'Below', 499.9, 0, 0), (3, 'Boundary', 300, 400, 0),
                (4, 'Above', 500.1, 0, 0), (5, 'Unknown', None, None, None),
                (6, 'Next', 1000, 0, 0),
            ])
        self.store = FavoriteStore(self.state.database)
        for address, name in enumerate(('Near', 'Below', 'Boundary', 'Above', 'Unknown'), 1):
            self.store.save(1, dict(type='system', system_address=address,
                                   system_name=name, name=name, category='bio', note=''))
        self.view = self.make_view()

    def make_view(self):
        view = FavoritesView(self.state, Mock(), Mock(), route_callback=Mock())
        self.addCleanup(view.close)
        return view

    def names(self):
        return {self.view.list.item(i).text().split('\n')[0] for i in range(self.view.list.count())}

    def test_disabled_boundaries_unknown_and_unchanged_storage(self):
        before = self.store.list(1)
        self.assertFalse(self.view.distance_filter.isChecked())
        self.assertEqual(self.view.max_distance.value(), 500)
        self.assertEqual(len(self.names()), 5)
        self.view.distance_filter.setChecked(True)
        self.assertEqual(self.names(), {'Near', 'Below', 'Boundary', 'Unknown'})
        unknown = next(self.view.list.item(i) for i in range(self.view.list.count())
                       if self.view.list.item(i).text().startswith('Unknown\n'))
        self.assertTrue(unknown.text().endswith('—'))
        self.view.distance_filter.setChecked(False)
        self.assertEqual(len(self.names()), 5)
        self.assertEqual(self.store.list(1), before)

    def test_unknown_reference_and_return_to_known(self):
        self.view.distance_filter.setChecked(True)
        self.state.system_address = 5
        self.state.system = 'Unknown'
        self.state.changed.emit()
        self.app.processEvents()
        self.assertEqual(len(self.names()), 5)
        self.assertFalse(self.view.distance_status.isHidden())
        self.assertTrue(self.view.distance_status.text())
        self.state.system_address = 0
        self.state.system = 'Origin'
        self.state.changed.emit()
        self.app.processEvents()
        self.assertNotIn('Above', self.names())
        self.assertTrue(self.view.distance_status.isHidden())

    def test_jump_before_snapshot_write_and_changed(self):
        self.view.distance_filter.setChecked(True)
        self.state.system, self.state.system_address = 'New', 7
        self.state.positionChanged.emit('New', 7, 'FSDJump')
        with self.state.database._connect() as con:
            con.execute("INSERT INTO systems(system_address,name,x,y,z) VALUES (7,'New',1000,0,0)")
        self.state.changed.emit()
        self.app.processEvents()
        self.assertEqual(self.names(), {'Above', 'Unknown'})
        self.assertTrue(self.view.distance_filter.isChecked())

    def test_filters_are_combined(self):
        self.store.save(1, dict(type='body', system_address=1, system_name='Near',
                               body_name='Near 1', name='Target', category='geo', note='needle'))
        self.store.save(1, dict(type='body', system_address=4, system_name='Above',
                               body_name='Above 1', name='Far target', category='geo', note='needle'))
        self.view.distance_filter.setChecked(True)
        self.view.kind.setCurrentIndex(self.view.kind.findData('body'))
        self.view.category.setCurrentIndex(self.view.category.findData('geo'))
        self.view.search.setText('needle')
        self.assertEqual(self.names(), {'Target'})
        self.view.distance_filter.setChecked(False)
        self.assertEqual(self.names(), {'Target', 'Far target'})
        self.view.search.setText('absent')
        self.assertEqual(self.names(), set())

    def test_qsettings_reloaded_from_disk(self):
        self.view.distance_filter.setChecked(True)
        self.view.max_distance.setValue(750.5)
        self.state.settings.sync()
        filename = self.state.settings.fileName()
        self.state.settings = QSettings(filename, QSettings.IniFormat)
        other = self.make_view()
        self.assertTrue(other.distance_filter.isChecked())
        self.assertEqual(other.max_distance.value(), 750.5)
        other.distance_filter.setChecked(False)
        self.state.settings.sync()
        self.state.settings = QSettings(filename, QSettings.IniFormat)
        restored = self.make_view()
        self.assertFalse(restored.distance_filter.isChecked())
        self.assertEqual(restored.max_distance.value(), 750.5)

    def test_coordinate_identity_validation_and_3d_distance(self):
        with self.state.database._connect() as con:
            origin = stored_coordinates(con, 0, 'Wrong name')
            self.assertEqual(origin.distance_to(stored_coordinates(con, 3, 'Boundary')), 500)
            self.assertEqual(stored_coordinates(con, None, 'near').x, 100)
            self.assertIsNone(stored_coordinates(con, 999, 'Near'))
            self.assertIsNone(stored_coordinates(con, None, 'Imagined system'))
            con.execute('UPDATE systems SET z=? WHERE system_address=1', (float('inf'),))
            self.assertIsNone(stored_coordinates(con, 1, 'Near'))
            con.execute('UPDATE systems SET x=0,y=0,z=100 WHERE system_address=1')
            self.assertEqual(origin.distance_to(stored_coordinates(con, 1, 'Near')), 100)

    def test_themes_and_route_keep_selected_identity(self):
        self.view.distance_filter.setChecked(True)
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.view.setStyleSheet(theme)
            self.view.resize(1000, 650)
            self.view.show()
            self.app.processEvents()
            self.view.list.setCurrentRow(0)
            record = self.view.selected()
            self.view.route_button.click()
            self.view.route_callback.assert_called_with(record['system_name'])
            self.assertTrue(self.view.distance_filter.isVisible())
            self.assertTrue(self.view.max_distance.isEnabled())
            self.assertGreaterEqual(self.view.max_distance.width(), self.view.max_distance.sizeHint().width())
            self.assertEqual(self.view.list.currentItem().data(Qt.UserRole), record['id'])


if __name__ == '__main__':
    unittest.main()
