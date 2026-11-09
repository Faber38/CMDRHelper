"""Read-only projection for the two-hold window; no I/O or reconstruction."""
from cmdrhelper.i18n import tr
from cmdrhelper.ui.cargo_hud import same_cargo_context


_UNSET = object()


def _ship_hold(state, inv):
    """Display the same published values as Mining, without a second admission policy."""
    if inv is None:
        return {}
    loadout = getattr(state, 'ship_loadout', None)
    matching_loadout = (type(inv.ship_id) is int
                       and inv.ship_id == getattr(loadout, 'ship_id', None)
                       and (not inv.ship_type or not getattr(loadout, 'ship_type', None)
                            or inv.ship_type.casefold() == loadout.ship_type.casefold()))
    ship = {'vehicle_name': ((loadout.ship_name or loadout.ship_type) if matching_loadout else None)
                            or inv.ship_type or ''}
    record = inv.vehicle_records.get('Ship', {})
    stock = inv.ship if inv.ship is not None else record.get('last_confirmed')
    quality = inv.displayed_stock('Ship', '')[1]
    notices = []
    if stock is not None:
        # Ask exactly the same accessor as Mining for every displayed symbol.
        quantities = {symbol: amount for symbol in stock
                      if (amount := inv.displayed_stock('Ship', symbol)[0]) is not None}
        if quantities or inv.displayed_stock('Ship', '')[0] is not None:
            ship['count'] = sum(quantities.values())
            ship['inventory'] = [dict(frontier_name=k, count=n, is_drones=k.casefold() == 'drones')
                                 for k, n in quantities.items() if n]
            if quality == 'stale':
                notices.append(tr('mining.stock_stale') +
                               (' · ' + record['confirmed_at'] if record.get('confirmed_at') else ''))
    capacity = getattr(loadout, 'cargo_capacity', None)
    if matching_loadout and type(capacity) is int and capacity >= 0:
        ship['capacity'] = capacity
        if loadout.loadout_stale or not loadout.loadout_complete:
            notices.append(tr('cargo.live.capacity_stale') +
                           (' · ' + loadout.loadout_timestamp if loadout.loadout_timestamp else ''))
    ship['notice'] = '\n'.join(notices)
    return ship


def holds(state, inventory=_UNSET):
    if inventory is _UNSET:
        inventory = getattr(getattr(state, 'mining_inventory_controller', None), '_last_inventory', None)
    ship, srv = _ship_hold(state, inventory), {'notice': tr('cargo.live.no_srv')}
    cid, fid = getattr(state, 'commander_id', None), getattr(state, 'commander_fid', '')
    if (not cid or not fid or getattr(state, 'viewed_commander_id', cid) != cid
            or (getattr(state, 'sources', None) is not None
                and not getattr(state, '_source_live_context', False))):
        return ship, {}
    active = getattr(state, 'active_srv_type', '')
    if active:
        srv = {'vehicle_name': active}
        snapshot = getattr(state, 'cargo_snapshot', None)
        if (isinstance(snapshot, dict) and snapshot.get('vessel') == 'SRV'
                and same_cargo_context(state, snapshot)):
            srv = dict(snapshot)
    return ship, srv
