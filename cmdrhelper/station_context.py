"""Conservative station evidence from boarding one's own ship."""
import re


def embark_station_context(event, context):
    """Return complete station identity, or None; never infer missing flags."""
    fid = context.get('FID')
    if (event.get('event') != 'Embark'
            or not isinstance(fid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', fid)
            or ('FID' in event and event['FID'] != fid)
            or event.get('OnStation') is not True
            or any(event.get(key) is not False for key in ('SRV', 'Taxi', 'Multicrew'))
            or event.get('Fighter', False) is not False
            or type(event.get('ID')) is not int or event['ID'] < 0):
        return None
    for key in ('StarSystem', 'StationName'):
        value = event.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > 512:
            return None
    for key in ('MarketID', 'SystemAddress'):
        value = event.get(key)
        if key == 'SystemAddress' and key not in event:
            continue
        if type(value) is not int or not 0 < value < 2**64:
            return None
    keys = ('StarSystem', 'SystemAddress', 'StationName', 'MarketID', 'StationType')
    for key in keys:
        if context.get(key) not in (None, '') and key in event and context[key] != event[key]:
            return None
    if 'StationType' in event and (
            not isinstance(event['StationType'], str) or not event['StationType'].strip()):
        return None
    return {key: event[key] for key in keys if key in event}
