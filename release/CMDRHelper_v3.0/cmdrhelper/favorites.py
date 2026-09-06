"""Commander-owned Explorer bookmarks and their private image copies."""
from datetime import datetime, timezone
from pathlib import Path
import math
import re
import shutil
import sqlite3
from uuid import uuid4

from PIL import Image
from cmdrhelper.screenshot_paths import commander_screenshot_folder, safe_filename_component

TYPES = ('system', 'body', 'surface_location')
CATEGORIES = ('bio', 'geo', 'mining', 'view', 'landing', 'interesting', 'other')
EDITABLE = ('name', 'category', 'note')


class FavoriteStore:
    def __init__(self, database):
        self.database = database
        self.root = database.path.parent.resolve()
        self.images = self.root / 'favorites' / 'images'
        with database._connect() as con:
            con.execute('''CREATE TABLE IF NOT EXISTS favorites (
                id TEXT PRIMARY KEY, commander_id INTEGER NOT NULL REFERENCES commanders(id),
                type TEXT NOT NULL CHECK(type IN ('system','body','surface_location')),
                system_name TEXT NOT NULL, system_address INTEGER,
                body_name TEXT NOT NULL DEFAULT '', body_id INTEGER,
                latitude REAL, longitude REAL, name TEXT NOT NULL,
                category TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
                image_path TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                CHECK ((type = 'surface_location' AND latitude IS NOT NULL
                        AND longitude IS NOT NULL AND latitude BETWEEN -90 AND 90
                        AND longitude BETWEEN -180 AND 180)
                    OR (type != 'surface_location' AND latitude IS NULL AND longitude IS NULL)))''')
            con.execute('CREATE INDEX IF NOT EXISTS favorites_commander ON favorites(commander_id, type, category)')

    def get(self, commander_id, favorite_id):
        with self.database._connect() as con:
            con.row_factory = sqlite3.Row
            row = con.execute('SELECT * FROM favorites WHERE commander_id=? AND id=?',
                              (commander_id, favorite_id)).fetchone()
        if row is None:
            raise ValueError('favorite_not_found')
        return dict(row)

    def list(self, commander_id, search='', kind='', category=''):
        with self.database._connect() as con:
            con.row_factory = sqlite3.Row
            rows = con.execute('SELECT * FROM favorites WHERE commander_id=?', (commander_id,)).fetchall()
        needle = search.strip().casefold()
        result = [dict(r) for r in rows if (not kind or r['type'] == kind)
                  and (not category or r['category'] == category)
                  and (not needle or needle in ' '.join(str(r[k]) for k in
                       ('name', 'system_name', 'body_name', 'note')).casefold())]
        return sorted(result, key=lambda r: (r['name'].casefold(), r['system_name'].casefold(), r['id']))

    def image_file(self, relative):
        """Only managed UUID files may be read or removed, never arbitrary paths."""
        if not isinstance(relative, str) or not re.fullmatch(
                r'favorites/images/[0-9a-f]{32}-[0-9a-f]{32}\.(png|jpg|webp)', relative):
            return None
        path = self.root / relative
        if path.is_symlink() or path.resolve().parent != self.images.resolve():
            return None
        # Do not follow a replaced managed directory outside the data folder.
        if self.images.resolve() != self.root / 'favorites' / 'images':
            return None
        return path if path.is_file() else None

    def _copy_image(self, favorite_id, source):
        source = Path(source)
        with Image.open(source) as im:
            fmt = im.format
            if fmt not in ('PNG', 'JPEG', 'WEBP', 'BMP'):
                raise ValueError('invalid_image')
            im.verify()
        if self.images.resolve() != self.root / 'favorites' / 'images':
            raise ValueError('invalid_image_directory')
        self.images.mkdir(parents=True, exist_ok=True)
        suffix = {'PNG':'png', 'JPEG':'jpg', 'WEBP':'webp', 'BMP':'png'}[fmt]
        target = self.images / f'{favorite_id}-{uuid4().hex}.{suffix}'
        try:
            if fmt == 'BMP':
                with Image.open(source) as im:
                    im.save(target, 'PNG')
            else:
                shutil.copyfile(source, target)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return target.relative_to(self.root).as_posix()

    def _remove_unreferenced(self, relative):
        path = self.image_file(relative)
        if path is None:
            return
        with self.database._connect() as con:
            used = con.execute('SELECT 1 FROM favorites WHERE image_path=? LIMIT 1', (relative,)).fetchone()
        if not used:
            path.unlink(missing_ok=True)

    def save(self, commander_id, values, favorite_id=None, image_source=None, remove_image=False):
        if type(commander_id) is not int or commander_id <= 0:
            raise ValueError('no_commander')
        old = self.get(commander_id, favorite_id) if favorite_id else None
        # Location is immutable on edit. Live values cannot overwrite the saved point.
        record = dict(old or values)
        for key in EDITABLE:
            record[key] = str(values.get(key, record.get(key, ''))).strip()
        record['category'] = record['category'] or 'other'
        if (not record['name'] or not record.get('system_name')
                or record.get('type') not in TYPES or record['category'] not in CATEGORIES):
            raise ValueError('invalid_favorite')
        if record['type'] != 'system' and not record.get('body_name'):
            raise ValueError('invalid_favorite')
        if record['type'] == 'surface_location':
            for key, limit in [('latitude',90), ('longitude',180)]:
                value = record.get(key)
                if type(value) not in (int,float) or not math.isfinite(value) or not -limit <= value <= limit:
                    raise ValueError('invalid_favorite')
        else:
            record['latitude'] = record['longitude'] = None
        if record['type'] == 'system':
            record['body_name'], record['body_id'] = '', None
        record['id'] = old['id'] if old else uuid4().hex
        record['commander_id'] = commander_id
        now = datetime.now(timezone.utc).isoformat()
        record['created_at'] = old['created_at'] if old else now
        record['updated_at'] = now
        previous = old['image_path'] if old else ''
        record['image_path'] = '' if remove_image else previous
        if image_source is not None:
            record['image_path'] = self._copy_image(record['id'], image_source)
        columns = ('id','commander_id','type','system_name','system_address','body_name','body_id',
                   'latitude','longitude','name','category','note','image_path','created_at','updated_at')
        try:
            with self.database._connect() as con:
                if old:
                    con.execute('UPDATE favorites SET name=?,category=?,note=?,image_path=?,updated_at=? '
                                'WHERE id=? AND commander_id=?',
                                tuple(record[k] for k in ('name','category','note','image_path','updated_at','id','commander_id')))
                else:
                    con.execute('INSERT INTO favorites ('+','.join(columns)+') VALUES ('+
                                ','.join('?' for _ in columns)+')', tuple(record.get(k) for k in columns))
        except Exception:
            if record['image_path'] != previous:
                self._remove_unreferenced(record['image_path'])
            raise
        if previous != record['image_path']:
            self._remove_unreferenced(previous)
        return self.get(commander_id, record['id'])

    def delete(self, commander_id, favorite_id):
        record = self.get(commander_id, favorite_id)
        with self.database._connect() as con:
            con.execute('DELETE FROM favorites WHERE id=? AND commander_id=?', (favorite_id, commander_id))
        self._remove_unreferenced(record['image_path'])


