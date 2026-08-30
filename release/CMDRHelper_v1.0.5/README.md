# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Your Co-Pilot for Elite Dangerous](/docs/cmdrh_en.png)

**Personal companion for Elite Dangerous -- exploration, system analysis
and Commander data at a glance**

CMDRHelper is a standalone desktop application for **Elite Dangerous**
that evaluates information from the game's local Journal files and
presents it clearly. Its goal is to provide a personal helper that,
while exploring a system, quickly shows what is already known, which
celestial bodies are interesting, and which discoveries and mappings
have been made by the Commander.

The project is still under active development.

## Feature overview

### Elite Dangerous Journals

CMDRHelper reads the local Journal files and processes, among other
things, star systems, stars, planets, moons, Belt Clusters, scans,
mappings, and biological and geological signals. The Commander's own
data remains distinguishable from supplementary external information.

### Missions

CMDRHelper evaluates mission events from the Elite Dangerous Journals
and displays active missions clearly. Mission status and associated
Journal events are tracked.

Mission offers received during gameplay through NPC messages
(`ReceiveText`) can also be detected and taken into account for further
mission assignment. Because Elite Dangerous does not provide all
information for every mission type in the same Journal event, the
assignment is built step by step from the available Journal data.

### System and Explorer view

Known bodies in a system are displayed graphically and can be selected
directly. CMDRHelper can display, among other things:

-   body name and type
-   distance within the system
-   scanned by the Commander or known only from external data
-   already discovered and mapped
-   possible first discovery and possible First Mapping
-   mapped by the Commander
-   efficient mapping
-   biological and geological signals
-   scan and mapping values

BIO signals are clearly highlighted on the affected body. Assignment is
system-specific so that BodyIDs from different star systems are not
confused.

### Body detail view

Clicking a body opens a detailed view. Depending on the available data,
it can show body type, mass, distance, gravity, atmosphere, volcanism,
landability, terraforming status, materials, BIO/GEO signals, scan
value, mapping value, and discovery status.

Missing information is shown as unknown rather than being presented as
certain data.

## Graphical body representation

CMDRHelper includes dedicated graphics for many body types, including
High Metal Content Worlds, Metal Rich Bodies, Rocky Bodies, Icy Bodies,
Rocky Ice Worlds, Earth-like Worlds, Water Worlds, Ammonia Worlds,
several gas giant classes, gas giants with water- or ammonia-based life,
helium-rich gas giants, various stellar classes, and Belt Clusters.

Normal PNG images are used in overview displays. For many bodies there
is also a **2:1 equirectangular `_texture.png`** for the animated detail
view.

### Rotating 3D planets

Suitable 2:1 textures are projected onto a rotating sphere. The CPU
renderer uses **PySide6 and NumPy** without additional OpenGL/PyOpenGL
dependencies. It includes sphere projection, slow rotation, lighting,
limb darkening, and an atmospheric rim.

### Animated life forms

Different animations are available for life-bearing gas giants:

**Water Life:** cyan/turquoise floating organisms with halos and moving
trails.

**Ammonia Life:** dedicated violet/amber semi-transparent organisms with
a pulsating core, short tendrils, and slower movement.

### Animated Belt Clusters

Belt Clusters are not rendered as spheres. The detail view generates a
procedural asteroid field with individual asteroids, different sizes and
depths, independent rotation, individual drift, parallax, craters, and
subtle dust and particle effects.

## EDSM as a supplementary data source

CMDRHelper can distinguish the Commander's own Journal data from EDSM
information. The source is identified accordingly as own Journal, EDSM,
or own Journal + EDSM. Local Journal data is especially important
because it shows what the Commander actually scanned or mapped.

CMDRHelper can automatically upload new Journal data to EDSM. The
current dynamic EDSM Discard list is respected so that only events
requested by EDSM are transmitted. Upload progress is stored safely for
each Journal file. When the feature is enabled for the first time,
existing old Journals are not uploaded again in full.

