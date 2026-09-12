"""Verified orbital ancestry, independent of rendering and body names."""
import json


def parent_metadata(parents, source):
    if not isinstance(parents, list) or source not in ('Journal', 'EDSM'):
        return {}
    path = []
    for entry in parents:
        if not isinstance(entry, dict) or len(entry) != 1:
            return {}
        kind, value = next(iter(entry.items()))
        if kind not in ('Planet', 'Star', 'Null', 'Ring') or isinstance(value, bool):
            return {}
        try:
            number = int(value)
        except (TypeError, ValueError, OverflowError):
            return {}
        if number < 0 or str(number) != str(value):
            return {}
        path.append({kind: number})
    direct = next((v for e in path for k, v in e.items() if k in ('Planet', 'Star')), None)
    star = next((e['Star'] for e in path if 'Star' in e), None)
    # Keep ancestry separate from the renderer's raw-Parents input: no layout change.
    return dict(parent_path=path, parent_source=source, parent_id=direct, parent_star_id=star)


def verified_parents(body):
    return parent_metadata(body.get('parent_path'), body.get('parent_source'))


def choose_parents(existing, incoming):
    old, new = verified_parents(existing), verified_parents(incoming)
    rank = {'Journal': 2, 'EDSM': 1}
    if new and (not old or rank[new['parent_source']] >= rank[old['parent_source']]):
        return new
    return old


def persist_parents(con, address, body):
    """Use existing app_meta for ancestry/provenance; no schema migration."""
    key = f'body_parents.v1:{int(address)}:{int(body["body_id"])}'
    row = con.execute('SELECT value FROM app_meta WHERE key=?', (key,)).fetchone()
    old = json.loads(row[0]) if row else {}
    chosen = choose_parents(old, body)
    if chosen:
        con.execute('INSERT OR REPLACE INTO app_meta(key,value) VALUES(?,?)',
                    (key, json.dumps(chosen, sort_keys=True)))
        con.execute('UPDATE bodies SET parent_id=?,parent_star_id=? WHERE system_address=? AND body_id=?',
                    (chosen['parent_id'], chosen['parent_star_id'], int(address), int(body['body_id'])))
    return chosen
