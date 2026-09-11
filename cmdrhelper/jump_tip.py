"""Read-only, UI-independent hierarchical exploration estimates.

See docs/hierarchical_jump_tip.md for observation rules, constants and limits.
No target index, credits actually earned, or mapping ownership enters the score.
"""
from collections import Counter, defaultdict
import math
from statistics import mean, median

from cmdrhelper.belt_projection import is_belt_cluster
from cmdrhelper.bio_valuation import base_value, is_complete
from cmdrhelper.score_analyzer import ScoreAnalyzer
from cmdrhelper.valuation import BODY_VALUES, calculate_body_values


PRIOR_SYSTEMS = 25.0
WINSOR_QUANTILE = 0.95
MIN_BIO_COMPARISONS = 5
CLASS_LIMITS = ((0.5, "weak"), (1.25, "average"), (2.0, "interesting"), (4.0, "good"))


def quantile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def quality_label(n):
    return "very_low" if n < 5 else "low" if n < 25 else "usable" if n < 50 else "good"


def wilson_interval(hits, n):
    """Nominal 95% interval for raw observations, not a predictive interval."""
    if not n:
        return None
    z = 1.96
    p = hits / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    width = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [max(0.0, centre - width), min(1.0, centre + width)]


def shrink(value, n, parent):
    if not n:
        return parent
    return (n * value + PRIOR_SYSTEMS * parent) / (n + PRIOR_SYSTEMS)


def is_astronomical_body(body):
    kind = str(body.get("body_type") or "").casefold()
    name = str(body.get("name") or "").casefold()
    return not (is_belt_cluster(body) or kind in {"ring", "beltcluster", "barycentre", "barycenter"}
                or name.endswith(" ring"))


def canonical_class(value):
    text = str(value or "").casefold()
    if text in {"earthlike body", "earthlike world", "earth-like world", "earth-like body"}:
        return "Earthlike body"
    return next((key for key in BODY_VALUES if key.casefold() == text), value or "")


def body_potential(body):
    """All planets normally discovered/mapped, efficient DSS; stars scan-only."""
    normalized = dict(body, planet_class=canonical_class(body.get("planet_class")),
                      was_discovered=True, was_mapped=True, self_mapped=False,
                      efficient_mapping=True, journal_scanned=True, source="Journal")
    values = calculate_body_values(normalized, correction_factor=1.0)
    return values["scan_value"] if body.get("star_type") or body.get("body_type") == "Star" else values["mapped_value"]


def observation(system, bodies, biology, learned_values):
    """Qualify a personal observation without treating missing data as zero."""
    real = [b for b in bodies if is_astronomical_body(b)]
    all_found = bool(system["all_bodies_found"])
    quality = "complete" if all_found else "partial" if real or system["fss_discovery_scan_seen"] else "unknown"
    issues = []
    if not all_found:
        issues.append("no_all_bodies_found_evidence")
    if not real or system["body_count_seen"] <= 0 or len(real) != system["body_count_seen"]:
        issues.append("body_count_unverified_or_inconsistent")
    if any(not b["scanned"] or not (b["star_type"] or canonical_class(b["planet_class"]) in BODY_VALUES) for b in real):
        issues.append("incomplete_body_details")
    counts = Counter()
    for body in real:
        cls = canonical_class(body["planet_class"])
        terra = bool(body["terraformable"])
        counts["water_world"] += cls == "Water world"
        counts["terraformable_water_world"] += cls == "Water world" and terra
        counts["earthlike"] += cls == "Earthlike body"
        counts["ammonia_world"] += cls == "Ammonia world"
        counts["terraformable_hmc"] += cls == "High metal content body" and terra
        counts["valuable"] += terra or cls in {"Water world", "Earthlike body", "Ammonia world"}
    potential = sum(body_potential(b) for b in real) if not issues else None
    signals = {b["body_id"]: int(b["biological_signals_seen"] or 0) for b in real}
    completed = defaultdict(dict)
    for entry in biology:
        if is_complete(entry) and entry["body_id"] in signals:
            key = (entry["species"].casefold(), entry["variant"].casefold())
            completed[entry["body_id"]][key] = base_value(entry, learned_values)
    values = [value for entries in completed.values() for value in entries.values()]
    # This certifies only coverage of KNOWN signals, never absence of unobserved BIO.
    covered = (bool(sum(signals.values())) and not issues
               and all(len(completed[body_id]) == count for body_id, count in signals.items())
               and bool(values) and all(value > 0 for value in values))
    return {**system, "quality": quality, "qualified": not issues, "issues": issues,
            "astronomical_bodies": len(real), "excluded_non_bodies": len(bodies) - len(real),
            "counts": dict(counts), "valuable_hit": bool(counts["valuable"]),
            "exploration_potential": potential,
            "bio": {"signals": sum(signals.values()), "completed_analyses": len(values),
                    "state": "known_signals_analysed" if covered else "analyses_present" if values
                    else "signals_only" if sum(signals.values()) else "unknown",
                    "analysed_base_value": sum(values) if values and all(v > 0 for v in values) else None,
                    "comparable_base_value": sum(values) if covered else None}}


