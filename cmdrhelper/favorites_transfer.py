"""Reusable, data-only favorites serialization and atomic commander-scoped import."""
from cmdrhelper.logging_config import logged_operation
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import math
from pathlib import Path
import sqlite3
import hashlib
from io import BytesIO
from tempfile import TemporaryDirectory
import warnings
import zlib
from zipfile import ZipFile, BadZipFile, ZIP_DEFLATED
from uuid import uuid4

from PIL import Image

from cmdrhelper.favorites import TYPES, CATEGORIES
from cmdrhelper.version import __version__

FORMAT = 'CMDRHelperFavorites'
FORMAT_VERSION = 1
# Database IDs and commander ownership deliberately do not travel between installs.
FIELDS = ('type', 'system_name', 'system_address', 'body_name', 'body_id',
          'latitude', 'longitude', 'name', 'category', 'note', 'image_path',
          'created_at', 'updated_at')
MAX_MEMBER_SIZE = 32 * 1024 * 1024
MAX_PACKAGE_SIZE = 256 * 1024 * 1024
logger = logging.getLogger(__name__)


class TransferError(ValueError):
    """The message is a translatable favorites.transfer.* suffix."""


def validate_record(value):
    if not isinstance(value, dict) or any(k not in value for k in FIELDS):
        raise TransferError('invalid_record')
    record = {k: value[k] for k in FIELDS}
    for key in ('type', 'system_name', 'body_name', 'name', 'category', 'note',
                'image_path', 'created_at', 'updated_at'):
        if not isinstance(record[key], str) or '\x00' in record[key]:
            raise TransferError('invalid_record')
    if (record['type'] not in TYPES or record['category'] not in CATEGORIES
            or not record['name'].strip() or not record['system_name'].strip()
            or (record['type'] != 'system' and not record['body_name'].strip())):
        raise TransferError('invalid_record')
    for key in ('system_address', 'body_id'):
        number = record[key]
        if number is not None and (type(number) is not int or not 0 <= number <= 2**63 - 1):
            raise TransferError('invalid_record')
    for key, limit in (('latitude', 90), ('longitude', 180)):
        number = record[key]
        if record['type'] == 'surface_location':
            if (type(number) not in (int, float) or not -limit <= number <= limit
                    or not math.isfinite(number)):
                raise TransferError('invalid_record')
        elif number is not None:
            raise TransferError('invalid_record')
    if record['type'] == 'system' and (record['body_name'] or record['body_id'] is not None):
        raise TransferError('invalid_record')
    for key in ('created_at', 'updated_at'):
        try:
            datetime.fromisoformat(record[key].replace('Z', '+00:00'))
        except ValueError as exc:
            raise TransferError('invalid_record') from exc
    return record


def serialize_favorites(records):
    favorites = []
    for row in records:
        record = validate_record(row)
        favorites.append(record)
    return json.dumps(dict(format=FORMAT, format_version=FORMAT_VERSION,
                           created_at=datetime.now(timezone.utc).isoformat(),
                           cmdrhelper_version=__version__, favorite_count=len(favorites),
                           favorites=favorites), ensure_ascii=False, indent=2,
                      allow_nan=False) + '\n'


def deserialize_favorites(text):
    def invalid_constant(_):
        raise TransferError('invalid_json')

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise TransferError('invalid_json')
            result[key] = value
        return result

    try:
        document = json.loads(text, parse_constant=invalid_constant,
                              object_pairs_hook=unique_object)
    except (ValueError, RecursionError) as exc:
        raise TransferError('invalid_json') from exc
    if not isinstance(document, dict) or document.get('format') != FORMAT:
        raise TransferError('invalid_format')
    if type(document.get('format_version')) is not int or document['format_version'] != FORMAT_VERSION:
        raise TransferError('unsupported_version')
    records = document.get('favorites')
    if (not isinstance(records, list) or type(document.get('favorite_count')) is not int
            or document['favorite_count'] != len(records)):
        raise TransferError('invalid_record')
    return [validate_record(row) for row in records]


def image_extension(data):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as picture:
                extension = {'PNG': 'png', 'JPEG': 'jpg', 'WEBP': 'webp', 'BMP': 'bmp'}.get(picture.format)
                picture.verify()
            # Decode as well: verify() alone does not detect all truncated JPEGs.
            with Image.open(BytesIO(data)) as picture:
                picture.load()
            return extension
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError,
            Image.DecompressionBombWarning):
        return None


@logged_operation('Favorites export')
def export_package(store, commander_id):
    records = store.list(commander_id)
    images = {}
    missing = 0
    for record in records:
        reference = record['image_path']
        record['image_path'] = ''
        if not reference:
            continue
        path = store.image_file(reference)
        try:
            if path and path.stat().st_size > MAX_MEMBER_SIZE:
                raise TransferError('invalid_archive')
            data = path.read_bytes() if path else b''
        except OSError:
            data = b''
        extension = image_extension(data) if data else None
        if not extension:
            missing += 1
            continue
        name = 'images/' + hashlib.sha256(data).hexdigest() + '.' + extension
        images.setdefault(name, data)
        if sum(map(len, images.values())) > MAX_PACKAGE_SIZE:
            raise TransferError('invalid_archive')
        record['image_path'] = name
    manifest = serialize_favorites(records).encode('utf-8')
    if (len(images) >= 10000 or len(manifest) > MAX_MEMBER_SIZE
            or len(manifest) + sum(map(len, images.values())) > MAX_PACKAGE_SIZE):
        raise TransferError('invalid_archive')
    output = BytesIO()
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
        archive.writestr('favorites.json', manifest)
        for name, data in images.items():
            archive.writestr(name, data)
    return output.getvalue(), dict(count=len(records), images=len(images), missing=missing)


