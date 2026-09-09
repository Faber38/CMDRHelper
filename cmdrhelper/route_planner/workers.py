from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
import sqlite3

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from .spansh_client import SpanshError, SpanshFleetCarrierClient
from .spansh_galaxy_client import SpanshGalaxyClient
from .system_resolution import valid_id64

logger = logging.getLogger(__name__)


class CarrierRouteSignals(QObject):
    finished = Signal(object)
    failed = Signal(str, str)


class CarrierRouteWorker(QRunnable):
    def __init__(self, request, client=None, *, database_path=None):
        super().__init__()
        self.request = request
        self.client = client or SpanshFleetCarrierClient()
        self.database_path = database_path
        self.signals = CarrierRouteSignals()
        self.setAutoDelete(False)

    @Slot()
    def run(self):
        try:
            route = self.client.calculate(with_known_system_ids(self.request, self.database_path))
        except SpanshError as exc:
            logger.warning("Spansh carrier route failed (%s): %s", exc.code, exc.detail)
            self.signals.failed.emit(exc.code, exc.detail)
        except Exception as exc:
            logger.exception("Unexpected Spansh carrier route failure")
            self.signals.failed.emit("unexpected", str(exc))
        else:
            self.signals.finished.emit(route)


class ShipRouteSignals(QObject):
    finished = Signal(int, object)
    failed = Signal(int, str, str)


class ShipRouteWorker(QRunnable):
    def __init__(self, request, generation, client=None, *, database_path=None):
        super().__init__()
        self.request = request
        self.generation = generation
        self.client = client or SpanshGalaxyClient()
        self.database_path = database_path
        self.signals = ShipRouteSignals()
        self.setAutoDelete(False)

    @Slot()
    def run(self):
        try:
            route = self.client.calculate(with_known_system_ids(self.request, self.database_path))
        except SpanshError as exc:
            logger.warning("Spansh ship route failed (%s): %s", exc.code, exc.detail)
            self.signals.failed.emit(self.generation, exc.code, exc.detail)
        except Exception as exc:
            logger.exception("Unexpected Spansh ship route failure")
            self.signals.failed.emit(self.generation, "unexpected", str(exc))
        else:
            self.signals.finished.emit(self.generation, route)


def with_known_system_ids(request, database_path):
    """Read stored identities in the worker; Spansh still validates each ID."""
    if not database_path:
        return request
    ids = {}
    try:
        with sqlite3.connect(Path(database_path).resolve().as_uri() + '?mode=ro', uri=True) as con:
            for side in ('source', 'destination'):
                if getattr(request, side + '_id64') is not None:
                    continue
                rows = con.execute(
                    'SELECT system_address FROM systems WHERE name = ? COLLATE NOCASE LIMIT 2',
                    (getattr(request, side).strip(),),
                ).fetchall()
                if len(rows) == 1 and valid_id64(rows[0][0]):
                    ids[side + '_id64'] = rows[0][0]
    except (sqlite3.Error, OSError, ValueError):
        logger.debug('No usable stored route system identities')
    return replace(request, **ids)
