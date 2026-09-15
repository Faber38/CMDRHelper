# Mining inventory (Phase 2)

The original 37 reference prices are unchanged. The shared catalogue now also
covers verified asteroid/ring commodities; see [catalogue provenance](mining-catalog-sources.md).
Inventory and market prices remain separate. No market API, carrier-stock
estimate or schema migration is introduced.

## Sources and carrier audit (2026-09-12)

Primary protocol reference: [Frontier Player Journal Manual v37](https://hosting.zaonce.net/community/journal/v37/Journal_Manual_v37.pdf),
sections 3.1 Cargo, 8 Market/MarketBuy/MarketSell, 11 Fleet Carriers,
and 13.52 CargoTransfer. This manual predates planetary mining; journal symbols
and local Ship/SRV events were also checked against the project's actual files.

The local archive inspected contained 2,973 Cargo, 1,114 MiningRefined,
313 CargoTransfer, 1,771 CarrierStats, 82 CarrierTradeOrder, 500 Market,
136 MarketSell, 213 MarketBuy, 73 CollectCargo and 19 EjectCargo events.
There was no CarrierMarket event or carrier-inventory sidecar.

| Candidate | Evidence | Interpretation |
|---|---|---|
| Cargo / Cargo.json | Vessel=Ship or SRV; full commodity Inventory and total Count | Complete vehicle snapshot, not carrier stock |
| CarrierStats | SpaceUsage.Cargo is total occupied cargo space | No commodity breakdown (not A) |
| CargoTransfer | Type, Count, Direction; no CarrierID in inspected transfers | Deltas, without a carrier opening balance (B insufficient) |
| CarrierTradeOrder | PurchaseOrder/SaleOrder/CancelTrade | Trade instructions; SaleOrder can expose that commodity's stock at order time, but is not a complete/current warehouse snapshot (C) |
| Market / Market.json | MarketID, Items with Stock/Demand/BuyPrice/SellPrice | Market offers, not a complete personal warehouse inventory (C) |
| CarrierMarket | Neither a local event nor a complete stock format established by the checked manual | No supported warehouse source (D) |
| commander_carriers table | Carrier identity, name, location and update time | No per-commodity opening balance |

Conclusion: **D for reliable personal carrier inventory**, with partial B/C data.
Transfers cannot establish an unknown opening balance and do not cover other
players' trades while the owner is offline. No carrier quantities are inferred,
even from a sale order, market stock, fuel reserve or total occupied space.
Carrier stock stays unknown unless the user explicitly confirms an opening
balance. This is a manually maintained ledger, not an Elite inventory snapshot.

## Split-vessel source audit (2026-09-13)

Before implementation the local Elite journal archive and current Cargo.json
were inspected again against Frontier's manual, sections 3.1 and 13.52:
3,047 Cargo events, exclusively Vessel=Ship (496 full, 1,564 count-only) or
Vessel=SRV (173 full, 814 count-only). The current sidecar explicitly identified
SRV and contained 12 tonnes of thortveitite. Cargo.json is one overwritten
vehicle snapshot, not a pair of inventories. Missing snapshots for the other
vehicle remain unknown. Full journal snapshots and trigger-bound checkpoints
provide separate trustworthy bases where available; transfers never invent one.

`Vessel=SRV` maps only to SRV; `Vessel=Ship` only to Ship (case-insensitive).
Unsupported or absent Vessel values invalidate the local projection. Existing
transfer rules remain: tosrv subtracts Ship/adds SRV, toship adds Ship and
subtracts SRV only in active SRV context. Carrier tracking is unchanged.

The stock filter checks positive SRV, Ship or Carrier stock independently.
Manual refresh reconstructs both local stocks and compares both for its status;
its existing verified-active-snapshot requirement and animation remain intact.

## Vehicle projection and live updates

`MiningInventoryReader` reads only identified `journal_sessions` belonging to
the requested commander and checks the file's Commander/LoadGame FID. Files are
ordered by the existing journal chronology; physical offsets identify events.
Complete Cargo events replace the prior vehicle stock. A count of zero establishes
an empty inventory. Duplicate commodity entries (including mission cargo) are
combined; total carried tonnes include stolen cargo, just as in the Cargo view.

For the last Cargo notification in the currently identified live journal, the
existing `read_cargo_snapshot` strictly validates Cargo.json's entries, vessel, exact
timestamp and total, with device/inode/size/mtime/ctime stability checks. The reader
also rejects ambiguous same-timestamp triggers and journals changed around the
sidecar read. An unmatched current snapshot remains pending; the controller makes
at most three delayed retries without a global State refresh.
Verified sidecar payloads are saved via QSettings under
`materials/mining/cargo_checkpoints/<commander_id>`, at most one per vessel.
Each is bound to its FID, resolved journal path, byte offset and event hash.
On restart a checkpoint is used only when that exact trigger is replayed.
It is never treated as a free-standing current balance. Full journal snapshots
already persist in the journal archive and require no additional storage.

MiningRefined and CollectCargo add one tonne, EjectCargo/MarketSell subtract the
event Count, and MarketBuy adds Count. Deltas only apply to a known snapshot.
Later complete Cargo snapshots always replace arithmetic projections. A count-only
notification is not another delta; a conflicting total invalidates the projection.
Invalid quantities, missing/changed files and malformed complete lines fail closed.
Other potentially cargo-changing event rules not implemented here invalidate the
affected projection until the next complete Cargo snapshot.

Ship and SRV are reconstructed and displayed separately;
LaunchSRV waits for its own snapshot, DockSRV waits for a fresh ship snapshot
because docking can automatically unload cargo. Ship changes or unproven LoadGame identities discard stale bases. A continuous
journal sequence with the same FID, ship type and ShipID preserves independent
Ship/SRV bases; a new Ship snapshot does not overwrite SRV stock. No absent baseline is inferred as zero.

CargoTransfer updates only known vehicle stocks: tocarrier subtracts from Ship;
tosrv subtracts from Ship and adds to SRV; toship adds to Ship and subtracts from
SRV when that vehicle is active. The separate CarrierLedger handles explicitly attributed carrier transfers.

`MiningInventoryController` subscribes to existing AppState change, cargo,
commander, journal-index and archive-import signals. A single-shot debounce
coalesces updates; one background worker performs file/SQL reads. A generation
check rejects obsolete results after commander changes. There is no new polling
loop and no database write or schema change.

Missing snapshots are displayed as `—`, not zero. Missing commodities within a
known full vehicle inventory are zero. Total is SRV + Ship + Carrier only when all three
are known; any unknown component makes Total unknown (`—`), never a partial
number presented as a complete balance. `MiningStock` exposes `srv_amount`,
`ship_amount`, `carrier_amount` and `total_amount`.

## Manually confirmed carrier ledger

Double-click a Carrier cell to confirm a nonnegative integer, correct it, or
explicitly reset it to unknown. Confirmation requires the existing database's
commander-owned CarrierID plus a currently identified live journal with matching
FID. The identity is checked again when accepting the dialog. Each commodity
remains independently unknown until confirmed, including a known zero.

`materials/mining/carrier/<escaped-FID>/<CarrierID>` is one QSettings value with
version, identity, commodity records, UTC confirmation timestamps and a journal
cursor (resolved filename, byte offset, SHA-256 prefix hash). No schema changes.
Balance and cursor are saved together. Ledger and cargo-checkpoint publication
checks QSettings status after sync; failures restore previous settings values on
a best-effort basis and do not publish a successful new cursor. Confirmation anchors at the current end
of complete journal events, not at an earlier UI snapshot. Corrections replace
only that commodity's baseline. Reset removes its record.

The existing event-driven controller reads the current journal in its worker.
Only CargoTransfer events after the saved cursor affect balances. Earlier events
provide docking/SRV context, never historical stock reconstruction. `tocarrier`
adds and `toship` subtracts. An explicit CarrierID/MarketID or unambiguous
FleetCarrier docking context must identify the owner's carrier. Foreign IDs and
Ship/SRV transfers are excluded. Unknown opening balances stay unknown.

Negative results and ambiguous relevant transfers invalidate the affected stock;
malformed transfers or uncertain journal continuity invalidate known records.
Truncated/replaced journals or an unverifiable indexed chain make current stock
unknown. A different live journal alone does not break continuity: verified
indexed successors are replayed from the saved prefix/offset, exactly once.
Temporary chain failures retain the old cursor and resume_count for a verified
retry; they never restore stock from the manual confirmation alone. Same-FID
Commander/LoadGame records do not erase established docking context within this
verified continuation. Positive location changes and conflicting identities do. Re-reading the same prefix,
including after restart, never reapplies consumed transfers. A missing Cargo.json
does not remove carrier balances when the live journal remains verifiable.

Tooltips distinguish manual confirmation, subsequent transfer tracking and
inconsistency. Unobserved trades, including other players' activity, cannot be
captured by this ledger; the user remains responsible for confirming corrections.
Ship/SRV refresh animation, stock filters and table settings are unchanged.

## Table settings

Columns: name, srv, ship, carrier, total, average_price, value_class. All numeric
columns and value classes are centered; resource names remain left-aligned. Unknown values sort last in both directions.
The class heading and values remain centered, with the existing colored dots.

Sort settings still use column identities, so old price/class sorts retain their
meaning. The old three-column layout is migrated by identity, preserving widths
and the relative user order; new stock columns are inserted after name.
The previous six-column layout replaces vehicle with srv and ship, copying its
width to both and preserving the other identities and relative order. A saved
vehicle sort migrates to ship; existing price/class/carrier/total sorts retain
their meaning. The existing persist_header_layout helper stores all seven widths/order. Live
inventory updates modify items in place, preserving search, filters and settings.
