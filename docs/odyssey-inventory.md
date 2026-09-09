# Odyssey inventory — phase O1

`cmdrhelper.odyssey_inventory` is independent of Qt, the Engineering inventory,
catalogs and database writes. It reconstructs Items, Components, Data and
Consumables separately for ShipLocker and Backpack.

## API

`OdysseyInventoryReader.reconstruct(commander_id, fid, journal_sessions, until=None)`
returns a fresh `OdysseyInventory`. `until` is an optional inclusive UTC/offset
timestamp for reproducible historical reads. Use `rows` for per-stack container
counts, safe totals, display names and mission status; `count(symbol, container)`
for a container aggregate, and `total_count` for a coherent personal total.
Unknown counts are `None`. No capacity or English translation is invented.
`Name_Localised` is retained solely as display information in its source language.

Each container exposes `snapshot_timestamp`, `updated_at`, `known`, pending
observations and diagnostic `issues`. `reconstructed_at` is the last relevant
journal event time, not wall-clock time. `last_change` identifies the last applied
delta with its physical source and changed stack keys. Authoritative snapshot
replacement does not invent an action such as “collected”. The public `rows` and
`count` accessors hide stale counts; internal `Container.stacks` can contain stale
facts and must never be used as current inventory without checking validity.

## Authority and container coherence

* All four arrays are required for a full snapshot. Validate atomically, then
  replace that container. Absence from a complete container means zero.
* Notification-only ShipLocker does not clear stacks: it invalidates their
  currentness until a full journal snapshot arrives. This is intentionally
  conservative; a sidecar notification cannot certify unchanged quantities.
* Snapshots with the same timestamp establish a coherent pair. A newer independent
  snapshot does not silently certify an older occupied backpack.
* Embark establishes an empty backpack and invalidates the locker until its full
  snapshot arrives. Do not assume a successful transfer in the face of capacity
  limits or losses. A subsequent locker snapshot pairs with this empty backpack.
* Disembark invalidates both containers until new snapshots establish allocation.
* TransferMicroResources, Died and Resurrect invalidate both containers; O1 does
  not guess their transfer/loss details. DropItems is an observation like use.
* Sidecars are deliberately not opened, even if present beside a journal. An old
  Backpack.json therefore cannot reappear after Embark or cross commanders.
  Future sidecar support requires a matching identified session, event timestamp,
  sequence and stable read. Missing historical sidecars are not reconstructible.

## Event strategy

BackpackChange Added/Removed is the authoritative backpack delta. CollectItems,
UseConsumable and DropItems are observations only. Match observations one-for-one
with a BackpackChange by timestamp, canonical name, category, signed quantity and
compatible available ownership/mission/stolen fields. Both event orders work;
multiple identical actions require multiple confirmations. Unmatched observations
make backpack counts unknown until confirmed or replaced by a snapshot. There is
no arbitrary time-window merge. A standalone collection is not guessed as a
second delta. A UseConsumable observation has quantity one when Count is absent.

Locker deltas support both BuyMicroResources formats, SellMicroResources,
TradeMicroResources, UpgradeSuit/UpgradeWeapon Resources and explicitly identified
Odyssey MissionCompleted MaterialsReward. Count is never multiplied. Raw,
Manufactured and Encoded are excluded. Bare `Data` rewards remain ambiguous;
without a catalog only `$MICRORESOURCE_CATEGORY_Data;` establishes Odyssey Data.

Missing categories may be resolved from an existing unique matching stack.
Ambiguous stacks, malformed events and underflows invalidate the affected
container; a full valid snapshot recovers it. Multi-item deltas are atomic.

## Mission stacks

Stack identity comprises category, canonical Frontier symbol, MissionID, OwnerID
and Stolen within its container. Unknown Stolen/OwnerID values are not fabricated.
Missing/zero MissionID and the historical unsigned sentinel 18446744073709551615
represent no mission identifier. Explicit mission stacks never supply ordinary
upgrade/trade consumption. A delta missing ownership cannot select between
multiple matching owner stacks.

MissionAccepted/Completed/Failed/Abandoned set auxiliary status only.
MissionRedirected never removes stock. Completion rewards can add stock; the
mission status itself cannot delete or reclassify an existing mission stack.

## Commander isolation, caching and limitations

Only identified journal_sessions with matching commander_id and fid_seen are
eligible. The file must also contain exactly that FID in Commander/LoadGame.
Conflicting duplicate index rows, unknown and ambiguous attribution are excluded.
Missing/unreadable selected files mask all public counts. Journal files are read
only through complete physical lines, sorted by timestamp, path and byte offset.

Duplicate index rows cannot repeat a source event. Exact complete journal copies
are deduplicated by SHA-256. Repeated reconstruction always uses a fresh reducer;
cached results are defensively copied. Partial or modified archive copies with
different contents are not heuristically merged: canonical source indexing is
required for those cases. No surface-mining processed-event keys are used.

Parsed file facts are cached by resolved path, device/inode, size, mtime and ctime.
Up to eight reconstruction results are cached by commander/FID, eligible source
signatures and cutoff. Appends, replacements or attribution changes invalidate
the result. No worker threads or AppState changes are introduced in O1.

## Real regression and provenance

`tests/fixtures/odyssey_faber38.json` contains original selected events from the
identified FABER38 / FTEST0001 journals: MissionCompleted 1064707191 on
2026-08-30T11:32:06Z, the simultaneous Backpack/ShipLocker pair on
2026-09-08T14:58:01Z, and Embark/locker updates through 14:58:26Z.

At the paired snapshot: locker 3,131, backpack 8, total 3,139. After Embark and
the new full locker snapshot: locker 3,139, backpack 0, total 3,139 (not 3,147).
The vehicle schematic remains quantity one with MissionID 1064707191 and status
completed. These are regression fixtures, not hardcoded inventory or repair rules.

The same results were checked read-only against all 411 identified FABER38
sessions (43 unknown sessions excluded). At the inspected latest Disembark,
2026-09-08T16:08:45Z, no new pair exists: the current total is correctly unknown.

## O2 remains separate

No static material catalog, capacity, suit-modifier rules, translations or UI are
included. O2 must validate current symbols, contextual groups, recipe relevance,
category capacities and consumable limits. Broader action-only recovery and
Powerplay-specific operations require further fixtures and explicit semantics;
notifications/full snapshots remain the conservative authority in O1.
