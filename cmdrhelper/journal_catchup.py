"""Import-local catch-up. All file IO and persistence run in the import worker.

The baseline is retained on failure. Each file's facts, index signature and
cursor commit together; retries therefore resume at the last committed cursor.
Replacement of an already observed file is rejected rather than replaying
non-idempotent personal history against an unrelated byte offset.
"""
import hashlib
import json
import logging
import time
from contextlib import closing
from .startup_runtime import JournalPending, StartupCancelled
from pathlib import Path

from .journal_files import journal_files

logger = logging.getLogger(__name__)


class JournalConflict(RuntimeError):
    reason = 'journal_replaced_or_truncated'


def _signature(stat):
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def _prefix_digest(path, size, cancel=None):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        remaining = size
        while remaining:
            if cancel is not None and cancel.is_set():
                raise StartupCancelled()
            block = stream.read(min(remaining, 1024 * 1024))
            if not block:
                raise JournalPending('journal_replaced_or_truncated')
            digest.update(block)
            remaining -= len(block)
    return digest.hexdigest()


def load_sessions(database):
    with closing(database._connect()) as con:
        cursor = con.execute('SELECT * FROM journal_sessions')
        names = [column[0] for column in cursor.description]
        rows = [dict(zip(names, row)) for row in cursor]
    from .journal_files import journal_sort_key
    return sorted(rows, key=lambda row: journal_sort_key(Path(row['journal_file'])))


def capture(database, folder, cancel=None):
    """Capture before the importer can change index metadata; never write here."""
    indexed = {row['journal_file']: row for row in load_sessions(database)}
    paths = journal_files(folder)
    baseline = {}
    for path in paths:
        if cancel is not None and cancel.is_set():
            raise StartupCancelled()
        stat = path.stat()
        row = indexed.get(str(path), {})
        offset = int(row.get('last_read_offset') or 0)
        if offset > stat.st_size:
            raise JournalConflict('Journal catch-up requires repair: journal was truncated')
        digest = None
        if path == paths[-1] or offset:
            # Bind the whole observed prefix, including bytes not yet persisted.
            digest = _prefix_digest(path, stat.st_size, cancel)
            after = path.stat()
            if ((after.st_dev, after.st_ino) != (stat.st_dev, stat.st_ino)
                    or after.st_size < stat.st_size
                    or (after.st_size == stat.st_size and _signature(after) != _signature(stat))):
                raise JournalPending('journal_changed_during_read')
        baseline[str(path)] = dict(signature=_signature(stat), digest=digest,
                                   offset=offset, fid=row.get('fid_seen'))
    return dict(folder=Path(folder), baseline=baseline,
                current=str(paths[-1]) if paths else None,
                tracked={str(paths[-1])} if paths else set())


def validate_input(context, path):
    """Reject replacement before the import index can reset a committed cursor."""
    old = context['baseline'].get(str(path))
    if old is None:
        return
    stat = path.stat()
    if _signature(stat) == old['signature']:
        return
    dev, ino, size, *_ = old['signature']
    if (stat.st_dev, stat.st_ino) != (dev, ino) or stat.st_size < size:
        raise JournalConflict('Journal catch-up requires repair: journal replaced or truncated')
    if old['digest'] is None:
        raise RuntimeError('Journal catch-up requires repair: unverified historical change')
    if _prefix_digest(path, size) != old['digest']:
        raise RuntimeError('Journal catch-up requires repair: observed prefix changed')


def catch_up(database, context, *, enqueue_fid=None, cancel=None, max_passes=3, time_budget=5.0):
    """Reconcile until the observed directory is stable; never overtake a tail."""
    logger.info('Journal catch-up started')
    deadline = time.monotonic() + time_budget
    for _ in range(max_passes):
        if cancel is not None and cancel.is_set():
            raise StartupCancelled()
        before = {str(path): _signature(path.stat()) for path in journal_files(context['folder'])}
        sessions = _catch_up_pass(database, context, enqueue_fid=enqueue_fid, cancel=cancel, deadline=deadline)
        after = {str(path): _signature(path.stat()) for path in journal_files(context['folder'])}
        if before == after:
            logger.info('Journal catch-up finished')
            return sessions
    raise JournalPending('catchup_budget')


