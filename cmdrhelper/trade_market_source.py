"""Bounded, read-only local candidates for trade workers (never a GUI query)."""
from concurrent.futures import TimeoutError
from contextlib import closing, nullcontext
from dataclasses import dataclass
from pathlib import Path
import sqlite3

from .commodity_master import lookup_by_id, lookup_by_symbol
from .market_store import CommodityRef, MarketStore


class TradeReadCancelled(Exception):
    pass


@dataclass(frozen=True)
class TradeMarketSource:
    path: Path | None
    fid: str
    origin_name: str
    origin_address: int | None = None
    coordinates_path: Path | None = None
    ready: object = None
    legacy_cache: object = None
    writer: object = None
    journal_folder: Path | None = None
    station_cache_folder: Path | None = None
    pad_database_path: Path | None = None

    def pad_metadata(self, cancel=None):
        from .pad_metadata import read_pad_metadata
        return read_pad_metadata(self.journal_folder, self.station_cache_folder, cancel,
                                 self.pad_database_path or self.coordinates_path)

    def fallback_cache(self, cancel=None):
        """Wait off-GUI; JSON is eligible only before database publication."""
        from .market_migration import database_authoritative
        def authoritative():
            return ((self.writer is not None and getattr(self.writer, 'authoritative', False))
                    or (self.path is not None and database_authoritative(self.path)))
        if self.writer is not None and self.writer.activated:
            return None
        if self.ready is not None:
            while True:
                if cancel is not None and cancel.is_set():
                    raise TradeReadCancelled()
                try:
                    self.ready.result(timeout=.05)
                    return None
                except TimeoutError:
                    if not self.ready.done():
                        continue
                    if authoritative():
                        raise
                    break
                except Exception:
                    if authoritative():
                        raise
                    break
        if authoritative():
            return None
        return self.legacy_cache

    def legacy_rows(self, cache, max_age):
        rows = cache.shared(max_age)
        from .pad_metadata import matching_pad
        metadata = self.pad_metadata()
        rows = [dict(row, largest_pad=matching_pad(metadata, row['market_id'],
            row['station_name'], row['system_name'], row.get('system_address'))) for row in rows]
        distances = {}
        coordinates = (closing(sqlite3.connect(Path(self.coordinates_path).resolve().as_uri()+'?mode=ro',
                        uri=True, timeout=.25)) if self.coordinates_path is not None else nullcontext(None))
        with coordinates as con:
            from .ui.favorites_view import stored_coordinates
            reference = stored_coordinates(con, self.origin_address, self.origin_name) if con is not None else None
            for row in rows:
                distance = None
                if con is not None:
                    target = stored_coordinates(con, row.get('system_address'), row['system_name'])
                    distance = reference.distance_to(target) if reference and target else None
                if ((self.origin_address is not None and row.get('system_address') == self.origin_address)
                        or row['system_name'].casefold() == self.origin_name.casefold()):
                    distance = 0.0
                distances[row['market_id']] = distance
        return rows, distances

    def candidates(self, query, now, cancel=None):
        def check():
            if cancel is not None and cancel.is_set():
                raise TradeReadCancelled()
        check()
        cache = self.fallback_cache(cancel)
        if cache is not None:
            rows, distances = self.legacy_rows(cache, query.max_age)
            for row in rows:
                check()
                yield row, distances[row['market_id']]
            return
        if self.path is None:
            raise RuntimeError('Local MarketStore is not initialized')
        master = lookup_by_id(query.commodity) if isinstance(query.commodity, int) else lookup_by_symbol(query.commodity)
        if master is None:
            return
        ref = CommodityRef(master.frontier_id, master.symbol)
        from .pad_metadata import matching_pad
        metadata = self.pad_metadata(cancel)
        # Open both connections in their owning worker. Coordinate access is
        # read-only and retains the existing resolver's identity/ambiguity rules.
        coordinates = (closing(sqlite3.connect(Path(self.coordinates_path).resolve().as_uri()+'?mode=ro', uri=True, timeout=.25))
                       if self.coordinates_path is not None else nullcontext(None))
        with MarketStore(self.path, read_only=True, clock=lambda: now) as store, coordinates as con:
            from .ui.favorites_view import stored_coordinates
            reference = stored_coordinates(con, self.origin_address, self.origin_name) if con is not None else None
            store._con.set_progress_handler(lambda: int(cancel is not None and cancel.is_set()), 1000)
            cursor, revision = None, None
            try:
                while True:
                    check()
                    # side=None is essential: missing/zero/insufficient rows
                    # still suppress older community offers before filtering.
                    page = store.query_current_candidates(ref, max_age=query.max_age,
                        limit=500, cursor=cursor, expected_revision=revision)
                    revision = page.revision
                    for candidate in page.items:
                        check()
                        h, value = candidate.header, candidate.commodity
                        distance = None
                        if con is not None:
                            target = stored_coordinates(con, h.system_address, h.system_name)
                            distance = reference.distance_to(target) if reference and target else None
                        if self.origin_address is not None and h.system_address == self.origin_address:
                            distance = 0.0
                        rows = [] if value is None else [dict(
                            commodity_id=value.commodity_id, symbol=value.symbol,
                            commander_buy_price=value.commander_buy_price,
                            commander_sell_price=value.commander_sell_price,
                            supply=value.supply, demand=value.demand)]
                        yield dict(fid=h.fid, source=h.source, market_id=h.market_id,
                            station_name=h.station_name, system_name=h.system_name,
                            system_address=h.system_address, station_type=h.station_type or '',
                            observed_at=h.observed_at.isoformat(), commodities=rows,
                            largest_pad=matching_pad(metadata, h.market_id, h.station_name,
                                                     h.system_name, h.system_address)), distance
                    cursor = page.next_cursor
                    if cursor is None:
                        break
            except sqlite3.OperationalError:
                check()
                raise
            finally:
                store._con.set_progress_handler(None, 0)


def prepare_trade_source(observer, fid, origin_name, origin_address=None, database=None):
    """O(1) GUI handoff: paths/scalars/future only; no DB I/O or cache copy."""
    if observer is None:
        return None
    writer = getattr(observer, 'writer', None)
    cache = getattr(observer, '_cache', None)
    if cache is None:
        # Legacy/injected observers expose an already constructed cache.
        cache = vars(observer).get('cache')
    path = writer.destination if writer is not None else cache.path.parent/'markets.db' if cache is not None else None
    return TradeMarketSource(Path(path) if path is not None else None, fid, origin_name, origin_address,
        Path(database.path) if database is not None else None,
        writer.ready if writer is not None and not writer.activated else None, cache, writer,
        getattr(observer, 'folder', None),
        cache.path.parent.parent/'external'/'spansh' if cache is not None else None,
        Path(database.path) if database is not None else None)
