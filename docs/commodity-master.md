# Commodity master (Phase 2)

This is an offline identity catalog, not an inventory, market-price source or
complete list of all possible Frontier game content. No existing consumer has
been migrated: Cargo, Mining, Carrier, missions, chronicle, UI and persistence
retain their current behavior. Engineering Raw/Manufactured/Encoded materials
and Odyssey MicroResources belong to their separate catalogs.

## Snapshot and provenance

`cmdrhelper/_commodity_master_data.py` contains 412 immutable data rows;
`cmdrhelper/commodity_master.py` exposes frozen definitions and lookups.
The data format is version 1. Canonical rows are sorted by numeric Frontier ID.

Reference: [EDCD/FDevIDs](https://github.com/EDCD/FDevIDs), pinned revision
`c35612952dd6a547d1a7ac4cffab9c7051e86579` (2026-09-05).
Retrieved and checked **2026-09-20**. EDCD is a community reference and explicitly
does not guarantee completeness of its collections.

| Source | Rows | Last file change (UTC) | SHA-256 of original CSV bytes |
|---|---:|---|---|
| [commodity.csv](https://github.com/EDCD/FDevIDs/blob/c35612952dd6a547d1a7ac4cffab9c7051e86579/commodity.csv) | 270 | 2026-09-02 14:04:33 | `b2ae885fcdf8a3eff8ad7a81d449fe7dbea032d0546c32f4fc61bc4b199bebde` |
| [rare_commodity.csv](https://github.com/EDCD/FDevIDs/blob/c35612952dd6a547d1a7ac4cffab9c7051e86579/rare_commodity.csv) | 142 | 2024-12-20 12:47:57 | `bda5166a1394ed3680aaeee7916ce41804b7a0e69866c0e0cc8d4352700e3e2b` |

Last-change revisions are `32ab38cecd72831771a273103243887db9e8fe2f` and
`7f658aa72e966113e508b7b7b7f088fb9d8eb5e5`, respectively. These and original
byte lengths are also recorded in `SOURCE_FILES` in the static data module.

The source files are disjoint, not a base list plus overlapping rare flags.
Union by ID produces 412 unique IDs and 412 case-insensitively unique symbols.
All 16 upstream categories, including `NonMarketable`, are retained.

## Identity and API

Each `CommodityDefinition` has `frontier_id`, `symbol`, `english_name`, `category`,
`rare` and `mining_origins`. Exact upstream symbol spelling is preserved,
including case, underscores and apparent typos such as `UnocuppiedEscapePod`.
English/localized labels are not primary keys or implicit aliases.

- `all_commodities()` returns an immutable tuple of definitions.
- `lookup_by_id(int)` returns a definition or `None` for no catalog match.
  It does not coerce booleans, floats or strings into IDs.
- `lookup_by_symbol(str)` accepts case-insensitive symbols and complete
  `$..._name;` wrappers, returning a definition or `None` for no match.
- `resolve_symbol(str)` returns the exact canonical upstream symbol if known;
  otherwise it returns the **original string unchanged**, including whitespace,
  wrappers, underscores and case. Non-string input raises `TypeError`.

Thus `platinum`, `Platinum` and `$platinum_name;` resolve to `Platinum`.
`$m_tissuesample_fluid_name;` resolves to `M_TissueSample_Fluid`.
`mtissuesamplefluid` is unknown, not silently merged. Unknown lookup results are
not stock values: callers must retain their raw input using `resolve_symbol`.
Only casing and complete token wrappers are accepted spelling equivalences;
there is no inferred display-name or fuzzy alias table. Index construction
rejects duplicate IDs and ambiguous case-insensitive symbols.

`Drones` identifies ID 128066403, English label `Limpets`; the label itself is
not accepted as an identity alias. `NonMarketable` does not mean that limpets
cannot be purchased through their dedicated service. There is deliberately no
`marketable` boolean, price, stock or market availability in this model.

## Rare and Mining

All 142 rare-file entries have `rare=True`; the other 270 have `rare=False`.
Rare origin `market_id` is intentionally omitted: it is separate location
metadata and would not prove current stock or availability.

Mining origins copy the existing 57 definitions in `mining_catalog.py`, with
provenance described in [mining-catalog-sources.md](mining-catalog-sources.md).
This is CMDRHelper evidence, not a field supplied by EDCD:

- 22 have `('surface',)`;
- 17 have `('asteroid',)`;
- 18 have `('surface', 'asteroid')`.

This yields 40 surface and 35 asteroid entries. Empty origins mean no evidence
recorded here, not proof that mining is impossible. Surface evidence can include
POI/container acquisition; it does not necessarily prove a Rhino deposit.
No PML composition or deposit properties are inferred. Existing reference prices
and all Mining translations remain in their original modules unchanged.

## Updates and limits

Updates are development-time operations, never an application startup download:

1. Explicitly choose a revision and obtain both CSV files at that revision.
2. Record retrieval/check dates, file revisions, lengths and original hashes.
3. Parse `id` as an integer; preserve `symbol`, `name`, `category` exactly. Set
   `rare` from source-file membership and join only reviewed Mining symbols by
   case-insensitive identity. Map existing `both` to `('surface', 'asteroid')`.
4. Sort rows by ID; review every addition, removal and changed identity/category.
   Do not infer translations, aliases, mining evidence or prices from names.
5. Update the snapshot metadata, expected counts and content fingerprint only
   after review; run catalog and existing-consumer regressions.

The tests pin the entire ordered snapshot and its ID/symbol relationship, not
just its length. Unknown future symbols remain representable without network
access. Later consumer migrations must separately address existing persisted
lowercase keys and localized mission descriptions; importing this module does
not migrate any data or change an existing normalizer.

## German display names (Phase 4a)

`commodity_localization.commodity_name()` resolves display text separately from
master identity. `_commodity_localization_de.py` contains 354 immutable tuples
`(frontier_id, canonical_symbol, German_name, source)`. Both ID and symbol must
match the master. The 57 existing German mining names remain in `i18n/de.py`:
411/412 names are maintained, including all 142 Rare Goods and 99 Salvage entries.
No identity, category, Rare flag, mining origin or master reference name changed.

The display order is maintained German catalog / existing locale mining name,
then English master name, then a readable symbol for a future unknown entry.
Other eleven languages retain their existing mining translations and English
fallback. The picker has no language-qualified Frontier observation, so it does
not insert a runtime Localised fallback or a learning cache. A future consumer
with a safely language-qualified observation may use it before English; never
silently replace a curated name or infer language from the UI setting alone.

Sources were checked against the 412 identities on 2026-09-21. Per-entry pinned
URLs, chosen names and review decisions are in
[commodity-localization-sources.csv](commodity-localization-sources.csv).
The sources are EDDI `Commodities.de.resx` at
`d3b964ea7c8bb959ad6537f55b308f293a326905` and EliteDangerousCore's German TLP
at `c86bee245acd482dd68f7e445fd3e67d4dc99bb1`. EDDI provides an ID/symbol
bridge; Core joins symbol through MCMRType's English resource key. Display-name
similarity was never used to infer identity. Local German Market names were
used only as corroborating evidence for already openly licensed values.
Conflicts without exact corroboration were individually reviewed; this is a
maintained community catalog, not a claim that every name is Frontier-certified.

The two upstream catalogs use Apache-2.0. Redistribute
[the full license](licenses/Apache-2.0.txt) and
[attribution/change notice](licenses/commodity-localization-NOTICE.txt)
with these data. Neither reviewed upstream tree contained a separate NOTICE.
Local observations are not declared Apache-licensed. No INARA values or new
FDevIDs translations were imported. Game assets were not extracted.

Mining decisions: keep **Kobalt**; correct **Praseodym** and **Periklas-Dunit**
as German mineral spellings. All other 54 German mining names and all mining
names in other languages are retained. Two non-mining proper-name typos in the
community data were editorially corrected to **Shintara-Wasser** and
**Korro-Kung-Pellets** using the master spelling; their original source remains
recorded in the attribution. Other community alternatives are not automatically
applied to the mining catalog.

`CuratedCommodity`, ID **129045961**, category **Industrial Materials**, keeps
**Curated Commodity Package** as its English fallback. It is not Rare and has no
recorded mining origin. It is user-relevant: the
[ED Odyssey Materials Helper release notes](https://github.com/jixxed/ed-odyssey-materials-helper/releases)
identify it as a Community Goal commodity. Market observations on
[EDSM](https://www.edsm.net/en/system/stations/id/23408/name/AD%2BLeonis/details/idS/588672/nameS/Cartmill%2BDepot/facility/market)
also list the commodity; this does not guarantee current availability. It remains
selectable, with no new trading restriction or invented German translation.

Updates require identity validation, per-entry source/license review, conflict
review and offline regression tests. Missing languages are a separate phase;
there is no startup download, mass translation, database migration, price storage
or persistent collection of observed names.