def _catch_up_pass(database, context, *, enqueue_fid=None, cancel=None, deadline=None):
    baseline = context['baseline']
    indexed = {row['journal_file']: row for row in load_sessions(database)}
    paths = journal_files(context['folder'])
    present = {str(path) for path in paths}
    if any(name not in present for name in baseline
           if name == context['current'] or baseline[name]['offset']):
        raise JournalPending('journal_replaced_or_truncated')
    files = events_count = 0
    for path in paths:
        if cancel is not None and cancel.is_set():
            raise StartupCancelled()
        if deadline is not None and time.monotonic() >= deadline:
            raise JournalPending('catchup_budget')
        name = str(path)
        before = path.stat()
        old = baseline.get(name)
        row = indexed.get(name, {})
        offset = int(row.get('last_read_offset') or 0)
        changed = old is None or old['signature'] != _signature(before)
        if not (changed or name == context['current']
                or (old['offset'] and offset < before.st_size)):
            continue
        context['tracked'].add(name)
        raw = path.read_bytes()
        if _signature(before) != _signature(path.stat()):
            raise JournalPending('journal_changed_during_read')
        if old is not None:
            dev, ino, size, *_ = old['signature']
            if ((before.st_dev, before.st_ino) != (dev, ino) or len(raw) < size
                    or (old['digest'] is not None
                        and hashlib.sha256(raw[:size]).hexdigest() != old['digest'])):
                raise JournalConflict('Journal catch-up requires repair: journal replaced or truncated')
            if changed and old['digest'] is None and size:
                raise RuntimeError('Journal catch-up requires repair: unverified historical change')
            if offset < old['offset']:
                raise RuntimeError('Journal catch-up requires repair: committed cursor changed')
        complete = raw.rfind(b'\n') + 1
        if offset > complete:
            raise RuntimeError('Journal catch-up requires repair: cursor outside complete input')
        if complete == offset == len(raw):
            baseline[name] = dict(signature=_signature(before),
                                  digest=hashlib.sha256(raw).hexdigest(), offset=offset,
                                  fid=row.get('fid_seen'))
            continue
        identities, parsed, source_keys, event_offsets, position = {}, [], [], [], 0
        first = last = ''
        for line_number, line in enumerate(raw[:complete].splitlines(keepends=True), 1):
            if position < offset < position + len(line):
                raise RuntimeError('Journal catch-up requires repair: cursor inside a line')
            try:
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise ValueError('Invalid journal event')
            except (ValueError, UnicodeError) as exc:
                if position < offset:
                    # Legacy readers may already have skipped a malformed
                    # historical line. Do not reinterpret committed input.
                    position += len(line)
                    continue
                raise ValueError('Journal catch-up contains invalid complete event') from exc
            stamp = event.get('timestamp') or ''
            first = first or stamp
            last = stamp or last
            if event.get('event') in ('Commander', 'LoadGame') and event.get('FID'):
                identities[str(event['FID'])] = event.get('Name') or event.get('Commander') or ''
            if position >= offset:
                parsed.append(event)
                source_keys.append(f'line:{line_number}')
                event_offsets.append(position)
            position += len(line)
        if complete > offset:
            if len(identities) != 1:
                raise ValueError('Journal catch-up identity is not unambiguous')
            fid, commander_name = next(iter(identities.items()))
            if old and old['offset'] and old['fid'] and old['fid'] != fid:
                raise ValueError('Journal catch-up identity changed')
            cid = database.upsert_commander(fid, commander_name, last)
            session = dict(journal_file=name, commander_id=cid, fid_seen=fid,
                           commander_name_seen=commander_name, first_event_at=first,
                           last_event_at=last, file_size=complete,
                           modified_ns=before.st_mtime_ns,
                           sha256=hashlib.sha256(raw[:complete]).hexdigest(), source_keys=source_keys,
                           event_offsets=event_offsets)
            if cancel is not None and cancel.is_set():
                raise StartupCancelled()
            database.apply_commander_journal_delta(
                cid, path, parsed, complete, enqueue_inara=fid == enqueue_fid,
                session=session, live_current=(path == paths[-1]))
            files += 1
            events_count += len(parsed)
        # Do not overtake an unfinished event in an older file or acknowledge
        # the complete file signature while a partial tail remains.
        if complete < len(raw):
            raise JournalPending('partial_final_line')
        baseline[name] = dict(signature=_signature(before),
                              digest=hashlib.sha256(raw).hexdigest(), offset=complete,
                              fid=next(iter(identities), None))
    logger.debug('Journal catch-up pass finished', extra={'diagnostic_fields': {
        'files': files, 'events': events_count}})
    return [row for row in load_sessions(database) if row['journal_file'] in present]
