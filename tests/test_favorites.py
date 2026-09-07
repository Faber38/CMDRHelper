import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PIL import Image
from PySide6.QtCore import QObject, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QMainWindow
from cmdrhelper.global_hotkey import GlobalHotkey
from cmdrhelper.ui.quick_favorite_settings import QuickFavoriteSettings
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.favorites import FavoriteStore, freeze_surface_location, latest_screenshot, navigate_to_favorite
from cmdrhelper.planet_navigation import PlanetNavigationController
from cmdrhelper.status_reader import StatusSnapshot
from cmdrhelper.ui.favorites_view import FavoriteDialog, FavoritesView, preview
from cmdrhelper.ui.planet_navigation_window import PlanetNavigationWindow
from cmdrhelper.ui.main_window import MainWindow


class State(QObject):
    commanderIdentityChanged = Signal(object,str,str)
    def __init__(self, database):
        super().__init__()
        self.database=database; self.commander_id=1; self.commander_fid='F1'
        self.system='Sol'; self.system_address=0
        self.system_bodies=[dict(name='Sol 1',body_id=0,body_type='Planet')]
        self.journal_folder=None
        self.values={}
        self.settings=SimpleNamespace(value=lambda key,default=None:self.values.get(key,default),
                                      setValue=lambda key,value:self.values.update({key:value}),sync=lambda:None)


class FavoriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.temp=TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.db=CMDRDatabase(self.root/'app.db')
        with self.db._connect() as con:
            con.executemany('INSERT INTO commanders(id,fid) VALUES (?,?)',[(1,'F1'),(2,'F2')])
        self.store=FavoriteStore(self.db); self.state=State(self.db)
    def record(self,kind='surface_location',**kwargs):
        return dict(type=kind,system_name='Sol',system_address=0,body_name='Sol 1',body_id=0,
                    latitude=0.0,longitude=0.0,name='Zero',category='bio',note='test',**kwargs)
    def image(self,name='original.png',color='red'):
        p=self.root/name; Image.new('RGB',(20,10),color).save(p); return p
    def controller(self):
        c=PlanetNavigationController(self.state)
        c.state=SimpleNamespace(snapshot=StatusSnapshot(datetime.now(timezone.utc),0,0.,0.,51.,1e6,'Sol 1',1<<21,0))
        c.poll=Mock()
        return c

    def test_all_types_persist_reload_and_delete_without_explorer_changes(self):
        for kind in ('system','body','surface_location'):
            with self.subTest(kind=kind):
                row=self.store.save(1,self.record(kind))
                self.assertEqual(FavoriteStore(self.db).get(1,row['id']),row)
                self.assertEqual(row['commander_id'],1)
                self.assertTrue(row['created_at']); self.assertTrue(row['updated_at'])
                if kind!='surface_location':self.assertIsNone(row['latitude']); self.assertIsNone(row['longitude'])
                if kind=='system':self.assertEqual(row['body_name'],'')
                self.store.delete(1,row['id']); self.assertEqual(self.store.list(1),[])
        with self.db._connect() as con:self.assertEqual(con.execute('SELECT COUNT(*) FROM commanders').fetchone()[0],2)

    def test_freeze_surface_including_zero_and_known_zero_ids(self):
        c=self.controller(); frozen=freeze_surface_location(c)
        c.state.snapshot=StatusSnapshot(datetime.now(timezone.utc),0,20.,30.,51.,1e6,'Other',1<<21,0)
        self.state.system='Other'; self.state.system_address=9
        dialog=FavoriteDialog(self.store,self.state,frozen)
        dialog.name.setText('Frozen'); dialog._save()
        row=dialog.saved
        self.assertEqual((row['latitude'],row['longitude']),(0.,0.))
        self.assertEqual((row['system_name'],row['body_name'],row['system_address'],row['body_id']),('Sol','Sol 1',0,0))
        dialog.close()

    def test_missing_snapshot_and_wrong_commander_are_rejected(self):
        c=self.controller(); c.state.snapshot=None
        with self.assertRaises(ValueError):freeze_surface_location(c)
        c=self.controller(); c.tail.context.fid='F2'
        with self.assertRaises(ValueError):freeze_surface_location(c)

    def test_location_is_immutable_on_edit(self):
        row=self.store.save(1,self.record())
        edited=self.store.save(1,dict(name='New',category='geo',note='new',latitude=55,longitude=66,
                                    system_name='Elsewhere',body_name='Other'),row['id'])
        for key in ('latitude','longitude','system_name','body_name','body_id','system_address','created_at'):
            self.assertEqual(edited[key],row[key])
        self.assertEqual(edited['name'],'New')

    def test_multi_commander_crud_isolation(self):
        row=self.store.save(1,self.record())
        self.assertEqual(self.store.list(2),[])
        for operation in (lambda:self.store.get(2,row['id']),lambda:self.store.delete(2,row['id']),
                          lambda:self.store.save(2,dict(name='steal'),row['id'])):
            with self.assertRaises(ValueError):operation()
        self.assertEqual(self.store.get(1,row['id']),row)

    def test_combined_search_type_category_and_sort(self):
        self.store.save(1,self.record())
        self.store.save(1,dict(self.record('body'),name='Alpha',category='geo',note='CRATER'))
        self.store.save(2,self.record())
        self.assertEqual([r['name'] for r in self.store.list(1)],['Alpha','Zero'])
        self.assertEqual(len(self.store.list(1,'crater','body','geo')),1)
        self.assertEqual(self.store.list(1,'crater','system','geo'),[])

    def test_choose_image_copies_and_preserves_original(self):
        source=self.image(); original=source.read_bytes()
        dialog=FavoriteDialog(self.store,self.state,dict(self.record(),commander_id=1))
        dialog.select_image(source)
        self.assertFalse(self.store.images.exists())
        dialog._save(); row=dialog.saved; copy=self.store.image_file(row['image_path'])
        self.assertFalse(Path(row['image_path']).is_absolute()); self.assertNotEqual(copy,source)
        self.assertEqual(copy.read_bytes(),original); self.assertEqual(source.read_bytes(),original)
        dialog.close()

    def test_replace_remove_and_delete_only_internal_image(self):
        original=self.image(); second=self.image('new.webp','blue'); data=original.read_bytes()
        row=self.store.save(1,self.record(),image_source=original); old=self.store.image_file(row['image_path'])
        row=self.store.save(1,dict(name='Changed'),row['id'],image_source=second)
        self.assertFalse(old.exists()); replacement=self.store.image_file(row['image_path'])
        row=self.store.save(1,{},row['id'],remove_image=True)
        self.assertFalse(replacement.exists()); self.assertEqual(row['image_path'],'')
        row=self.store.save(1,{},row['id'],image_source=original); copy=self.store.image_file(row['image_path'])
        self.store.delete(1,row['id']); self.assertFalse(copy.exists())
        self.assertEqual(original.read_bytes(),data); self.assertTrue(second.exists())

    def test_missing_image_robust_and_path_escape_refused(self):
        source=self.image(); row=self.store.save(1,self.record(),image_source=source)
        self.store.image_file(row['image_path']).unlink()
        self.assertTrue(preview(self.store.image_file(row['image_path'])).isNull())
        self.assertEqual(self.store.get(1,row['id'])['name'],'Zero')
        self.assertIsNone(self.store.image_file(str(source)))
        self.assertIsNone(self.store.image_file('../original.png'))
        self.store.delete(1,row['id']); self.assertTrue(source.exists())

    def test_symlinked_image_directory_cannot_modify_external_files(self):
        source=self.image()
        external=self.root/'external'; external.mkdir()
        (self.root/'favorites').symlink_to(external,target_is_directory=True)
        with self.assertRaises(ValueError):
            self.store.save(1,self.record(),image_source=source)
        self.assertEqual(list(external.iterdir()),[])
        self.assertTrue(source.exists())

    def test_no_screenshot_does_not_choose_arbitrary_image(self):
        self.state.values['screenshots/source_dir']=str(self.root)
        self.image('holiday.png'); self.image('Screenshot_holiday.png')
        self.assertIsNone(latest_screenshot(self.state.settings))
        with patch.object(QMessageBox,'information') as message:
            dialog=FavoriteDialog(self.store,self.state,dict(self.record(),commander_id=1)); dialog._latest()
        message.assert_called_once(); self.assertIsNone(dialog.image_source); dialog.close()

    def test_latest_plausible_screenshot_and_bmp_copy(self):
        self.state.values['screenshots/source_dir']=str(self.root)
        first=self.image('Screenshot_0001.bmp'); second=self.image('Screenshot_0002.png')
        self.image('holiday.png'); bad=self.root/'Screenshot_0003.png'; bad.write_bytes(b'invalid')
        os.utime(first,(10,10)); os.utime(second,(20,20))
        self.assertEqual(latest_screenshot(self.state.settings),second)
        before=first.read_bytes(); row=self.store.save(1,self.record(),image_source=first)
        self.assertTrue(row['image_path'].endswith('.png')); self.assertEqual(first.read_bytes(),before)
        with Image.open(self.store.image_file(row['image_path'])) as im:self.assertEqual(im.format,'PNG')

    def test_screenshot_requires_confirmation_and_cancel_does_not_import(self):
        self.state.values['screenshots/source_dir']=str(self.root); source=self.image('Screenshot_0001.png')
        dialog=FavoriteDialog(self.store,self.state,dict(self.record(),commander_id=1))
        with patch.object(QDialog,'exec',return_value=QDialog.Rejected):dialog._latest()
        self.assertIsNone(dialog.image_source)
        with patch.object(QDialog,'exec',return_value=QDialog.Accepted):dialog._latest()
        self.assertEqual(dialog.image_source,source); self.assertFalse(self.store.images.exists()); dialog.close()

    def converted_image(self, stamp, *, fid='F1', commander='Same', color='blue'):
        target = self.root / 'converted'
        self.state.values['screenshots/target_dir'] = str(target)
        folder = target / f'{commander}_{fid}'
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (datetime.fromtimestamp(stamp).strftime('%Y-%m-%d_%H-%M-%S') + f'_{commander}_Sol.png')
        Image.new('RGB', (20, 10), color).save(path)
        return path

    def latest_for_active(self):
        return latest_screenshot(self.state.settings, commander_fid='F1', commander_name='Same')

    def test_latest_source_then_actual_conversion_and_bmp_deletion(self):
        from cmdrhelper.ui.screenshot_view import _ConvertWorker
        self.state.values['screenshots/source_dir'] = str(self.root)
        old = self.image('Screenshot_0001.bmp')
        new = self.image('Screenshot_0002.bmp')
        stamp = datetime(2026, 9, 6, 12, 0, 0).timestamp()
        os.utime(old, (stamp - 10, stamp - 10)); os.utime(new, (stamp, stamp))
        self.assertEqual(self.latest_for_active(), new)
        target = self.converted_image(stamp)
        # Run the existing converter, including its existing delete_bmp behavior.
        _ConvertWorker(new, target, 'PNG', True).run()
        self.assertFalse(new.exists())
        content = target.read_bytes()
        self.assertEqual(self.latest_for_active(), target)
        self.assertEqual(target.read_bytes(), content)
        self.assertTrue(old.exists())

    def test_converted_capture_time_wins_over_late_conversion_mtime(self):
        self.state.values['screenshots/source_dir'] = str(self.root)
        stamp = datetime(2026, 9, 6, 12, 0, 0).timestamp()
        older = self.converted_image(stamp - 60)
        newest = self.converted_image(stamp)
        os.utime(older, (stamp + 1000, stamp + 1000))
        os.utime(newest, (stamp + 5, stamp + 5))
        self.assertEqual(self.latest_for_active(), newest)
        source = self.image('Screenshot_0003.bmp')
        os.utime(source, (stamp + 10, stamp + 10))
        self.assertEqual(self.latest_for_active(), source)

    def test_converted_search_excludes_other_fid_and_unassigned_images(self):
        self.state.values['screenshots/source_dir'] = str(self.root)
        stamp = datetime(2026, 9, 6, 12, 0, 0).timestamp()
        own = self.converted_image(stamp)
        self.converted_image(stamp + 60, fid='F2')  # Same commander name, different FID.
        Image.new('RGB', (20, 10)).save(own.parent / 'holiday.png')
        self.converted_image(stamp + 120, fid='UNKNOWN')
        self.assertEqual(self.latest_for_active(), own)
        own.unlink()
        self.assertIsNone(self.latest_for_active())
        self.assertIsNone(latest_screenshot(self.state.settings))

    def test_timestamped_original_uses_filename_capture_time(self):
        self.state.values['screenshots/source_dir'] = str(self.root)
        dated = self.image('Screenshot_2026-09-06_12-00-00.bmp')
        newer = self.image('Screenshot_0003.bmp')
        stamp = datetime(2026, 9, 6, 12, 0, 0).timestamp()
        os.utime(dated, (stamp + 1000, stamp + 1000))
        os.utime(newer, (stamp + 10, stamp + 10))
        self.assertEqual(self.latest_for_active(), newer)

    def test_each_latest_click_rescans_and_reloads_preview(self):
        self.state.values['screenshots/source_dir'] = str(self.root)
        self.state.commander = 'Same'
        first = self.image('Screenshot_0001.bmp', 'red')
        stamp = datetime(2026, 9, 6, 12, 0, 0).timestamp()
        os.utime(first, (stamp - 60, stamp - 60))
        dialog = FavoriteDialog(self.store, self.state, dict(self.record(), commander_id=1))
        with patch.object(QDialog, 'exec', return_value=QDialog.Accepted):
            dialog._latest()
            self.assertEqual(dialog.image_source, first)
            newest = self.converted_image(stamp, color='blue')
            original = newest.read_bytes()
            dialog._latest()
            self.assertEqual(dialog.image_source, newest)
            self.assertEqual(dialog.image.pixmap().toImage().pixelColor(0, 0).name(), '#0000ff')
            Image.new('RGB', (20, 10), 'green').save(newest)
            dialog._latest()
            self.assertEqual(dialog.image.pixmap().toImage().pixelColor(0, 0).name(), '#008000')
        dialog._save()
        self.assertTrue(first.exists()); self.assertTrue(newest.exists())
        self.assertNotEqual(dialog.saved['image_path'], str(newest))
        self.assertEqual(self.store.image_file(dialog.saved['image_path']).read_bytes(), newest.read_bytes())
        dialog.close()

    def test_navigate_uses_existing_controller_and_rejects_other_commander(self):
        row=self.store.save(1,self.record()); c=PlanetNavigationController(self.state)
        navigate_to_favorite(self.store,1,row['id'],c)
        self.assertEqual((c.target.latitude,c.target.longitude,c.target.binding.body_name),(0.,0.,'Sol 1'))
        self.assertEqual(c.state.reason,'waiting_planetary_position')
        target=c.target
        with self.assertRaises(ValueError):navigate_to_favorite(self.store,2,row['id'],c)
        self.assertIs(c.target,target)

    def test_commander_switch_refreshes_view_and_rejects_open_editor(self):
        row=self.store.save(1,self.record()); self.store.save(2,dict(self.record(),name='Second'))
        controller=PlanetNavigationController(self.state)
        view=FavoritesView(self.state,lambda:controller,Mock())
        self.assertEqual(view.list.count(),1); self.assertIn('Zero',view.list.item(0).text())
        view.list.setCurrentRow(0); view.navigate_selected(); self.assertIsNotNone(controller.target)
        dialog=FavoriteDialog(self.store,self.state,row); dialog.show()
        self.state.commander_id=2; self.state.commanderIdentityChanged.emit(2,'F2','Second')
        self.assertIn('Second',view.list.item(0).text()); self.assertFalse(dialog.isVisible())
        self.assertIsNone(controller.target); view.close()

    def test_invalid_coordinates_rejected(self):
        for latitude in (None,float('nan'),91):
            with self.assertRaises(ValueError):self.store.save(1,dict(self.record(),latitude=latitude))

    def test_failed_save_does_not_leave_image_copy(self):
        source=self.image()
        with self.assertRaises(Exception):self.store.save(999,self.record(),image_source=source)
        self.assertEqual(list(self.store.images.iterdir()),[]); self.assertTrue(source.exists())

    def test_navigator_save_button_tracks_valid_snapshot(self):
        c=self.controller(); c.state.last_confirmed_at=None; c.state.target=None; c.state.reason='no_target'; c.state.solution=None
        window=PlanetNavigationWindow(c,self.state.settings)
        self.assertTrue(window.save_location_button.isEnabled())
        save=Mock(); window.save_location_requested.connect(save)
        window.save_location_button.click(); save.assert_called_once_with()
        c.state.snapshot=None; window.refresh_navigation(c.state)
        self.assertFalse(window.save_location_button.isEnabled()); window.close()

    def test_explorer_favorites_action_reuses_view_without_extra_tab(self):
        # Build the real Explorer without starting unrelated main-window services.
        window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(window)
        window.state = self.state
        window._planet_navigation_controller = None
        window.ui_theme = 'dark'
        window._quick_favorite_hotkey = GlobalHotkey(self.state.settings, backend_factory=Mock())
        self.addCleanup(window._quick_favorite_hotkey.close)
        window.quick_favorite_settings = QuickFavoriteSettings(window._quick_favorite_hotkey, window)
        window.setCentralWidget(window._explorer())
        self.addCleanup(window.deleteLater)
        self.addCleanup(window._favorites_window.close)

        self.assertEqual(window.explorer_tabs.count(), 3)
        self.assertEqual([window.explorer_tabs.widget(i) for i in range(3)],
                         [window.system_scroll, window.explorer_value_table,
                          window.explorer_bio_table])
        layout = window.favorites_button.parentWidget().layout()
        row = next(layout.itemAt(i).layout() for i in range(layout.count())
                   if layout.itemAt(i).layout() is not None
                   and layout.itemAt(i).layout().indexOf(window.favorites_button) >= 0)
        self.assertEqual([row.itemAt(i).widget() for i in range(row.count())
                          if row.itemAt(i).widget() is not None],
                         [window.favorites_button, window.planet_navigation_button,
                          window.system_overview_button])

        view = window.favorites_view
        view.search.setText('retained search')
        self.assertFalse(window._favorites_window.isVisible())
        window.favorites_button.click()
        self.assertTrue(window._favorites_window.isVisible())
        with patch.object(window.quick_favorite_settings, 'choose') as choose:
            view.quick_favorite_setup_button.click()
            choose.assert_called_once_with()
        self.assertIs(window._favorites_window.layout().itemAt(0).widget(), view)
        window._favorites_window.close()
        window.favorites_button.click()
        self.assertIs(window.favorites_view, view)
        self.assertEqual(view.search.text(), 'retained search')

    def hint_view(self, binding=''):
        backend = Mock()
        hotkey = GlobalHotkey(self.state.settings, backend_factory=Mock(return_value=backend))
        self.addCleanup(hotkey.close)
        if binding:
            self.assertTrue(hotkey.set_hotkey(binding))
        configure = Mock()
        view = FavoritesView(self.state, Mock(), Mock(), quick_favorite_hotkey=hotkey,
                             configure_hotkey_callback=configure)
        self.addCleanup(view.close)
        view.show()
        return view, hotkey, backend, configure

    def test_unassigned_hotkey_shows_hint_without_opening_configuration(self):
        view, hotkey, backend, configure = self.hint_view()
        self.assertTrue(view.quick_favorite_hint.isVisible())
        configure.assert_not_called()
        backend.register.assert_not_called()
        view.quick_favorite_setup_button.click()
        configure.assert_called_once_with()

    def test_assigned_hotkey_hides_hint(self):
        view, hotkey, backend, configure = self.hint_view('Ctrl+F8')
        self.assertFalse(view.quick_favorite_hint.isVisible())

    def test_successful_assignment_hides_hint_and_removal_restores_it(self):
        view, hotkey, backend, configure = self.hint_view()
        view.search.setText('keep filter')
        self.assertTrue(hotkey.set_hotkey('Ctrl+F8'))
        self.assertFalse(view.quick_favorite_hint.isVisible())
        self.assertEqual(view.search.text(), 'keep filter')
        self.assertTrue(hotkey.set_hotkey(''))
        self.assertTrue(view.quick_favorite_hint.isVisible())
        view.close()
        view.show()
        view.refresh()
        self.assertTrue(view.quick_favorite_hint.isVisible())
        self.assertEqual(view.search.text(), 'keep filter')

    def test_failed_assignment_keeps_hint_visible(self):
        view, hotkey, backend, configure = self.hint_view()
        backend.register.side_effect = RuntimeError('conflict')
        self.assertFalse(hotkey.set_hotkey('Ctrl+F8'))
        self.assertTrue(view.quick_favorite_hint.isVisible())

    def live_status(self, latitude=0.0, longitude=0.0):
        self.state.journal_folder = str(self.root)
        (self.root / 'Status.json').write_text(json.dumps(dict(
            event='Status', timestamp=datetime.now(timezone.utc).isoformat(),
            Flags=1 << 21, Flags2=0, Latitude=latitude, Longitude=longitude,
            Heading=51, PlanetRadius=1000000, BodyName='Sol 1')))

    def location_view(self):
        controller = PlanetNavigationController(self.state)
        view = FavoritesView(self.state, Mock(), Mock(),
                             location_controller_callback=lambda: controller)
        self.addCleanup(view.close)
        return view, controller

    def test_location_button_visible_and_automatically_tracks_live_validity(self):
        view, controller = self.location_view()
        view.show()
        self.assertTrue(view.save_location_button.isVisible())
        self.assertFalse(view.save_location_button.isEnabled())
        self.live_status()
        QTest.qWait(350)
        self.assertTrue(view.save_location_button.isEnabled())
        (self.root / 'Status.json').write_text('{}')
        QTest.qWait(350)
        self.assertFalse(view.save_location_button.isEnabled())
        self.assertTrue(view.save_location_button.isVisible())
        self.live_status()
        self.state.commander_id = None
        QTest.qWait(350)
        self.assertFalse(view.save_location_button.isEnabled())

    def test_location_click_freezes_fresh_snapshot_before_editor_and_live_updates(self):
        self.live_status(10, 20)
        view, controller = self.location_view()
        view.show()
        self.assertTrue(view.save_location_button.isEnabled())
        self.live_status(0.0, 0.0)  # Newer than the availability check.

        def edit(dialog):
            self.assertEqual((dialog.record['latitude'], dialog.record['longitude']), (0.0, 0.0))
            self.live_status(45, 90)
            controller.poll()
            dialog.name.setText('Frozen at click')
            dialog._save()
            return QDialog.Accepted

        with patch.object(FavoriteDialog, 'exec', new=edit):
            view.save_location_button.click()
        row, = self.store.list(1)
        self.assertEqual(row['type'], 'surface_location')
        self.assertEqual((row['latitude'], row['longitude']), (0.0, 0.0))
        self.assertEqual((row['commander_id'], row['system_name'], row['body_name'],
                          row['system_address'], row['body_id']), (1, 'Sol', 'Sol 1', 0, 0))
        self.assertEqual(controller.state.snapshot.latitude, 45)

    def test_navigator_location_button_still_uses_same_save_path(self):
        self.live_status()
        view, controller = self.location_view()
        controller.poll()
        window = PlanetNavigationWindow(controller, self.state.settings)
        self.addCleanup(window.close)
        window.save_location_requested.connect(lambda: view.save_surface(controller))

        def edit(dialog):
            dialog._save()
            return QDialog.Accepted

        with patch.object(FavoriteDialog, 'exec', new=edit):
            window.save_location_button.click()
        row, = self.store.list(1)
        self.assertEqual(row['type'], 'surface_location')
        self.assertEqual((row['latitude'], row['longitude']), (0.0, 0.0))

    def test_location_click_rechecks_snapshot_and_hidden_view_stops_its_timer(self):
        self.live_status()
        view, controller = self.location_view()
        view.show()
        self.assertTrue(view.save_location_button.isEnabled())
        (self.root / 'Status.json').write_text('{}')
        with patch.object(QMessageBox, 'information') as message:
            view.save_location_button.click()
        message.assert_called_once()
        self.assertEqual(self.store.list(1), [])
        view.hide()
        self.assertFalse(view._location_timer.isActive())

    def test_three_save_buttons_wrap_without_clipping(self):
        view, _ = self.location_view()
        view.resize(1200, 600)
        view.show()
        self.app.processEvents()
        row = view.layout().itemAt(0).layout()
        buttons = [row.itemAt(i).widget() for i in range(row.count())]
        self.assertEqual(len(buttons), 3)
        self.assertIs(buttons[-1], view.save_location_button)
        self.assertEqual(len({b.y() for b in buttons}), 1)
        view.resize(460, 650)
        self.app.processEvents()
        self.assertGreater(len({b.y() for b in buttons}), 1)
        for button in buttons:
            self.assertGreaterEqual(button.width(), button.minimumSizeHint().width())
            self.assertTrue(view.rect().contains(button.geometry()))


if __name__=='__main__':unittest.main()
