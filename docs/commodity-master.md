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
