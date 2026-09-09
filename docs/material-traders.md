# Material trader search service

`cmdrhelper.material_traders.MaterialTraderSearchService` is a
synchronous service used by the on-demand material-page worker. It imports no Qt and uses no
settings, commander identity, inventory, journal uploader or personal API key.

```python
from cmdrhelper.material_traders import Coordinates, MaterialTraderSearchService, TraderType
service = MaterialTraderSearchService()
result = service.find_nearest(TraderType.RAW, coordinates=Coordinates(0, 0, 0))
# Alternatively: service.find_nearest(TraderType.RAW, system_name="Sol")
```

## Adapter and transport

`SpanshMaterialTraderClient` owns all Spansh JSON details:

- `POST https://spansh.co.uk/api/stations/search`: explicit `material_trader.value`
  filter (Raw/Manufactured/Encoded), reference coordinates, ascending distance,
  page and size. The published OpenAPI currently does not document this search.
- `GET /station/{market_id}`: mandatory final detail revalidation against the
  documented station record, including the Material Trader service.
- Name-only requests use `GET /search/systems?q=...` with exact name matching and
  `GET /system/{id64}` to obtain coordinates. Ambiguous or incomplete references
  fail instead of using a guessed location. Known coordinates avoid those calls.

The existing route clients' urllib execution, JSON decoding and transport error
handling were extracted to `cmdrhelper.spansh_transport`. Both route clients keep
their form encoding, timeout defaults, injectable urlopen and legacy error codes.
Trader retries remain confined to the trader adapter. Ship and carrier routing
now share exact name/ID64 validation through `route_planner/system_resolution.py`;
this is separate from the trader retry policy.

The public models are immutable `Coordinates`, `TraderStation`, `CandidatePage`
and `TraderSearchResult`. Callers do not receive raw Spansh JSON. Required station
fields are names, IDs, finite coordinates, type and an exact known trader subtype.
Optional malformed metadata remains unknown. Carrier type recognition is isolated
in `is_fleet_carrier`, covering Drake-Class Carrier and other carrier variants.
Station names and economies never determine the trader subtype.

## Selection and bounded requests

At most three pages of ten candidates are read, deduplicated by Market-ID and
sorted by locally calculated Euclidean light-year distance (Market-ID breaks ties).
Up to five candidates receive sequential detail checks. Wrong trader types,
carriers and invalid candidates are discarded. Changed system identity or
coordinates at detail time invalidate the candidate rather than retaining stale
location data. Valid detail metadata replaces search metadata, never merges stale
search values back into missing detail fields.

The result is the nearest validated candidate in the bounded, source-ordered
candidate window, not a claim of complete or perfectly current galactic coverage.
This distinction also matters if the upstream distance sort becomes unreliable.
The UI presents the nearest known validated candidate, not guaranteed galactic coverage.

Every HTTP request has a 10-second timeout and at most one retry for network,
timeout, 429, 500, 502, 503 or 504 errors. Requests are sequential, spaced at least
one second apart; retry backoff is two seconds, respecting Retry-After up to 30
seconds. Longer Retry-After values abort the attempt rather than retrying too early.
Maximum request attempts: 16 with coordinates, 20 with name resolution. No fixed
provider quota or service availability guarantee has been established. Confirm
search API terms/stability with Spansh before public UI rollout.

## Cache and error semantics

The service serializes calls and maintains a 32-entry LRU cache with **300 seconds
TTL**, using monotonic time. Keys include exact reference coordinates (or normalized
system name) and trader type. Five minutes avoids repeated refresh traffic without
presenting days-old recommendations. Cached records keep their original retrieval
time. Only FOUND and an exhausted, valid NOT_FOUND search are cached.

Statuses distinguish FOUND, NOT_FOUND, SEARCH_LIMIT, INVALID_INPUT,
REFERENCE_UNKNOWN, NETWORK_ERROR, HTTP_ERROR (with status), TIMEOUT, INVALID_JSON,
SCHEMA_ERROR and DETAIL_VALIDATION_FAILED. A network failure never means that no
trader exists. A bounded search without a match does not become NOT_FOUND. Missing
or unknown trader fields are invalid data, not an inferred trader type. Exhausted
detail checks with no valid candidate report DETAIL_VALIDATION_FAILED.

