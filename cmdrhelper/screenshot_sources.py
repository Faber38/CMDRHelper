"""Screenshot ownership comes from verified journal sources, never UI selection."""
from pathlib import Path
from urllib.parse import quote

from .game_instances import confirmed_selection, inspect_instances


def source_key(fid):
    return 'screenshots/commanders/' + quote(str(fid), safe='') + '/source_dir'


def configured_source(settings, fid):
    return str(settings.value(source_key(fid), '') or '').strip() if fid else ''


def screenshot_dir(journal_dir):
    """Preserve the actual Wine user/prefix (also works with native Saved Games)."""
    path = Path(journal_dir).expanduser()
    if tuple(path.parts[-3:]) != ('Saved Games', 'Frontier Developments', 'Elite Dangerous'):
        return None
    return path.parents[2] / 'Pictures/Frontier Developments/Elite Dangerous'


def source_owners(manager):
    # Disabled sources still carry provenance and can reveal a conflicting owner.
    registry = getattr(manager, 'registry', None)
    sources = {source.id: source for source in getattr(registry, 'sources', ())}
    sources.update({key: runtime.source for key, runtime in manager.runtimes.items()})
    result = []
    for key, source in sources.items():
        runtime = manager.runtimes.get(key)
        rows = runtime.processor.sessions if runtime is not None else ()
        fids = {r.get('fid_seen') for r in rows
                if r.get('attribution_status') == 'identified' and r.get('fid_seen')}
        fids.update(fid for fid, _ in getattr(source, 'identities', ()) if fid)
        result.append((source, fids))
    return result


def migrate_legacy(settings, manager):
    legacy = str(settings.value('screenshots/source_dir', '') or '').strip()
    if not legacy or manager is None:
        return
    path = Path(legacy).expanduser().resolve()
    owners = set()
    for source, fids in source_owners(manager):
        candidate = screenshot_dir(source.path)
        if candidate is not None and candidate.resolve() == path:
            if not fids:
                return
            owners.update(fids)
    if len(owners) == 1:
        fid = next(iter(owners))
        if not configured_source(settings, fid) and not source_conflicts(settings, manager, fid, legacy):
            settings.setValue(source_key(fid), legacy)
            settings.sync()


def suggested_source(manager, fid):
    if manager is None or not fid:
        return ''
    paths = {str(path) for source, fids in source_owners(manager)
             if source.enabled and fids == {fid} and (path := screenshot_dir(source.path)) is not None}
    return next(iter(paths)) if len(paths) == 1 else ''


def live_context(state):
    manager = getattr(state, 'sources', None)
    if manager is None:
        return None
    # Reinspect processes: a cached selection may outlive a game/login switch.
    selected = confirmed_selection(inspect_instances(), manager.runtimes.values())
    if selected is None:
        return None
    source_id, cid, fid = selected
    runtime = manager.runtimes[source_id]
    rows = [r for r in runtime.processor.sessions if r.get('commander_id') == cid
            and r.get('fid_seen') == fid and r.get('attribution_status') == 'identified']
    data = runtime.processor.projection_for(rows)
    if not data or data.get('commander_fid') != fid:
        return None
    session = data.get('latest_journal_session') or {}
    if (session.get('fid_seen') != fid or session.get('attribution_status') != 'identified'
            or session.get('journal_file') != rows[-1]['journal_file']):
        return None
    return dict(fid=fid, commander=data.get('commander_identity_name') or data.get('commander') or '',
                system=data.get('system') or '', source_id=source_id,
                journal=session['journal_file'], first_event_at=session.get('first_event_at', ''),
                last_timestamp=data.get('last_timestamp', ''), suggested=str(screenshot_dir(runtime.source.path) or ''))


def source_conflicts(settings, manager, fid, path):
    """Explicit mappings may not silently share another commander's source."""
    if not path:
        return False
    canonical = Path(path).expanduser().resolve()
    for key in settings.allKeys():
        if (key.startswith('screenshots/commanders/') and key.endswith('/source_dir')
                and key != source_key(fid)):
            other_path = str(settings.value(key, '') or '').strip()
            if other_path and Path(other_path).expanduser().resolve() == canonical:
                return True
    if manager is None:
        return False
    for source, fids in source_owners(manager):
        for other in fids - {fid}:
            configured = configured_source(settings, other)
            candidates = [screenshot_dir(source.path)]
            if configured:
                candidates.append(Path(configured).expanduser())
            if any(candidate is not None and candidate.resolve() == canonical for candidate in candidates):
                return True
    return False


def capture_identity(context, source):
    """Do not attach an earlier session's BMP or a later system to a capture."""
    from datetime import datetime
    from .screenshot_paths import screenshot_capture_time
    stamp = screenshot_capture_time(source)
    def event_time(value):
        try:
            parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            return parsed.timestamp() if parsed.tzinfo is not None else None
        except (ValueError, TypeError):
            return None
    first = event_time(context.get('first_event_at'))
    if first is not None and stamp < first:
        return None
    identity = dict(context)
    last = event_time(context.get('last_timestamp'))
    if last is None or stamp < last:
        identity['system'] = ''
    return identity
