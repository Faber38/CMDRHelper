# Odyssey identity catalog — O2

The catalog is offline Python data, independent of Qt, databases, capacity
observation and commander inventories. The inventory reader remains responsible
for quantities and confidence; the [Odyssey view](odyssey-view.md) supplies the UI.
Engineering and Odyssey retain separate catalogs and inventory semantics.

## Exact scope and provenance

Checked 2026-09-08. The 223 identities are the intersection of active EDDI
definitions with the publicly inspectable Odyssey Materials Helper definitions:

* [EDDI MicroResource.cs](https://github.com/EDCD/EDDI/blob/aacbf3b921eff696e3e590fc13c09a3dad49bd2c/DataDefinitions/MicroResource.cs),
  revision `aacbf3b921eff696e3e590fc13c09a3dad49bd2c`.
* [Odyssey Materials Helper](https://github.com/jixxed/ed-odyssey-materials-helper/tree/2e6d4c3e767d2b714ffddc5c9386831d66812916),
  revision `2e6d4c3e767d2b714ffddc5c9386831d66812916`. Sources below
  `application/src/main/java/nl/jixxed/eliteodysseymaterials`: enums Asset, Good,
  Data, Consumable, Suit; constants/OdysseyBlueprintConstants.java. Names from
  `application/src/main/resources/locale/material/odyssey/*.csv`.
* Cross-check: [FDevIDs microresources.csv](https://github.com/EDCD/FDevIDs/blob/c35612952dd6a547d1a7ac4cffab9c7051e86579/microresources.csv),
  revision `c35612952dd6a547d1a7ac4cffab9c7051e86579`, 196 base definitions.
* Cross-check: [INARA](https://inara.cz/elite/components/), including the specific
  item pages. Its overview “Used” count includes non-engineering uses; it is
  deliberately not the source of engineering flags.

Helper application revision `e20a98e5e8255ed946f732afbf5a9c3d2c980bc5` (3.15.5)
has moved its data to a separate Core dependency. That dependency was not
publicly retrievable at verification time. The earlier explicit data revision
above is used, not an assertion that its data came from the newest executable.

| Category | Count |
|---|---:|
| Items | 61 |
| Components | 33 |
| Data | 123 |
| Consumables | 6 |

Components have Chemicals 10, Circuits 12, Tech 11. Other categories have no
invented subgroup. Every symbol is a lowercase Frontier identity, not a display
name. Preserve Frontier spellings such as `surveilleancelogs` and `seedgeneaology`.

Excluded: `powermegashipdata` (EDDI unconfirmed, Helper TODO), UNKNOWN/None
placeholders, and orphan translation key `geographicaldata`. The latter is not
an alias for `geologicaldata`.

## Special groups and availability

Groups are standard 196, powerplay 22, thargoid_spire 2, operations 2, unica 1.
The additions to FDevIDs comprise 15 Powerplay Items, 7 Powerplay Data and:

| Symbol | Name | Group |
|---|---|---|
| biomechanicalcomponent | Spire Refinery Compound | thargoid_spire |
| sabotagedcomponent | Contaminated Spire Refinery Compound | thargoid_spire |
| operationsstrikedata | Researcher Location Data | operations |
| operationscounterattackdata | Facilities Intelligence Report | operations |
| nm_seed | Unica Seed | unica |

`confirmed_identity` means a confirmed catalog identity, not guaranteed present
availability. These five special identities have `context_dependent` availability:
their current general obtainability was not fully established. Special groups do
not imply recipe relevance, tradeability or a current mission association.

`usage_tags={upload}` applies to spyware, virus, powerpreparationspyware,
powerspyware and operationscounterattackdata, from the source's upload flag.
No static MissionID, mission boolean or mission status is included.

## Engineering flags

Membership is derived from material references in the five explicit recipe maps
of OdysseyBlueprintConstants, not from preferences, commander unlock progress,
generic usefulness or economic value. No recipe execution/requirements are
implemented here.

| Flag | Unique identities |
|---|---:|
| suit_upgrade | 7 |
| weapon_upgrade | 9 |
| suit_modification | 50 |
| weapon_modification | 46 |
| engineer_unlock | 19 |

The overlapping union is 98: 33 Components, 54 Data, 11 Items. The remaining 125
have no use in these five recipe maps; this never means “only tradeable”. The
power regulator has no such flags. Powerplay inventory record is Items,
`powerinventory`, English “Inventory Record”, group powerplay, no engineering flag.

## Controlled names and i18n

English names come from the Helper CSV's default English column. For de/es/it/fr,
use a non-empty explicit language cell, otherwise the matching EDDI
`DataDefinitions/Properties/MicroResources.<language>.resx` entry. Canonical
symbol matching is case-insensitive; do not manufacture aliases or translations.

| Language | Actual names | English fallback |
|---|---:|---:|
| en | 223 | 0 |
| de | 221 | 2 |
| es | 223 | 0 |
| it | 217 | 6 |
| fr | 205 | 18 |
| no, sv, fi, pl, nl, tr, el (each) | 0 | 223 |

German operationsstrikedata and operationscounterattackdata remain English.
Italian gaps: biologicalweapondata, biometricdata, digitaldesigns, both
operations identities and nm_seed. French gaps comprise the five special
identities above and 13 Powerplay Items. No German journal localization is copied
to any other language.

Names are domain-owned static resources in `_odyssey_catalog_data.py`.
`odyssey.material.<symbol>` keys identify these resources. Use `localized_name`
or `merge_inventory` to resolve them; these new keys are deliberately not injected
into the existing twelve global UI translation dictionaries. An omitted language
reads the current i18n language without changing it; an explicit language does
not mutate application language. Unsupported or missing translations use name_en.

Adaptation: source formats converted into immutable public definitions, recipe
references converted into membership flags, invalid identities excluded, names
combined with the precedence above. License copies and attribution are in
[odyssey-catalog-licenses.md](odyssey-catalog-licenses.md).

## Capacity API

`capacity(container, category, suit=None, extra_backpack=False)` uses O1 container
and category identifiers. No material entry has a maximum.

* ShipLocker: Items/Components/Data each 1,000; not a shared 3,000 pool.
* Backpack bases, in Items/Components/Data order:
  maverick 40/60/20, artemis 20/40/10, dominator 10/20/10, flight_suit 5/10/10.
* An explicitly supplied Extra Backpack modifier doubles the three base limits;
  it never changes locker limits. The caller supplies an observed suit/modifier
  configuration; this API does not infer upgrade eligibility from a suit name.
* Consumables: None for every container/configuration. No 100-unit rule.
* Unknown suit/modifier: None. No combined Locker+Backpack hard limit is defined.

Sources: the pinned Suit.java and EXTRA_BACKPACK_CAPACITY recipe modifiers;
[Frontier Update 18.08](https://store.steampowered.com/news/posts/?appids=359320&enddate=1732121069&feed=steam_community_announcements).
The earlier Helper total/1000 display must not be used to impose a hard personal
combined limit or a maximum on each item.

## Projection and filters

Public API: `get_material`, `all_materials`, `materials_by_category`,
`localized_name`, `translation_coverage`, `capacity`, `merge_inventory`.
Definitions and their flag/tag sets are immutable. No commander cache exists
in this module. The existing O1 reader remains responsible for reconstruction.

`merge_inventory` preserves each O1 InventoryRow and StackKey exactly, including
MissionID, OwnerID, Stolen, mission status, container counts and known flags.
The wrapper adds commander/FID, reconstruction and snapshot times, definition
and localized name. O1's last_change remains available on the unchanged inventory.

For entirely absent catalog identities, optional placeholder rows use O1's
known/unknown container semantics. There is no invented normal stack alongside
an existing mission-only identity. Placeholder rows have `observed=False`.
Unknown future symbols survive with their O1 display name/counts and no static
definition. Category conflicts remain unresolved O1 rows; never silently recast.
Multiple O1 stacks can yield more than 223 rows for 223 catalog identities.

`matches_filter` prepares stable domain selectors:

* all: every row, including unknown.
* mission: observed O1 stack with MissionID; status alone is never a selector.
* engineering: at least one confirmed engineering flag.
* backpack/locker: known count in that container > 0, independent of the other.
* empty: known coherent total == 0; unknown totals do not match.

Search, tabs, grades, styling and capacity bars are not implemented. O3 can use
these APIs without modifying the Engineering view or O1 stack semantics.

## Validation

The existing real O1 fixture supplies all 131 FABER38 symbols. All resolve without
aliases. Its synchronous 2026-09-08T14:58:01Z pair remains total 3,139, as does the
post-Embark snapshot. Mission 1064707191 remains completed, with the vehicle
schematic present and mission-tagged. Two simulated commanders are projected
through the same reader with different inventories/actions and no mixing.
