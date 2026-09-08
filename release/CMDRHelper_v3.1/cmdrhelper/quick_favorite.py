"""Dialog-free quick save through the existing frozen location/store path."""
from datetime import datetime
import logging
import sqlite3
from cmdrhelper.favorites import freeze_surface_location
from cmdrhelper.i18n import tr


def save_quick_favorite(controller, store, notify, refresh):
    try:
        record = freeze_surface_location(controller)
        context = controller.tail.context
        if context.fid and not context.running:
            raise ValueError('no_position')
    except (ValueError, OSError):
        notify(('⚠ ' + tr('quick_favorite.no_coordinates').upper(),))
        return None
    now = datetime.now().astimezone()
    base = tr('quick_favorite.marker') + now.strftime(' %d.%m.%Y %H:%M:%S')
    try:
        names = {row['name'] for row in store.list(record['commander_id'])}
        name, suffix = base, 2
        while name in names:
            name = f'{base} ({suffix})'
            suffix += 1
        record.update(name=name, category='other', note='')
        saved = store.save(record['commander_id'], record)
    except (ValueError, OSError, sqlite3.Error):
        logging.getLogger(__name__).exception('Quick favorite could not be saved')
        notify(('⚠ ' + tr('quick_favorite.save_failed').upper(),))
        return None
    notify(('★ ' + tr('quick_favorite.saved').upper(), saved['body_name'],
            f"{saved['latitude']:.6f}° / {saved['longitude']:.6f}°"))
    refresh()
    return saved
