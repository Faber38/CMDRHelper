"""Volatile presentation evidence from the existing uploader results.

No scheduling, journal access, checkpoints or persistence. A successful empty
run is not a server acknowledgement. Sources of the same FID retain separate
errors so success on another source cannot clear an unresolved upload.
"""


def publish(state):
    evidence = getattr(state, '_edsm_runtime_by_fid', {}).get(state.commander_fid, {})
    sources = evidence.get('sources', {})
    records = list(sources.values())
    statuses = {row['status'] for row in records}
    status = next((value for value in ('error', 'running', 'waiting', 'unknown', 'ok')
                   if value in statuses), 'unknown')
    if not getattr(state, 'edsm_enabled', False):
        status = 'disabled'
    state.edsm_upload_status = status
    state.edsm_upload_message = next((row['error'] for row in records if row['error']), '')
    state.edsm_upload_details = {
        'confirmed': evidence.get('confirmed', 0),
        'outcomes': tuple(dict.fromkeys(row['outcome'] for row in records)),
        'errors': tuple(dict.fromkeys(row['error'] or row['message'] for row in records
                                    if row['error'] or row['message'])),
    }


def observe(state, fid, source, result):
    """Consume one progress/result notification, bound to its original owner."""
    if not fid:
        return
    cache = getattr(state, '_edsm_runtime_by_fid', None)
    if cache is None:
        cache = state._edsm_runtime_by_fid = {}
    evidence = cache.setdefault(fid, {'sources': {}, 'confirmed': 0})
    row = evidence['sources'].setdefault(source, {
        'status': 'unknown', 'error': '', 'message': '', 'outcome': 'unknown',
        'confirmed': False,
    })
    count = result.get('events_confirmed', 0)
    count = count if type(count) is int and count > 0 else 0
    if count or result.get('upload_attempted'):
        # This is a last-result count, deliberately not an accumulating counter.
        evidence['confirmed'] = count
    error = result.get('error') or ''
    if result.get('running'):
        row.update(status='running', outcome='running')
    elif result.get('cancelled') or error == '__cancelled__':
        row.update(status='error' if row['error'] else 'unknown', outcome='cancelled', confirmed=False)
    elif result.get('skipped') or result.get('initialized'):
        row.update(status='error' if row['error'] else 'unknown', outcome='skipped', confirmed=False)
    elif result.get('retry_paused'):
        row.update(status='waiting', outcome='retry')
        if not row['error']:
            row['message'] = error
    elif error:
        if result.get('upload_attempted'):
            row['error'] = error
        row.update(status='waiting' if result.get('retry_scheduled') else
                   'error' if row['error'] else 'unknown',
                   message=error, outcome='partial' if count else
                   'retry' if result.get('retry_scheduled') else 'failed')
    elif count and result.get('confirmation_complete'):
        row.update(status='ok', error='', message='', outcome='confirmed', confirmed=True)
    elif result.get('upload_attempted') or result.get('events_sent'):
        row.update(status='error' if row['error'] else 'unknown',
                   outcome='partial' if count else 'unconfirmed', confirmed=False)
    else:
        # Never heal an open error or create success merely because error=''.
        if row['status'] == 'running':
            row['status'] = 'error' if row['error'] else 'unknown'
        elif row['status'] == 'waiting':
            row['status'] = 'error' if row['error'] else 'ok' if row['confirmed'] else 'unknown'
        row['message'] = ''
        row['outcome'] = 'idle'
    if fid == getattr(state, 'commander_fid', ''):
        publish(state)
        state.changed.emit()


def retire_source(state, source):
    """Discard evidence belonging to a removed source generation."""
    for evidence in getattr(state, '_edsm_runtime_by_fid', {}).values():
        evidence['sources'].pop(source, None)
    publish(state)
    state.changed.emit()
