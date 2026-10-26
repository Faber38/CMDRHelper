"""Geometry checks use translated real widgets, never production data."""
import unittest
from unittest.mock import patch

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.ui.powerplay_view import PowerplayView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_powerplay as base
from tests import test_powerplay_day_cache as cache_base


class ToolbarTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)

    def settle(self):
        for _ in range(3):
            self.app.processEvents()

    def check_geometry(self, view, width):
        controls = (view.navigation, view.today_button, view.time_filter,
                    view.system_filter, view.filtered_merits,
                    view.manage_history, view.detach_chronicle_button)
        layout = view.chronicle_header
        self.assertEqual(tuple(layout.itemAt(i).widget() for i in range(layout.count())), controls)
        bounds = layout.geometry()
        rects = [widget.geometry() for widget in controls]
        for widget, rect in zip(controls, rects):
            self.assertTrue(widget.isVisible())
            self.assertTrue(bounds.contains(rect), (bounds, widget.text() if hasattr(widget, 'text') else widget, rect))
            self.assertGreaterEqual(rect.width(), widget.sizeHint().width())
        for i, rect in enumerate(rects):
            for other in rects[i + 1:]:
                self.assertFalse(rect.intersects(other))
        for first, second in zip(rects, rects[1:]):
            self.assertTrue(second.top() > first.bottom() or
                            (abs(second.center().y() - first.center().y()) <= 1 and second.left() > first.right()))
        self.assertEqual(rects[0].left(), bounds.left())
        self.assertEqual(rects[-1].right(), bounds.right())
        rows = {rect.center().y() // 2 for rect in rects}
        centers = [rect.center().y() for rect in rects]
        if width == 2000:
            self.assertLessEqual(max(centers) - min(centers), 1)
            self.assertGreater(rects[-2].left() - rects[-3].right(), layout.spacing())
        if width == 480:
            self.assertGreater(len(rows), 1)
        self.assertLess(view.chronicle_title.geometry().bottom(), bounds.top())
        self.assertGreater(view.chronicle_help.geometry().top(), max(r.bottom() for r in rects))
        self.assertGreater(view.recent.geometry().top(), view.chronicle_help.geometry().bottom())
        # The date arrows and both clock controls also remain fully inside
        # their existing wrappers.
        for wrapper, children in ((view.navigation, (view.previous_day, view.day_label, view.next_day)),
                                  (view.time_filter, (view.time_filter_enabled, view.from_time))):
            for child in children:
                self.assertTrue(wrapper.rect().contains(child.geometry()))

    def test_languages_themes_widths_and_docking(self):
        original = get_language()
        self.addCleanup(set_language, original)
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language in _TRANSLATIONS:
            set_language(language)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                view = PowerplayView(base.ViewState())
                try:
                    view.setStyleSheet(theme)
                    view.show()
                    view.timer.stop()
                    table, model = view.recent, view.recent.model()
                    for detached in (False, True):
                        if detached:
                            view.detach_chronicle()
                            view.timer.stop()
                        host = view.chronicle_window if detached else view
                        for width in (2000, 1000, 600, 480, 2000):
                            with self.subTest(language=language, dark=theme == DARK_STYLESHEET,
                                              detached=detached, width=width):
                                host.resize(width, 1000)
                                self.settle()
                                self.assertEqual(host.width(), width)
                                self.check_geometry(view, width)
                    view.attach_chronicle()
                    self.settle()
                    self.assertIs(view.recent, table)
                    self.assertIs(view.recent.model(), model)
                    self.check_geometry(view, 2000)
                finally:
                    view.attach_chronicle()
                    view.close()
                    view.deleteLater()
                    self.settle()


class ToolbarCacheTests(unittest.TestCase):
    setUpClass = classmethod(cache_base.DayCacheTests.setUpClass.__func__)
    setUp = cache_base.DayCacheTests.setUp
    dispose = cache_base.DayCacheTests.dispose
    journal = cache_base.DayCacheTests.journal
    sync = cache_base.DayCacheTests.sync

    def test_resize_has_no_queries_decoding_render_or_reconstruction(self):
        self.view.show()
        self.app.processEvents()
        for detached in (False, True):
            if detached:
                self.view.detach_chronicle()
            self.view.timer.stop()
            self.app.processEvents()
            statements = []
            self.view._day_cache._con.set_trace_callback(statements.append)
            with patch.object(self.view, 'render') as render, \
                    patch.object(self.view._day_cache, 'load') as load, \
                    patch('cmdrhelper.powerplay_store._decode_day') as decode, \
                    patch.object(self.view.recent, 'setRowCount') as rebuild:
                host = self.view.chronicle_window if detached else self.view
                for width in (2000, 480, 1000, 600, 2000):
                    host.resize(width, 1000)
                    for _ in range(3):
                        self.app.processEvents()
                render.assert_not_called()
                load.assert_not_called()
                decode.assert_not_called()
                rebuild.assert_not_called()
            self.assertEqual(statements, [])
        self.view.attach_chronicle()