EDSM status is displayed directly at the top of the overview. A green
indicator signals successful transmission; errors are shown in red and
also recorded in the CMDRHelper log.

## Local database

CMDRHelper uses SQLite. The following rules apply:

-   `cmdrhelper/database.py` is program code and is part of the release.
-   `data/cmdrhelper.db` contains personal Commander data and is **not**
    distributed.
-   On a fresh installation, the local database is rebuilt for the
    individual user.

This prevents personal Commander data from being included in a release.

## Diagnostics and log file

CMDRHelper maintains its own rotating log file for diagnostics and
troubleshooting. Important program, Journal, database, and EDSM events
are logged. EDSM logging has been reduced so that Journal events simply
discarded by EDSM do not unnecessarily fill the normal log, while
successful transmissions, warnings, and errors remain visible.

## Platforms

CMDRHelper is developed with Python and PySide6 and is intended for
**Linux and Windows**. Development is primarily performed on Linux;
Windows can be set up using the included batch files.

## Requirements

Python 3 and the packages listed in `requirements.txt`:

``` text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

## Installation on Linux

``` bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Existing Linux start scripts can be used as an alternative.

## Installation on Windows

`install.bat` and `start.bat` are provided for Windows.

`install.bat` checks for Python 3, creates `venv`, updates pip, and
installs `requirements.txt`. CMDRHelper is then started using
`start.bat`.

## Creating a release

``` bash
./create_release.sh
```

The release version is defined directly in the script. The generated ZIP
contains program code and assets, but no personal database, virtual
Python environment, Git files, cache files, or editor files.

## Version 1.0

With **Version 1.0**, CMDRHelper reaches the first complete development
stage of its planned core scope.

Important changes and additions up to Version 1.0:

### Completed body and star representation

-   image material for supported planet, star, and special-object types
    has been further completed.
-   additional stellar classes and special star types are represented by
    dedicated graphics instead of falling back to the general default
    representation.
-   suitable bodies continue to use rotating 2:1 equirectangular
    textures in the detail view.
-   special astronomical objects can additionally be represented by
    suitable videos in the detail view.
-   neutron stars, white dwarfs, black holes, and supermassive black
    holes therefore receive a much more individual presentation.
-   external image and video material is documented with source and
    credit in the **"Image and video material / Media Credits"**
    section.

### Completed multilingual support

-   user-interface translations have been completed for the supported
    languages and aligned to a common set of translation keys.
-   all **12 interface languages** use the same complete translation-key
    set.
-   automatic translation checking verifies missing, additional, and
    duplicate keys as well as differing format placeholders.
-   German serves as the fully maintained reference for the user
    interface and further documentation.

### Changes from Version 0.9.9

### Multilingual support and translation checking

-   the user interface was converted to a central multilingual system.
-   CMDRHelper now supports **12 interface languages**: **German,
    English, French, Italian, Norwegian (Bokmål), Swedish, Finnish,
    Polish, Dutch, Spanish, Turkish, and Greek**.
-   the language can be selected and stored in Settings; language names
    are displayed in their own language in the selection field.
-   missing translations use a defined fallback order: **selected
    language → English → German → translation key**.
-   translations are stored centrally in the language files under
    `cmdrhelper/i18n/`.
-   the new developer tool `tools/check_i18n.py` automatically checks:
    -   `tr("...")` keys used by the program,
    -   missing or additional translation keys,
    -   duplicate keys,
    -   differing format placeholders such as `{system}` or `{count}`.
-   on Linux, the i18n check runs automatically at startup through
    `start.sh`. Translation problems are clearly reported but do not
    prevent the program from starting.
-   mission and Journal processing remains separated from the selected
    CMDRHelper interface language so that internal Elite Dangerous data
    does not depend on localized display text.

### Explorer and system map

-   the Parent/Child structure of the system map was revised: stars,
    planets, moons, and Belt Clusters are arranged according to their
    Journal hierarchy.
