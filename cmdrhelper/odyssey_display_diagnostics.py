"""Strict export boundary for the optional, in-memory Odyssey UI snapshot."""
from datetime import datetime, timezone
import math
import re

from cmdrhelper.logging_config import sanitize

STALE_SECONDS = 300
ROW_LIMIT = 2048
COUNTER_LIMIT = 1_000_000
# Every exported leaf has an explicit type, limit or vocabulary. Unknown keys
# never cross this boundary. There is no raw model/log/settings payload field.
COUNT = ('int', 0, COUNTER_LIMIT)
SIZE = ('int', 0, 100_000)
COORD = ('int', -100_000, 100_000)
REAL = ('float', 0, 100_000)
BOOL = ('bool',)
TEXT = ('technical_text',)
VERSION = ('version',)
GEOMETRY = {'x': COORD, 'y': COORD, 'width': SIZE, 'height': SIZE}
DIMENSIONS = {'width': SIZE, 'height': SIZE}
SCROLL = {'value': COUNT, 'minimum': COUNT, 'maximum': COUNT, 'page_step': COUNT}
SCHEMA = {
    'environment': {
        'os': ('enum', 'Linux', 'Windows', 'Darwin', 'other'),
        'app_version': VERSION, 'python_version': VERSION, 'qt_version': VERSION,
        'pyside_version': VERSION, 'platform_plugin': TEXT,
        'theme': ('enum', 'dark', 'light'), 'font_family': TEXT,
        'font_point_size': REAL, 'font_pixel_size': SIZE,
        'window_logical_size': DIMENSIONS, 'window_dpr': REAL,
        'screen_available': BOOL, 'screen_logical_geometry': GEOMETRY,
        'screen_available_logical_geometry': GEOMETRY, 'screen_dpr': REAL,
        'logical_dpi_x': REAL, 'logical_dpi_y': REAL,
        'physical_dpi_x': REAL, 'physical_dpi_y': REAL,
    },
    'table': {
        'widget_logical_size': DIMENSIONS, 'viewport_logical_size': DIMENSIONS,
        'column_widths_logical': ('list', SIZE, 7),
        'column_visual_order': ('list', ('int', 0, 6), 7),
        'columns_hidden': ('list', BOOL, 7),
        'visible_row_heights_logical': ('list', SIZE, 256),
        'row_heights_truncated': BOOL, 'font_height_logical': SIZE,
        'font_ascent_logical': SIZE, 'font_descent_logical': SIZE,
        'digit_width_logical': SIZE, 'horizontal_scroll': SCROLL,
        'vertical_scroll': SCROLL,
        'delegate': ('enum', 'OdysseyRowDelegate', 'other'),
        'selected_rows': COUNT, 'hovered_row': BOOL, 'pointer_inside': BOOL,
        'visible_summary_rows': COUNT, 'visible_detail_rows': COUNT,
        'visible_single_rows': COUNT,
        'palette_base': ('color',), 'palette_text': ('color',),
    },
    'stock_cells': {key: COUNT for key in (
        'numeric', 'zero', 'dash', 'empty', 'unknown', 'omitted_detail', 'not_applicable',
        'other_text', 'potentially_elided', 'projection_mismatch',
        'rows_examined', 'cells_examined')},
    'scan_truncated': BOOL,
    'events': {key: COUNT for key in (
        'resize', 'scroll', 'paint', 'viewport_update_requests', 'geometry_changes')},
}


def _checked(value, spec):
    if isinstance(spec, dict):
        if type(value) is not dict:
            return None
        result = {}
        for key, child in spec.items():
            if key in value:
                clean = _checked(value[key], child)
                if clean is not None:
                    result[key] = clean
        return result
    kind = spec[0]
    if kind == 'int':
        return value if type(value) is int and spec[1] <= value <= spec[2] else None
    if kind == 'float':
        return value if type(value) in (int, float) and math.isfinite(value) and spec[1] <= value <= spec[2] else None
    if kind == 'bool':
        return value if type(value) is bool else None
    if kind == 'enum':
        return value if type(value) is str and value in spec[1:] else None
    if kind == 'list':
        if type(value) is not list or len(value) > spec[2]:
            return None
        clean = [_checked(item, spec[1]) for item in value]
        return clean if all(item is not None for item in clean) else None
    if type(value) is not str or len(value) > 96:
        return None
    pattern = {'technical_text': r'[\w .()+-]{1,96}',
               'version': r'\d+(?:\.\d+){1,3}(?:[a-zA-Z0-9+-]*)?',
               'color': r'#[0-9a-fA-F]{6}'}[kind]
    return value if re.fullmatch(pattern, value) and sanitize(value) == value else None


def export_snapshot(snapshot=None, *, now=None):
    """Return only validated technical fields, never stale measurements as live."""
    result = {'status': 'unavailable', 'message': 'Kein Odyssey-Snapshot verfügbar',
              'last_visible': False, 'stale_after_seconds': STALE_SECONDS}
    if type(snapshot) is not dict:
        return result
    status = snapshot.get('status')
    if status not in ('valid', 'invalidated', 'capture_failed'):
        return result
    if status == 'capture_failed':
        return dict(result, status=status, message='Odyssey-Snapshot konnte nicht erfasst werden')
    try:
        created = datetime.fromisoformat(snapshot['created_at'])
        if created.tzinfo is None:
            return result
        age = max(0, int(((now or datetime.now(timezone.utc)) - created).total_seconds()))
    except (KeyError, TypeError, ValueError, OverflowError):
        return result
    result.update(created_at=created.astimezone(timezone.utc).isoformat(),
                  age_seconds=age, last_visible=True)
    if status == 'invalidated':
        return dict(result, status=status, message='Odyssey-Snapshot ungültig: Kontextwechsel oder erneutes Laden')
    result.update(_checked(snapshot, SCHEMA))
    result.update(status='stale' if age > STALE_SECONDS else 'valid',
                  message='Zuletzt sichtbar; veralteter Snapshot' if age > STALE_SECONDS else 'Zuletzt sichtbar; Momentaufnahme',
                  size_units='Qt logical pixels; DPR is physical/logical ratio',
                  counter_scope='Observed Qt events since view creation; saturating counters',
                  paint_proves_correct_display=False,
                  projection_scope='Existing in-memory stock projection; text and DisplayRole are the same model',
                  classification_scope='Loaded table rows, at most 2048; zero is a subset of numeric; unknown, omitted and not_applicable are projection counts')
    return result
