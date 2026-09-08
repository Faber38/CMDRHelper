"""Versioned startup orchestration of the existing three historical backfills."""
from contextlib import closing
from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3

from cmdrhelper.backfill_support import IncompleteRepair, create_repair_backup
from cmdrhelper.biology_backfill import plan_biology_backfill
from cmdrhelper.database import COMMANDER_STATE_REPAIR_REVISIONS, _store_biology_rows
from cmdrhelper.mapping_metadata_backfill import plan_mapping_backfill, apply_mapping_plan
from cmdrhelper.system_visits import apply_visit_plan
from cmdrhelper.visits_backfill import plan_visits_backfill

logger = logging.getLogger(__name__)
FEATURES = ('biology_findings', 'system_visits', 'mapping_metadata')


def repair_status(con, commander_id, feature):
    target = COMMANDER_STATE_REPAIR_REVISIONS[feature]
    row = con.execute('''SELECT revision,status,attempted_revision,last_error
        FROM commander_state_repairs WHERE commander_id=? AND feature=?''',
        (commander_id, feature)).fetchone()
    if row and row[0] >= target:
        return 'complete'
    if row and row[2] == target:
        return 'failed' if row[1] == 'running' else row[1]
    return 'not_run'


def _record(con, commander_id, feature, status, detail=''):
    revision = COMMANDER_STATE_REPAIR_REVISIONS[feature]
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    con.execute('''INSERT INTO commander_state_repairs
        (commander_id,feature,revision,repaired_at,status,attempted_revision,last_attempt_at,last_error)
        VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(commander_id,feature) DO UPDATE SET
        revision=CASE WHEN excluded.status='complete' THEN excluded.revision ELSE revision END,
        repaired_at=CASE WHEN excluded.status='complete' THEN excluded.repaired_at ELSE repaired_at END,
        status=excluded.status,attempted_revision=excluded.attempted_revision,
        last_attempt_at=excluded.last_attempt_at,last_error=excluded.last_error''',
        (commander_id, feature, revision if status == 'complete' else 0,
         now if status == 'complete' else '', status, revision, now, detail))


def _plan(con, commander_id, feature):
    # Personal history with no retained journal manifest cannot be certified complete.
    sources = con.execute('SELECT 1 FROM journal_sessions WHERE commander_id=? OR repair_commander_id=? UNION ALL '
                          'SELECT 1 FROM journal_imports WHERE commander_id=? LIMIT 1',
                          (commander_id, commander_id, commander_id)).fetchone()
    if not sources and con.execute('''SELECT 1 FROM commander_bodies WHERE commander_id=?
        UNION ALL SELECT 1 FROM system_visits WHERE commander_id=?
        UNION ALL SELECT 1 FROM biology WHERE commander_id=? LIMIT 1''',
        (commander_id, commander_id, commander_id)).fetchone():
        raise IncompleteRepair('Personal history exists without retained journal source records')
    if feature == 'biology_findings':
        return plan_biology_backfill(con, commander_id)
    if feature == 'system_visits':
        return plan_visits_backfill(con, commander_id)
    return plan_mapping_backfill(con, commander_id)


def _has_changes(feature, plan):
    if feature == 'mapping_metadata':
        return bool(plan['updates'])
    return bool(plan['missing'] or plan.get('redundant_ids'))


def _apply(con, commander_id, feature, plan):
    if feature == 'biology_findings':
        return _store_biology_rows(con, plan['missing'], missing_only=True)
    if feature == 'system_visits':
        apply_visit_plan(con, plan)
        return len(plan['missing']) + len(plan['redundant_ids'])
    return apply_mapping_plan(con, plan['updates'])


def run_startup_repairs(database, progress=None):
    """Never mark a failed/partial attempt successful; normal startup may continue.

    Data and success marker commit together. On a hard process kill SQLite rolls
    both back; the revision remains pending. Missing inputs and ordinary failures
    are recorded separately after rollback. Completed revisions do no journal I/O.
    """
    path = Path(database).resolve()
    results, backup = [], None
    with closing(sqlite3.connect(path.as_uri() + '?mode=rw', uri=True, timeout=30)) as con:
        con.execute('PRAGMA foreign_keys=ON')
        commanders = [row[0] for row in con.execute('SELECT id FROM commanders ORDER BY id')]
        for commander_id in commanders:
            for feature in FEATURES:
                if repair_status(con, commander_id, feature) == 'complete':
                    continue
                if progress:
                    progress(commander_id, feature)
                try:
                    con.execute('BEGIN IMMEDIATE')
                    # Another process may have finished while we waited for its lock.
                    if repair_status(con, commander_id, feature) == 'complete':
                        con.rollback()
                        continue
                    # Persist the attempt separately so a process kill is distinguishable
                    # from a revision that has never run. This is not a success marker.
                    _record(con, commander_id, feature, 'running',
                            'Attempt started; no committed completion (interrupted if no longer running)')
                    con.commit()
                    con.execute('BEGIN IMMEDIATE')
                    if repair_status(con, commander_id, feature) == 'complete':
                        con.rollback()
                        continue
                    plan = _plan(con, commander_id, feature)
                    if _has_changes(feature, plan) and backup is None:
                        backup = create_repair_backup(path)
                    changed = _apply(con, commander_id, feature, plan)
                    unresolved = plan.get('unresolved', [])
                    status = 'incomplete' if unresolved else 'complete'
                    detail = f'Mapping metadata absent from available journals: {unresolved}' if unresolved else ''
                    _record(con, commander_id, feature, status, detail)
                    con.commit()
                except BaseException as exc:
                    con.rollback()
                    status = 'incomplete' if isinstance(exc, IncompleteRepair) else 'failed'
                    detail = f'{type(exc).__name__}: {exc}'
                    changed = 0
                    try:
                        with con:
                            _record(con, commander_id, feature, status, detail)
                    except Exception:
                        logger.exception('Could not persist repair failure; revision remains pending')
                    if not isinstance(exc, Exception):
                        raise
                result = dict(commander_id=commander_id, feature=feature, status=status,
                              changed=changed, detail=detail, backup=str(backup) if backup else None)
                results.append(result)
                log = logger.info if status == 'complete' else logger.warning
                log('Startup repair commander=%s feature=%s status=%s changed=%s %s',
                    commander_id, feature, status, changed, detail)
    return results
