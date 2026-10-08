import re
import unittest
from unittest.mock import patch

from cmdrhelper import i18n
from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.powerplay import ACTION_TOKENS
from tools.check_i18n import discover_languages, format_fields, intentional_english_fallback
from tests import test_powerplay as base
from tests.test_powerplay_rare_sales import REAL, DAY, replay


class PP2CatalogTests(unittest.TestCase):
    def test_full_catalog_reader_matches_runtime_and_pp2_never_falls_back(self):
        catalogs = discover_languages()
        self.assertEqual(set(catalogs), set(HELP_LANGUAGES))
        expected = {key for key in i18n.DE if key.startswith('pp2.') or key == 'nav.pp2'}
        self.assertEqual(len(expected), 132)
        for language, (_, catalog, duplicates) in catalogs.items():
            with self.subTest(language=language):
                self.assertEqual(catalog, i18n._TRANSLATIONS[language])
                self.assertEqual(duplicates, [])
                self.assertTrue(expected <= catalog.keys(), expected - catalog.keys())
                for key in expected:
                    self.assertTrue(catalog[key].strip(), key)
                    self.assertFalse(intentional_english_fallback(key, i18n.EN))
                    self.assertEqual(format_fields(catalog[key]), format_fields(i18n.DE[key]), key)
                    self.assertEqual(i18n.tr_for_language(language, key), catalog[key])
                missing = i18n.DE.keys() - catalog.keys()
                self.assertTrue(all(intentional_english_fallback(key, i18n.EN) for key in missing))

    def test_pp2_critical_prose_is_translated_not_copied_from_english(self):
        # Names, units and specific shared words legitimately match English;
        # an English paragraph copied into a catalog must still fail this test.
        neutral = {'nav.pp2', 'pp2.title', 'pp2.ethos', 'pp2.chronicle.tonnes',
                   'pp2.chronicle.item', 'pp2.chronicle.reward', 'pp2.rank.bar'}
        shared = {
            'de': {'pp2.system_name', 'pp2.chronicle.details', 'pp2.chronicle.merits'},
            'fr': {'pp2.mode.acquisition', 'pp2.chronicle.action', 'pp2.portrait.placeholder'},
            'no': {'pp2.system_name'}, 'sv': {'pp2.system_name'},
            'pl': {'pp2.system_name'}, 'nl': {'pp2.chronicle.details'},
        }
        keys = {key for key in i18n.EN if key.startswith('pp2.') or key == 'nav.pp2'}
        for language in HELP_LANGUAGES:
            if language != 'en':
                for key in keys - neutral - shared.get(language, set()):
                    with self.subTest(language=language, key=key):
                        self.assertNotEqual(i18n._TRANSLATIONS[language][key], i18n.EN[key])

    def test_dynamic_key_families_exist_in_every_catalog(self):
        families = {
            'action': ACTION_TOKENS,
            'mode': ('reinforcement', 'undermining', 'acquisition', 'conflict', 'unknown'),
            'relationship': ('own', 'opposing', 'unoccupied', 'unknown'),
            'status': ('unoccupied', 'exploited', 'fortified', 'stronghold'),
            'metric': ('control', 'reinforcement', 'undermining', 'conflict'),
            'chronicle': ('time', 'action', 'details', 'merits', 'certainty', 'PowerplayCollect',
                          'PowerplayDeliver', 'Bounty', 'ShipTargeted', 'SearchAndRescue',
                          'MarketSell', 'explicit', 'temporal', 'unknown'),
            'history': ('delete7', 'delete30', 'delete_all', 'reset_columns'),
            'rank': ('next', 'next_calculated', 'next_band', 'pending', 'unconfirmed',
                     'conflict', 'beyond100'),
        }
        for language in HELP_LANGUAGES:
            for prefix, suffixes in families.items():
                for suffix in suffixes:
                    key = 'pp2.' + prefix + '.' + suffix
                    with self.subTest(language=language, key=key):
                        self.assertIn(key, i18n._TRANSLATIONS[language])

    def test_every_pp2_template_formats_without_unresolved_fields(self):
        values = dict(power='Edmund Mahon', count='12', system='Sol', station='Galileo',
                      value='1', time='14:27', token='Token', amount='6', name='Leestian Evil Juice',
                      category='Acquisition', seconds=1, rank=2, threshold=100, remaining=10,
                      current=90, upper=100, lower=0, confirmed=1, calculated=2, merits=90,
                      commander='FABER38', events=3, days=1, error='Example', total=100,
                      use='Acquisition', first='2026-10-08', last='2026-10-08',
                      percent=90, next=100, span=100, earned=90, status='Exploited')
        for language in HELP_LANGUAGES:
            for key, template in i18n._TRANSLATIONS[language].items():
                if key.startswith('pp2.'):
                    with self.subTest(language=language, key=key):
                        rendered = template.format(**values)
                        self.assertEqual(i18n.tr_for_language(language, key, **values), rendered)
                        self.assertNotRegex(rendered, r'\{[^}]+\}')

    def test_help_retains_sale_evidence_and_explicit_limitations_in_all_languages(self):
        phrases = {
            'de': ('Verkauf seltener Waren', 'weder automatisch', 'wöchentlichen PP2-Auftrags'),
            'en': ('rare goods sale', 'not automatically', 'weekly PP2 assignment'),
            'fr': ('vente de marchandises rares', 'sans confirmer automatiquement', 'tâche PP2 hebdomadaire'),
            'it': ('vendita di merci rare', 'non automaticamente', 'incarico PP2 settimanale'),
            'no': ('salg av sjeldne varer', 'ikke automatisk', 'ukentlig PP2-oppdrag'),
            'sv': ('försäljning av sällsynta varor', 'inte automatiskt', 'veckouppdrag i PP2'),
            'fi': ('harvinaisten tavaroiden myynnin', 'ei automaattisesti', 'viikoittaisen PP2-tehtävän'),
            'pl': ('sprzedaż rzadkich towarów', 'nie potwierdza automatycznie', 'tygodniowego zadania PP2'),
            'nl': ('verkoop van zeldzame goederen', 'niet automatisch', 'wekelijkse PP2-opdracht'),
            'es': ('venta de mercancías raras', 'no automáticamente', 'encargo PP2 semanal'),
            'tr': ('nadir mal satışını', 'otomatik olarak doğrulamaz', 'haftalık PP2 görevinin'),
            'el': ('πώληση σπάνιων εμπορευμάτων', 'όχι αυτόματα', 'εβδομαδιαίας ανάθεσης PP2'),
        }
        for language, required in phrases.items():
            with self.subTest(language=language):
                paragraph = next(p for p in re.findall(r'<p>(.*?)</p>', help_topic('pp2', language).text)
                                 if '✓' in p and '≈' in p)
                for phrase in required + ('✓', '≈', '?', '—'):
                    self.assertIn(phrase, paragraph)
                for symbol in ('✓', '≈', '?'):
                    self.assertIn(symbol, i18n._TRANSLATIONS[language]['pp2.history.legend'])


