# Market data provider

## Scope and architecture

`cmdrhelper.market_data` defines the immutable `MarketSearch`, `MarketOffer`,
`MarketSearchResult`, `MarketStatus`, `TradeSide`, and `PadSize` contracts and the
structural `MarketDataProvider` protocol. Consumers call `search_sell` (the
commander owns cargo) or `search_buy` (the commander wants cargo). Neither the
contract nor prospective trading logic needs to import Spansh.

`cmdrhelper.spansh_market.SpanshMarketProvider` is the first adapter. It uses the
existing `spansh_transport.request_json` transport, not a new HTTP stack. It is
synchronous: a future UI must schedule it off its event thread. This phase adds
no UI, inventory integration, recommendations, profit calculations or routes.

## Commodity identity and prices

Queries accept an exact Frontier integer ID or a known master symbol/journal
token. The existing 412-entry commodity master supplies the canonical ID,
unchanged symbol and English name. Only the adapter uses that English name for
Spansh's commodity filter and response matching. There is no second commodity
list, fuzzy matching or localized identity key. Engineering materials and
Odyssey microresources are outside this commodity contract.

Unknown identities return `UNKNOWN_COMMODITY` without HTTP. The result retains
the original query, including an unknown future raw value, for later display.
An unknown commodity elsewhere in a station's market does not affect matching
the requested commodity. A future mismatch between the master's English name
and Spansh's vocabulary needs a reviewed adapter mapping; no alias is guessed.

Spansh price fields are commander-centric:

| Provider field | Internal field | Meaning |
| --- | --- | --- |
| `buy_price` | `commander_buy_price` | Commander pays when buying |
| `sell_price` | `commander_sell_price` | Commander receives when selling |

Both prices and `supply`/`demand` are retained. Zero is retained as zero; invalid
or missing values are `None`, not invented prices. Only a positive price and
positive available quantity for the requested direction qualify. The explicit
minimum quantity, when supplied, must be met. This is reported availability,
not a reservation or guarantee of execution price for an entire cargo load.

## Requests and filters

