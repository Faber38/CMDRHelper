# Mining catalogue provenance (2026-09-12)

One catalogue and table cover both planetary and asteroid/ring commodities.
`origin` describes verified acquisition routes, not station economy types.
It is not a planet-type spawn prediction. A planetary extraction economy alone
does not prove that a commander can mine that commodity at a surface location.

## Identity and localized names

Internal symbols and English labels: [EDCD FDevIDs commodity.csv](https://github.com/EDCD/FDevIDs/blob/master/commodity.csv).
New German, French, Spanish and Italian labels were checked against EDDI's
[commodity resources](https://github.com/EDCD/EDDI/tree/develop/DataDefinitions/Properties).
Where no verified localization was available, the explicit English FDevIDs
label is retained in the language file (including Spanish Void Opal).
No translations were inferred from mineral names outside Elite.

## Origin evidence

- The original 37 entries retain the project owner's supplied surface-mining
  reference as their planetary provenance. Eighteen are also documented in the
  [ring-mining resource table](https://elite-dangerous.fandom.com/wiki/Miner):
  Monazite, Alexandrite, Grandidierite, Serendibite, Rhodplumsite, Low Temperature
  Diamonds, Platinum, Osmium, Tritium, Palladium, Gold, Silver, Samarium,
  Bertrandite, Thorium, Uraninite, Methanol Monohydrate Crystals and Water.
  These are `both`; the other original entries remain `surface`.
- Jadeite is `surface`: the owner's current in-game observation is independently
  supported by this project's `surface_mining_commodities` record (`jadeite`,
  `Jadeit`) and local ship/SRV CargoTransfer records containing 22 tonnes.
- [Taaffeite](https://elite-dangerous.fandom.com/wiki/Taaffeite) and
  [Moissanite](https://elite-dangerous.fandom.com/wiki/Moissanite) are documented
  planetary-mining commodities. Their classification includes planetary mining
  POIs/containers, not a claim of verified Rhino deposits on every planet type.
- Seventeen additional asteroid/ring entries come from the resource table:
  Bauxite, Benitoite, Bromellite, Cobalt, Coltan, Gallite, Hydrogen Peroxide,
  Indite, Lepidolite, Liquid oxygen, Lithium Hydroxide, Methane Clathrate,
  Musgravite, Void Opal, Painite, Praseodymium and Rutile. There is no verified
  surface acquisition claim for these additions, so they are `asteroid` only.

Total: 57 entries, comprising 22 `surface`, 17 `asteroid` and 18 `both`.
The filters therefore show 40 planetary and 35 asteroid/ring commodities.

Cryolite and Pyrophyllite were reviewed but are deliberately not added:
planetary market production/supply is documented, but no sufficiently reliable
player-mining acquisition route was established. They are not guessed to be
surface resources. Future verified observations can extend this catalogue.

## Prices and missing information

The original 37 prices remain byte-for-byte numerically unchanged. Jadeite uses
41,895 Cr/t, supplied by the owner from an Elite screenshot. All other 19 new
entries have `average_price=None` and `price_source=None`: older community prices,
EDDI base values and current station offers do not establish the requested
reference average. No INARA scraping or runtime market/network fetch is used.
Unknown prices have no value class and sort last in both directions.

## UI and local stock check

`materials/mining/origin_filter` stores `all`, `surface` or `asteroid` in QSettings.
`materials/mining/value_class_filter` stores `all` or the existing class rank.
Search, class, origin and positive-stock filters are combined with AND.
`both` is included in either specific origin filter. ABBAU navigation first
creates/activates the lazy Mining tab, then selects `surface`.

The inspected current journal records 22 tonnes of Jadeite transferred to Ship
at 09:43:43 UTC and to Carrier at 10:47:44 UTC on 2026-09-12. The inspected
Cargo.json at 10:47:46 UTC contains no Jadeite. Consequently, the current ship
snapshot must not be made to display the earlier 22 tonnes. Regression tests
verify that a known positive Jadeite ship snapshot is visible, including with
the positive-stock and planetary filters. Carrier tracking rules are unchanged;
an old transfer without a confirmed carrier baseline does not create a balance.