def freeze_surface_location(controller):
    """Poll once, then copy scalar identity/position values before opening an editor."""
    controller.poll()
    app = controller.app_state
    snapshot = controller.state.snapshot
    commander_id = getattr(app, 'commander_id', None)
    context = controller.tail.context
    if snapshot is None or not commander_id:
        raise ValueError('no_position')
    if context.fid and context.fid != getattr(app, 'commander_fid', ''):
        raise ValueError('no_position')
    binding = controller.body_binding(snapshot.body_name)
    system = context.system_name or getattr(app, 'system', '')
    if not system:
        raise ValueError('no_position')
    return dict(commander_id=commander_id, type='surface_location', system_name=system,
                system_address=binding.system_address if binding.system_address is not None else
                    context.system_address if context.system_name else getattr(app,'system_address',None),
                body_name=snapshot.body_name, body_id=binding.body_id,
                latitude=snapshot.latitude, longitude=snapshot.longitude,
                name=snapshot.body_name, category='other', note='')


def navigate_to_favorite(store, commander_id, favorite_id, controller):
    record = store.get(commander_id, favorite_id)
    if record['type'] != 'surface_location' or controller.app_state.commander_id != commander_id:
        raise ValueError('favorite_not_found')
    controller.set_target(record['latitude'], record['longitude'], record['body_name'], record['name'])


