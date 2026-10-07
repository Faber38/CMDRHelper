"""Offline regeneration from the hash-pinned original EDCD CSVs (no network)."""
import csv
import hashlib
import io
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cmdrhelper._commodity_master_data import SOURCE_FILES
from cmdrhelper.mining_catalog import MINING_COMMODITIES


def build_rows(source_root=ROOT / 'tools/data/fdevids'):
    mining = {m.symbol.casefold(): ('surface', 'asteroid') if m.origin == 'both'
              else (m.origin,) for m in MINING_COMMODITIES}
    rows, ids, symbols = [], set(), set()
    for filename, _, _, size, digest in SOURCE_FILES:
        raw = (source_root / filename).read_bytes()
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Source snapshot checksum mismatch: ' + filename)
        rare = filename == 'rare_commodity.csv'
        for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
            cid, symbol = int(row['id']), row['symbol']
            if cid in ids or symbol.casefold() in symbols:
                raise ValueError('Ambiguous commodity identity')
            ids.add(cid); symbols.add(symbol.casefold())
            raw_origin = row.get('market_id', '').strip() if rare else ''
            origin = int(raw_origin) if raw_origin else None
            if origin is not None and not 0 < origin < 2**64:
                raise ValueError('Invalid origin MarketID')
            rows.append((cid, symbol, row['name'], row['category'], rare,
                         mining.get(symbol.casefold(), ()), origin))
    return tuple(sorted(rows))


def render(rows):
    return 'COMMODITIES = (\n' + ''.join('    ' + repr(row) + ',\n' for row in rows) + ')\n'


if __name__ == '__main__':
    path = ROOT / 'cmdrhelper/_commodity_master_data.py'
    header = path.read_text().split('COMMODITIES = (', 1)[0]
    path.write_text(header + render(build_rows()))
