"""Compare old UI patterns and the new API using a read-only DB snapshot.

Usage: python tools/compare_jump_tips.py --database data/cmdrhelper.db
Prints JSON; never constructs CMDRDatabase or invokes imports/migrations.
"""
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cmdrhelper.jump_tip import HierarchicalJumpTip, evaluate_observations
from cmdrhelper.score_analyzer import ScoreAnalyzer


def compare(connection, commander_id):
    class Snapshot:
        def _connect(self):
            return connection

        def _require_commander_id(self):
            return commander_id

    rows = HierarchicalJumpTip(Snapshot()).observations()
    qualified = [r for r in rows if r["qualified"]]
    names = ["Plio Aip KN-B d13-201"]
    names += [r["name"] for r in sorted(qualified, key=lambda r: (-r["exploration_potential"], r["name"]))[:3]]
    names += [r["name"] for r in sorted(qualified, key=lambda r: (r["exploration_potential"], r["name"]))[:3]]
    names = list(dict.fromkeys(names))
    selected_ids = [r["system_address"] for r in rows if r["name"] in names]
    old = {r["key"]: r for r in ScoreAnalyzer(Snapshot()).jump_recommendations("valuable", limit=10000)["recommendations"]}
    comparisons = []
    for name in names:
        parsed = ScoreAnalyzer.parse_system_name(name)
        result = evaluate_observations(name, rows)
        held_out = evaluate_observations(name, rows, excluded_system_addresses=selected_ids)
        found = next((r for r in rows if r["name"] == name), None)
        pattern = old.get(parsed["code_mass"])
        comparisons.append({"target": name,
                            "observed_standardized_potential": found["exploration_potential"] if found else None,
                            "old_ui_pattern": {k: pattern[k] for k in ("key", "systems", "hits", "score", "recommendation")} if pattern else None,
                            "new": result,
                            "new_common_holdout": {k: held_out.get(k) for k in ("ok", "potential_index", "recommendation", "exploration_potential")}})
    return {"snapshot_at": datetime.now(timezone.utc).isoformat(), "commander_id": commander_id,
            "procedural_systems": len(rows), "qualified_systems": len(qualified),
            "observation_quality": dict(Counter(r["quality"] for r in rows)),
            "qualification_issues": dict(Counter(issue for r in rows for issue in r["issues"])),
            "bio_states": dict(Counter(r["bio"]["state"] for r in rows)),
            "comparison_scope": "Descriptive historical comparison, not a predictive validation. Old uses its actual UI pattern API; new_common_holdout excludes all selected systems together.",
            "comparisons": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--commander-id", type=int)
    args = parser.parse_args()
    with closing(sqlite3.connect(args.database.resolve().as_uri() + "?mode=ro", uri=True)) as source:
        with closing(sqlite3.connect(":memory:")) as snapshot:
            source.backup(snapshot)
            snapshot.execute("PRAGMA query_only=ON")
            ids = [r[0] for r in snapshot.execute("SELECT id FROM commanders")]
            commander = args.commander_id
            if commander is None and len(ids) == 1:
                commander = ids[0]
            if commander not in ids:
                parser.error("Choose an existing --commander-id (required for multiple commanders).")
            print(json.dumps(compare(snapshot, commander), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