def screenshot_capture_time(path, *, converted=False):
    """Converted filenames record local source time, not conversion completion time."""
    stem = path.stem
    if not converted:
        stem = re.sub(r'(?i)^(?:Screenshot|HighResScreenshot)[ _-]?', '', stem)
    match = re.match(r'^(\d{4}-\d{2}-\d{2})[_ ](\d{2})[-.](\d{2})[-.](\d{2})(?:_|$)', stem)
    if match:
        try:
            stamp = datetime.strptime('-'.join(match.groups()), '%Y-%m-%d-%H-%M-%S')
            return stamp.timestamp()
        except ValueError:
            pass
    # A converted file without a valid generated timestamp has no reliable
    # capture time or provenance. Do not mistake its conversion mtime for one.
    if converted:
        raise ValueError('invalid_screenshot_name')
    return path.stat().st_mtime


def latest_screenshot(settings, *, commander_fid='', commander_name=''):
    """Freshly scan original Elite images and the active commander's conversions."""
    configured = str(settings.value('screenshots/source_dir', '') or '').strip()
    home = Path.home()
    folders = [Path(configured).expanduser()] if configured else [
        home / 'Pictures/Frontier Developments/Elite Dangerous',
        *[home / base / 'steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Pictures/Frontier Developments/Elite Dangerous'
          for base in ('.steam/steam', '.local/share/Steam')]]
    candidates = []
    for folder in folders:
        try:
            for path in folder.iterdir():
                if (path.is_file() and not path.is_symlink()
                        and path.suffix.lower() in ('.bmp','.png','.jpg','.jpeg','.webp')
                        and re.fullmatch(r'(?i)(?:Screenshot|HighResScreenshot)(?:[ _-]?\d[\d _.-]*)?', path.stem)):
                    candidates.append((screenshot_capture_time(path), path))
        except OSError:
            continue
    target = str(settings.value('screenshots/target_dir', '') or '').strip()
    if target and commander_fid:
        try:
            folder = commander_screenshot_folder(Path(target).expanduser(), commander_name, commander_fid)
            if folder is not None and folder.is_dir():
                # Existing folders can retain the commander's name before a rename.
                folder_name = folder.name[:-(len(safe_filename_component(commander_fid)) + 1)]
                names = {safe_filename_component(commander_name), folder_name}
                for path in folder.iterdir():
                    if (not path.is_file() or path.is_symlink()
                            or path.suffix.lower() not in ('.png', '.jpg', '.jpeg')):
                        continue
                    tail = path.stem[20:]  # YYYY-MM-DD_HH-MM-SS_ followed by commander/system.
                    if not any(tail == name or tail.startswith(name + '_') for name in names):
                        continue
                    try:
                        candidates.append((screenshot_capture_time(path, converted=True), path))
                    except (OSError, ValueError):
                        continue
        except OSError:
            pass
    for _, path in sorted(candidates, key=lambda item:(item[0], str(item[1])), reverse=True):
        try:
            with Image.open(path) as im:
                if im.width > 0 and im.height > 0:
                    im.verify()
                    return path
        except (OSError, ValueError):
            continue
    return None
