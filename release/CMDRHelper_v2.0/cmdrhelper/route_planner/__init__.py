"""Eigenständiger Bereich für die Routenplanung."""

__all__ = ["RoutePlannerView"]


def __getattr__(name):
    # Datenmodelle dürfen vom Journalparser verwendet werden, ohne dabei die
    # komplette Qt-Oberfläche des Routenplaners zu importieren.
    if name == "RoutePlannerView":
        from .route_planner_view import RoutePlannerView

        return RoutePlannerView
    raise AttributeError(name)