class HierarchicalJumpTip:
    """Load a personal DB snapshot with SELECT only; score many names consistently."""

    def __init__(self, database):
        self.database = database

    def observations(self):
        commander = self.database._require_commander_id()
        with self.database._connect() as con:
            # A single read transaction prevents mixing concurrently updated tables.
            con.execute("BEGIN")
            def rows(sql, args=()):
                cursor = con.execute(sql, args)
                names = [column[0] for column in cursor.description]
                return [dict(zip(names, row)) for row in cursor.fetchall()]
            systems = rows("""SELECT s.system_address,s.name,cs.body_count_seen,
                cs.fss_discovery_scan_seen,cs.all_bodies_found,cs.first_seen,cs.last_seen
                FROM systems s JOIN commander_systems cs USING(system_address)
                WHERE cs.commander_id=?""", (commander,))
            bodies = rows("""SELECT b.*,cb.scanned,cb.biological_signals_seen
                FROM bodies b JOIN commander_bodies cb USING(system_address,body_id)
                WHERE cb.commander_id=?""", (commander,))
            biology = rows("SELECT * FROM biology WHERE commander_id=?", (commander,))
            learned = {r["species"]: r["base_value"] for r in rows("SELECT species,base_value FROM learned_bio_values")}
        body_groups, bio_groups = defaultdict(list), defaultdict(list)
        for body in bodies:
            body_groups[body["system_address"]].append(body)
        for entry in biology:
            bio_groups[entry["system_address"]].append(entry)
        result = []
        for system in systems:
            parsed = ScoreAnalyzer.parse_system_name(system["name"])
            if parsed is None:
                continue
            result.append(observation({**system, **parsed}, body_groups[system["system_address"]],
                                      bio_groups[system["system_address"]], learned))
        return result

    def evaluate(self, target, *, excluded_system_addresses=()):
        return evaluate_observations(target, self.observations(),
                                     excluded_system_addresses=excluded_system_addresses)


def summarize(rows, cap):
    values = [row["exploration_potential"] for row in rows]
    counts = Counter()
    for row in rows:
        counts.update(row["counts"])
    return {"systems": len(rows), "hits": sum(row["valuable_hit"] for row in rows),
            "counts": dict(counts), "median": median(values) if values else None,
            "winsorized_mean": mean(min(value, cap) for value in values) if values else None}


def recommendation(ratio):
    return next((label for limit, label in CLASS_LIMITS if ratio < limit), "very_good")


