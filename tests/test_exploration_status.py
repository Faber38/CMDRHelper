"""Historical journal evidence stays separate from mapping and external metadata."""
import copy
import itertools
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QFormLayout, QLabel, QTableWidget, QTabWidget, QWidget
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.exploration_status import exploration_status, journal_flag, status_rows, status_tooltip
from cmdrhelper.i18n import set_language, tr, _TRANSLATIONS
from cmdrhelper.online_services import _normalize_edsm_body
from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.state import AppState
from cmdrhelper.ui.body_detail_window import BodyDetailWindow
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.system_view import SystemMapWidget
from cmdrhelper.valuation import calculate_body_values


class ExplorationStatusTests(unittest.TestCase):
    def setUp(self):
        set_language("de")

    def body(self, **extra):
        return dict(name="Example 1", body_id=1, body_type="Planet", planet_class="Water world",
                    journal_scanned=True, source="Journal", **extra)

    def test_discovery_tristate(self):
        for value in (True, False, None):
            with self.subTest(value=value):
                b=self.body(was_discovered=value)
                self.assertIs(exploration_status(b)["was_discovered_at_scan"], value)
                self.assertEqual(exploration_status(b)["first_discovery_candidate"], value is False)
        self.assertIsNone(journal_flag(self.body(), "was_discovered"))

    def test_mapping_tristate(self):
        for value in (True, False, None):
            with self.subTest(value=value):
                b=self.body(was_mapped=value)
                self.assertIs(exploration_status(b)["was_mapped_at_scan"], value)
                self.assertEqual(exploration_status(b)["first_mapping_candidate"], value is False)
        self.assertIsNone(journal_flag(self.body(), "was_mapped"))

    def test_invalid_values_are_unknown(self):
        for value in ("false", "true", 0, 1, [], {}):
            self.assertIsNone(journal_flag(self.body(was_discovered=value), "was_discovered"))

    def test_self_mapping_is_independent_in_all_combinations(self):
        for d,m in itertools.product((True,False,None),repeat=2):
            with self.subTest(discovered=d,mapped=m):
                b=self.body(was_discovered=d,was_mapped=m,self_mapped=True)
                s=exploration_status(b)
                self.assertIs(s['self_mapped'],True)
                self.assertEqual(s['first_discovery_candidate'],d is False)
                self.assertEqual(s['first_mapping_candidate'],m is False)
                if m is None:
                    self.assertEqual(dict(status_rows(b))[tr('body_detail.first_mapping')],tr('common.unknown'))

    def test_external_known_does_not_establish_elite_discovery(self):
        body=_normalize_edsm_body(dict(bodyId=1,type="Planet",subType="Water world",isMapped=True),"Example")
        s=exploration_status(body)
        self.assertTrue(s['edsm_known'])
        self.assertIsNone(s['was_discovered_at_scan'])
        self.assertIsNone(s['was_mapped_at_scan'])
        self.assertIsNone(s['self_mapped'])
        self.assertFalse(s['first_discovery_candidate'])
        self.assertFalse(s['first_mapping_candidate'])

    def test_external_unknown_does_not_override_journal(self):
        b=self.body(was_discovered=False,was_mapped=True,edsm_known=False)
        self.assertTrue(exploration_status(b)['first_discovery_candidate'])
        self.assertTrue(SystemMapWidget._already_mapped(b))
        # Existing False also means not queried; never invent a verified negative.
        self.assertNotIn('EDSM:',status_tooltip(b))

    def test_external_discovery_flags_do_not_override_own_false(self):
        b=self.body(was_discovered=False,was_mapped=False,edsm_was_discovered=True,edsm_was_mapped=True)
        self.assertFalse(SystemMapWidget._already_discovered(b))
        self.assertFalse(SystemMapWidget._already_mapped(b))
        self.assertTrue(exploration_status(b)['first_mapping_candidate'])

    def test_old_edsm_cache_cannot_fill_missing_own_flags(self):
        for own in ([],[self.body()]):
            state=SimpleNamespace(edsm_enabled=True,system_bodies=copy.deepcopy(own),
                database=SimpleNamespace(learned_cartography_factor=lambda *a,**k:1),commander_id=1)
            external=self.body(was_discovered=True,was_mapped=False,self_mapped=True,
                               current_value=999999999,edsm_was_discovered=True)
            AppState._merge_edsm_into_system(state,{'bodies':[external]})
            body=state.system_bodies[0]
            self.assertIsNone(journal_flag(body,'was_discovered'))
            self.assertIsNone(journal_flag(body,'was_mapped'))
            self.assertIsNot(exploration_status(body)['self_mapped'],True)
            self.assertNotEqual(body.get('current_value'),999999999)
            self.assertTrue(body['edsm_known'])
            self.assertNotIn('edsm_was_discovered',body)

    def test_valuation_ignores_external_personal_flags(self):
        clean=self.body()
        clean.update(source='EDSM',journal_scanned=False)
        external={**clean,'was_discovered':False,'was_mapped':False,'self_mapped':True}
        self.assertEqual(calculate_body_values(clean),calculate_body_values(external))

    def test_stars_are_not_mapping_candidates(self):
        self.assertFalse(exploration_status(dict(body_type='Star',was_mapped=False))['first_mapping_candidate'])

    def test_sales_and_revisits_do_not_claim_current_availability(self):
        for extra in ({},{'sold_at':'2026-09-04T13:15:27Z'},{'last_seen':'2026-09-07T05:16:17Z'}):
            b=self.body(was_discovered=False,was_mapped=False,self_mapped=True,**extra)
            self.assertIn('zum Scanzeitpunkt',status_tooltip(b))
            self.assertIn('Erstanspruch unbestätigt',status_tooltip(b))
            self.assertIn('Heutige Verfügbarkeit und offizieller Erstanspruch unbekannt',status_tooltip(b))

    def test_real_body_regressions(self):
        # Read-only observations from actual DB and Scan/SAAScanComplete journals.
        for name,d in [('Nuekuae LS-B d28 1 b',True),('Prua Hypai RB-D c29-73 AB 2 f',False)]:
            b=self.body(was_discovered=d,was_mapped=False,self_mapped=True)
            b['name']=name
            s=exploration_status(b)
            self.assertEqual(s['first_discovery_candidate'],not d)
            self.assertTrue(s['first_mapping_candidate'])
            self.assertTrue(s['self_mapped'])
            self.assertIn('Scan',status_tooltip(b))

    def test_journal_scan_flags_and_later_saa_remain_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            events = [dict(event="Commander", Name="Test", FID="TEST-FID"),
                      dict(event="Location", StarSystem="Example", SystemAddress=42)]
            combinations = list(itertools.product((True, False, None), repeat=2))
            for i, (discovered, mapped) in enumerate(combinations):
                scan = dict(event="Scan", BodyID=i, BodyName=f"Example {i}",
                            SystemAddress=42, StarSystem="Example", PlanetClass="Water world")
                if discovered is not None:
                    scan["WasDiscovered"] = discovered
                if mapped is not None:
                    scan["WasMapped"] = mapped
                events.extend([scan, dict(event="SAAScanComplete", BodyID=i,
                    BodyName=f"Example {i}", SystemAddress=42, ProbesUsed=3, EfficiencyTarget=6)])
            journal = Path(folder) / "Journal.2026-09-08T100000.01.log"
            journal.write_text("".join(json.dumps(dict(timestamp=f"2026-09-08T10:00:{i:02}Z", **event))
                                       + "\n" for i, event in enumerate(events)))
            bodies = read_latest_state(Path(folder))["system_bodies"]
            self.assertEqual(len(bodies), len(combinations))
            for body, (discovered, mapped) in zip(bodies, combinations):
                status = exploration_status(body)
                self.assertIs(status["was_discovered_at_scan"], discovered)
                self.assertIs(status["was_mapped_at_scan"], mapped)
                self.assertTrue(status["self_mapped"])

    def test_persistence_roundtrip_preserves_unknown_and_explicit_flags(self):
        with tempfile.TemporaryDirectory() as folder:
            db=CMDRDatabase(Path(folder)/'test.db')
            commander=db.upsert_commander('TEST-FID','Test')
            for i,(d,m) in enumerate(itertools.product((True,False,None),repeat=2)):
                b=self.body(was_discovered=d,was_mapped=m,self_mapped=True)
                b['body_id']=i
                db.store_snapshot(dict(system_address=42,system='Example',last_timestamp='2026-09-08T10:00:00Z',system_bodies=[b]),commander)
            restored=db.chronicle_system_details(42,commander_id=commander,scanned_only=True)['bodies']
            for b,(d,m) in zip(restored,itertools.product((True,False,None),repeat=2)):
                self.assertIs(journal_flag(b,'was_discovered'),d)
                self.assertIs(journal_flag(b,'was_mapped'),m)
                self.assertTrue(exploration_status(b)['self_mapped'])

    def test_twelve_languages_have_explicit_unknown_and_historical_wording(self):
        for lang in _TRANSLATIONS:
            set_language(lang)
            unknown=dict(status_rows(self.body()))
            self.assertEqual(unknown[tr('body_detail.already_discovered')],tr('common.unknown'))
            self.assertEqual(unknown[tr('body_detail.already_mapped')],tr('common.unknown'))
            self.assertNotEqual(tr('exploration.historical_notice'),'exploration.historical_notice')
        set_language('de')


class ExplorationStatusUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def test_map_list_detail_use_same_rows_in_dark_and_light(self):
        set_language('de')
        for light in (False,True):
            for d,m,own in [(True,False,True),(False,False,True),(True,True,False),(None,None,False)]:
                with self.subTest(light=light,d=d,m=m,own=own):
                    body=dict(name='Example 1',body_id=1,body_type='Planet',planet_class='Water world',
                        journal_scanned=d is not None,source='Journal' if d is not None else 'EDSM',
                        was_discovered=d,was_mapped=m,self_mapped=own,edsm_known=d is None)
                    widget=SystemMapWidget()
                    widget.set_light_mode(light)
                    widget.set_system('Example',[body])
                    rows=status_rows(body)
                    tooltip=widget._tooltip(body)
                    form=QFormLayout()
                    detail=SimpleNamespace(body=body,_yes_no=BodyDetailWindow._yes_no,_add_row=lambda f,l,v:f.addRow(l,QLabel(str(v))))
                    BodyDetailWindow._add_explorer_rows(detail,form)
                    values={form.itemAt(i,QFormLayout.LabelRole).widget().text():form.itemAt(i,QFormLayout.FieldRole).widget().text()
                            for i in range(form.rowCount()) if form.itemAt(i,QFormLayout.LabelRole)}
                    table=QTableWidget(0,8)
                    bio=QTableWidget(0,11)
                    tabs=QTabWidget()
                    main=SimpleNamespace(state=SimpleNamespace(system_bodies=[body]),explorer_value_table=table,
                        explorer_bio_table=bio,explorer_tabs=tabs,_explorer_value_yellow_threshold=lambda:200000)
                    for method in ('_explorer_body_name','_explorer_body_visited','_explorer_distance_text','_format_reward'):
                        setattr(main,method,getattr(MainWindow,method))
                    MainWindow._refresh_explorer_tables(main)
                    for label,value in rows:
                        self.assertEqual(values[label+':'],value)
                        self.assertIn(label+': '+value,tooltip)
                        self.assertIn(label+': '+value,table.item(0,0).toolTip())
                    if d is None:
                        self.assertEqual(table.item(0,6).text(),tr('common.unknown'))
                    widget.show()
                    self.app.processEvents()
                    self.assertFalse(widget.grab().isNull())
                    widget.close()
                    for w in (widget,table,bio,tabs):w.deleteLater()
