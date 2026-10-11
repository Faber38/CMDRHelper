# Facility type images

Bundled PNG files are resolved centrally by `ui/station_assets.py`. Both the
Explorer station cards and the station detail dialog use `station_preview()`.
Images are generic type illustrations, not photographs of the named facilities.

| Station type | Image |
| --- | --- |
| `Coriolis` | `coriolis.png` |
| `Orbis` | `orbis.png` |
| `Ocellus`, `Bernal` | `ocellus.png` |
| `Dodec` | `dodec.png` |
| `Outpost` | `outpost.png` |
| `SurfaceStation`, `CraterPort`, `CraterOutpost` | `surface_station.png` |
| `PlanetaryConstructionDepot`, `Planetary Construction Depot` | `surface_station.png` |
| `OnFootSettlement` | `settlement.png` |
| `MegaShip`, `Mega ship` | `megaship.png` |
| `FleetCarrier` | `fleet_carrier.png` |
| `AsteroidBase`, `Asteroid base` | `asteroid_base.png` |
| `SpaceConstructionDepot`, `Space Construction Depot` | `space_construction_depot.png` |
| Unmapped type with reliable `is_planetary=True` | `surface_station.png` |
| Unknown type/location | `neutral_station.png` |

Explicit mappings take precedence over the planetary flag. The existing
`station_types.normalize_station_type()` supplies the `Bernal` alias; names,
services, landing pads and proximity do not establish a station subtype.
`stations.load_stations()` converts SQLite INTEGER flags to model booleans
(`1` to `True`, `0` to `False`, SQL NULL to `None`) without updating stored data.
The projection may omit unknown fields; a later untyped approach does not erase
an already known station subtype.

## Fallbacks and display

Missing or unreadable settlement artwork falls back to `surface_station.png`.
Other specific artwork, or an unavailable surface fallback, falls back to
`neutral_station.png`, then the existing graphical diamond placeholder if that
image also cannot be decoded. A surface image never substitutes for an explicit
orbital type or Fleet Carrier. The legacy `standard.png` is retained unchanged
but is no longer selected or used as a fallback.

The supplied neutral artwork depicts a generic orbital facility; “neutral” means
unspecified station design, not a depiction that proves a planetary/orbital
location. Reliable planetary evidence therefore selects the surface image first.

The existing image widget fits the whole canvas with `KeepAspectRatio`, without
stretching or additional cropping, in both themes and at high pixel densities.
Double-clicking a decoded image opens the existing full-resolution viewer.
A graphical placeholder has no source image and does not open a viewer.
No download or personal-image selection is performed.

## Asset format and conversion

All thirteen assets are 8-bit RGB PNGs without transparency, using lossless
DEFLATE compression (PNG method 0), PNG filter method 0 and no interlace.
The exact encoder/compression level of the original ten files is not recorded
in PNG metadata and cannot be reliably reconstructed from the file alone.

Seven original images use 1280 × 720 (16:9). `coriolis.png` and `orbis.png` use
1280 × 853; `fleet_carrier.png` uses 1066 × 676. All ten remain byte-for-byte
unchanged, including `standard.png`.

The three added motifs were visually identified before conversion:

| Original source | Final file | Original pixels | Scaled motif | Final bytes |
| --- | --- | --- | --- | ---: |
| `Industrielle Asteroidenstation im All.png` — facility built into rock | `asteroid_base.png` | 1404 × 1120 | 903 × 720 | 1,194,003 |
| `Willkommen am orbitalen Raumhafen.png` — generic station | `neutral_station.png` | 1536 × 1024 | 1080 × 720 | 1,159,516 |
| `Orbitale Raumwerft über der Erde.png` — cranes and construction structures | `space_construction_depot.png` | 1536 × 1024 | 1080 × 720 | 1,390,197 |

Each new image uses a 1280 × 720 RGB canvas. Pillow Lanczos resizing preserves
source proportions (within integer pixel rounding). Centered dark side margins
(`#080a0e`) preserve the complete motif, including towers, cranes and landing
pads; no crop was needed. PNG saving uses `optimize=True` and `compress_level=9`,
without palette reduction or lossy encoding. Combined size falls from 7,900,267
to 3,743,716 bytes. Original source files are removed after successful conversion
and verification; no duplicate source artwork is shipped.
