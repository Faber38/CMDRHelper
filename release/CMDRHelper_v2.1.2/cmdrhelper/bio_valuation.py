from __future__ import annotations

import re


# Vista-Genomics-Basiswerte für mit dem Genetic Sampler erfasste
# Odyssey-Exobiologie. "First Logged" = Basiswert + 4x Bonus = 5x gesamt.
BIO_VALUES = {
    "Aleoida Arcus": 7_252_500,
    "Aleoida Coronamus": 6_284_600,
    "Aleoida Gravis": 12_934_900,
    "Aleoida Laminiae": 3_385_200,
    "Aleoida Spica": 3_385_200,

    "Bacterium Acies": 1_000_000,
    "Bacterium Alcyoneum": 1_658_500,
    "Bacterium Aurasus": 1_000_000,
    "Bacterium Bullaris": 1_152_500,
    "Bacterium Cerbrus": 1_689_800,
    "Bacterium Informem": 8_418_000,
    "Bacterium Nebulus": 5_289_900,
    "Bacterium Omentum": 4_638_900,
    "Bacterium Scopulum": 4_934_500,
    "Bacterium Tela": 1_949_000,
    "Bacterium Verrata": 3_897_000,
    "Bacterium Vesicula": 1_000_000,
    "Bacterium Volu": 7_774_700,

    "Cactoida Cortexum": 3_667_600,
    "Cactoida Lapis": 2_483_600,
    "Cactoida Peperatis": 2_483_600,
    "Cactoida Pullulanta": 3_667_600,
    "Cactoida Vermis": 16_202_800,

    "Clypeus Lacrimam": 8_418_000,
    "Clypeus Margaritus": 11_873_200,
    "Clypeus Speculumi": 16_202_800,

    "Concha Aureolas": 7_774_700,
    "Concha Biconcavis": 19_010_800,
    "Concha Labiata": 2_352_400,
    "Concha Renibus": 4_572_400,

    "Electricae Pluma": 6_284_600,
    "Electricae Radialem": 6_284_600,

    "Fonticulua Campestris": 1_000_000,
    "Fonticulua Digitos": 1_804_100,
    "Fonticulua Fluctus": 20_000_000,
    "Fonticulua Lapida": 3_111_000,
    "Fonticulua Segmentatus": 19_010_800,
    "Fonticulua Upupam": 5_727_600,

    "Frutexa Acus": 7_774_700,
    "Frutexa Collum": 1_639_800,
    "Frutexa Fera": 1_632_500,
    "Frutexa Flabellum": 1_808_900,
    "Frutexa Flammasis": 10_326_000,
    "Frutexa Metallicum": 1_632_500,
    "Frutexa Sponsae": 5_988_000,

    "Fumerola Aquatis": 6_284_600,
    "Fumerola Carbosis": 6_284_600,
    "Fumerola Extremus": 16_202_800,
    "Fumerola Nitris": 7_500_900,

    "Fungoida Bullarum": 3_703_200,
    "Fungoida Gelata": 3_330_300,
    "Fungoida Setisis": 1_670_100,
    "Fungoida Stabitis": 2_680_300,

    "Osseus Cornibus": 1_483_000,
    "Osseus Discus": 12_934_900,
    "Osseus Fractus": 4_027_800,
    "Osseus Pellebantus": 9_739_000,
    "Osseus Pumice": 3_156_300,
    "Osseus Spiralis": 2_404_700,

    "Recepta Conditivus": 14_313_700,
    "Recepta Deltahedronix": 16_202_800,
    "Recepta Umbrux": 12_934_900,

    "Stratum Araneamus": 2_448_900,
    "Stratum Cucumisis": 16_202_800,
    "Stratum Excutitus": 2_448_900,
    "Stratum Frigus": 2_637_500,
    "Stratum Laminamus": 2_788_300,
    "Stratum Limaxus": 1_362_000,
    "Stratum Paleas": 1_362_000,
    "Stratum Tectonicas": 19_010_800,

    "Tubus Cavas": 11_873_200,
    "Tubus Compagibus": 7_774_700,
    "Tubus Conifer": 2_415_500,
    "Tubus Rosarium": 2_637_500,
    "Tubus Sororibus": 5_727_600,

    "Tussock Albata": 3_252_500,
    "Tussock Capillum": 7_025_800,
    "Tussock Caputus": 3_472_400,
    "Tussock Catena": 1_766_600,
    "Tussock Cultro": 1_766_600,
    "Tussock Divisa": 1_766_600,
    "Tussock Ignis": 1_849_000,
    "Tussock Pennata": 5_853_800,
    "Tussock Pennatis": 1_000_000,
    "Tussock Propagito": 1_000_000,
    "Tussock Serrati": 4_447_100,
    "Tussock Stigmasis": 19_010_800,
    "Tussock Triticum": 7_774_700,
    "Tussock Ventusa": 3_227_700,
    "Tussock Virgam": 14_313_700,
}

