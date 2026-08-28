# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| 🇬🇧 English

![CMDRHelper – Dein Co-Pilot für Elite Dangerous](/docs/cmdrh_engl.png)

**A personal Elite Dangerous companion for exploration, system analysis
and Commander data**

CMDRHelper is an independent desktop application for **Elite
Dangerous**. It evaluates the game's local Journal files and presents
exploration information in a clear visual interface. Its goal is to show
what is known about a system, which bodies may be interesting, and which
discoveries or mappings were made by the current Commander.

The project is under active development.

## Features

### Elite Dangerous Journals

CMDRHelper reads local Elite Dangerous Journal files and processes star
systems, stars, planets, moons, belt clusters, scans, mappings,
biological signals and geological signals. Personal Commander data
remains distinguishable from supplementary external information.

### Missions

CMDRHelper evaluates mission events from the Elite Dangerous Journals
and presents active missions in a clear overview. Mission status and
related Journal events are tracked.

Mission offers received through NPC messages (`ReceiveText`) can also be
detected and considered for subsequent mission assignment. Since Elite
Dangerous does not provide all mission information in a single Journal
event for every mission type, CMDRHelper builds the assignment
progressively from the available Journal data.

### System and Explorer views

Known bodies are presented graphically and can be selected directly.
CMDRHelper can show:

-   body name and type
-   distance within the system
-   scanned by the current Commander or only externally known
-   previously discovered and mapped status
-   possible first discovery and first mapping
-   mapped by the current Commander
-   efficient mapping
-   biological and geological signals
-   scan and mapping values

Bodies with BIO signals are clearly highlighted. Assignments are
system-specific so BodyIDs from different systems are not mixed up.

### Body details

Selecting a body opens a detailed view. Depending on available data it
can show body type, mass, distance, gravity, atmosphere, volcanism,
landability, terraforming status, materials, BIO/GEO signals, scan
value, mapping value and discovery status.

Missing information is shown as unknown rather than being presented as
certain.

## Visual body representation

CMDRHelper includes custom artwork for many body types, including High
Metal Content Worlds, Metal Rich Bodies, Rocky Bodies, Icy Bodies, Rocky
Ice Worlds, Earth-like Worlds, Water Worlds, Ammonia Worlds, several gas
giant classes, water-life and ammonia-life gas giants, helium-rich gas
giants, several stellar classes and belt clusters.

Normal PNG files are used in overview screens. Many bodies also have a
**2:1 equirectangular `_texture.png`** for the animated detail view.

### Rotating 3D planets

Matching 2:1 textures are projected onto a rotating sphere. The CPU
renderer uses **PySide6 and NumPy** without an additional
OpenGL/PyOpenGL dependency. Rendering includes spherical projection,
slow rotation, lighting, limb darkening and an atmospheric rim.

### Animated life forms

Life-bearing gas giants use distinct animations:

**Water Life:** cyan/turquoise floating organisms with a glow and moving
tails.

**Ammonia Life:** separate violet/amber translucent organisms with a
pulsating core, short filaments and slower movement.

### Animated belt clusters

Belt clusters are not rendered as planets. Their detail view creates a
procedural asteroid field with individual asteroids, different sizes and
depths, individual rotation, independent drift, parallax, crater details
and subtle dust/particle effects.

## EDSM as a supplementary source

CMDRHelper can distinguish personal Journal data from EDSM information.
Sources can be shown as personal Journal, EDSM, or personal Journal +
EDSM. Journal data is especially important because it reflects what the
current Commander actually scanned or mapped.

CMDRHelper can automatically upload new Journal data to EDSM. The
current dynamic EDSM discard list is applied so that only events
requested by EDSM are transmitted. Upload progress is safely stored per
Journal file. Existing older Journals are not fully re-uploaded when the
feature is activated for the first time.

The EDSM status is shown directly at the top of the overview. A green
indicator signals a working transmission; errors are shown in red and
are also recorded in the CMDRHelper log.

## Local database

CMDRHelper uses SQLite:

-   `cmdrhelper/database.py` is application code and belongs in the
    release.
-   `data/cmdrhelper.db` contains personal Commander data and is **not**
    distributed.
-   A fresh installation builds a new local database for the individual
    user.

This prevents personal Commander data from being shipped with a release.

## Diagnostics and log file

CMDRHelper maintains its own rotating log file for diagnostics and
troubleshooting. Important application, Journal, database and EDSM
events are recorded. EDSM logging is kept concise so that events
discarded by EDSM do not unnecessarily fill the normal log, while
successful transmissions, warnings and errors remain visible.

## Platforms

CMDRHelper is developed with Python and PySide6 for **Linux and
Windows**. Development is primarily performed on Linux; Windows can be
set up using the supplied batch files.

## Requirements

Python 3 and the packages listed in `requirements.txt`:

``` text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

## Linux installation

``` bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Included Linux helper scripts may be used instead when available.

## Windows installation

Windows uses `install.bat` and `start.bat`.

`install.bat` checks for Python 3, creates `venv`, upgrades pip and
installs `requirements.txt`. CMDRHelper can then be launched using
`start.bat`.

## Creating a release

``` bash
./create_release.sh
```

The release version is set directly in the script. The generated ZIP
contains the required application code and assets but excludes the
personal database, Python virtual environments and Git/cache/editor
files.

## Version 0.9.8

Important changes since version 0.5.5:

### Explorer and system map

-   reworked parent/child structure of the system map: stars, planets,
    moons and belt clusters are arranged according to their Journal
    hierarchy.
