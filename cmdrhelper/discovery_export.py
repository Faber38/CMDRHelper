"""Serialize the displayed discovery snapshot, without querying the database."""
import csv
import io
from cmdrhelper.i18n import tr


COLUMNS = ("time", "commander", "system", "body", "event", "assessment")


def discovery_row(result):
    return (
        result.get("timestamp") or "",
        result.get("commander_name") or result.get("fid") or "",
        result.get("system_name") or "",
        result.get("short_name") or result.get("body_name") or str(result["body_id"]),
        tr("discovery.event." + result["kind"]),
        tr("discovery.assessment." + result["kind"]),
    )


def serialize_discoveries(headers, rows, delimiter=";"):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\r\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue()
