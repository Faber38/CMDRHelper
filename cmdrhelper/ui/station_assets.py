"""Bundled facility artwork only; no personal images or data enrichment."""
from pathlib import Path
from cmdrhelper.stations import ORBITAL_TYPES
from cmdrhelper.ui.ship_assets import _image_preview

STATION_ASSET_DIR = Path(__file__).resolve().parents[1] / 'assets' / 'stations'
IMAGE_CLASSES = {
    'Dodec': 'dodec', 'Coriolis': 'coriolis', 'Orbis': 'orbis', 'Ocellus': 'ocellus',
    'Outpost': 'outpost', 'SurfaceStation': 'surface_station',
    'CraterPort': 'surface_station', 'CraterOutpost': 'surface_station',
    'Planetary Construction Depot': 'surface_station',
    'Space Construction Depot': 'standard',
    'OnFootSettlement': 'settlement', 'MegaShip': 'megaship', 'FleetCarrier': 'fleet_carrier',
}


def station_image_class(station):
    station = station or {}
    kind = station.get('station_type')
    if kind in IMAGE_CLASSES:
        return IMAGE_CLASSES[kind]
    # Known orbital types must not become surface stations through a bad flag.
    if kind not in ORBITAL_TYPES and station.get('is_planetary') is True:
        return 'surface_station'
    return 'standard'


def bundled_image(image_class):
    if image_class not in set(IMAGE_CLASSES.values()) | {'standard'}:
        return None
    try:
        root = STATION_ASSET_DIR.resolve()
        path = root / (image_class + '.png')
        return path if path.is_file() and path.resolve().parent == root else None
    except (OSError, RuntimeError):
        return None


def station_preview(station, width, height, dpr=1.0, personal_path=None):
    # Same decoder/cache contract as ShipImage, deliberately no personal path.
    image_class = station_image_class(station)
    classes = [image_class]
    if image_class == 'settlement':
        classes.append('surface_station')
    classes.append('standard')
    return _image_preview(tuple(bundled_image(key) for key in dict.fromkeys(classes)),
                          width, height, dpr)
