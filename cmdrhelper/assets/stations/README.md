# Facility type images

Optional bundled PNG files, resolved centrally by `ui/station_assets.py`:

`dodec.png`, `coriolis.png`, `orbis.png`, `ocellus.png`, `outpost.png`,
`surface_station.png`, `settlement.png`, `megaship.png`, `fleet_carrier.png`, `standard.png`.

All ten listed images are bundled, including `fleet_carrier.png`.
`Planetary Construction Depot`, `SurfaceStation`, `CraterPort` and `CraterOutpost`
use `surface_station.png`. `OnFootSettlement` uses `settlement.png`, falling back
to `surface_station.png` if its specific image is missing or unreadable.
Explicit type mappings take precedence over `is_planetary`. Unmapped types with
the boolean flag `is_planetary=True` use `surface_station.png`, except known
orbital types. `Space Construction Depot` uses `standard.png`; no specific
station design is inferred. Other unknown types also use `standard.png`.
Missing or unreadable images finally fall back to `standard.png`, then to the
technical ShipImage placeholder if no image can be decoded. No download or
personal-image selection is performed. The station fallback is named
`standard.png`; the independent ship asset naming is unchanged.

The resolver is injected into the existing image widget; double-clicking a decoded
image uses the existing full-resolution ShipImageViewer. A placeholder has no source
image and therefore does not open an image viewer.