## Metadata and access

The result retains trader type, station/system names and IDs, coordinates, local
ly distance, raw arrival distance, station type, planetary/large-pad flags, pad
counts, source updated_at and UTC retrieval time. Optional source permit, docking,
station-state and faction-state fields are carried when supplied. Access remains
unverified even if some access metadata exists; missing permit flags do not mean
"no permit required". The service does not select for a particular ship's pad size
or possession of permits. The later UI must not promise an accessible/open trader.

## Arrival distance reference check, 2026-09-09

The official https://docs.spansh.co.uk/ OpenAPI 2.3.2 describes station arrival
values as kilometres. Read-only local Docked/DistFromStarLS observations were
compared with two public `/station/{market_id}` responses:

| Station | Market-ID | Journal ls | Spansh raw |
| --- | --- | ---: | ---: |
| Elizabethii Sanctuary | 4368262147 | 542.953628 | 542.684355 |
| Foden Orbital | 3231487744 | 80.180179 | 89.349195 |

The fixture `tests/fixtures/material_trader_arrival_reference.json` records both
observation dates and source timestamps, without commander identity. These values
support the light-second interpretation, but are not simultaneous measurements:
Foden differs by about 11.4%. They do not settle a universal endpoint contract
against the contradictory schema. **arrival_distance_unit remains unknown**;
there is no ls property and no conversion. Tests preserve the raw observations.

## Real network verification, 2026-09-09

Using public Sol coordinates (0,0,0), all three service calls returned a detail-
validated non-carrier, with finite coordinates and locally recomputed distances:

- Raw: Broglie Terminal / 61 Cygni, 11.368731102238279 ly.
- Manufactured: Patterson Enterprise / Sirius, 8.588748544607649 ly.
- Encoded: Magnus Gateway / EZ Aquarii, 11.098326520809342 ly.

System-name resolution for Sol also succeeded. These are observations, not stable
station-name test assertions. The detail records reported UnderRepairs for Patterson
and DamagedHuman for Magnus, illustrating why access is deliberately unverified.
The search API and detail API had different timestamps. Automated tests use offline
responses and do not depend on current community data or require network access.

## Material page integration

`ui/material_trader_panel.py` owns the compact information card and its QRunnable
worker, using the existing QThreadPool/queued-signal pattern. The search button is
in the MaterialView title row; the result card is below search/filter controls.
Raw, Manufactured and Encoded follow the active category; Odyssey hides both.
No initialization, tab change, inventory refresh or jump starts a search.

The worker snapshots the active AppState commander/system identity and uses known
coordinates, including a read-only lookup by SystemAddress in the existing systems
table. Name-only references use the service resolver. Commander identity is only
used locally to reject obsolete results and never enters a Spansh request.

The page remembers results per type and clears them when the reference changes.
Late results cannot replace recommendations for another reference. One job at a
time prevents duplicate calls; the service cache is retained across requests.
Expired results are hidden without automatic network activity. Nothing is persisted
in DB or QSettings. The card displays the explicit type, local ly distance, station
record update date and unverified access. Raw arrival distance is never displayed.

The route signal carries only a target system. MainWindow opens the existing route
page and invokes RoutePlannerView.set_destination_system, selecting its ship tab.
This does not calculate a route, copy a station target or start navigation.

Live UI verification on 2026-09-09 from the locally saved current reference
Plio Aip KN-B d13-201 (4425.875, 77.625, 10335.21875) found:

| Type | Station | System | Local distance ly |
| --- | --- | --- | ---: |
| Raw | Helgrind Gateway | NGC 6530 Sector ZE-X b2-0 | 7797.248766216558 |
| Manufactured | Pellegrino Hub | Xi-2 Lupi | 11053.755145002266 |
| Encoded | Hay Hub | Desubi | 11072.872854148585 |

Each card was checked and handed to the real route planner without starting a
route. Dark/Light images are under /tmp/cmdrhelper-trader-ui; their material stocks
are replayed from the existing offline material fixture, while trader results were
obtained through the real service. UI text has 13 new keys in all twelve languages.
The trader explanation is available in all twelve help languages, including
explicit categories, direct system distance, uncertain access and route handoff.
