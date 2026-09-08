from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math


COMPLETE_SCAN_TYPES = {"analyse", "analyze"}


@dataclass(frozen=True)
class BioCandidate:
    name: str
    genus: str
    kind: str
    confidence: str
    support: int
    score: float
    habitat_score: float
    low_data: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class BioPrediction:
    candidates: tuple[BioCandidate, ...]
    identified_count: int
    completed_count: int
    expected_signals: int
    open_signals: int


def _text(value) -> str:
    return str(value or "").strip()


def _number(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _composition(value) -> dict[str, float]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    if isinstance(value, dict):
        value = [{"Name": name, "Percent": percent} for name, percent in value.items()]
    if not isinstance(value, list):
        return {}
    result = {}
    for item in value:
        if not isinstance(item, dict):
            continue
        name = _text(item.get("Name") or item.get("name")).casefold()
        percent = _number(item.get("Percent") if "Percent" in item else item.get("percent"))
        if name and percent is not None:
            result[name] = percent
    return result


def _smooth_ratio(a, b, scale):
    a = _number(a)
    b = _number(b)
    if a is None or b is None or a <= 0 or b <= 0:
        return None
    return math.exp(-abs(math.log(a / b)) / scale)


class BioPredictor:
    """Qt-freie, lokale Species-Prognose aus CMDRHelpers eigenen Funden."""

    # Gewichte werden ausschließlich über auf beiden Seiten vorhandene
    # Merkmale normalisiert. Neue Habitatfelder helfen daher inkrementell.
    FEATURE_WEIGHTS = {
        "atmosphere": 35.0,
        "planet_class": 25.0,
        "gravity_g": 15.0,
        "mass_em": 10.0,
        "surface_temperature": 8.0,
        "surface_pressure": 6.0,
        "atmosphere_composition": 8.0,
        "biological_signals": 8.0,
        "terraformable": 4.0,
        "volcanism": 2.0,
        "primary_star_type": 3.0,
        "parent_star_id": 1.0,
        "distance_ls": 2.0,
    }

    def __init__(self, training_rows=()):
        self._bodies = {}
        self._species_support = Counter()
        self._genus_support = Counter()
        self._species_genus = {}
        self._species_profiles = {}
        self._pair_count = Counter()
        self._complete_species_count = Counter()
        self._complete_body_count = 0
        self._prediction_cache = {}
        self.replace_training(training_rows)

    @staticmethod
    def is_complete(scan_type) -> bool:
        return _text(scan_type).casefold() in COMPLETE_SCAN_TYPES

    def replace_training(self, training_rows):
        self._prediction_cache = {}
        bodies = {}
        for raw in training_rows or ():
            row = dict(raw)
            if not self.is_complete(row.get("scan_type")):
                continue
            species = _text(row.get("species"))
            genus = _text(row.get("genus")) or (species.split()[0] if species else "")
            if not species or not genus:
                continue
            key = (row.get("system_address"), row.get("body_id"))
            entry = bodies.setdefault(key, {"features": row, "species": {}, "genera": set()})
            entry["species"][species] = genus
            entry["genera"].add(genus)
        self._bodies = bodies
        self._rebuild_index()

    def _rebuild_index(self):
        self._species_support = Counter()
        self._genus_support = Counter()
        occurrences = defaultdict(list)
        for body in self._bodies.values():
            for species, genus in body["species"].items():
                self._species_support[species] += 1
                self._species_genus[species] = genus
                occurrences[species].append(body["features"])
            for genus in body["genera"]:
                self._genus_support[genus] += 1
        self._species_profiles = {}
        for species, rows in occurrences.items():
            self._species_profiles[species] = {
                "planet_class": Counter(_text(row.get("planet_class")) for row in rows if _text(row.get("planet_class"))),
                "atmosphere": Counter(_text(row.get("atmosphere")) for row in rows if _text(row.get("atmosphere"))),
            }

        self._pair_count = Counter()
        self._complete_species_count = Counter()
        self._complete_body_count = 0
        for body in self._bodies.values():
            signals = int(body["features"].get("biological_signals") or 0)
            species = sorted(body["species"])
            if signals <= 0 or len(species) < signals:
                continue
            self._complete_body_count += 1
            for item in species:
                self._complete_species_count[item] += 1
            for index, first in enumerate(species):
                for second in species[index + 1:]:
                    self._pair_count[(first, second)] += 1

    def _remember_prediction(self, key, result):
        if len(self._prediction_cache) >= 256:
            self._prediction_cache.pop(next(iter(self._prediction_cache)))
        self._prediction_cache[key] = result
        return result

    def _similarity(self, target, historical):
        weighted = 0.0
        available = 0.0
        reasons = []

        def add(field, value, label):
            nonlocal weighted, available
            left = target.get(field)
            right = historical.get(field)
            if left is None or left == "" or right is None or right == "":
                return
            weight = self.FEATURE_WEIGHTS[field]
            available += weight
            similarity = max(0.0, min(1.0, value(left, right)))
            weighted += weight * similarity
            if similarity >= 0.9:
                reasons.append(label)

        add("atmosphere", lambda a, b: float(_text(a).casefold() == _text(b).casefold()), "Atmosphäre")
        add("planet_class", lambda a, b: float(_text(a).casefold() == _text(b).casefold()), "PlanetClass")
        add("gravity_g", lambda a, b: _smooth_ratio(a, b, 0.55) or 0.0, "Gravitation")
        add("mass_em", lambda a, b: _smooth_ratio(a, b, 1.1) or 0.0, "Masse")
        add("surface_temperature", lambda a, b: _smooth_ratio(a, b, 0.35) or 0.0, "Temperatur")
        add("surface_pressure", lambda a, b: _smooth_ratio(a, b, 0.8) or 0.0, "Druck")

        left_comp = _composition(target.get("atmosphere_composition"))
        right_comp = _composition(historical.get("atmosphere_composition"))
        if left_comp and right_comp:
            names = set(left_comp) | set(right_comp)
            distance = sum(abs(left_comp.get(name, 0.0) - right_comp.get(name, 0.0)) for name in names) / 200.0
            weight = self.FEATURE_WEIGHTS["atmosphere_composition"]
            available += weight
            score = max(0.0, 1.0 - distance)
            weighted += weight * score
            if score >= 0.9:
                reasons.append("Atmosphärenmix")

        add("biological_signals", lambda a, b: math.exp(-abs(float(a) - float(b)) / 1.5), "Signalzahl")
        add("terraformable", lambda a, b: float(bool(a) == bool(b)), "Terraforming")
        add("volcanism", lambda a, b: float(_text(a).casefold() == _text(b).casefold()), "Vulkanismus")
        add("primary_star_type", lambda a, b: float(_text(a).casefold() == _text(b).casefold()), "Sternklasse")
        add("parent_star_id", lambda a, b: float(a == b), "Sternkontext")
        add("distance_ls", lambda a, b: _smooth_ratio(a, b, 2.5) or 0.0, "Sterndistanz")
        if available < 35.0:
            return 0.0, ()
        return weighted / available, tuple(dict.fromkeys(reasons))

    def _empirical_penalty(self, species, target):
        support = self._species_support[species]
        penalty = 1.0
        mismatch = False
        for field in ("atmosphere", "planet_class"):
            target_value = _text(target.get(field))
            counts = self._species_profiles.get(species, {}).get(field, Counter())
            total = sum(counts.values())
            if not target_value or total < 5 or not counts:
                continue
            dominant, dominant_count = counts.most_common(1)[0]
            dominance = dominant_count / total
            if target_value.casefold() != dominant.casefold() and dominance >= 0.9:
                penalty *= 0.25 if support >= 10 else 0.4
                mismatch = True
        return penalty, mismatch

    def _cooccurrence_bonus(self, species, known_species):
        if not known_species or self._complete_body_count <= 0:
            return 0.0
        best = 0.0
        for known in known_species:
            pair = tuple(sorted((species, known)))
            together = self._pair_count.get(pair, 0)
            if together < 5:
                continue
            left = self._complete_species_count.get(species, 0)
            right = self._complete_species_count.get(known, 0)
            if left <= 0 or right <= 0:
                continue
            lift = (together + 1.0) * (self._complete_body_count + 2.0) / ((left + 1.0) * (right + 1.0))
            confidence = (together + 1.0) / (right + 2.0)
            best = max(best, min(0.15, 0.04 * max(0.0, lift - 1.0) + 0.05 * confidence))
        return best

    @staticmethod
    def _confidence(support, habitat_score, mismatch):
        if support >= 10 and habitat_score >= 0.78 and not mismatch:
            return "high"
        if support >= 5 and habitat_score >= 0.66:
            return "medium"
        if support >= 3 and habitat_score >= 0.48:
            return "low"
        return ""

    def predict(self, body, known_findings=(), limit=8):
        body = dict(body or {})
        known_findings = tuple(
            item for item in (known_findings or ()) if isinstance(item, dict)
        )
        cache_key = (
            tuple((field, json.dumps(body.get(field), sort_keys=True, default=str))
                  for field in ("system_address", "body_id", *self.FEATURE_WEIGHTS)),
            tuple(sorted((
                _text(item.get("genus")), _text(item.get("species")),
                _text(item.get("scan_type")).casefold()
            ) for item in known_findings)),
            int(limit),
        )
        cached = self._prediction_cache.get(cache_key)
        if cached is not None:
            return cached
        expected = max(0, int(body.get("biological_signals") or 0))
        known_species = set()
        known_genera = set()
        species_genera = set()
        completed = set()
        for finding in known_findings:
            species = _text(finding.get("species"))
            genus = _text(finding.get("genus")) or (species.split()[0] if species else "")
            if species:
                known_species.add(species)
            if genus:
                known_genera.add(genus)
            if species and genus:
                species_genera.add(genus)
            if species and self.is_complete(finding.get("scan_type")):
                completed.add(species)
        identified_count = len(known_species) + len(known_genera - species_genera)
        result_base = dict(
            identified_count=identified_count,
            completed_count=len(completed),
            expected_signals=expected,
            open_signals=max(0, expected - identified_count),
        )
        if expected <= 0:
            result = BioPrediction(candidates=(), **result_base)
            return self._remember_prediction(cache_key, result)

        target_key = (body.get("system_address"), body.get("body_id"))
        neighbors = []
        for key, historical in self._bodies.items():
            if key == target_key:
                continue
            similarity, reasons = self._similarity(body, historical["features"])
            if similarity > 0:
                neighbors.append((similarity, reasons, historical))
        neighbors.sort(key=lambda item: item[0], reverse=True)
        neighbors = neighbors[:25]
        if not neighbors or neighbors[0][0] < 0.45:
            result = BioPrediction(candidates=(), **result_base)
            return self._remember_prediction(cache_key, result)

        votes = defaultdict(float)
        habitat = defaultdict(list)
        reason_votes = defaultdict(Counter)
        genus_votes = defaultdict(float)
        genus_habitat = defaultdict(list)
        for similarity, reasons, historical in neighbors:
            weight = math.exp((similarity - 0.70) / 0.12)
            for species, genus in historical["species"].items():
                votes[species] += weight
                habitat[species].append(similarity)
                reason_votes[species].update(reasons)
            for genus in historical["genera"]:
                genus_votes[genus] += weight
                genus_habitat[genus].append(similarity)

        candidates = []
        concrete_genera = set()
        for species, vote in votes.items():
            support = self._species_support[species]
            if support < 3 or species in known_species:
                continue
            genus = self._species_genus.get(species, species.split()[0])
            top_scores = sorted(habitat[species], reverse=True)[:5]
            habitat_score = sum(top_scores) / len(top_scores)
            penalty, mismatch = self._empirical_penalty(species, body)
            reliability = support / (support + 5.0)
            base_score = vote * reliability * penalty
            confidence = self._confidence(support, habitat_score * penalty, mismatch)
            if not confidence:
                continue
            bonus = self._cooccurrence_bonus(species, known_species)
            score = base_score * (1.0 + bonus)
            reasons = tuple(item for item, _ in reason_votes[species].most_common(3))
            candidates.append(BioCandidate(
                name=species, genus=genus, kind="species", confidence=confidence,
                support=support, score=score, habitat_score=habitat_score * penalty,
                low_data=support < 5, reasons=reasons,
            ))
            concrete_genera.add(genus)

        # Seltene Species werden nicht namentlich ausgegeben. Nur wenn für
        # ihre Gattung keine belastbare konkrete Species übrig blieb, dient
        # eine vorsichtige Genus-Zeile als ehrlicher Fallback.
        rare_genera = {
            self._species_genus[species]
            for species, support in self._species_support.items()
            if support < 3 and species in self._species_genus
        }
        for genus in rare_genera:
            if genus in concrete_genera or genus in known_genera or self._genus_support[genus] < 5:
                continue
            values = sorted(genus_habitat.get(genus, ()), reverse=True)[:5]
            if not values:
                continue
            habitat_score = sum(values) / len(values)
            if habitat_score < 0.48:
                continue
            candidates.append(BioCandidate(
                name=genus, genus=genus, kind="genus", confidence="low",
                support=self._genus_support[genus],
                score=genus_votes[genus] * 0.35,
                habitat_score=habitat_score, low_data=True,
                reasons=(),
            ))

        candidates.sort(key=lambda item: (-item.score, -item.habitat_score, item.name.casefold()))
        result = BioPrediction(
            candidates=tuple(candidates[:max(0, int(limit))]), **result_base
        )
        return self._remember_prediction(cache_key, result)
