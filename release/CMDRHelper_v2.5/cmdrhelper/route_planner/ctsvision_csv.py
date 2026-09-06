from __future__ import annotations

import csv
from pathlib import Path

from .models import CarrierRoute


HEADER = (
    "System Name",
    "Distance",
    "Distance Remaining",
    "Tritium in tank",
    "Tritium in market",
    "Fuel Used",
    "Icy Ring",
    "Pristine",
    "Restock Tritium",
)


def export_ctsvision_csv(route: CarrierRoute, path) -> Path:
    """Schreibt eine Spansh-Carrierroute im CTSVision-Referenzformat."""
    target = Path(path)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(
            handle,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_ALL,
            lineterminator="\r\n",
        )
        writer.writerow(HEADER)
        for jump in route.jumps:
            writer.writerow(
                (
                    jump.system,
                    _csv_value(jump.distance),
                    _csv_value(jump.distance_remaining),
                    _csv_value(jump.fuel_in_tank),
                    _csv_value(jump.tritium_in_market),
                    _csv_value(jump.tritium_used),
                    _csv_bool(jump.has_icy_ring),
                    _csv_bool(jump.is_system_pristine),
                    _csv_bool(jump.must_restock),
                )
            )
    return target


def _csv_value(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _csv_bool(value):
    if value is None:
        return ""
    return "Yes" if value else "No"