def evaluate_observations(target, observations, *, excluded_system_addresses=()):
    """Pure API. Exclusions are explicit and identical for all compared targets.

    No automatic leave-target-out: different indices of one family must receive
    the same estimate for the same training data. Use exclusions for backtests.
    """
    parsed = ScoreAnalyzer.parse_system_name(target)
    if parsed is None:
        return {"ok": False, "reason": "unsupported_name", "target": target}
    excluded = set(excluded_system_addresses)
    source = [row for row in observations if row["system_address"] not in excluded]
    qualified = [row for row in source if row["qualified"]]
    result = {"ok": False, "target": target, "mass": parsed["mass"], "sector": parsed["sector"],
              "family_key": parsed["family_key"], "quality_counts": dict(Counter(r["quality"] for r in source)),
              "excluded_observations": len(source) - len(qualified), "levels": [],
              "scenario": "normal_discovery_efficient_mapping", "prior_systems": PRIOR_SYSTEMS}
    if not qualified:
        return {**result, "reason": "no_qualified_observations"}
    cap = quantile([r["exploration_potential"] for r in qualified], WINSOR_QUANTILE)
    global_summary = summarize(qualified, cap)
    base_potential = global_summary["winsorized_mean"]
    parent_rate = global_summary["hits"] / global_summary["systems"]
    parent_potential = base_potential
    mass_rows = [r for r in qualified if r["mass"] == parsed["mass"]]
    if not mass_rows:
        return {**result, "reason": "no_mass_observations"}
    region_rows = [r for r in mass_rows if r["sector"].casefold() == parsed["sector"].casefold()]
    family_rows = [r for r in region_rows if r["family_key"].casefold() == parsed["family_key"].casefold()]
    for kind, rows in [("mass", mass_rows), ("sector_mass", region_rows), ("family", family_rows)]:
        stats = summarize(rows, cap)
        n, hits = stats["systems"], stats["hits"]
        rate = hits / n if n else None
        adjusted = shrink(rate, n, parent_rate)
        potential = shrink(stats["winsorized_mean"], n, parent_potential)
        bio_values = [r["bio"]["comparable_base_value"] for r in rows
                      if r["bio"]["comparable_base_value"] is not None]
        result["levels"].append({"kind": kind, **stats, "rate": rate, "adjusted_rate": adjusted,
                                 "rate_interval_95": wilson_interval(hits, n), "data_quality": quality_label(n),
                                 "local_weight": n / (n + PRIOR_SYSTEMS),
                                 "rate_influence": adjusted - parent_rate,
                                 "potential_influence": potential - parent_potential,
                                 "adjusted_potential": potential,
                                 "bio": {"signal_systems": sum(r["bio"]["signals"] > 0 for r in rows),
                                         "analysed_systems": sum(r["bio"]["completed_analyses"] > 0 for r in rows),
                                         "comparable_systems": len(bio_values),
                                         "median_base_value": median(bio_values) if bio_values else None,
                                         "scope": "conditional_on_known_signals_analysed"}})
        parent_rate, parent_potential = adjusted, potential
    ratio = parent_potential / max(base_potential, 1.0)
    result.update(ok=True, global_reference=global_summary, winsor_cap=cap,
                  valuable_rate=parent_rate, exploration_potential=parent_potential,
                  potential_index=100 * ratio, recommendation=recommendation(ratio),
                  data_quality=quality_label(len(mass_rows)),
                  family_data_quality=quality_label(len(family_rows)),
                  weights={"cartography": 1.0, "biology": 0.0},
                  bio_hint="BIO is conditional evidence, not a zero for unexamined systems.")
    # Diagnostic alternatives only: normalization uses the same eligible BIO cohort.
    bio_reference = [r["bio"]["comparable_base_value"] for r in qualified
                     if r["bio"]["comparable_base_value"] is not None]
    bio_cap = quantile(bio_reference, WINSOR_QUANTILE)
    bio_base = mean(min(v, bio_cap) for v in bio_reference) if bio_reference else None
    bio_estimate = bio_base
    bio_n_mass = 0
    for i, rows in enumerate([mass_rows, region_rows, family_rows]):
        values = [r["bio"]["comparable_base_value"] for r in rows if r["bio"]["comparable_base_value"] is not None]
        if i == 0:
            bio_n_mass = len(values)
        if values and bio_base:
            bio_estimate = shrink(mean(min(v, bio_cap) for v in values), len(values), bio_estimate)
    bio_ratio = bio_estimate / bio_base if bio_base and bio_n_mass >= MIN_BIO_COMPARISONS else None
    result["weight_comparison"] = [
        {"cartography_weight": weight, "bio_weight": round(1 - weight, 1),
         "potential_index": 100 * (weight * ratio + (1 - weight) * bio_ratio)
         if bio_ratio is not None else (100 * ratio if weight == 1 else None),
         "status": "selected" if weight == 1 else "diagnostic_selection_biased" if bio_ratio is not None
         else "insufficient_bio_observations"}
        for weight in (1.0, 0.8, 0.7)]
    return result
