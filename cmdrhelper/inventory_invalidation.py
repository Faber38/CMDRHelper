"""Inventory dependencies of a verified source batch; no inventory calculation."""

KINDS = frozenset(('materials', 'mining', 'odyssey'))


def event_kinds(events):
    from .material_inventory import EVENTS as materials
    from .mining_inventory import EVENTS as mining
    from .odyssey_inventory import EVENTS as odyssey
    names = {event.get('event') for event in events}
    return {kind for kind, relevant in (
        ('materials', materials), ('mining', mining | {'CarrierStats'}),
        ('odyssey', odyssey | {'CarrierStats'})) if names & relevant}


def batch_kinds(before, after, applied, *, full=False, indexed=None):
    """Only a verified append to the same current session permits narrow reuse.

    New/removed/reassigned sessions, history changes and recovery after a partial
    commit may change continuity or deduplication, even without inventory events.
    Catch-up has already verified the old byte prefix and committed every delta.
    """
    if full:
        return set(KINDS)
    identity = lambda row: tuple(row.get(key) for key in (
        'journal_file', 'commander_id', 'fid_seen', 'commander_name_seen',
        'attribution_status', 'first_event_at'))
    if [identity(row) for row in before] != [identity(row) for row in after]:
        return set(KINDS)
    for index, (old, new) in enumerate(zip(before, after)):
        cursor = old.get('last_read_offset')
        if cursor != new.get('last_read_offset'):
            # Odyssey deduplicates complete files by digest. Extending a copy
            # changes that reconstruction basis even for a position-only tail.
            digests = {digest for digest in (old.get('sha256'), new.get('sha256')) if digest}
            if any(row.get('sha256') in digests and row['journal_file'] != new['journal_file']
                   for row in (after if indexed is None else indexed)):
                return set(KINDS)
            additions = [event for path, fid, event in applied
                         if path == new['journal_file'] and fid == new.get('fid_seen')]
            if (index != len(after) - 1 or not additions
                    or new.get('attribution_status') != 'identified'
                    or cursor is None or new['last_read_offset'] <= cursor
                    or additions[0].get('_journal_offset') != cursor
                    or new['last_read_offset'] != new.get('file_size')):
                return set(KINDS)
        else:
            # A touch with the same verified digest does not change the input.
            for key in ('file_size', 'sha256', 'committed_prefix_sha256'):
                if old.get(key) != new.get(key):
                    return set(KINDS)
            if (old.get('modified_ns') != new.get('modified_ns')
                    and (not new.get('sha256')
                         or new.get('attribution_status') != 'identified')):
                return set(KINDS)
    return event_kinds(event for _, _, event in applied)
