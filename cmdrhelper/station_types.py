"""Exact Elite station type aliases for semantic comparisons."""


def normalize_station_type(value):
    """Elite reports Ocellus in Docked and Bernal in Market for the same port.

    Keep all other values exact; no case folding, trimming or type inference.
    Callers may retain the original spelling when storing observations.
    """
    return 'Ocellus' if value == 'Bernal' else value
