# Manual commodity trading (Phases 4/4a and 5)

The main navigation places **Materials → Trade** after Explorer. Existing page
indices stay stable. Trade has functional **Sell** and **Buy** tabs and its own help.
There are no recommendation, rare-goods or route actions.

## Inputs and identity

The single commodity field opens a local selection dialog with a search field
and a responsive grid of compact tiles. It reads the existing 412-entry master
and filters by localized display name, English master name and canonical symbol,
without starting a market request. A QListView/model/delegate paints the tiles
without creating individual commodity widgets. Normal desktop widths show four
to six columns; narrower windows or larger fonts reduce columns and wrap names.
The grid scrolls vertically. Tab focuses the grid, arrow keys move between tiles,
Enter selects, and Escape or Cancel preserves the existing selection. The existing 57 mining translations
are reused. German additionally uses the reviewed offline commodity catalog (411/412
maintained names); other languages retain their English fallback. See
[commodity-master.md](commodity-master.md#german-display-names-phase-4a) for
identity checks, provenance, licensing and the CuratedCommodity exception. Selection and requests
use the Frontier commodity ID, not display text.

Defaults: 1 whole tonne, 100 ly, 24 hours, any pad, no Fleet Carriers, unlimited
arrival distance. Radius choices are 25/50/100/250/500 ly; age choices are
1/6/12/24 hours and 3/7 days. Quantity is bounded to 1–2147483647 tonnes. Optional
arrival distance accepts whole positive light seconds up to 2147483647; blank
means unlimited. Invalid input receives a localized message.

The reference is `state.system`, shown above the filters. Unknown current
location prevents a request. A system change cancels an active search and clears
previous results. Changing filters clears previous results without searching. There is no manual location entry or automatic cargo/ship input.

## Execution and results

Only the search button starts a `MarketWorker` (`QRunnable` plus queued Qt signal).
The page owns one `SpanshMarketProvider` for its lifetime and delegates to
`search_sell` with `minimum_quantity` and `limit=100`. It does not build Spansh
requests, normalize prices or create a second cache. Existing provider pad,
carrier, freshness, demand and arrival filters remain authoritative.

During a search the input fields and search button are disabled. Cancellation
sets the provider's `threading.Event`; an in-flight network request may need to
finish its bounded timeout before the worker exits. Late results after a cancel
or a reference change are discarded. Closing/deleting the page or quitting the
application cancels active work. No polling is scheduled.

Results show system, station, distance, commander selling price per tonne,
demand, potential revenue, arrival distance, pad, human-readable age and type.
Fleet Carriers are explicitly labeled. Revenue uses only
`commander_sell_price × requested quantity`, and is absent if demand is
insufficient. Numeric columns sort numerically; selling price descending is the
initial order. The exact UTC market timestamp is available in the age tooltip.
Each row retains its `MarketOffer` identity for possible future route actions.

The UI distinguishes missing selection/location, unknown commodity/system,
invalid inputs, empty results, connectivity errors, timeout, rate limit, malformed
responses and cancellation, without displaying raw exception text. Provider
`truncated` results carry a visible refinement warning, including empty bounded
results. At most 100 rows are rendered; no UI pagination requests are made.
Cache hits still refresh the UI and are marked. The provider rechecks freshness
when serving its existing in-memory cache.

## Persistence and validation

The page has no database or QSettings access and stores no prices persistently.
There is no schema or version change. All new strings and contextual help cover
the twelve supported languages. Forms wrap long rows; the page and result table
scroll, columns are user-resizable, and application font/theme styling is reused.

Offline tests use synthetic state and market data. `test_trade_view.py` covers
filters, identity, asynchronous responsiveness, cancellation, error mapping,
prices/revenue, numeric sorting, data age, a real-provider cache hit with fake
transport, and all twelve languages in dark/light at normal/enlarged font sizes.
MainWindow/help regression tests cover the new navigation position and help.
The existing provider suite retains the Giant's Rest price-direction regression.
Live validation is intentionally a single manual search after offline checks;
results are neither fixtures nor saved market data.

## Community market information (Phase 4a)

A permanent, wrapping information label above the result table states that
community market reports may have changed and that users should check data age.
It is ordinary UI text translated into all twelve languages, applies to future
trade workflows too, and is not an error, popup or freshness guarantee.
The existing minutes/hours/days column and exact UTC tooltip remain unchanged.
No provider, filter, worker, cache, sorting, price or revenue behavior changed.
Commodity searches continue matching localized names, English master names and
canonical symbols: both Bier and Beer select the same Beer identity.

## Phase 4/4a acceptance

The user confirmed live acceptance before requesting the development commit:

- The Trade page was started in the real application and a live Spansh sell
  search succeeded, including displayed Grandidierite results.
- The commodity picker was checked live. Its focus/scroll selection defect was
  reproduced with Qt mouse events and corrected: mouse focus no longer scrolls
  the previous selection underneath the pointer before hit testing. Subsequent
  Grandidierite selection was stable; identity remains the Frontier ID role.
- The community-data notice and German "Landeplatz" label were visible, the
  result table was sortable, and result wording correctly described markets
  buying from the commander (German "Ankaufsangebote").

This records user-reported live acceptance, not an additional live request
performed while preparing the commit. No commander identifiers, locations,
prices, timestamps from market responses or other personal runtime data are
included. The final corrections concerned UI, text, sorting and picker focus;
no new live Spansh request was required for the commit checks.

## Buying (Phase 5)

Buy and Sell move the same scrollable form and results table between two tab
pages. Commodity picker, all filter widgets, worker/status/cancellation, data-age
rendering, sorting items and community-data notice are shared. Current filter
values survive tab switches in memory; displayed results are cleared. No settings
or database writes are introduced. The existing 412-entry picker and German
411/412 localization are unchanged.

The worker captures the trade direction and a UI generation at submission. Buy
calls only `MarketDataProvider.search_buy()`, using the existing Spansh adapter.
Quantity becomes minimum **supply**. Price / t is `commander_buy_price`, Angebot
(supply) is the reported available quantity, and total cost is purchase price
times requested tonnes. Rows without sufficient supply or a positive purchase
price are not displayed. The provider remains responsible for reference, radius,
age, pad, carrier and optional arrival-distance filtering. No second transport,
cache or price normalization exists.

Buy starts with price ascending; Sell keeps price descending. Text columns are
case-insensitive/stable, numerical columns use raw values, pads use S/M/L with
unknown last, and age uses elapsed seconds with the first header click showing
freshest data first. Existing age text and UTC tooltip remain unchanged. Up to
100 results are visible; truncated results retain the shared refinement notice.

Switching tabs cancels any active search and increments the generation, even
when switching back to the original direction. The form stays disabled until
the old worker finishes; its result is discarded if its generation differs.
Thus no overlapping UI searches or late cross-direction results are accepted.
A new search is manual. Cancel is visible only while the request is cancellable.
The same provider instance retains its existing side-specific in-memory cache
keys, allowing repeated Buy or Sell searches to reuse their respective entries.

Result wording follows the market perspective: Commander Sell finds market
buying offers (German Ankaufsangebote); Commander Buy finds market selling offers
(German Verkaufsangebote). The new `trade.buy_*` texts, Buy tab label and extended
trade help cover all twelve languages. Help explains the payable price, reported
supply and cost calculation, and warns that supply may be lower on arrival.
The common notice explicitly asks users to check data age; it is no guarantee.

`test_trade_buy.py` covers direction dispatch, minimum supply, costs, cache
separation, cancellation/generation rejection, shared state, filters, sorting,
errors, truncation, twelve-language help, both themes and enlarged fonts.
Existing sell, picker identity, commodity, provider and MainWindow regressions
remain required. The Phase 4/4a acceptance recorded above applies to selling;
the separate Phase 5 acceptance is recorded below. No market prices or personal
runtime data are stored in this documentation or in fixtures.

## Phase 5 manual acceptance

The user confirmed live acceptance of Trade → Buy before requesting the
development commit. The manual scenario used Beer, 1 tonne, a 100 ly radius,
market data at most 24 hours old, Fleet Carriers excluded and any landing pad.
The UI displayed two market selling offers and correctly presented price per
tonne, supply, total cost, distance, arrival distance, landing pad and data age.
This is a user-reported acceptance record, not a fixed expected live result or
an automated fixture. No prices, station/system names, commander identifiers or
personal runtime records are included. No further live Spansh search was made
while preparing the commit.

### Eigene Marktdaten

Unter dem Ausgangspunkt steht die Anzahl selbst beobachteter Stationsmärkte des
aktiven Commanders und das Alter der jüngsten Beobachtung. Ein Markt wird beim
Öffnen des Warenmarkts in Elite bei laufendem Helper automatisch aufgenommen.
Jede MarketID zählt einmal; nur lokale Snapshots unter 24 Stunden zählen.
Spansh-Ergebnisse sind in dieser Zahl nicht enthalten. Die Statuszeile verändert
weder Verkaufs- noch Einkaufssuche. Details: [Lokaler Marktcache](observed-market-cache.md#status-auf-der-handel-seite).
