from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from .spansh_client import SpanshError, SpanshFleetCarrierClient
from .spansh_galaxy_client import SpanshGalaxyClient

logger = logging.getLogger(__name__)


class CarrierRouteSignals(QObject):
    finished = Signal(object)
    failed = Signal(str, str)


class CarrierRouteWorker(QRunnable):
    def __init__(self, request, client=None):
        super().__init__()
        self.request = request
        self.client = client or SpanshFleetCarrierClient()
        self.signals = CarrierRouteSignals()
        self.setAutoDelete(False)

    @Slot()
    def run(self):
        try:
            route = self.client.calculate(self.request)
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
    def __init__(self, request, generation, client=None):
        super().__init__()
        self.request = request
        self.generation = generation
        self.client = client or SpanshGalaxyClient()
        self.signals = ShipRouteSignals()
        self.setAutoDelete(False)

    @Slot()
    def run(self):
        try:
            route = self.client.calculate(self.request)
        except SpanshError as exc:
            logger.warning("Spansh ship route failed (%s): %s", exc.code, exc.detail)
            self.signals.failed.emit(self.generation, exc.code, exc.detail)
        except Exception as exc:
            logger.exception("Unexpected Spansh ship route failure")
            self.signals.failed.emit(self.generation, "unexpected", str(exc))
        else:
            self.signals.finished.emit(self.generation, route)