-   new **“Show all”** function with a compact overview of the complete
    system
-   bodies in the miniature overview can be selected and the main map
    then jumps directly to the selected body.
-   improved navigation in large system maps:
    -   the mouse wheel moves the map horizontally.
    -   holding the right mouse button and dragging up/down moves the
        map vertically.
-   visual body sizes are scaled more closely according to their actual
    radius.
-   improved presentation and marking of BIO, GEO, terraforming, first
    discovery and first mapping information.
-   new **value list** in Explorer: planets and moons are shown in rows
    sorted by their current estimated cartography value.
-   mapping status now clearly distinguishes between
    **First Mapping possible**, **already mapped** and
    **mapped by the current Commander**.
-   the currently achieved cartography value is highlighted while status
    and metadata use a calmer presentation.
-   new **“Not yet sold”** display for open cartography and BIO values
    across all systems since the last sale; cartography and BIO reset
    independently.
-   open Explorer values are highlighted in yellow in the main window so
    unsold data is immediately visible.

### Explorer live windows

-   new freely positionable **live windows for valuable bodies and BIO finds** that appear automatically during exploration.
-   live-window position and size are saved and reused the next time the window appears.
-   when entering another star system, the live windows are automatically closed and cleared; they reappear only when matching data is detected in the new system.
-   the **“Valuable bodies”** window automatically lists planets and moons whose currently achievable cartography value reaches the threshold selected in Settings.
-   the same configurable threshold now controls value-list highlighting, the valuable-bodies live window and the **gold frame in the system map**.
-   the **BIO live window** compactly shows bodies, detected genera/species, scan progress and known Vista Genomics values while playing.
-   BIO finds use the same colour logic as the main window: grey = detected by DSS/FSS, white = first sample, yellow = second sample, green = analysis complete.
-   partially identified BIO signals automatically expand a planet into individual find rows while still showing remaining unknown signals.
-   once all BIO species on a body have been fully analysed, the body collapses back into a compact green summary row.
-   generic DSS/FSS genus names are automatically replaced by the concrete BIO species once `ScanOrganic` identifies it.
-   known individual values are shown directly with each BIO find; fully known bodies additionally show their combined value.
-   the live windows use a subtle reddish-brown background so they remain visually distinct from the main CMDRHelper window while playing.

### BIO valuation

-   biological data is evaluated and displayed separately from normal
    cartography values.
-   dedicated **BIO planets list** containing all bodies with detected
    biological signals.
-   BIO genera from `SAASignalsFound` and `FSSBodySignals` are also
    reconstructed retrospectively from existing Journal files.
-   concrete BIO species and variants from `ScanOrganic` are shown
    directly in the list.
-   scan progress for each BIO find is color coded:
    -   grey = known only from DSS/FSS
    -   white = first sample
    -   yellow = second sample
    -   green = third sample / analysis complete
-   the known Vista Genomics base value is shown as soon as a BIO species
    has been identified.
-   display of the base value of fully analysed BIO samples
-   display of the possible **First Logged total value ×5**
-   known BIO values can be supplemented from existing sale data.
-   species without a known value are marked in the valuation.
-   BIO status distinguishes between open, visited and fully analysed.

### Missions

-   improved processing of `MissionRedirected`
-   redirected missions can inherit their name, new destination system
    or station, and information about the previous destination.
-   in certain cases missions can be reconstructed even when no
    complete `MissionAccepted` event was previously available.
-   mission columns can be freely resized and their widths are saved.
-   display of the **total reward of all currently active missions**.

### Images and screenshots

-   dedicated screenshot area with gallery and preview
-   automatic conversion of new Elite Dangerous BMP screenshots
-   PNG or JPG output
-   optional deletion of the BMP file after successful conversion
-   adjustable brightness correction from 0 to 50%
-   easier use of the Elite Dangerous screenshot folder under
    Steam/Proton
-   gallery refreshes when image files are deleted externally.
-   improved visibility of the automatic conversion and deletion
    options

### Online services

-   automatic EDSM Journal upload further integrated with status
    information in the main window
-   status display for active transmission, waiting, errors and disabled
    EDSM
-   Inara status indicator prepared for future automatic transmission

### Usability and stability

-   UI font family and font size can be selected in Settings and are applied to the complete interface after restarting CMDRHelper.
-   the Settings page is scrollable so all options remain accessible at smaller window sizes.
-   visible **“Exit”** button in the left sidebar
-   single-instance protection prevents accidentally starting CMDRHelper
    twice at the same time.
-   safe miniature system overview without directly rendering the
    already visible Explorer widget
-   various improvements to the interface, Journal processing, database
    handling and update process

## Project status

CMDRHelper is under development. The interface, data model and
presentation may still change. Additional body types, Journal features,
Explorer functions, data sources and calculations are planned. Linux and
Windows will continue to be tested.

CMDRHelper started as a personal tool and is gradually growing into a
more comprehensive Elite Dangerous companion.

## License

CMDRHelper is free software released under the **GNU General Public
License Version 3 (GPL-3.0)**.

The source code may be used, modified and redistributed under the terms
of the GPL-3.0. Distributed derivative versions are likewise subject to
the GPL-3.0 terms.

Copyright © 2026 **Holger Mangold (Faber38)**.

The complete license terms are provided in the `LICENSE` file.

## Elite Dangerous notice

CMDRHelper is an independent community/hobby project and is not an
official Frontier Developments product.

**Elite Dangerous** and related names and content belong to their
respective rights holders.
