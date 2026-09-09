# Odyssey inventory view (O3)

Odyssey is the fourth category of the existing Materials page. Its four flat
subcategories use O1's Items, Components, Data and Consumables identities. There
are 61/33/123/6 catalog identities; multiple mission/ownership stacks can produce
additional rows. No grade groups or per-item capacity bars are used.

## Data and presentation

`OdysseyView` projects O1 through `odyssey_catalog.merge_inventory`. It never
adds containers or merges stacks itself. Missing quantities are `?`; the zero
filter requires O2's safely known total of zero. The locker summary sums a known
container category, including its mission stacks. Consumable capacity is omitted;
no backpack capacity is displayed without reliable suit/modification information.

Names use the O2 language resources and English fallback. Mission and Engineering
labels remain compact; tooltips give the mission ID/status and individual uses.
Special identities stay visible, with availability uncertainty retained. The
mission status never removes an inventory row. Owner and stolen distinctions are
preserved in stack keys and disclosed in tooltips/labels.

The existing search input is shared; Odyssey has independent filters. Rows use
the shared five-color delegate in visible alphabetical order, with selection,
live highlighting and hover taking priority. Engineering rendering is unchanged.

Settings are independent of personal inventory:

- `materials/category`: includes Odyssey alongside the three Engineering categories.
- `materials/odyssey/category`: last Odyssey subcategory.
- `materials/odyssey/filter`: last Odyssey filter.
- `materials/odyssey/columns`: versioned logical widths and visual order via
  `persist_header_layout`; invalid configurations restore safe defaults.

## Background lifecycle

The view and its `OdysseyController` are created on first selecting Odyssey.
One reader and one worker pool slot are reused. Refresh signals are coalesced;
SQL and journal access run outside the GUI thread. Commander/FID generations
clear the visible state immediately and discard late results from another
generation. The controller uses read-only SQLite connections and O1's attributed
journal sessions, never unassigned sidecars.

After a known baseline, a new, confirmed, exclusively positive `BackpackChange`
may highlight exactly its affected stack keys for four seconds. O1 already
deduplicates observational `CollectItems` events. Consumption, transfer, unknown
states and historical changes on first loading do not produce a pickup label.
Re-reading the same source does not restart the highlight.

## Validation on 2026-09-08

Read-only reconstruction of the 411 FABER38 sessions and UI projection confirmed:

| UTC cutoff | Locker | Backpack | Total |
|---|---:|---:|---:|
| 14:58:01 | 3131 | 8 | 3139 |
| 14:58:26, after Embark | 3139 | 0 | 3139 |

Vehicle Schematic remains quantity 1, mission 1064707191, completed. Manufacturing
Instructions 68, Weapon Test Data 34, Graphene 3, Microelectrode 113, Medkit 100 and
Energy Cell 100 are preserved. Cold reconstruction took approximately 4.2 s;
repeat reconstruction about 25 ms in this environment.

The later journal state at 16:08:45 UTC follows Disembark without a reliable new
snapshot pair: O1 correctly reports unknown. Historical screenshots must not be
interpreted as the current live state. Dark/Light examples of the safe 14:58:26
state were rendered to `/tmp/cmdrhelper-odyssey-{dark,light}-{goods,data}.png`.

31 new UI keys are present in all 12 UI languages. Item name coverage remains
O2's: en/es 223, de 221, it 217, fr 205; no/sv/fi/pl/nl/tr/el use English fallback.
All twelve help languages cover Engineering, Odyssey and the material trader search.
Positive Odyssey stock numbers use gold in both themes; Engineering stock numbers
retain the normal theme text color.