FIRST_LOGGED_MULTIPLIER = 5


def _clean(value):
    text = str(value or "").strip()
    text = text.replace("$", "").replace(";", "")
    text = re.sub(r"\s+", " ", text)
    return text


def species_name(entry):
    """
    Liefert möglichst den Gattung+Art-Namen, unabhängig davon, ob das
    Journal in species bereits 'Stratum Tectonicas' oder nur 'Tectonicas'
    gespeichert hat.
    """
    genus = _clean(entry.get("genus"))
    species = _clean(entry.get("species"))
    variant = _clean(entry.get("variant"))

    candidates = [species, variant, f"{genus} {species}".strip()]

    # Längste bekannte Bezeichnung zuerst, damit Teiltreffer nicht stören.
    for known in sorted(BIO_VALUES, key=len, reverse=True):
        known_lower = known.casefold()
        for candidate in candidates:
            if known_lower in candidate.casefold():
                return known

    return species or variant or genus


def _normalise_name(value):
    return _clean(value).casefold()


def base_value(entry, learned_values=None):
    """
    Liefert den Basiswert einer BIO-Art.

    Reihenfolge:
    1. aus echten SellOrganicData-Verkäufen gelernter Wert
    2. feste Referenztabelle
    3. 0 = noch unbekannt
    """
    name = species_name(entry)

    if learned_values:
        wanted = _normalise_name(name)

        for learned_name, learned_value in learned_values.items():
            if _normalise_name(learned_name) == wanted:
                try:
                    return int(learned_value or 0)
                except (TypeError, ValueError):
                    pass

        # Falls die Verkaufsbezeichnung etwas anders lokalisiert ist,
        # zusätzlich über enthaltene Namen abgleichen.
        candidates = [
            _clean(entry.get("species")),
            _clean(entry.get("variant")),
            _clean(entry.get("genus")),
            name,
        ]

        for learned_name, learned_value in learned_values.items():
            learned_norm = _normalise_name(learned_name)
            if not learned_norm:
                continue

            if any(
                learned_norm in _normalise_name(candidate)
                or _normalise_name(candidate) in learned_norm
                for candidate in candidates
                if candidate
            ):
                try:
                    return int(learned_value or 0)
                except (TypeError, ValueError):
                    pass

    return int(BIO_VALUES.get(name, 0))


def is_complete(entry):
    # Elite Journal: dritter erfolgreicher Genetic-Sampler-Scan = Analyse.
    return _clean(entry.get("scan_type")).casefold() in {
        "analyse",
        "analyze",
    }


def biology_totals(entries, learned_values=None):
    """
    Zählt nur vollständig analysierte Organismen.

    base_total:
        Sicherer Vista-Genomics-Basiswert.

    first_logged_total:
        Möglicher Gesamtwert, falls jede Probe beim Verkauf First Logged ist.
        Der tatsächliche First-Logged-Status steht beim Sammeln nicht sicher
        fest und wird daher bewusst nur als Maximalwert ausgewiesen.
    """
    base_total = 0
    completed = 0
    unknown = []

    for entry in entries or []:
        if not isinstance(entry, dict) or not is_complete(entry):
            continue

        completed += 1
        value = base_value(
            entry,
            learned_values=learned_values,
        )

        if value:
            base_total += value
        else:
            unknown.append(species_name(entry) or "Unbekannte BIO-Art")

    return {
        "completed_count": completed,
        "base_total": int(base_total),
        "first_logged_total": int(base_total * FIRST_LOGGED_MULTIPLIER),
        "unknown": unknown,
    }
