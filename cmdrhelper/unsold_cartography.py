"""Sale-scoped cartography claims, independent of cumulative body history."""
from cmdrhelper.valuation import calculate_body_values, journal_valuation_context


def scan_claim(body, previous, timestamp):
    previous = previous or {}
    state = dict(body)
    for field in ('self_mapped', 'efficient_mapping'):
        state[field] = bool(previous.get(field))
    values = calculate_body_values(state)
    # Empty scanned_at denotes mapping performed after the scan was sold.
    scanned_at = previous.get('scanned_at', timestamp)
    value = values['current_value']
    if state['self_mapped'] and not scanned_at:
        value = max(0, value - values['scan_value'])
    return dict(previous, scanned_at=scanned_at,
                mapped_at=previous.get('mapped_at', ''),
                self_mapped=state['self_mapped'],
                efficient_mapping=state['efficient_mapping'],
                estimated_value=value)


def mapping_claim(body, previous, event):
    probes, target = event.get('ProbesUsed'), event.get('EfficiencyTarget')
    claim = dict(previous or {}, mapped_at=event.get('timestamp', ''),
                 self_mapped=True, probes_used=probes, efficiency_target=target,
                 efficient_mapping=(type(probes) is int and type(target) is int
                                    and probes <= target))
    claim.setdefault('scanned_at', '')
    return scan_claim(body, claim, event.get('timestamp', ''))


def plan_cartography_repair(con, commander_id):
    """Reconstruct committed, identity-validated journals without changing the DB."""
    from cmdrhelper.backfill_support import committed_journals, IncompleteRepair
    bodies, claims, unresolved = {}, {}, set()
    address, system = None, ''
    checked = 0
    for filename, events in committed_journals(con, commander_id, relevant_events={
            'Scan', 'SAAScanComplete', 'SellExplorationData', 'MultiSellExplorationData',
            'Location', 'FSDJump', 'CarrierJump'}):
        checked += 1
        valuation_context = journal_valuation_context(filename)
        # The common validator permits irrelevant/menu-only files. Independently
        # require identified ownership before consuming any cartography facts.
        if events:
            fid = con.execute('SELECT fid FROM commanders WHERE id=?', (commander_id,)).fetchone()[0]
            identities = {str(e['FID']) for e in events
                          if e.get('event') in ('Commander', 'LoadGame') and e.get('FID')}
            status = con.execute('SELECT attribution_status FROM journal_sessions WHERE journal_file=?',
                                 (filename,)).fetchone()
            if identities != {str(fid)} or (status and status[0] != 'identified'):
                raise IncompleteRepair(f'Uncertain journal ownership: {filename}')
        for event in events:
            kind, ts = event.get('event'), event.get('timestamp', '')
            if kind in ('Location', 'FSDJump', 'CarrierJump'):
                address = event.get('SystemAddress', address)
                system = event.get('StarSystem', system)
            if kind in ('SellExplorationData', 'MultiSellExplorationData'):
                claims.clear()
                unresolved.clear()
                continue
            addr, bid = event.get('SystemAddress', address), event.get('BodyID')
            if addr is None or bid is None:
                continue
            key = (int(addr), int(bid))
            if kind == 'Scan':
                if event.get('StarType') or 'belt cluster' in event.get('BodyName', '').lower():
                    continue
                body = dict(name=event.get('BodyName', ''), planet_class=event.get('PlanetClass', ''),
                            mass_em=event.get('MassEM'), terraformable=event.get('TerraformState') == 'Terraformable',
                            was_discovered=event.get('WasDiscovered'), was_mapped=event.get('WasMapped'))
                body.update(valuation_context)
                bodies[key] = body
                if event.get('ScanType') == 'NavBeaconDetail':
                    continue
                claim = scan_claim(body, claims.get(key), ts)
            elif kind == 'SAAScanComplete':
                if key not in bodies:
                    unresolved.add(key)
                    continue
                body = bodies[key]
                body.update(valuation_context)
                claim = mapping_claim(body, claims.get(key), event)
            else:
                continue
            claim.update(system_address=key[0], body_id=key[1], system_name=system,
                         body_name=body['name'], planet_class=body['planet_class'],
                         terraformable=body['terraformable'])
            claims[key] = claim
    if unresolved:
        raise IncompleteRepair(f'Mapping without retained scan facts: {sorted(unresolved)}')
    row = con.execute("""SELECT SUM(CASE WHEN base_value>0 THEN base_value ELSE total_earnings END),
        SUM(estimated_total) FROM cartography_sales WHERE commander_id=? AND estimated_total>0
        AND (base_value>0 OR total_earnings>0)""", (commander_id,)).fetchone()
    factor = row[0] / row[1] if row[1] else 1.0
    expected = sorted((key[0], key[1], c['scanned_at'], c['mapped_at'], int(c['self_mapped']),
                       c['estimated_value'], round(c['estimated_value'] * factor),
                       int(c['efficient_mapping']), c.get('probes_used'), c.get('efficiency_target'))
                      for key, c in claims.items())
    existing = con.execute("""SELECT system_address,body_id,scanned_at,mapped_at,self_mapped,
        raw_estimated_value,estimated_value,efficient_mapping,probes_used,efficiency_target
        FROM commander_unsold_cartography WHERE commander_id=? ORDER BY system_address,body_id""",
        (commander_id,)).fetchall()
    if existing and not checked:
        raise IncompleteRepair('Unsold claims have no retained committed journal coverage')
    return {'claims': list(claims.values()), 'factor': factor, 'changed': expected != existing}


def apply_cartography_repair(con, commander_id, plan):
    from cmdrhelper.database import CMDRDatabase
    if not plan['changed']:
        return 0
    before = con.total_changes
    con.execute('DELETE FROM commander_unsold_cartography WHERE commander_id=?', (commander_id,))
    for claim in plan['claims']:
        body = dict(name=claim['body_name'], planet_class=claim['planet_class'],
                    terraformable=claim['terraformable'])
        CMDRDatabase._write_cartography_claim(con, commander_id, claim['system_address'],
            claim['body_id'], claim['system_name'], body, claim, plan['factor'])
    return con.total_changes - before

