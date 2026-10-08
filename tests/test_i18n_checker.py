import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import check_i18n as checker


class CatalogReaderTests(unittest.TestCase):
    def read(self, source):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'catalog.py'
            path.write_text(source, encoding='utf-8')
            return checker.load_translation_file(path)

    def test_all_definition_forms_and_composed_text_in_execution_order(self):
        table, duplicates = self.read('''
TRANSLATIONS = {'part.a': 'First', 'part.b': 'second'}
TRANSLATIONS.update({'part.a': 'New', 'snapshot': TRANSLATIONS['part.a']})
TRANSLATIONS['assembled'] = ' / '.join(TRANSLATIONS['part.' + key] for key in ('a', 'b'))
TRANSLATIONS['assembled'] = TRANSLATIONS['assembled'] + (' ' 'end')
''')
        self.assertEqual(table, {'part.a': 'New', 'part.b': 'second',
                                 'snapshot': 'First', 'assembled': 'New / second end'})
        self.assertEqual(duplicates, ['part.a', 'assembled'])

    def test_duplicate_literal_keys_are_not_lost(self):
        table, duplicates = self.read("TRANSLATIONS = {'a': 'one', 'a': 'two'}\n"
                                      "TRANSLATIONS.update({'a': 'three', 'a': 'four'})\n"
                                      "TRANSLATIONS['a'] = 'five'\n")
        self.assertEqual(table, {'a': 'five'})
        self.assertEqual(duplicates, ['a'] * 4)

    def test_reassignment_evaluates_rhs_before_replacing_table(self):
        table, _ = self.read("TRANSLATIONS = {'old': 'text'}\n"
                             "TRANSLATIONS = {'new': TRANSLATIONS['old']}\n")
        self.assertEqual(table, {'new': 'text'})

    def test_unsupported_code_and_nonstring_values_are_rejected(self):
        for source in ("TRANSLATIONS = {'a': str(123)}",
                       "TRANSLATIONS = {'a': 1}", "TRANSLATIONS = {1: 'a'}",
                       "import os\nTRANSLATIONS = {}",
                       "TRANSLATIONS = {}\nraise RuntimeError('must not run')"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.read(source)


class FormatValidationTests(unittest.TestCase):
    def test_format_specs_conversions_repetitions_and_escaped_braces(self):
        self.assertEqual(checker.format_fields('{{literal}} {x:.1f} {name!r} {x:.1f}'),
                         (('name', '', 'r'), ('x', '.1f', ''), ('x', '.1f', '')))
        self.assertEqual(checker.placeholders('{power} {point.x} {items[key]}'),
                         {'power', 'point', 'items'})
        self.assertEqual(checker.format_fields('{count:0{width}d}'),
                         (('count', '0{width}d', ''), ('width', '', '')))
        self.assertEqual(checker.format_fields('{a} {b}'), checker.format_fields('{b} {a}'))

    def test_bad_format_fields_are_rejected(self):
        for text in ('{', '}', '{power', '{}', '{0}', '{power!z}', '{x:.1q}',
                     '{x[}', '{x.}', '{x!s:d}', '{x!r:.1f}', '{x:{width:{depth}}}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                checker.format_fields(text)

    def run_checker(self, en, other, duplicates=()):
        catalogs = {'en': (Path('en.py'), en, []),
                    'fr': (Path('fr.py'), other, list(duplicates))}
        output = io.StringIO()
        with patch.object(checker, 'discover_languages', return_value=catalogs), \
                patch.object(checker, 'find_used_translation_keys', return_value=(set(), [])), \
                contextlib.redirect_stdout(output):
            result = checker.main()
        return result, output.getvalue()

    def test_checker_fails_for_each_defect_including_reference_formats(self):
        for en, other, duplicates, message in (
                ({'k': 'ok'}, {'k': '   '}, (), 'leerer Text'),
                ({'k': '{x!z}'}, {'k': '{x!z}'}, (), 'ungültiges Format'),
                ({'k': '{x:.1f}'}, {'k': '{x:.2f}'}, (), 'PLATZHALTER'),
                ({'k': '{x!r}'}, {'k': '{x!s}'}, (), 'PLATZHALTER'),
                ({'k': '{x} {x}'}, {'k': '{x}'}, (), 'PLATZHALTER'),
                ({'k': '{power}'}, {'k': '{system}'}, (), 'PLATZHALTER'),
                ({'k': 'ok'}, {'k': 'ok'}, ('k',), 'DOPPELTE'),
                ({'pp2.actions': 'Actions'}, {}, (), 'fehlt')):
            with self.subTest(message=message, other=other):
                result, output = self.run_checker(en, other, duplicates)
                self.assertEqual(result, 1)
                self.assertIn(message, output)

    def test_material_fallback_is_permitted_but_pp2_is_not(self):
        key = sorted(checker.ENGLISH_FALLBACK_KEYS)[0]
        self.assertEqual(self.run_checker({key: 'Material'}, {})[0], 0)
        self.assertFalse(checker.intentional_english_fallback('pp2.actions', {'pp2.actions': 'Actions'}))

    def test_scanner_understands_language_argument_position(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'view.py'
            path.write_text("tr('pp2.actions')\ntr_for_language(language, 'pp2.actions_for', power=name)\n"
                            "tr('pp2.action.' + token)\n", encoding='utf-8')
            with patch.object(checker, 'PROJECT_ROOT', Path(folder)), \
                    patch.object(checker, 'iter_project_python_files', return_value=[path]):
                keys, dynamic = checker.find_used_translation_keys()
            self.assertEqual(keys, {'pp2.actions', 'pp2.actions_for'})
            self.assertEqual(dynamic, [('view.py', 3)])
