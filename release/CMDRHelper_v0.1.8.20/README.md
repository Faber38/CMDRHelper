# CMDRHelper

**A personal Elite Dangerous companion for exploration, system analysis and Commander data**

CMDRHelper is an independent desktop application for **Elite Dangerous**. It evaluates the game's local Journal files and presents exploration information in a clear visual interface. Its goal is to show what is known about a system, which bodies may be interesting, and which discoveries or mappings were made by the current Commander.

The project is under active development.

## Features

### Elite Dangerous Journals
CMDRHelper reads local Elite Dangerous Journal files and processes star systems, stars, planets, moons, belt clusters, scans, mappings, biological signals and geological signals. Personal Commander data remains distinguishable from supplementary external information.

### System and Explorer views
Known bodies are presented graphically and can be selected directly. CMDRHelper can show:

- body name and type
- distance within the system
- scanned by the current Commander or only externally known
- previously discovered and mapped status
- possible first discovery and first mapping
- mapped by the current Commander
- efficient mapping
- biological and geological signals
- scan and mapping values

Bodies with BIO signals are clearly highlighted. Assignments are system-specific so BodyIDs from different systems are not mixed up.

### Body details
Selecting a body opens a detailed view. Depending on available data it can show body type, mass, distance, gravity, atmosphere, volcanism, landability, terraforming status, materials, BIO/GEO signals, scan value, mapping value and discovery status.

Missing information is shown as unknown rather than being presented as certain.

## Visual body representation

CMDRHelper includes custom artwork for many body types, including High Metal Content Worlds, Metal Rich Bodies, Rocky Bodies, Icy Bodies, Rocky Ice Worlds, Earth-like Worlds, Water Worlds, Ammonia Worlds, several gas giant classes, water-life and ammonia-life gas giants, helium-rich gas giants, several stellar classes and belt clusters.

Normal PNG files are used in overview screens. Many bodies also have a **2:1 equirectangular `_texture.png`** for the animated detail view.

### Rotating 3D planets
Matching 2:1 textures are projected onto a rotating sphere. The CPU renderer uses **PySide6 and NumPy** without an additional OpenGL/PyOpenGL dependency. Rendering includes spherical projection, slow rotation, lighting, limb darkening and an atmospheric rim.

### Animated life forms
Life-bearing gas giants use distinct animations:

**Water Life:** cyan/turquoise floating organisms with a glow and moving tails.

**Ammonia Life:** separate violet/amber translucent organisms with a pulsating core, short filaments and slower movement.

### Animated belt clusters
Belt clusters are not rendered as planets. Their detail view creates a procedural asteroid field with individual asteroids, different sizes and depths, individual rotation, independent drift, parallax, crater details and subtle dust/particle effects.

## EDSM as a supplementary source

CMDRHelper can distinguish personal Journal data from EDSM information. Sources can be shown as personal Journal, EDSM, or personal Journal + EDSM. Journal data is especially important because it reflects what the current Commander actually scanned or mapped.

## Local database

CMDRHelper uses SQLite:

- `cmdrhelper/database.py` is application code and belongs in the release.
- `data/cmdrhelper.db` contains personal Commander data and is **not** distributed.
- A fresh installation builds a new local database for the individual user.

This prevents personal Commander data from being shipped with a release.

## Platforms

CMDRHelper is developed with Python and PySide6 for **Linux and Windows**. Development is primarily performed on Linux; Windows can be set up using the supplied batch files.

## Requirements

Python 3 and the packages listed in `requirements.txt`:

```text
PySide6>=6.7,<7
numpy
```

## Linux installation

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Included Linux helper scripts may be used instead when available.

## Windows installation

Windows uses `install.bat` and `start.bat`.

`install.bat` checks for Python 3, creates `venv`, upgrades pip and installs `requirements.txt`. CMDRHelper can then be launched using `start.bat`.

## Creating a release

```bash
./create_release.sh
```

The release version is set directly in the script. The generated ZIP contains the required application code and assets but excludes the personal database, Python virtual environments and Git/cache/editor files.

## Project status

CMDRHelper is under development. The interface, data model and presentation may still change. Additional body types, Journal features, Explorer functions, data sources and calculations are planned. Linux and Windows will continue to be tested.

CMDRHelper started as a personal tool and is gradually growing into a more comprehensive Elite Dangerous companion.

## Elite Dangerous notice

CMDRHelper is an independent community/hobby project and is not an official Frontier Developments product.

**Elite Dangerous** and related names and content belong to their respective rights holders.