-   new **"Show all"** function with a compact miniature overview of the
    entire system.
-   bodies can be clicked in the miniature overview; the main map then
    jumps directly to the selected body.
-   improved navigation in large system maps:
    -   the mouse wheel moves the map horizontally.
    -   holding the right mouse button and dragging up/down moves the
        map vertically.
-   visual body sizes are scaled more strongly according to actual
    radius.
-   representation and marking of BIO, GEO, Terraforming, first
    discovery, and First Mapping were further improved.
-   new **value list** in Explorer: planets and moons are sorted row by
    row according to their currently estimated mapping value.
-   the value list clearly distinguishes between **First Mapping
    possible**, **already mapped**, and **mapped by the Commander**.
-   the currently achieved mapping value is specifically highlighted in
    the value list, while status and metadata are deliberately presented
    more quietly.
-   new **"Not yet sold"** display for outstanding mapping and BIO
    values across all systems since the last sale; mapping and BIO are
    reset separately.
-   outstanding Explorer values are highlighted in yellow in the main
    window so unsold data is immediately visible.

### Explorer live windows

-   new freely positionable **live windows for valuable bodies and BIO
    finds** that appear automatically during exploration.
-   position and size of the live windows are stored and reused the next
    time they appear.
-   when changing to another star system, the live windows are
    automatically closed and cleared; they appear again only when
    matching data is detected in the new system.
-   the **"Valuable bodies"** window automatically includes all planets
    and moons whose currently achievable mapping value reaches the
    threshold selected in Settings.
-   the same configurable threshold now controls the yellow highlighting
    in the value list, the valuable-bodies live window, and the **gold
    border in the system map**.
-   the **BIO live window** compactly displays bodies, detected genera
    or species, scan progress, and known Vista Genomics values during
    play.
-   BIO finds use the same color logic as the main window: gray =
    detected by DSS/FSS, white = first sample, yellow = second sample,
    green = analysis complete.
-   for partially identified BIO signals, a planet automatically expands
    and displays the individual finds in separate rows; still-unknown
    signals remain visible.
-   once all BIO species on a body have been fully analyzed, the planet
    collapses again into a compact green summary row.
-   general DSS/FSS genus names are automatically replaced by the
    concrete BIO species as soon as it is known through `ScanOrganic`.
-   known individual values are displayed directly for each BIO find;
    fully known bodies additionally show the total value.
-   the live windows use a subtle reddish-brown background so they are
    clearly distinguishable from the CMDRHelper main window while
    playing.

### BIO evaluation

-   biological data is evaluated and displayed separately from normal
    mapping values.
-   dedicated **BIO planet list** containing all bodies on which
    biological signals were detected.
-   BIO genera from `SAASignalsFound` and `FSSBodySignals` are also
    imported retrospectively from existing Journals.
-   concrete BIO species and variants from `ScanOrganic` are shown
    directly in the list.
-   scan progress for each BIO find is color-coded:
    -   gray = known only through DSS/FSS
    -   white = first sample
    -   yellow = second sample
    -   green = third sample / analysis complete
-   the known Vista Genomics base value is shown as soon as a BIO
    species is identified unambiguously.
-   display of the base value of fully analyzed BIO samples.
-   display of the possible **First Logged total value ×5**.
-   known BIO values can be supplemented from existing sales data.
-   species without a known value are identified in the evaluation.
-   BIO status distinguishes between open, visited, and fully analyzed.

### Missions

-   processing of `MissionRedirected` was improved.
-   redirected missions can inherit names, a new target system or target
    station, and information about the previous destination.
-   missions can in certain cases also be reconstructed when no complete
    `MissionAccepted` entry was previously available.
-   mission columns can be freely resized; selected widths are stored.
-   display of the **total reward of all currently open missions**.

### Images and screenshots