class PP2LocalizedViewTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)
    setUp = base.PowerplayViewTests.setUp

    def test_heading_updates_on_power_change_and_handles_no_or_unknown_membership(self):
        self.addCleanup(i18n.set_language, 'de')
        for language in HELP_LANGUAGES:
            i18n.set_language(language)
            for power in ('Nakato Kaine', 'Edmund Mahon'):
                with self.subTest(language=language, power=power):
                    self.state.powerplay.apply(base.event('PowerplayJoin', Power=power))
                    self.state.changed.emit()
                    self.assertEqual(self.view.action_heading.text(),
                                     i18n._TRANSLATIONS[language]['pp2.actions_for'].format(power=power))
                    self.assertIn(power, self.view.action_heading.text())
            self.state.powerplay.apply(base.event('PowerplayLeave', Power='Edmund Mahon'))
            self.state.changed.emit()
            self.assertEqual(self.view.action_heading.text(), i18n._TRANSLATIONS[language]['pp2.actions'])
            self.state.powerplay = base.PowerplayState()
            self.state.changed.emit()
            self.assertEqual(self.view.action_heading.text(), i18n._TRANSLATIONS[language]['pp2.actions'])

    def test_real_sale_and_unknown_merits_render_in_all_languages(self):
        self.addCleanup(i18n.set_language, 'de')
        self.state.powerplay = replay(*REAL)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                i18n.set_language(language)
                with patch('cmdrhelper.ui.powerplay_view.local_today', return_value=DAY):
                    self.view.render()
                table = self.view.recent
                catalog = i18n._TRANSLATIONS[language]
                self.assertEqual(table.rowCount(), 2)
                self.assertEqual(table.item(0, 4).text(), '?')
                self.assertEqual(table.item(0, 1).text(), catalog['pp2.unknown'])
                self.assertEqual(table.item(1, 1).text(), catalog['pp2.chronicle.MarketSell'])
                self.assertEqual(table.item(1, 2).text(),
                                 '12 t Leesti-Teufelssaft\nPeebles Holdings · Crucis Sector HC-U b3-5')
                self.assertEqual(table.item(1, 3).text(), '—')
                self.assertEqual(table.item(1, 4).text(), '✓')
                self.assertIn(catalog['pp2.chronicle.sale_evidence'], table.item(1, 4).toolTip())
