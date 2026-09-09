# System overview

The additional **System overview** window uses `SystemOverviewDialog` and
`SystemOverviewView` in `cmdrhelper/ui/system_overview.py`. The former miniature
renderer has been removed from `main_window.py`. The normal Explorer/Chronicle
`SystemMapWidget` shares the visual belt projection described below. Its existing
layout algorithm, discovery/mapping values and signal displays remain unchanged.

## Entry points and data

- Explorer's existing overview button opens a snapshot of its current CMDRHelper
  body data. The dialog records the system address and commander ID.
- The opened Chronicle system window offers the same button and renderer. It uses
  the bodies already loaded through `chronicle_system_details(address, commander_id)`.
  It does not read the live journal state or request online data.
- Both windows use the existing `BodyDetailWindow` callback when a body is clicked.
  The overview copies its body dictionaries, so later live updates cannot substitute
  a different system or commander beneath an open historical view.

## Hierarchy and layout

`build_layout` reserves a rectangle for each complete subtree before placing its
neighbours. Stars and their planets form horizontal axes. Companion stars get
separate axes below their parent system. Planet satellites branch vertically;
more than four direct satellites continue in a further column. Submoons remain
within their parent's subtree. Belt clusters are grouped into one visual element
per belt and structural parent. Explicit belt/ring IDs take precedence; otherwise
the controlled Frontier suffix `A Belt Cluster 1` identifies `A Belt`. This is
only belt membership, never an inference of body ancestry. Groups occupy the
horizontal axis at their earliest reliable orbit/BodyID sort position. Their
original cluster dictionaries remain in the view snapshot and group membership.
Belt groups have no BodyID and cannot be clicked; their tooltip lists the cluster
count. Normal body clicks are unchanged.

Stored `parent_id` is authoritative; `parent_star_id` is a fallback when it is
absent. Full `Parents`/`parents` paths, when supplied, retain intermediate
barycentre/ring junctions. Missing parents are represented by junctions, not
invented named bodies. Corrupt cycles are broken deterministically. Body names
are used only for labels, never to infer ancestry.

Current database snapshots retain direct parent and host-star IDs, but do **not**
retain complete barycentre paths or semi-major axes. The overview does not invent
these missing historical data. Separate root stars therefore remain independent
unless the stored data establishes a connection. Available semi-major axes order
siblings; otherwise the stable BodyID order is used. Distance from arrival is not
an orbital radius and does not reorder moons or planets.

Existing `SystemMapWidget` image resolution, body colors, class translations and
radius sizing are reused. Images preserve their aspect ratios. Overview sizes are
bounded separately: stars 124–148 px, gas giants 78–100 px, other bodies 30–70 px,
and belt clusters 50 px. Distances are schematic, not astronomical scale.

Only short names and body classes are displayed. Full names/classes are available
in tooltips. Detailed values and signal panels stay in the existing detail view.
Dark and light palettes cover the background, connections, labels, hover and selection.

## View controls

Small systems are centered at readable native size. Larger systems start at the
upper left and have horizontal and vertical scrollbars. Ctrl + mouse wheel zooms
between 60% and 180%; **100 %** restores native size and the start of the system.
**Fit to window** can additionally reduce a large system to a complete overview.
It never enlarges a small system automatically. The shared geometry is saved under
`system_overview/geometry`; the previous overview had no stored geometry key.

## Offline regression data and images

`tests/fixtures/system_overview_saved.json` was extracted through the existing
Chronicle projection using a read-only SQLite connection to the local database:

| System | Address | Bodies | Purpose |
| --- | --- | ---: | --- |
| Blua Eaec PP-E d12-1 | 43310255979 | 3 | Small system |
| Slengie EM-A b28-0 | 712025519345 | 39 | Planets, moons and belt clusters |
| Prua Hypai VF-C d14-126 | 4340324470011 | 46 | Two stars, child planets, submoon and belts |

The fixtures retain commander ID 1 and the saved body data; no database migration
or update was performed. Tests also cover synthetic barycentres, missing parents,
cycles and 64-body layouts.

Generate native-size full-scene images and actual window screenshots for both themes:

```sh
QT_QPA_PLATFORM=offscreen venv/bin/python tools/render_system_overview.py /tmp/cmdrhelper-system-overview
```

The output contains `small`, `complex` and `binary`, each with `dark`/`light` and
`window`/`full` PNG variants. No new body assets are generated.

The belt regression fixture `tests/fixtures/system_overview_plio_aip.json` contains
**Plio Aip KN-B d13-201** (address 6917724327283), loaded read-only through the same
Chronicle projection. Its 24 saved bodies include five A Belt clusters and ten
B Belt clusters. These render as two belt elements; the five moons of planet 2
retain their recorded pre-grouping relative layout, parents and sizes.

## Shared normal-map belt projection

`cmdrhelper/belt_projection.py` contains the UI-independent parent resolution and
belt grouping used by both renderers. The normal map projects only grouped belt
leaves into its existing tree layout, retaining its BodyID sorting and existing
asteroid image. A group shows its short belt name without a cluster value panel
or a click target. Ordinary bodies retain their original objects and detail
callbacks. `SystemMapWidget.bodies` still contains every original cluster, including
when passed from Explorer or Chronicle to the additional overview. No stored data
is changed. The real regression system has 24 source bodies and 11 visual elements
in the normal map; planet 2 retains its five moons at their original relative offsets.