-   dedicated screenshot area with gallery and preview.
-   automatic conversion of new Elite Dangerous BMP screenshots.
-   output as PNG or JPG.
-   optional deletion of the BMP file after successful conversion.
-   configurable brightness correction from 0 to 50%.
-   easier use of the Elite screenshot folder under Steam/Proton.
-   the gallery is updated even after files are deleted externally.
-   improved visibility of the automatic conversion and deletion
    options.

### Online services

-   automatic EDSM Journal transmission is further integrated and
    visible through the status area in the main window.
-   status for transmission, waiting, errors, and disabled EDSM.
-   Inara status display as preparation for later automatic
    transmission.

### Operation and stability

-   interface font and font size can be selected in Settings and applied
    to the entire interface after a restart.
-   the Settings page is scrollable so all options remain accessible on
    smaller window sizes.
-   visible **"Exit"** button in the left sidebar.
-   a Single Instance lock prevents accidentally starting a second copy
    of the program at the same time.
-   safe miniature system overview without directly rendering the
    already visible Explorer widget.
-   various improvements to the interface, Journal processing, database,
    and update process.

## Project status

CMDRHelper is under development. The user interface, data model, and
visual representation may still change. Additional body types, Journal
features, Explorer features, data sources, and calculations are planned.
Linux and Windows continue to be tested.

CMDRHelper began as a personal tool and is gradually being expanded into
a more comprehensive Elite Dangerous helper.

## Image and video material / Media Credits

CMDRHelper uses visualizations from the **NASA Scientific Visualization
Studio (NASA SVS)** for selected special astronomical objects. The
respective media remain the property of their rights holders and are
credited according to the information provided on the NASA SVS pages.

### Neutron star

-   CMDRHelper file: `star_neutron.webm`
-   Source: NASA Scientific Visualization Studio, **Neutron Star
    Animations** (SVS ID 20267)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animators: Walt Feimer (KBR Wyle Services, LLC) and Lisa Poje (USRA)
-   Source: https://svs.gsfc.nasa.gov/20267/

### Black hole

-   CMDRHelper file: `black_hole.mp4` or the video extension used in the
    project
-   Source: NASA Scientific Visualization Studio, **Black Hole Accretion
    Disk Visualization** (SVS ID 13326)
-   Credit: **NASA's Goddard Space Flight Center/Jeremy Schnittman**
-   Source: https://svs.gsfc.nasa.gov/13326/

### Supermassive black hole

-   CMDRHelper file: `black_hole_supermassive.mp4` or the video
    extension used in the project
-   Source: NASA Scientific Visualization Studio (SVS ID 14576)
-   Credit: **NASA's Goddard Space Flight Center/J. Schnittman and B.
    Powell**
-   Source: https://svs.gsfc.nasa.gov/14576/

### White dwarf

-   CMDRHelper file: `star_white_dwarf.webm`
-   NASA medium used: **White Dwarf establishing shot**
    (`WDStar_4k_60fps_ProRes.webm`)
-   Source: NASA Scientific Visualization Studio, **Type Ia Supernovae
    Animations** (SVS ID 20344)
-   Credit: **NASA's Goddard Space Flight Center Conceptual Image Lab**
-   Animator: Adriana Manrique Gutierrez (USRA)
-   Producer: Scott Wiessinger (USRA)
-   Source: https://svs.gsfc.nasa.gov/20344/

The naming of these sources and credits does not imply that CMDRHelper
is supported, certified, or published by NASA. Reuse of NASA media is
subject to the respective notices and reproduction guidelines of the
original sources.

## License

CMDRHelper is free software released under the **GNU General Public
License Version 3 (GPL-3.0)**.

The source code may be used, modified, and redistributed under the terms
of GPL-3.0. Distribution of derived versions is likewise subject to the
terms of GPL-3.0.

Copyright © 2026 **Holger Mangold (Faber38)**.

The complete license terms can be found in the `LICENSE` file.

## Note on Elite Dangerous

CMDRHelper is an independent community/hobby project and is not an
official Frontier Developments product.

**Elite Dangerous** and related names and content are the property of
their respective rights holders.