def safe_archive_name(name):
    parts = name.rstrip('/').split('/')
    return (bool(name) and not name.startswith('/') and '\\' not in name and ':' not in name
            and '\x00' not in name and all(p not in ('', '.', '..') for p in parts))


@logged_operation('Favorites package validation')
def read_package(path):
    """Read only the manifest and its images, never extract or follow archive paths."""
    try:
        with ZipFile(path) as archive:
            members = archive.infolist()
            names = [member.filename for member in members]
            if (len(members) > 10000 or len(set(names)) != len(names)
                    or any(not safe_archive_name(m.orig_filename) for m in members)
                    or any(m.file_size > MAX_MEMBER_SIZE or m.flag_bits & 1
                           or (m.external_attr >> 16) & 0o170000 == 0o120000 for m in members)
                    or sum(m.file_size for m in members) > MAX_PACKAGE_SIZE
                    or 'favorites.json' not in names):
                raise TransferError('invalid_archive')
            records = deserialize_favorites(archive.read('favorites.json').decode('utf-8-sig'))
            images = {}
            missing = 0
            for record in records:
                name = record['image_path']
                if not name:
                    continue
                if not safe_archive_name(name) or not name.startswith('images/'):
                    raise TransferError('invalid_archive')
                if name not in images:
                    try:
                        data = archive.read(name)
                        images[name] = data if image_extension(data) else None
                    except (KeyError, BadZipFile, OSError, RuntimeError, NotImplementedError, zlib.error):
                        images[name] = None
                if images[name] is None:
                    missing += 1
            return records, images, missing
    except (BadZipFile, UnicodeError, RuntimeError, NotImplementedError, EOFError, zlib.error) as exc:
        raise TransferError('invalid_archive') from exc


def favorite_identity(record):
    """Stable codes and numeric IDs take precedence over display/location names."""
    def name(key):
        return record[key].strip().casefold()

    system = (('address', record['system_address']) if record['system_address'] is not None
              else ('name', name('system_name')))
    body = None if record['type'] == 'system' else (
        ('id', record['body_id']) if record['body_id'] is not None else ('name', name('body_name')))
    return (record['type'], system, body, record['latitude'], record['longitude'],
            record['category'], name('name'))


@dataclass
class ImportPlan:
    commander_id: int
    records: list
    existing: list
    new_count: int
    duplicate_count: int
    images: dict
    missing_images: int


def prepare_import(store, commander_id, records, images=None, missing_images=0):
    if type(commander_id) is not int or commander_id <= 0:
        raise TransferError('commander_changed')
    records = [validate_record(row) for row in records]
    existing = store.list(commander_id)
    seen = {favorite_identity(row) for row in existing}
    duplicates = 0
    for row in records:
        identity = favorite_identity(row)
        duplicates += identity in seen
        seen.add(identity)
    return ImportPlan(commander_id, records, existing, len(records) - duplicates, duplicates,
                      images or {}, missing_images)


@logged_operation('Favorites import')
def apply_import(store, plan, policy='skip'):
    """Roll back database changes and remove newly copied images on failure.

    Superseded old image files are retained, avoiding irreversible cleanup during import.
    """
    copied = []
    try:
        return _apply_import(store, plan, policy, copied)
    except BaseException:
        for path in copied:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                logger.warning('Could not remove rolled-back favorite image: %s', path, exc_info=True)
        raise


def _apply_import(store, plan, policy, copied):
    if policy not in ('skip', 'replace', 'new'):
        raise ValueError('invalid import policy')
    records = [validate_record(row) for row in plan.records]
    counts = dict(added=0, updated=0, skipped=0)
    local_images = {}
    with store.database._connect() as con:
        con.row_factory = sqlite3.Row
        con.execute('BEGIN IMMEDIATE')
        current = [dict(row) for row in con.execute(
            'SELECT * FROM favorites WHERE commander_id=?', (plan.commander_id,))]
        if sorted(current, key=lambda r: r['id']) != sorted(plan.existing, key=lambda r: r['id']):
            raise TransferError('changed')
        identities = {}
        for row in sorted(current, key=lambda r: (r['created_at'], r['id'])):
            identities.setdefault(favorite_identity(row), row['id'])
        for record in records:
            identity = favorite_identity(record)
            existing_id = identities.get(identity)
            if existing_id and policy == 'skip':
                counts['skipped'] += 1
                continue
            record = dict(record)
            image_name = record['image_path']
            record['image_path'] = ''
            data = plan.images.get(image_name)
            if data:
                if image_name not in local_images:
                    with TemporaryDirectory(prefix='cmdrhelper-favorites-') as temporary:
                        source = Path(temporary) / 'image'
                        source.write_bytes(data)
                        relative = store._copy_image(uuid4().hex, source)
                        copied.append(store.root / relative)
                    local_images[image_name] = relative
                record['image_path'] = local_images[image_name]
            if existing_id and policy == 'replace':
                con.execute('UPDATE favorites SET ' + ','.join(k + '=?' for k in FIELDS)
                            + ' WHERE id=? AND commander_id=?',
                            tuple(record[k] for k in FIELDS) + (existing_id, plan.commander_id))
                counts['updated'] += 1
            else:
                favorite_id = uuid4().hex
                columns = ('id', 'commander_id') + FIELDS
                con.execute('INSERT INTO favorites (' + ','.join(columns) + ') VALUES ('
                            + ','.join('?' for _ in columns) + ')',
                            (favorite_id, plan.commander_id) + tuple(record[k] for k in FIELDS))
                identities.setdefault(identity, favorite_id)
                counts['added'] += 1
    return counts
