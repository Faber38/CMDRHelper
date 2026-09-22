# Local observations in Sell / Buy (3.6.2)

Implementation note; the existing user help remains deliberately unchanged.

`TradeView.start_search` copies `ObservedMarketCache.all(active_fid)` and resolves
local distances through the existing recommendation coordinate resolver. The
worker invokes `search_trade`, which calls the unchanged Spansh provider once.
Commander changes cancel and invalidate pending results. The current station is
an eligible target, unlike recommendations.

`market_candidates` contains the previously used snapshot conversion, MarketID
merge and location filters. Recommendation behavior and diagnostic counters are
unchanged. `observed_at` becomes the local offer's `market_updated_at`;
`retrieved_at` never participates in freshness. Local age must be nonnegative,
strictly below 24 hours, and within the user age limit. Equal timestamps prefer
local. Different IDs remain distinct even when names match.

As in recommendations, a newer valid snapshot supersedes older quotes before
price, quantity and metadata filters. This prevents reviving an old quote when
the observed commodity is absent, has zero price, or insufficient stock/demand.
Local snapshots currently lack pad/arrival metadata and cannot satisfy those
active filters. No provider metadata is grafted onto a local quote.

After merging the actually delivered provider candidates with local candidates,
Sell sorts by descending sell price, Buy by ascending buy price. The common
result is limited to 100 (or a smaller query limit). Provider limits are unchanged:
there is **no global mathematical top-100 guarantee** for Spansh candidates that
were never delivered. No extra page or refill request is made. `truncated`
continues to describe provider/search/result limits only.

`MarketSearchResult.community_failure` is an optional original `MarketStatus`.
With usable locals, status is OK and this field records the failed community
search. The existing status area explains that offers may be missing. Without
usable locals, the original error survives. Cancellation discards all results.
The table retains ten columns; row objects retain provider identity, and existing
system/station tooltips display it. A local/mixed result uses an accurate market
notice. New notice translations are separate to preserve existing help edits.

No storage path is added. Spansh stays RAM-only; local snapshots are not inserted
into its cache. Only the established observed-cache API is used.

Offline coverage: `test_combined_trade.py` runs the same matrix for both sides;
`test_combined_trade_view.py` tests actual worker completion, displayed partial
results and commander changes using a temporary observed cache.

## Deliberately deferred help corrections (all twelve languages)

- Trade / market data: replace the assertion that Sell and Buy use only Spansh
  community data with valid own observations plus community data.
- Trade / own market data: remove the assertion that Sell and Buy do not search
  these observations.
- Explain own TTL (<24 hours), the additional age filter, MarketID freshness and
  the local tie-break for Sell/Buy, including the current station as a target.
- Explain local results surviving a community failure and the separate incomplete
  search notice; distinguish this from a bounded/truncated search.
- Clarify that the visible top 100 are selected after merging delivered candidates,
  not a global guarantee; sources are available in existing cell tooltips.
- `trade.help`: scope “prices remain exclusively in memory” to community data;
  valid own observations continue to use the persistent observed cache.
- `trade.buy_help`: broaden the community-only freshness warning to both sources.
- `recommend.help` and recommendation behavior need no functional correction.
