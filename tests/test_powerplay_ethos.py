"""Ethos regression evidence extracted verbatim from the real local Elite cache.

Set CMDRHELPER_TEST_POWERS_CACHE to also compare the fixture to that binary
source. Ordinary test runs remain portable and never contact Elite servers.
"""
import copy
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.i18n import set_language, tr
from cmdrhelper.powerplay import _crypt, decode_powers_cache, powerplay_actions
from cmdrhelper.ui.help_dialog import HelpDialog
from cmdrhelper.ui.powerplay_view import PowerplayView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_powerplay import ViewState


def document():
    return json.loads((Path(__file__).parent / 'fixtures/powerplay_ethos_20261007.json').read_text())


def encoded(doc, language='german'):
    payload = json.dumps({'powers': doc['powers']}).encode()
    header = struct.pack('<IB', 3, 1)
    for value in (language, 'api.orerve.net', ''):
        value = value.encode()
        header += struct.pack('<H', len(value)) + value
    return _crypt(header + struct.pack('<HI', 65535, len(payload)) + payload)


def statuses(powers, name, category):
    return {a.token: a.ethos for a in powerplay_actions(powers[name], category)}


class EthosEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.doc = document()
        self.powers = decode_powers_cache(encoded(self.doc))

    def test_real_cache_marker_and_language_survive_decoding(self):
        self.assertEqual(self.powers.language, self.doc['source']['language'])
        for power in self.doc['powers']:
            self.assertEqual(self.powers[power['name']]['ethos'], power['ethos'])
        self.assertEqual(self.powers['Nakato Kaine']['id'], 200130)

    def test_kaine_acquisition_from_real_cache(self):
        values = statuses(self.powers, 'Nakato Kaine', 'acquisition')
        self.assertEqual({k for k, v in values.items() if v is True}, {
            'TransportPowerplayCommodities', 'HoloscreenHacking', 'RebootMission',
            'SellMinedResourcess', 'CompleteAidMissions'})
        self.assertIs(values['BountyHunting'], False)
        self.assertIs(values['SellExoticGoods'], False)
        self.assertEqual(len(values), 16)

    def test_kaine_reinforcement_from_real_cache(self):
        values = statuses(self.powers, 'Nakato Kaine', 'reinforcement')
        self.assertEqual({k for k, v in values.items() if v is True}, {
            'TransportPowerplayCommodities', 'CompleteAidMissions', 'TransferClassifiedData',
            'HandInSalvage', 'ScanShipsWakes', 'HandInExplorationData'})
        self.assertIs(values['SellExoticGoods'], False)
        self.assertEqual(len(values), 15)

    def test_real_conflict_duplicates_keep_ethos_in_either_order_without_mutation(self):
        power = self.powers['Nakato Kaine']
        original = copy.deepcopy(power)
        for rows in (power['ethos']['conflict'], list(reversed(power['ethos']['conflict']))):
            activities = powerplay_actions({'ethos': {'conflict': rows}}, 'conflict')
            self.assertEqual(len(activities), 16)
            for token in ('TransferClassifiedData', 'ScanDatalinks'):
                matches = [a for a in activities if a.token == token]
                self.assertEqual(len(matches), 1)
                self.assertIs(matches[0].ethos, True)
        self.assertEqual(power, original)

    def test_same_token_varies_by_power_and_category(self):
        for name, expected in [('Nakato Kaine', False), ('Edmund Mahon', True), ('Aisling Duval', True)]:
            self.assertIs(statuses(self.powers, name, 'acquisition')['SellExoticGoods'], expected)
        self.assertIs(statuses(self.powers, 'Nakato Kaine', 'acquisition')['HandInSalvage'], False)
        self.assertIs(statuses(self.powers, 'Nakato Kaine', 'reinforcement')['HandInSalvage'], True)
        self.assertIs(statuses(self.powers, 'Nakato Kaine', 'undermining')['HandInSalvage'], True)

    def test_unknown_suffix_is_not_a_negative_ethos_decision_or_guessed_translation(self):
        base = '$PP2_Action_BountyHunting;'
        for language in ('german', 'english', 'future-language'):
            for suffix in (' (Ethos Bonus)', ' (Future modifier)', ' (Ethos-Bonus) extra'):
                doc = {'powers': [{'id': 1, 'name': 'P', 'ethos': {'acquisition': [base, base + suffix]}}]}
                powers = decode_powers_cache(encoded(doc, language))
                self.assertEqual(powers.language, language)
                activity, = powerplay_actions(powers['P'], 'acquisition')
                self.assertIsNone(activity.ethos)
                self.assertEqual(activity.annotations, (suffix.strip(),))

    def test_explicit_evidence_wins_but_unknown_annotation_is_preserved(self):
        base = '$PP2_Action_BountyHunting;'
        rows = [base, base + ' (Future modifier)', base + ' (Ethos-Bonus)']
        for entries in (rows, list(reversed(rows))):
            activity, = powerplay_actions({'ethos': {'reinforcement': entries}}, 'reinforcement')
            self.assertIs(activity.ethos, True)
            self.assertEqual(activity.annotations, ('(Future modifier)',))

    def test_unknown_tokens_can_preserve_evidence_and_distinct_raw_entries(self):
        rows = ['$PP2_Action_FutureAction;', '$PP2_Action_FutureAction; (Ethos-Bonus)', 'unparsed A', 'unparsed B']
        activities = powerplay_actions({'ethos': {'acquisition': rows}}, 'acquisition')
        self.assertEqual(len(activities), 3)
        self.assertEqual(activities[0].token, 'FutureAction')
        self.assertIs(activities[0].ethos, True)
        self.assertIsNone(activities[1].ethos)
        self.assertEqual(powerplay_actions({'ethos': {}}, 'reinforcement'), [])

    @unittest.skipUnless(os.environ.get('CMDRHELPER_TEST_POWERS_CACHE'), 'optional local binary cache comparison')
    def test_fixture_matches_actual_local_binary_cache(self):
        raw = Path(os.environ['CMDRHELPER_TEST_POWERS_CACHE']).read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), self.doc['source']['sha256'])
        real = decode_powers_cache(raw)
        self.assertEqual(real.language, self.doc['source']['language'])
        for power in self.doc['powers']:
            self.assertEqual({k: real[power['name']][k] for k in ('id', 'name', 'ethos')}, power)


class EthosViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        set_language('de')
        self.addCleanup(set_language, 'de')
        self.powers = decode_powers_cache(encoded(document()))
        self.state = ViewState()
        self.state.powerplay.power = 'Nakato Kaine'
        self.state.powerplay.system['ControllingPower'] = 'Nakato Kaine'
        self.view = PowerplayView(self.state)
        self.addCleanup(self.view.close)
        loader = patch.object(self.view.cache, 'load', return_value=self.powers)
        loader.start()
        self.addCleanup(loader.stop)
        self.view.render()

    def test_inline_marker_tooltip_and_unmarked_row(self):
        self.assertIn('✓ Bergungsgut einreichen · ★ Ethos', self.view.actions.text())
        self.assertIn('✓ Kopfgeldjagd', self.view.actions.text().splitlines())
        self.assertEqual(self.view.actions.toolTip(), tr('pp2.ethos_tooltip'))
        self.assertEqual(self.view.actions.textFormat(), Qt.PlainText)
        self.assertTrue(self.view.actions.wordWrap())

    def test_render_merges_before_translation_and_preserves_ethos(self):
        # Real conflict list exercises the rendering merge without activating
        # conflict in context(): temporarily present it as reinforcement data.
        self.powers['Nakato Kaine']['ethos']['reinforcement'] = self.powers['Nakato Kaine']['ethos']['conflict']
        self.view.render()
        self.assertEqual(self.view.actions.text().count('Geheimdaten der Macht übertragen'), 1)
        self.assertIn('✓ Geheimdaten der Macht übertragen · ★ Ethos', self.view.actions.text())

    def test_unknown_suffix_remains_visible_and_uninterpreted(self):
        self.powers['Nakato Kaine']['ethos']['reinforcement'] = ['$PP2_Action_HandInSalvage; (Future modifier)']
        self.view.render()
        self.assertEqual(self.view.actions.text(), '✓ Bergungsgut einreichen (Future modifier)')
        self.assertEqual(self.view.actions.toolTip(), tr('pp2.ethos_unknown_tooltip'))

    def test_unknown_token_keeps_all_suffix_evidence_when_merged(self):
        self.powers['Nakato Kaine']['ethos']['reinforcement'] = [
            '$PP2_Action_FutureAction;', '$PP2_Action_FutureAction; (Future modifier)',
            '$PP2_Action_FutureAction; (Ethos-Bonus)']
        self.view.render()
        self.assertEqual(self.view.actions.text().count('$PP2_Action_FutureAction;'), 1)
        self.assertIn('(Future modifier) · ★ Ethos', self.view.actions.text())

    def test_power_category_changes_clear_previous_markers_and_tooltips(self):
        self.state.powerplay.system.update(PowerplayState='Unoccupied', Powers=['Nakato Kaine'])
        self.state.powerplay.system.pop('ControllingPower')
        self.view.render()
        self.assertIn('✓ Seltene Waren verkaufen', self.view.actions.text().splitlines())
        self.state.powerplay.power = 'Edmund Mahon'
        self.state.powerplay.system['Powers'] = ['Edmund Mahon']
        self.view.render()
        self.assertIn('✓ Seltene Waren verkaufen · ★ Ethos', self.view.actions.text())
        self.state.powerplay.system['Powers'] = ['Nakato Kaine', 'Edmund Mahon']
        self.view.render()
        self.assertEqual(self.view.actions.text(), tr('pp2.context_unknown'))
        self.assertEqual(self.view.actions.toolTip(), '')
        self.powers['Edmund Mahon']['ethos']['acquisition'] = ['$PP2_Action_SellExoticGoods;']
        self.state.powerplay.system['Powers'] = ['Edmund Mahon']
        self.view.render()
        self.assertNotIn('★', self.view.actions.text())
        self.assertEqual(self.view.actions.toolTip(), '')

    def test_twelve_languages_help_and_both_themes(self):
        self.assertEqual(len(HELP_LANGUAGES), 12)
        old_style = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, old_style)
        before = copy.deepcopy(self.state.powerplay)
        for theme, style in [('dark', DARK_STYLESHEET), ('light', LIGHT_STYLESHEET)]:
            self.app.setStyleSheet(style)
            for language in HELP_LANGUAGES:
                with self.subTest(theme=theme, language=language):
                    set_language(language)
                    catalog = import_module('cmdrhelper.i18n.' + language).TRANSLATIONS
                    for key in ('pp2.ethos', 'pp2.ethos_tooltip', 'pp2.ethos_unknown_tooltip', 'pp2.cache_source'):
                        self.assertEqual(catalog[key], tr(key))
                    self.view.render()
                    self.view.resize(1050, 900)
                    self.view.show()
                    self.app.processEvents()
                    self.assertEqual(self.view.actions.text().count('★ Ethos'), 6)
                    self.assertEqual(self.view.actions.toolTip(), catalog['pp2.ethos_tooltip'])
                    self.assertEqual(self.view.notice.text(), catalog['pp2.cache_source'])
                    self.assertFalse(self.view.actions.grab().isNull())
                    dialog = HelpDialog('pp2', language=language)
                    try:
                        dialog.resize(900, 750)
                        dialog.show()
                        self.app.processEvents()
                        help_text = help_topic('pp2', language).text
                        self.assertEqual(dialog.help_text.text(), help_text)
                        self.assertIn('★ Ethos', help_text)
                        self.assertNotRegex(help_text + self.view.actions.text() + self.view.actions.toolTip(), r'\d\s*[%％]')
                        self.assertFalse(dialog.grab().isNull())
                    finally:
                        dialog.close()
        self.assertEqual(self.state.powerplay, before)


if __name__ == '__main__':
    unittest.main()
