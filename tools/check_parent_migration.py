#!/usr/bin/env python3
"""Exercise the actual modal migration on a fresh copy; never migrate the input DB.

Usage: QT_QPA_PLATFORM=offscreen python tools/check_parent_migration.py BACKUP_DB
The journal folder defaults to the first recorded journal session's parent.
Artifacts and the working copy stay in a new temporary directory.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QEventLoop, QRectF, QTimer
from PySide6.QtWidgets import QApplication, QDialog
from cmdrhelper.parent_migration import (
    apply_candidates, check_integrity, collect_candidates, digest, fingerprint,
    inventory, migration_required, readonly,
)
from cmdrhelper.ui.parent_migration import ParentMigrationDialog
from cmdrhelper.ui.styles import DARK_STYLESHEET
from cmdrhelper.ui.system_overview import build_layout
from cmdrhelper.ui.system_layout import build_positions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    parser.add_argument('--journals', type=Path)
    parser.add_argument('--system', action='append', default=[],
                        help='Optional system name to include in the regression report')
    parser.add_argument('--reference-341', action='store_true', help='Assert the aggregate 3.4 reference regression totals')
    parser.add_argument('--app-version', help='Simulate a later runtime without changing version.py')
    args = parser.parse_args()
    if args.app_version:
        from cmdrhelper import parent_migration
        parent_migration.__version__ = args.app_version
    source = args.backup.resolve()
    original_hash = digest(source)
    with readonly(source) as con:
        folder = args.journals or Path(con.execute('SELECT journal_file FROM journal_sessions LIMIT 1').fetchone()[0]).parent
        baseline = fingerprint(con)
    journals_before = {p: digest(p) for p in inventory(folder)}
    root = Path(tempfile.mkdtemp(prefix='cmdrhelper-parent-regression-'))
    copy = root / 'cmdrhelper.db'
    shutil.copyfile(source, copy)
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(DARK_STYLESHEET)
    # Cancel the actual modal before starting; compare bytes and directory entries.
    files_before = set(root.iterdir())
    cancel = ParentMigrationDialog(copy, folder)
    QTimer.singleShot(0, cancel.cancel_button.click)
    assert cancel.exec() == QDialog.Rejected
    assert digest(copy) == original_hash and set(root.iterdir()) == files_before
    assert migration_required(copy)
    dialog = ParentMigrationDialog(copy, folder)
    dialog.show()
    app.processEvents()
    dialog.grab().save(str(root / 'dialog.png'))
    loop = QEventLoop()
    result = []
    dialog.start_button.click()
    dialog.worker.completed.connect(result.append)
    dialog.worker.completed.connect(loop.quit)
    watchdog = QTimer()
    watchdog.setSingleShot(True)
    watchdog.timeout.connect(loop.quit)
    watchdog.start(180000)
    loop.exec()
    if not result:
        dialog.worker.wait()
        raise RuntimeError('Migration exceeded regression timeout')
    assert dialog.succeeded, dialog.outcome.text()
    counts = result[0]
    if args.reference_341:
        for key, expected in dict(systems=1262, bodies=10985, parent_id=10980,
                                  parent_star_id=5961, fields=16941, remaining=0).items():
            assert counts[key] == expected, (key, counts[key], expected)
    app.processEvents()
    dialog.grab().save(str(root / 'success.png'))
    dialog.start_button.click()
    assert dialog.result() == QDialog.Accepted
    assert not migration_required(copy)
    with readonly(counts['backup']) as con:
        assert fingerprint(con) == baseline
    with readonly(copy) as con:
        check_integrity(con)
        # A second repair needs no writes, so it also succeeds on a read-only connection.
        second = apply_candidates(con, collect_candidates(inventory(folder))[0])
        assert second['fields'] == second['metadata'] == 0
        con.row_factory = __import__('sqlite3').Row
        systems = con.execute('SELECT system_address,name FROM systems').fetchall()
        layouts = 0
        regressions = {}
        for system in systems:
            bodies = [dict(row) for row in con.execute('SELECT * FROM bodies WHERE system_address=?',
                                                       (system['system_address'],))]
            for body in bodies:
                row = con.execute('SELECT value FROM app_meta WHERE key=?',
                                  (f"body_parents.v1:{system['system_address']}:{body['body_id']}",)).fetchone()
                if row:
                    body.update(json.loads(row[0]))
            for build in (build_layout, build_positions):
                nodes = build(bodies)
                rects = [(n.key, QRectF(n.x, n.y, n.layout_width, n.layout_height))
                         for n in nodes.values() if n.body is not None]
                for i, (key, rect) in enumerate(rects):
                    for other, other_rect in rects[i+1:]:
                        assert not rect.intersects(other_rect), (system['name'], key, other, build.__name__)
            layouts += 1
            if system['name'] in args.system:
                regressions[system['name']] = len(bodies)
    assert digest(source) == original_hash
    assert journals_before == {p: digest(p) for p in inventory(folder)}
    report = dict(result=counts, original_sha256=original_hash, journals_unchanged=len(journals_before),
                  layout_systems=layouts, named_regressions=regressions,
                  animation_ticks=dialog.ships.animation_ticks, artifacts=str(root))
    (root / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