Reference: public [Spansh station search](https://spansh.co.uk/stations) and
[searchable fields](https://spansh.co.uk/api/stations/searchable_fields), checked
2026-09-20. These are public web-application interfaces, not a pinned API version.

Search uses JSON `POST https://spansh.co.uk/api/stations/search`, with
`reference_system`, `filters`, `sort`, zero-based `page` and `size`. Sell searches
use `market[].sell_price` and `demand`; buy searches use `buy_price` and `supply`.
Numeric and timestamp filters use `comparison: "<=>"` and two-value ranges;
distance uses `{min, max}`. Price and quantity upper bounds are 2,147,483,647.
The adapter passes radius, quantity, age, pad, carrier and optional star-distance
filters to the server and defensively checks returned offers locally as well.

Carrier inclusion defaults to false. On the first excluding search per provider
instance, `GET /api/stations/field_values/type` discovers Spansh's current type
vocabulary. The adapter sends the non-carrier types as an allowlist in `type`.
Types containing `carrier` (case-insensitive, including `Drake-Class Carrier`)
are recognized locally too. The vocabulary stays in memory for the instance's
lifetime. Instantiate a new provider to refresh it; future non-carrier type names
can otherwise be omitted until refresh. Docking access is retained when supplied,
not interpreted as assurance that this commander may dock.

Pad semantics:

* `ANY`: no pad restriction; unknown pad data may be returned.
* `LARGE`: Large pad confirmed.
* `MEDIUM`: Medium or Large confirmed.
* `SMALL`: Small, Medium or Large confirmed.

Spansh's conjunctive filters require separate pad branches: Large flag, positive
Medium count, positive Small count. Medium uses the first two, Small all three.
Overlapping results are deduplicated by market ID. A Medium/Small branch does
not require negative or zero information about other pad sizes.
Missing pad information cannot establish reachability; this
may conservatively omit stations with incomplete pad metadata. No ship detection
is performed. `distance_to_arrival` is in light-seconds, reference distance in ly.

## Results, age and cache

Normalized offers retain commodity identity, system/market IDs, station type,
distances, largest known pad, carrier/access information, both prices and both
quantities. `provider` identifies the source.

`market_updated_at` is the original market-report timestamp as an aware UTC
datetime. `retrieved_at` is when that response was received. Fetching a record
does not make its market report fresh. Missing, malformed, timezone-less or
future market timestamps cannot qualify. The default maximum age is 24 hours;
callers can set another positive `timedelta`.

The per-instance in-memory LRU search cache defaults to 300 seconds and 32
entries, configurable at construction. Its key includes provider, normalized
master identity, side and every query option, including result limit. Known ID,
symbol and wrapper forms share their commodity identity. Successful empty
results are cached; errors and cancelled searches are not. Cache hits preserve
original retrieval timestamps and recheck current market age. Thus an expired
market report can disappear during the cache TTL without a new HTTP request.
There is no automatic fallback to old cache entries on network failure.

Results are locally sorted by directional price (sell descending, buy ascending),
then younger market report, nearer reference distance, station name; system name
and market ID break remaining ties. Duplicate market IDs are consolidated,
preferring the newer market report. Sorting is over fetched valid candidates.

## Request bounds and cancellation

Defaults: 10-second socket timeout (configurable up to 30), at least one second
between request starts, at most one transient retry, 50 stations per page and
six search pages total. Limits are bounded by constructor validation. Pages
rotate through pad branches so every branch receives a first page. At most
seven logical requests are needed for a cold default search including type
discovery; retries may double the HTTP attempts. Results are limited to 1–100.

`truncated` reports unfinished pagination or more candidates than the requested
result limit. No exhaustive best-price claim is made across unseen pages, nor
is the ordering among unseen price ties guaranteed. Local filtering can reduce
the returned count below the limit. Spansh's changing community dataset is not
a transactional snapshot across pages.

Calls on one provider instance are serialized, including identical cache misses.
Use a shared instance for application requests; this is not a global rate limiter
for other existing Spansh clients. No background polling is started.

Pass a `threading.Event` as `cancel`. Lock acquisition, request spacing and retry
waits are cancellable; cancellation is checked before/after each HTTP request.
An already running urllib request cannot be forcibly interrupted and remains
subject to its socket timeout. Cancellation returns no partial offers.

HTTP 429 preserves `Retry-After`, accepts seconds or HTTP-date, and uses at most
one retry when the wait is at most 30 seconds. Longer or invalid waits do not
cause an early retry. A per-instance cooldown also protects subsequent queries;
invalid Retry-After values use a conservative 30-second cooldown. Retry-After is
also observed for other transient HTTP failures. These are CMDRHelper policies,
not claims of an officially published Spansh rate quota.

## Error contract and privacy

Statuses distinguish `OK`, `NO_RESULTS`, `UNKNOWN_COMMODITY`, `UNKNOWN_SYSTEM`,
`INVALID_QUERY`, `NETWORK_ERROR`, `TIMEOUT`, `HTTP_ERROR`, `RATE_LIMIT`,
`INVALID_JSON`, `INVALID_RESPONSE`, and `CANCELLED`. HTTP status and Retry-After
are structured metadata. Provider errors do not leak raw HTTP bodies or
exceptions through the search interface. Unrecognized provider error messages
remain generic errors rather than being guessed into unknown-system failures.
Malformed individual offers are omitted; an empty result means no qualifying
validated offers in the bounded search, not proof of absence in the game.

Only the reference system and public search criteria are transmitted. No FID,
commander name, cargo inventory or carrier holdings are sent. No DB tables,
QSettings entries, journal/sidecar changes, persistent price files or telemetry
are introduced. The seven-day system cache is not used. Community prices,
quantities, carrier positions and access rights can change before arrival.

## Tests and future integration

`tests/test_market_data_provider.py` uses synthetic JSON and an injected opener,
clock and wait function. It performs no network requests and writes no settings
or database. It covers request filters, identity mapping, directional prices,
timestamps, cache behavior, bounded pagination, errors, retries and cancellation.
Historical live result counts are not permanent test assertions.

A later phase can consume this protocol from a manually triggered sell/buy
search UI, showing report age and incomplete-result state explicitly. Profit,
route generation and inventory integration remain separate future work.
