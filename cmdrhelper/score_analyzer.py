from __future__ import annotations

import math
import re

from cmdrhelper.i18n import tr


class ScoreAnalyzer:
    """
    Persönliche statistische Auswertung prozeduraler Elite-Systemnamen.

    Die Analyse arbeitet ausschließlich mit der lokalen CMDRHelper-Datenbank.
    Sie sagt keine Funde voraus, sondern bewertet historische Trefferquoten.
    """

    def __init__(self, database):
        self.database = database

    @staticmethod
    def parse_system_name(system_name):
        text = str(system_name or "").strip()
        if not text:
            return None

        match = re.match(
            r"^(?P<sector>.+?)\s+"
            r"(?P<code>[A-Z]{1,2}-[A-Z])\s+"
            r"(?P<mass>[A-H])(?P<number>\d+)"
            r"(?:-(?P<suffix>\d+))?$",
            text,
            re.IGNORECASE,
        )
        if not match:
            return None

        sector = " ".join(match.group("sector").split())
        code = match.group("code").upper()
        mass = match.group("mass").lower()

        return {
            "sector": sector,
            "code": code,
            "mass": mass,
            "number": int(match.group("number")),
            "suffix": (
                int(match.group("suffix"))
                if match.group("suffix") is not None
                else None
            ),
            "code_mass": f"{code} {mass}",
        }

    @staticmethod
    def _adjusted_rate(hits, total, baseline, prior_strength=20.0):
        total = max(0, int(total or 0))
        hits = max(0, min(total, int(hits or 0)))
        baseline = min(1.0, max(0.0, float(baseline or 0.0)))
        prior_strength = max(1.0, float(prior_strength or 20.0))

        return (
            hits + baseline * prior_strength
        ) / (
            total + prior_strength
        )

    @staticmethod
    def _component_score(adjusted_rate, baseline, total):
        """
        50 entspricht ungefähr dem persönlichen Gesamtdurchschnitt.
        Kleine Stichproben werden bewusst Richtung 50 gedrückt.
        """
        total = max(0, int(total or 0))
        adjusted_rate = min(1.0, max(0.0, float(adjusted_rate or 0.0)))
        baseline = min(1.0, max(0.000001, float(baseline or 0.0)))

        ratio = adjusted_rate / baseline
        raw = 50.0 + 28.0 * math.log2(
            max(0.125, min(8.0, ratio))
        )

        confidence = total / (total + 25.0)
        score = 50.0 + (raw - 50.0) * confidence

        return int(round(max(0.0, min(100.0, score))))

    @staticmethod
    def level(score):
        score = int(score or 0)
        if score >= 75:
            return tr("score.level.high")
        if score >= 60:
            return tr("score.level.above_average")
        if score >= 40:
            return tr("score.level.medium")
        if score >= 25:
            return tr("score.level.below_average")
        return tr("score.level.low")

    def statistics(self, min_sector_samples=10, min_code_mass_samples=8):
        with self.database._connect() as con:
            rows = con.execute(
                """
                SELECT
                    s.system_address,
                    s.name,
                    COALESCE(SUM(b.biological_signals), 0) AS bio_signals,
                    MAX(
                        CASE
                            WHEN b.terraformable = 1 THEN 1
                            WHEN LOWER(b.planet_class) LIKE '%earthlike%' THEN 1
                            WHEN LOWER(b.planet_class) LIKE '%earth-like%' THEN 1
                            WHEN LOWER(b.planet_class) LIKE '%water world%' THEN 1
                            WHEN LOWER(b.planet_class) LIKE '%ammonia world%' THEN 1
                            ELSE 0
                        END
                    ) AS value_hit,
                    SUM(
                        CASE
                            WHEN LOWER(b.planet_class) LIKE '%earthlike%'
                              OR LOWER(b.planet_class) LIKE '%earth-like%'
                            THEN 1 ELSE 0
                        END
                    ) AS earthlikes,
                    SUM(
                        CASE
                            WHEN LOWER(b.planet_class) LIKE '%water world%'
                            THEN 1 ELSE 0
                        END
                    ) AS water_worlds,
                    SUM(
                        CASE
                            WHEN LOWER(b.planet_class) LIKE '%ammonia world%'
                            THEN 1 ELSE 0
                        END
                    ) AS ammonia_worlds,
                    SUM(
                        CASE
                            WHEN b.terraformable = 1
                            THEN 1 ELSE 0
                        END
                    ) AS terraformables
                FROM systems AS s
                LEFT JOIN bodies AS b
                  ON b.system_address = s.system_address
                GROUP BY s.system_address, s.name
                ORDER BY s.name COLLATE NOCASE
                """
            ).fetchall()

        parsed_rows = []

        for row in rows:
            parsed = self.parse_system_name(row[1])
            if not parsed:
                continue

            parsed_rows.append({
                "system_address": row[0],
                "name": row[1] or "",
                **parsed,
                "bio_signals": int(row[2] or 0),
                "bio_hit": 1 if int(row[2] or 0) > 0 else 0,
                "value_hit": 1 if int(row[3] or 0) > 0 else 0,
                "earthlikes": int(row[4] or 0),
                "water_worlds": int(row[5] or 0),
                "ammonia_worlds": int(row[6] or 0),
                "terraformables": int(row[7] or 0),
            })

        total = len(parsed_rows)
        if total <= 0:
            return {
                "systems": 0,
                "bio_baseline": 0.0,
                "value_baseline": 0.0,
                "mass": [],
                "sectors": [],
                "code_mass": [],
            }

        bio_total = sum(row["bio_hit"] for row in parsed_rows)
        value_total = sum(row["value_hit"] for row in parsed_rows)

        bio_baseline = bio_total / total
        value_baseline = value_total / total

        def groups_for(field):
            groups = {}

            for row in parsed_rows:
                key = row[field]
                entry = groups.setdefault(
                    key,
                    {
                        "key": key,
                        "systems": 0,
                        "bio_systems": 0,
                        "bio_signals": 0,
                        "value_systems": 0,
                        "earthlikes": 0,
                        "water_worlds": 0,
                        "ammonia_worlds": 0,
                        "terraformables": 0,
                    },
                )

                entry["systems"] += 1
                entry["bio_systems"] += row["bio_hit"]
                entry["bio_signals"] += row["bio_signals"]
                entry["value_systems"] += row["value_hit"]
                entry["earthlikes"] += row["earthlikes"]
                entry["water_worlds"] += row["water_worlds"]
                entry["ammonia_worlds"] += row["ammonia_worlds"]
                entry["terraformables"] += row["terraformables"]

            result = []

            for entry in groups.values():
                n = entry["systems"]

                entry["bio_rate"] = (
                    entry["bio_systems"] / n if n else 0.0
                )
                entry["value_rate"] = (
                    entry["value_systems"] / n if n else 0.0
                )

                bio_adjusted = self._adjusted_rate(
                    entry["bio_systems"],
                    n,
                    bio_baseline,
                )
                value_adjusted = self._adjusted_rate(
                    entry["value_systems"],
                    n,
                    value_baseline,
                )

                entry["bio_score"] = self._component_score(
                    bio_adjusted,
                    bio_baseline,
                    n,
                )
                entry["value_score"] = self._component_score(
                    value_adjusted,
                    value_baseline,
                    n,
                )

                result.append(entry)

            return result

        mass = groups_for("mass")

        sectors = [
            row
            for row in groups_for("sector")
            if row["systems"] >= int(min_sector_samples)
        ]

        code_mass = [
            row
            for row in groups_for("code_mass")
            if row["systems"] >= int(min_code_mass_samples)
        ]

        mass.sort(key=lambda row: row["key"])

        sectors.sort(
            key=lambda row: (
                -row["bio_score"],
                -row["systems"],
                str(row["key"]).lower(),
            )
        )

        code_mass.sort(
            key=lambda row: (
                -row["bio_score"],
                -row["systems"],
                str(row["key"]).lower(),
            )
        )

        return {
            "systems": total,
            "bio_baseline": bio_baseline,
            "value_baseline": value_baseline,
            "mass": mass,
            "sectors": sectors,
            "code_mass": code_mass,
        }


    def available_targets(self):
        """
        Liefert die auswählbaren Score-Ziele.

        Neben festen Explorer-/BIO-Zielen werden BIO-Gattungen und
        BIO-Arten dynamisch aus der persönlichen Datenbank ergänzt.
        """
        targets = [
            {
                "key": "overall",
                "label": tr("score.target.overall"),
                "kind": "overall",
            },
            {
                "key": "bio_any",
                "label": tr("score.target.bio_any"),
                "kind": "bio",
            },
            {
                "key": "valuable",
                "label": tr("score.target.valuable"),
                "kind": "explorer",
            },
            {
                "key": "terraformable",
                "label": tr("score.target.terraformable"),
                "kind": "explorer",
            },
            {
                "key": "water_world",
                "label": tr("score.target.water_world"),
                "kind": "explorer",
            },
            {
                "key": "earthlike",
                "label": tr("score.target.earthlike"),
                "kind": "explorer",
            },
            {
                "key": "ammonia_world",
                "label": tr("score.target.ammonia_world"),
                "kind": "explorer",
            },
        ]

        try:
            commander_id = self.database._require_commander_id()
            with self.database._connect() as con:
                rows = con.execute(
                    """
                    SELECT genus, species
                    FROM biology
                    WHERE commander_id=?
                      AND (genus <> '' OR species <> '')
                    """,
                    (commander_id,),
                ).fetchall()
        except Exception:
            rows = []

        genus_names = {}
        species_names = {}

        for genus, species in rows:
            genus = str(genus or "").strip()
            species = str(species or "").strip()

            if genus:
                genus_names.setdefault(
                    genus.casefold(),
                    genus,
                )

            if species:
                species_names.setdefault(
                    species.casefold(),
                    species,
                )

        for genus in sorted(
            genus_names.values(),
            key=str.casefold,
        ):
            targets.append({
                "key": "bio_genus:" + genus,
                "label": tr("score.target.bio_genus", name=genus),
                "kind": "bio",
            })

        for species in sorted(
            species_names.values(),
            key=str.casefold,
        ):
            targets.append({
                "key": "bio_species:" + species,
                "label": tr("score.target.bio_species", name=species),
                "kind": "bio",
            })

        return targets

    @staticmethod
    def _target_label(target_key):
        key = str(target_key or "bio_any")

        fixed = {
            "bio_any": tr("score.target.bio_any"),
            "valuable": tr("score.target.valuable"),
            "terraformable": tr("score.target.terraformable"),
            "water_world": tr("score.target.water_world"),
            "earthlike": tr("score.target.earthlike"),
            "ammonia_world": tr("score.target.ammonia_world"),
        }

        if key in fixed:
            return fixed[key]

        if key.startswith("bio_genus:"):
            return tr("score.target.bio_genus", name=key.split(":", 1)[1])

        if key.startswith("bio_species:"):
            return tr("score.target.bio_species", name=key.split(":", 1)[1])

        return key

    def _target_system_rows(self, target_key):
        """
        Liefert pro auswertbarem System:
            - target_hit: mindestens ein Treffer
            - target_count: Anzahl Treffer/Körper/Funde
        """
        target_key = str(target_key or "bio_any")

        with self.database._connect() as con:
            system_rows = con.execute(
                """
                SELECT system_address, name
                FROM systems
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()

            target_counts = {}

            if target_key == "bio_any":
                rows = con.execute(
                    """
                    SELECT system_address,
                           SUM(
                               CASE
                                   WHEN biological_signals > 0
                                   THEN biological_signals
                                   ELSE 0
                               END
                           )
                    FROM bodies
                    GROUP BY system_address
                    """
                ).fetchall()

                target_counts = {
                    int(address): int(count or 0)
                    for address, count in rows
                }

            elif target_key in (
                "valuable",
                "terraformable",
                "water_world",
                "earthlike",
                "ammonia_world",
            ):
                conditions = {
                    "valuable": """
                        (
                            terraformable = 1
                            OR LOWER(planet_class) LIKE '%earthlike%'
                            OR LOWER(planet_class) LIKE '%earth-like%'
                            OR LOWER(planet_class) LIKE '%water world%'
                            OR LOWER(planet_class) LIKE '%ammonia world%'
                        )
                    """,
                    "terraformable": "terraformable = 1",
                    "water_world": "LOWER(planet_class) LIKE '%water world%'",
                    "earthlike": """
                        (
                            LOWER(planet_class) LIKE '%earthlike%'
                            OR LOWER(planet_class) LIKE '%earth-like%'
                        )
                    """,
                    "ammonia_world": "LOWER(planet_class) LIKE '%ammonia world%'",
                }

                rows = con.execute(
                    f"""
                    SELECT system_address, COUNT(*)
                    FROM bodies
                    WHERE {conditions[target_key]}
                    GROUP BY system_address
                    """
                ).fetchall()

                target_counts = {
                    int(address): int(count or 0)
                    for address, count in rows
                }

            elif target_key.startswith("bio_genus:"):
                target = target_key.split(":", 1)[1].strip()
                commander_id = self.database._require_commander_id()

                rows = con.execute(
                    """
                    SELECT system_address, COUNT(*)
                    FROM biology
                    WHERE commander_id=? AND (
                          genus = ? COLLATE NOCASE
                       OR genus LIKE ? COLLATE NOCASE
                    )
                    GROUP BY system_address
                    """,
                    (
                        commander_id, target,
                        f"{target}%",
                    ),
                ).fetchall()

                target_counts = {
                    int(address): int(count or 0)
                    for address, count in rows
                }

            elif target_key.startswith("bio_species:"):
                target = target_key.split(":", 1)[1].strip()
                commander_id = self.database._require_commander_id()

                rows = con.execute(
                    """
                    SELECT system_address, COUNT(*)
                    FROM biology
                    WHERE commander_id=? AND (
                          species = ? COLLATE NOCASE
                       OR species LIKE ? COLLATE NOCASE
                       OR variant = ? COLLATE NOCASE
                       OR variant LIKE ? COLLATE NOCASE
                    )
                    GROUP BY system_address
                    """,
                    (
                        commander_id, target,
                        f"{target}%",
                        target,
                        f"{target}%",
                    ),
                ).fetchall()

                target_counts = {
                    int(address): int(count or 0)
                    for address, count in rows
                }

        parsed_rows = []

        for address, name in system_rows:
            parsed = self.parse_system_name(name)
            if not parsed:
                continue

            count = int(
                target_counts.get(
                    int(address),
                    0,
                )
                or 0
            )

            parsed_rows.append({
                "system_address": int(address),
                "name": str(name or ""),
                **parsed,
                "target_hit": 1 if count > 0 else 0,
                "target_count": count,
            })

        return parsed_rows

    def target_statistics(
        self,
        target_key,
        min_sector_samples=10,
        min_code_mass_samples=8,
    ):
        """
        Zielbezogene Score-Statistik.

        Beispiel:
            target_key = "water_world"
            target_key = "terraformable"
            target_key = "bio_genus:Stratum"
            target_key = "bio_species:Stratum Tectonicas"
        """
        rows = self._target_system_rows(
            target_key
        )

        total = len(rows)

        if total <= 0:
            return {
                "target_key": target_key,
                "target_label": self._target_label(target_key),
                "systems": 0,
                "baseline": 0.0,
                "hits": 0,
                "finds": 0,
                "mass": [],
                "sectors": [],
                "code_mass": [],
            }

        hits = sum(
            row["target_hit"]
            for row in rows
        )
        finds = sum(
            row["target_count"]
            for row in rows
        )

        baseline = hits / total

        def groups_for(field):
            groups = {}

            for row in rows:
                key = row[field]

                entry = groups.setdefault(
                    key,
                    {
                        "key": key,
                        "systems": 0,
                        "hits": 0,
                        "finds": 0,
                    },
                )

                entry["systems"] += 1
                entry["hits"] += row["target_hit"]
                entry["finds"] += row["target_count"]

            result = []

            for entry in groups.values():
                n = int(entry["systems"] or 0)

                entry["rate"] = (
                    entry["hits"] / n
                    if n
                    else 0.0
                )

                adjusted = self._adjusted_rate(
                    entry["hits"],
                    n,
                    baseline,
                )

                entry["score"] = self._component_score(
                    adjusted,
                    baseline,
                    n,
                )

                result.append(entry)

            return result

        mass = groups_for("mass")

        sectors = [
            row
            for row in groups_for("sector")
            if row["systems"] >= int(
                min_sector_samples
            )
        ]

        code_mass = [
            row
            for row in groups_for("code_mass")
            if row["systems"] >= int(
                min_code_mass_samples
            )
        ]

        mass.sort(
            key=lambda row: row["key"]
        )

        sectors.sort(
            key=lambda row: (
                -row["score"],
                -row["hits"],
                -row["systems"],
                str(row["key"]).casefold(),
            )
        )

        code_mass.sort(
            key=lambda row: (
                -row["score"],
                -row["hits"],
                -row["systems"],
                str(row["key"]).casefold(),
            )
        )

        return {
            "target_key": target_key,
            "target_label": self._target_label(
                target_key
            ),
            "systems": total,
            "baseline": baseline,
            "hits": hits,
            "finds": finds,
            "mass": mass,
            "sectors": sectors,
            "code_mass": code_mass,
        }


    def best_patterns(
        self,
        target_key,
        min_samples=3,
        limit=100,
    ):
        """
        Rückwärts-Auswertung:

            gewünschter Fund
                -> statistisch beste Systembezeichnungen

        Beispiel:
            "BIO-Art: Stratum Tectonicas"
                -> "DF-J b", "ZL-Z b", "NR-C d", ...

        Die Muster bestehen aus dem Buchstabencode und dem Massencode.
        Kleine Stichproben werden bereits über den Score geglättet.
        """
        stats = self.target_statistics(
            target_key,
            min_sector_samples=1,
            min_code_mass_samples=1,
        )

        rows = [
            dict(row)
            for row in (stats.get("code_mass") or [])
            if (
                int(row.get("systems") or 0) >= int(min_samples)
                and int(row.get("hits") or 0) > 0
            )
        ]

        # Prüfen, ob ein Muster nur in einem einzelnen Sektor auffällig war
        # oder ob sich der Effekt über mehrere Regionen wiederholt.
        source_rows = self._target_system_rows(
            target_key
        )

        distribution = {}

        for source in source_rows:
            key = str(
                source.get("code_mass")
                or ""
            )
            sector = str(
                source.get("sector")
                or ""
            )

            entry = distribution.setdefault(
                key,
                {
                    "sectors": set(),
                    "hit_sectors": set(),
                    "hits_by_sector": {},
                },
            )

            if sector:
                entry["sectors"].add(
                    sector.casefold()
                )

            hits = int(
                source.get("target_hit")
                or 0
            )

            if hits > 0 and sector:
                sector_key = sector.casefold()
                entry["hit_sectors"].add(
                    sector_key
                )
                entry["hits_by_sector"][sector_key] = (
                    entry["hits_by_sector"].get(
                        sector_key,
                        0,
                    )
                    + hits
                )

        for row in rows:
            key = str(
                row.get("key")
                or ""
            )

            dist = distribution.get(
                key,
                {},
            )

            sector_count = len(
                dist.get("sectors")
                or []
            )
            hit_sector_count = len(
                dist.get("hit_sectors")
                or []
            )

            hits_by_sector = dist.get(
                "hits_by_sector"
            ) or {}

            total_hits = max(
                0,
                int(
                    row.get("hits")
                    or 0
                ),
            )

            dominant_hits = max(
                hits_by_sector.values(),
                default=0,
            )

            dominant_share = (
                dominant_hits / total_hits
                if total_hits > 0
                else 1.0
            )

            systems = max(
                0,
                int(
                    row.get("systems")
                    or 0
                ),
            )

            # Aussagekraft 0..100:
            # - genügend untersuchte Systeme
            # - Muster in mehreren Sektoren gesehen
            # - Treffer in mehreren Sektoren wiederholt
            # - keine extreme Konzentration aller Treffer auf nur einen Sektor
            sample_factor = min(
                1.0,
                systems / 25.0,
            )
            sector_factor = min(
                1.0,
                sector_count / 4.0,
            )
            hit_spread_factor = min(
                1.0,
                hit_sector_count / 3.0,
            )

            if total_hits <= 0:
                concentration_factor = 0.0
            elif hit_sector_count <= 1:
                concentration_factor = 0.25
            else:
                concentration_factor = max(
                    0.25,
                    1.0 - max(
                        0.0,
                        dominant_share - 0.50,
                    ),
                )

            confidence_score = int(
                round(
                    100.0 * (
                        0.40 * sample_factor
                        + 0.20 * sector_factor
                        + 0.30 * hit_spread_factor
                        + 0.10 * concentration_factor
                    )
                )
            )

            if (
                confidence_score >= 70
                and sector_count >= 3
                and hit_sector_count >= 2
                and total_hits >= 4
            ):
                confidence = "hoch"
            elif (
                confidence_score >= 45
                and sector_count >= 2
                and total_hits >= 2
            ):
                confidence = "mittel"
            else:
                confidence = "gering"

            row["sector_count"] = sector_count
            row["hit_sector_count"] = hit_sector_count
            row["dominant_sector_share"] = dominant_share
            row["confidence_score"] = confidence_score
            row["confidence"] = confidence

        rows.sort(
            key=lambda row: (
                -int(row.get("score") or 0),
                -float(row.get("rate") or 0.0),
                -int(row.get("hits") or 0),
                -int(row.get("confidence_score") or 0),
                -int(row.get("finds") or 0),
                -int(row.get("systems") or 0),
                str(row.get("key") or "").casefold(),
            )
        )

        for rank, row in enumerate(rows, start=1):
            row["rank"] = rank
            row["level"] = self.level(
                int(row.get("score") or 0)
            )

        if limit is not None:
            rows = rows[: max(1, int(limit))]

        return {
            "target_key": target_key,
            "target_label": stats.get("target_label") or self._target_label(target_key),
            "systems": int(stats.get("systems") or 0),
            "hits": int(stats.get("hits") or 0),
            "finds": int(stats.get("finds") or 0),
            "baseline": float(stats.get("baseline") or 0.0),
            "min_samples": int(min_samples),
            "patterns": rows,
            "mass": list(stats.get("mass") or []),
            "sectors": list(stats.get("sectors") or []),
        }


    def jump_recommendations(
        self,
        target_key,
        min_samples=3,
        limit=50,
    ):
        """
        Spielerorientierte Empfehlung für die Galaxiekarte.

        Liefert nur Kürzel, bei denen das gewählte Ziel in der eigenen
        Historie tatsächlich gefunden wurde. Die komplizierte Statistik
        bleibt im Hintergrund; für die Oberfläche werden daraus eine
        verständliche Erfolgsangabe und eine Empfehlung erzeugt.
        """
        result = self.best_patterns(
            target_key,
            min_samples=min_samples,
            limit=limit,
        )

        rows = []

        for source in result.get("patterns") or []:
            row = dict(source)

            systems = max(
                0,
                int(row.get("systems") or 0),
            )
            hits = max(
                0,
                int(row.get("hits") or 0),
            )
            score = max(
                0,
                min(100, int(row.get("score") or 0)),
            )
            confidence = str(
                row.get("confidence") or "gering"
            )

            if score >= 72:
                stars = 5
                recommendation = tr("score.recommendation.very_good")
            elif score >= 62:
                stars = 4
                recommendation = tr("score.recommendation.good")
            elif score >= 54:
                stars = 3
                recommendation = tr("score.recommendation.interesting")
            elif score >= 46:
                stars = 2
                recommendation = tr("score.recommendation.maybe")
            else:
                stars = 1
                recommendation = tr("score.recommendation.weak")

            # Kleine bzw. regional stark konzentrierte Datenbasis nicht
            # überbewerten. Die Reihenfolge bleibt vom geglätteten Score
            # bestimmt, aber die sichtbare Empfehlung wird vorsichtiger.
            if confidence == "gering" and stars > 3:
                stars = 3
                recommendation = tr("score.recommendation.interesting_low_data")
            elif confidence == "gering":
                recommendation += tr("score.recommendation.low_data_suffix")

            row["success_text"] = f"{hits} / {systems}"
            row["stars"] = stars
            row["recommendation"] = recommendation
            row["recommendation_text"] = (
                ("★" * stars)
                + ("☆" * (5 - stars))
                + "  "
                + recommendation
            )

            rows.append(row)

        result = dict(result)
        result["recommendations"] = rows
        return result


    def score_system_target(
        self,
        system_name,
        target_key,
    ):
        """
        Bewertet einen Systemnamen nur für das ausgewählte Ziel.
        """
        parsed = self.parse_system_name(
            system_name
        )

        if not parsed:
            return {
                "ok": False,
                "reason": tr("score.reason.unsupported_name"),
            }

        stats = self.target_statistics(
            target_key,
            min_sector_samples=1,
            min_code_mass_samples=1,
        )

        if stats["systems"] <= 0:
            return {
                "ok": False,
                "reason": tr("score.reason.no_data"),
            }

        mass_map = {
            row["key"]: row
            for row in stats["mass"]
        }

        sector_map = {
            str(row["key"]).casefold(): row
            for row in stats["sectors"]
        }

        code_mass_map = {
            str(row["key"]).casefold(): row
            for row in stats["code_mass"]
        }

        mass_row = mass_map.get(
            parsed["mass"]
        )
        sector_row = sector_map.get(
            parsed["sector"].casefold()
        )
        code_mass_row = code_mass_map.get(
            parsed["code_mass"].casefold()
        )

        parts = []

        if mass_row:
            parts.append(
                (
                    0.25,
                    int(
                        mass_row.get("score")
                        or 50
                    ),
                )
            )

        if sector_row:
            parts.append(
                (
                    0.30,
                    int(
                        sector_row.get("score")
                        or 50
                    ),
                )
            )

        if code_mass_row:
            parts.append(
                (
                    0.45,
                    int(
                        code_mass_row.get("score")
                        or 50
                    ),
                )
            )

        if parts:
            total_weight = sum(
                weight
                for weight, _score
                in parts
            )

            score = int(
                round(
                    sum(
                        weight * component
                        for weight, component
                        in parts
                    )
                    / total_weight
                )
            )
        else:
            score = 50

        evidence = []

        for kind, name, row in (
            (
                tr("score.evidence.sector"),
                parsed["sector"],
                sector_row,
            ),
            (
                tr("score.evidence.code"),
                parsed["code_mass"],
                code_mass_row,
            ),
            (
                tr("score.evidence.mass_code"),
                parsed["mass"],
                mass_row,
            ),
        ):
            if not row:
                continue

            evidence.append({
                "type": kind,
                "name": name,
                "systems": int(
                    row.get("systems")
                    or 0
                ),
                "hits": int(
                    row.get("hits")
                    or 0
                ),
                "finds": int(
                    row.get("finds")
                    or 0
                ),
                "rate": float(
                    row.get("rate")
                    or 0.0
                ),
                "score": int(
                    row.get("score")
                    or 0
                ),
            })

        return {
            "ok": True,
            "parsed": parsed,
            "target_key": target_key,
            "target_label": stats["target_label"],
            "score": score,
            "level": self.level(score),
            "baseline": stats["baseline"],
            "systems": stats["systems"],
            "hits": stats["hits"],
            "finds": stats["finds"],
            "evidence": evidence,
        }


    def score_system(self, system_name):
        parsed = self.parse_system_name(system_name)
        if not parsed:
            return {
                "ok": False,
                "reason": tr("score.reason.unsupported_name"),
            }

        stats = self.statistics(
            min_sector_samples=1,
            min_code_mass_samples=1,
        )

        if stats["systems"] <= 0:
            return {
                "ok": False,
                "reason": tr("score.reason.no_data"),
            }

        mass_map = {
            row["key"]: row
            for row in stats["mass"]
        }
        sector_map = {
            str(row["key"]).casefold(): row
            for row in stats["sectors"]
        }
        code_mass_map = {
            str(row["key"]).casefold(): row
            for row in stats["code_mass"]
        }

        mass_row = mass_map.get(parsed["mass"])
        sector_row = sector_map.get(parsed["sector"].casefold())
        code_mass_row = code_mass_map.get(parsed["code_mass"].casefold())

        def combined(metric):
            parts = []

            if mass_row:
                parts.append((0.25, mass_row[f"{metric}_score"]))

            if sector_row:
                parts.append((0.30, sector_row[f"{metric}_score"]))

            if code_mass_row:
                parts.append((0.45, code_mass_row[f"{metric}_score"]))

            if not parts:
                return 50

            weight = sum(item[0] for item in parts)

            return int(round(
                sum(item[0] * item[1] for item in parts)
                / weight
            ))

        bio_score = combined("bio")
        value_score = combined("value")

        evidence = []

        for kind, name, row in (
            ("Sektor", parsed["sector"], sector_row),
            ("Code", parsed["code_mass"], code_mass_row),
            ("Massencode", parsed["mass"], mass_row),
        ):
            if not row:
                continue

            evidence.append({
                "type": kind,
                "name": name,
                "systems": row["systems"],
                "bio_systems": row["bio_systems"],
                "bio_rate": row["bio_rate"],
                "value_systems": row["value_systems"],
                "value_rate": row["value_rate"],
            })

        return {
            "ok": True,
            "parsed": parsed,
            "bio_score": bio_score,
            "bio_level": self.level(bio_score),
            "value_score": value_score,
            "value_level": self.level(value_score),
            "evidence": evidence,
            "systems": stats["systems"],
            "bio_baseline": stats["bio_baseline"],
            "value_baseline": stats["value_baseline"],
        }
