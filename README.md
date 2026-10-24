# CMDRHelper

[🇩🇪 Deutsch](README_DE.md) \| [🇬🇧 English](README.md) \| [🇫🇷
Français](README_FR.md) \| [🇮🇹 Italiano](README_IT.md) \| [🇳🇴
Norsk](README_NO.md) \| [🇸🇪 Svenska](README_SV.md) \| [🇫🇮
Suomi](README_FI.md) \| [🇵🇱 Polski](README_PL.md) \| [🇳🇱
Nederlands](README_NL.md) \| [🇪🇸 Español](README_ES.md) \| [🇹🇷
Türkçe](README_TR.md) \| [🇬🇷 Ελληνικά](README_EL.md)

![CMDRHelper -- Your Co-Pilot for Elite Dangerous](cmdrhelper/assets/readme/cmdrhelper_readme_en.png)

**Personal companion for Elite Dangerous – exploration, navigation and commander data at a glance**

CMDRHelper is a standalone desktop application that processes the local Elite Dangerous journals and uses planetary position data from `Status.json`. It helps you identify interesting bodies, return to saved locations and review your travels and discoveries. Personal data persists across restarts and is kept separate for each commander.

## 🚀 Quick Start

Download the latest **CMDRHelper release ZIP** (`CMDRHelper_v*.zip`) from [GitHub Releases](https://github.com/Faber38/CMDRHelper/releases/latest) under **Assets** and extract the entire ZIP into its own folder.

### Windows

1. Run **`install.bat` once** in the extracted folder. It sets up the local Python environment (`venv`) and dependencies. If suitable Python is missing, it can install Python automatically through `winget` after your consent; `winget` must be available.
2. After installation, launch with **`start.bat`**. Use this file for normal starts as well.

### Linux

Python **3.10 or newer** with its matching `venv` module must already be installed. Open a terminal in the extracted folder and run once:

```bash
bash install.sh
```

The script sets up the local environment and dependencies; it does not install system packages. Then start CMDRHelper, and on subsequent launches, with **`bash start.sh`**.

### First start and updates

The Elite Dangerous journal folder is detected automatically when possible. If it is missing or incorrect, select it in **Settings**.

CMDRHelper checks for updates at startup and offers an integrated updater. Confirm an offered update in the app; it updates the program and dependencies and restarts CMDRHelper. After initial installation, normally just use `start.bat` (Windows) or `bash start.sh` (Linux). You do not need to run `install.bat` or `install.sh` manually for normal updates.

## CMDRHelper v3.9.19

- The mining column “Own selling price / t” shows the latest recorded sale by the selected commander. A newer lower price also replaces the older price.
- The sale tooltip shows date and time, station, system, quantity and price per tonne where known. Market offers and purchase prices are not treated as personal sales.
- Inventory-only mining changes do not start a price worker or rewrite unchanged price cells. MarketSell refreshes prices; switching commander immediately clears previous personal prices.
- The PP2 daily chronicle has a compact system filter with multiple selection, “All systems” and “Unknown system”. Combined with the time filter, it determines visible events and “Merits in filter”.
- The system filter resets on day or commander changes and keeps its selection when new events arrive on the same day. Detaching and docking are supported; the menu uses existing daily data without another daily SQL query.
- Database schema remains 23. Targeted tests with synthetic data and Qt offscreen cover twelve languages and dark/light mode. No full regression or native Windows validation.

## CMDRHelper v3.9.18

- Maintenance and reliability update for EDSM journal uploads; no new features.
- The top EDSM indicator and tooltip assess uploads only: green OK, yellow Waiting, red Error, grey Unknown or Off. Downloads, cache hits and connection tests do not change the colour.
- HTTP, overall and individual responses are checked together. Missing or unknown confirmations do not release a checkpoint; 500/501 do not count as confirmed storage.
- 100–103 count as registration evidence; 104/304 can complete events but cannot make the indicator green on their own. Only an unambiguously completed prefix advances the checkpoint.
- Endpoints, batch size, timeouts, retry intervals, upload order and commander/FID attribution remain unchanged. Original journals are unchanged; database schema remains 23.
- Confirmed events after a gap may be sent again. Rejected events are not skipped automatically; the indicator starts without success evidence after restart. No native Windows validation.

## CMDRHelper v3.9.17

- External Explorer system search above “CURRENT SYSTEM”: Enter or the button starts asynchronous Spansh name resolution. The existing system map shows stars, planets, moons and facilities in a separate resizable window without forced always-on-top; click a body for details.
- Spansh body data, uniquely identified local EDSM caches and chronicle data from all commanders are combined with sources and conflicts. Personal scan and mapping evidence stays attributed to its commander; external data is not treated as personal discoveries. The chronicle is read only.
- Landable planets are clearly marked. Body details show planet type, gravity, atmosphere and known materials; unverified Spansh material shares are not displayed as percentages. Spansh/EDSM do not guarantee specific Rhino mining sites or their resources.
- Completed Explorer search workers and their signal objects are released; obsolete search results are discarded. Repeated searches do not accumulate QRunnable objects.
- The PP2 daily chronicle reuses unchanged daily data and tables. New merits and later corrections update the display; day and time filters, commander switching and the detached chronicle remain supported.
- External windows show snapshots. EDSM caches without an unambiguous system identity are not merged. Database schema remains 23; notes in twelve languages. Native Windows testing is pending.

## CMDRHelper v3.9.16

- PP2 sections for the current system, activities and onboard articles can be collapsed individually: closed on first use, with their state saved thereafter. Your power and the daily chronicle remain visible.
- An unclear activity type now shows a short general tip about intercepting other CMDRs, without claiming confirmed local availability. Unambiguous activities, Ethos markers and safeguards are retained.
- Foreign controlling powers receive an existing 42 × 56 pixel portrait beside their name in the current system. Your own power receives no additional portrait.
- The four-stage control graphic for controlled systems is about 25% shorter, including captions and legend. Marker positions, red/blue shading and CP calculations remain unchanged.

## CMDRHelper v3.9.15

- More compact PP2 conflict cards for unoccupied systems: portraits, bars and spacing are about 25% smaller; text is reduced from 12 to 10 pixels to retain readability.
- With at least three participating powers and sufficient window width, the two leading powers appear on the left and all others on the right. Narrow windows and up to two powers retain a single column.
- The existing system card uses the width below action advice and onboard articles without covering them. Both conflict columns start at the same height and use less vertical space; all participants remain visible.

## CMDRHelper v3.9.14

- Reworked PP2 conflict view for unoccupied systems: larger existing power portraits, power name and control points in a responsive layout; progress sorting and existing power colors are retained.
- Conflict control points as an empirically supported approximation: CP ≈ ConflictProgress × 120000. The bar uses an assumed scale from 0 to 180000 CP, capped at 100%; missing values remain unknown.
- Dashed conflict markers at 36000 CP (20%) and 120000 CP (66.67%), with symbols and translated tooltips. The boundaries and bar scale are not confirmed official game constants; crossing a marker does not change system status.
- Your power appears separately as “No presence” when absent, without duplicate participants. Name variants of the same power are merged.
- Odyssey missions: generated detail text follows later destination changes. Explicit original destinations in MissionRedirected are stored separately for each commander; the new destination remains the navigation target. Missing locations or planets are not guessed.
- The main window saves its size, position and maximized state and restores them on restart. Invalid saved geometry falls back to a default; positions that are no longer visible are corrected.

## CMDRHelper v3.9.13

- PP2 system control: four colored areas for Unoccupied, Exploited, Fortified and Stronghold; a white triangle for system status and a yellow triangle for current cycle progress.
- Marker positions are explicitly approximate, not a confirmed Frontier calculation. The interval between markers is tinted red when white is right of yellow and blue when white is left. Reinforcement and undermining are shown as unchanged journal values in CP.
- Dedicated PP2 conflict view for unoccupied systems: powers sorted by conflict progress, with relative bars and existing portraits. Confirmed colors for Aisling Duval and Nakato Kaine, otherwise neutral styling; missing values remain unknown and absolute conflict CP are unavailable.
- All twelve existing power portraits are used; A. Lavigny-Duval maps to Arissa Lavigny-Duval. Existing fallback displays are preserved.
- Missions: sort all seven columns in ascending or descending order, rewards numerically and deadlines chronologically; sorting is saved through QSettings.
- Mission details stay linked to the correct mission after sorting and refreshing; switching commanders clears the previous selection. New PP2 text is available in all twelve languages.

## CMDRHelper v3.9.12

- Explorer auxiliary windows: reliable refresh and value sorting in all twelve languages.
- Detach and reattach the PP2 event chronicle: freely resizable window with saved size and position; filters are retained. Single-line merit total for the displayed daily events and selected time filter, including unassigned credits.
- Control live commander following directly in the overview; synchronized with the CMDR view and saved across restarts. A yellow hint explains disabled automatic selection in manual commander mode; it blinks for ten seconds, then remains visible.
- Favorites: copy system names using the copy icon without selecting or navigating; a green check mark confirms copying for two seconds.
- Long active journals: reuse verified processing results, avoid duplicate state reconstruction and reduce UI pauses.
- Startup progress window restored: one display for enabled journal sources and correct error reporting when initial import fails.

## CMDRHelper v3.9.11

- Windows: automatically follow a confirmed match between the Elite process, current journal and commander FID; preserve automatic following for legacy settings.
- Trade assistant: recommendations use the selected journal source’s market observer, without carrying station context across sources.
- PP2 chronicle: single-line details separated by “ | ”, with ellipsis when space is limited and complete tooltips.
- Modeless auxiliary windows stay on top; the main window and modal dialogs remain unchanged.

## CMDRHelper v3.9.10

- Journal directories: manage multiple sources with Steam/Heroic discovery, editing, monitoring checkboxes and separate statistics.
- Commanders: FID-verified attribution, saved selection and optional automatic following of an unambiguously identified game instance on Linux.
- Powerplay 2.0: optional time filter, compact transport rows and improved ship-scan matching for +1 to +100 merits and new complete scans of previously seen targets.
- Auxiliary windows stay independently open when the main window is minimized and close when the helper exits.
- EDSM and Inara: separate EDSM send/receive switches, source-specific upload positions, reliable acknowledgements and improved retry handling.
- More reliable journal processing with transactional read positions and identity checks; privacy-conscious Odyssey display diagnostics in the diagnostic package.

## CMDRHelper v3.9.9

- Detach planet navigation into a separate window and reattach it with the same target and live data.
- Open favorite images at original resolution, zoom with the mouse wheel and drag to pan.
- Favorite titles appear in Elite yellow (#FFCC33), preserving selection highlighting and other text lines.
- Export all or selected favorites with images and coordinates in the existing compatible ZIP/JSON format.
- Clearer navigation with a compass symbol and “To planet navigation”.

## CMDRHelper v3.9.8

- Favorites and planet navigation are integrated directly into the main interface as two tabs.
- Navigation opens a shared main page without additional favorites or navigator windows.
- When no hotkey is configured, the quick-favorite hint appears in Elite yellow, gently blinks three times and explains setup under Settings.
- The integrated help describes the new tabs and navigation paths in all twelve languages.

## CMDRHelper v3.9.6.7

- Improved Powerplay merit matching for ship scans and commodity sales.
- Ship scans support +5 and +10 merits; ordinary commodity sales can receive multiple credits within four seconds (≈). Competing or ambiguous events remain unresolved (?).
- Cargo displays remain visible while enabled, without inactivity hiding; cargo and limpet values update without reopening the displays.
- New expandable Navigation main menu with Favorites and Planet navigation, replacing the former Explorer buttons.
- Integrated help documents the new menu paths in all twelve supported languages.

## CMDRHelper v3.9.6.6

- Improved Powerplay merit matching for consecutive commodity sales.

## CMDRHelper v3.9.6.5

- More robust Windows startup: Noncritical background failures are reported as partial failures while the main window remains usable.
- Bounded retries for landing pad data and journal catch-up, improved cartography repair, and safer journal indexing and shutdown.
- More informative technical error categories in diagnostics while personal data remains anonymized.
- Calmer cargo displays during mining by reusing windows and table rows; automatic hiding only 15 seconds after the last inventory change.
- Consistent localized commodity names without changing inventory calculations or the separate limpet display.
- PP2 daily chronicle: Ordinary commodity sales can also be conservatively linked to merit credits (≈); ambiguous cases remain ?, with total merits and rank calculations unchanged.

## CMDRHelper v3.9.5

- New Odyssey ratings: 192 of 223 items are rated A–D; 31 remain marked ? pending verification.
- Colored rating column with tooltips and saved A–D or D–A sorting; personal cleanup markings remain independent.
- Corrected Fleet Carrier routes: total confirmed capacity usage is sent to Spansh, with tank and stored tritium kept separate.
- CarrierStats imports capacity and tank data with identity, session and freshness checks; stored tritium still requires manual input.
- Clearer carrier input guidance, highlighted invalid fields and three orange flashes for missing confirmation, in both themes and twelve languages.
- Additional safeguards against stale carrier confirmations and delayed route results after context changes; CTSVision export remains compatible.

## CMDRHelper v3.9.4

- Improved ship route planner with 7A SCO FSD support and correct use of engineering, Guardian boosters, cargo and reserve fuel.
- New ship data assistant explains, supplements and saves missing values per ship; confirmed automatic data takes priority.
- More precise temporal matching of Powerplay deliveries to merit messages within three seconds when the context is unambiguous.
- Mining, Odyssey, material and fleet views avoid unnecessary rebuilding and reuse existing display elements.
- New Odyssey cleanup helper with 81 default candidates, a personal selection from 223 items, color highlighting and saved sorting.
- Improved input validation, error messages and loading feedback, with updated text in all twelve languages.

## CMDRHelper v3.9.3

- Three new station images, improved type mapping and corrected planetary station flags.
- Confirmed Interstellar Factors are shown in turquoise beside the station name.
- The image gallery loads in the background with a holographic loading scanner and protection against repeated clicks.
- Powerplay rank progress is shown in green or orange; merit priority and persistence have been corrected.
- Merit credits can be temporally associated with rare goods sales within two seconds when the context is unambiguous.
- Updated Nakato Kaine portrait and revised text in all twelve languages.

## CMDRHelper v3.9.2

- New nearby search for rare goods, with destinations saved to the trade shortlist.
- Improved material inventory display when game data conflicts.
- Expanded and clarified Powerplay 2.0 help.
- Extensive translation improvements.
- Further stability improvements.

## CMDRHelper v3.9.1

- Powerplay activities now show the Ethos activities marked by Elite.
- Powerplay help updated accordingly.
- Added acknowledgements for supporting commanders and the EOT player group.
- Minor improvements and fixes.

## CMDRHelper v3.9.0

- Rare goods integrated into the trade assistant.
- Origin stations for rare goods are recognized and automatically looked up when needed.
- Improved cargo detection with direct selection of carried goods for selling searches.
- Search for suitable selling stations for several carried commodities at once.
- Significantly expanded Powerplay 2.0 help.
- Further stability and reliability improvements.

## CMDRHelper v3.8.3

- Fixed an issue that stopped new local market data from updating after accepting certain missions.
- Improved the stability of local market monitoring.

## CMDRHelper v3.8.2

- Bug fixes and improvements to the trade assistant.
- More reliable detection of cargo holds, stations and local markets.
- Improved landing pad information and station display.
- Faster processing of station and landing pad data.
- Small improvements to usability and status indicators.

## CMDRHelper v3.8.0

- New “Sell here” trade tab: Find low-cost sources for goods you can sell profitably at the current market.
- Make better use of both legs: From a bookmarked supply station entry, find goods for the outbound trip, then buy the planned commodity there for the return trip.
- More source details: View supply and demand separately, with known planetary bodies shown for surface stations.
- Local-only trade searches now also cover buying and selling, with better use of known landing pad sizes.
- More reliable cargo detection: Confirmed quantities remain valid while their context stays valid and unchanged; ship, SRV and on-foot modes are better distinguished.
- Keep the station market recognized after boarding: Returning to your own ship no longer requires docking again.

## CMDRHelper v3.7.8

- Bug fixes in the trade assistant.
- Improved cargo space detection and updates.
- Fixed material inventory issues at capacity limits.
- General stability and reliability improvements.

## Internal version 3.7.5

Internal build for testing during gameplay; not published.

- Explorer: EDSM status and star-class normalization, retained completion of missing bodies, first footfall across sessions with corrected merging, automatic value-list width and linear layout. Copy icon for recent systems; updated help, translations and tests.
- [Detailed notes (German)](docs/release-3.7.5.md)

## New in version 3.7.0

- New Trade section: selling and buying combine your observed markets with Spansh offers. Matching local results remain usable, marked incomplete, if the community search fails.
- Opening an Elite commodity market automatically records the station market. Your observations survive restarts, remain valid for strictly less than 24 hours and replace older offers from the same market.
- Recommendations use your current observed buying market, free ship cargo space, supply and demand. Minimum margin, possible quantity and potential profit help you choose; optionally use only your own destination markets.
- Trade includes progress, copyable diagnostics and market status. A remembered trade flight keeps the commodity and destination; copy the destination system name.
- The full system overview can fit the window once when opened. The option is enabled by default and remembered; manual zoom remains available.
- In-app help reviewed and expanded across twelve topics and twelve languages, with translation and large-font improvements. Mining carrier stock is preserved across short shutdown journals.

## New in version 3.6.2

- Combat bonds in “Missions & Rewards”, with faction balances, a total and a local reset.
- Live combat bonds persist per commander across Helper restarts; verified journal anchors prevent duplicate counting.
- Bounties, combat bonds and Odyssey processing share live journal reads with independent acknowledgements.
- An unambiguous combat-bond redemption clears the observed balance of the named faction; old holdings and the redemption amount do not affect other factions.
- Death removes observed unredeemed combat bonds; resurrection and SRV loss cause no additional reset.
- Bounties and combat bonds remain separate. Capture gaps and storage errors are shown clearly.

## New in version 3.6.1

- Live bounties under Missions, stored persistently and separately for each commander.
- Encounter and messenger jobs from space encounters are visible before the final MissionID is available.
- Encounter offers survive restarts and become normal missions after unambiguous confirmation, without duplicates.
- Improved matching of commodity, quantity, destination, reward and time; ambiguous offers are not guessed. Unconfirmed offers expire after 24 hours.
- Commander → Missions shows current missions. New completions no longer build a growing mission archive; existing historical rows are preserved.
- Encounter processing is fully connected again; old events cannot overwrite newer mission state. Removed the conflicting mission reset.

## New in version 3.6

- Stations and facilities on the system map, plus a dedicated STATIONS tab with search, filters and sorting.
- Station images, an image viewer and details of known services, landing pads, sources and timestamps.
- Optional Spansh station information in Settings → Online Services, disabled by default. After a successful fetch, further manual fetches are blocked for the same local day. Without Spansh, the stations tab explains the limits of journal knowledge.
- Personal ship and carrier images, type/default images and an image viewer. Remove ships from the fleet or restore them with “Reread all ships”; sold ships are recognised more reliably.
- Improved system map, value list with coloured mapping status, Cargo HUD and navigation. Lower background load on Linux and for screenshots, the gallery and Explorer.
- Fixed: harmless short Elite journals no longer interrupt Mining carrier balances. Unknown or uncertain data remains clearly identified.

## New in version 3.5

- Faster Chronicle and interface; BIO/cartography processing runs in the background.
- Odyssey shows locker, backpack, personal category occupancy and projected carrier stock.
- Carrier setup via ! clearly distinguishes confirmed 0 from unknown —.
- Carrier stock is displayed separately from storage reserved by bartender buy orders.
- More reliable Mining stock with safer Cargo snapshots, transfer catch-up and checked persistence.
- Fixed fresh-install migration prompts; improved Chronicle copy feedback and hidden-view updates.

Locker and backpack use validated current ShipLocker/Backpack data. Goods, Assets and Data each show personal locker occupancy with their own capacity of 1000. Total includes locker + backpack + carrier only when the required balances are known and coherent. Purchases, sales and trades are distinguished from private transfers. After restart, location is reconstructed and a new personal baseline is set; missed Odyssey transfers are not invented. Illustrative example: 500 existing units + 100 spaces reserved for buy orders = 600 / 1000 occupied. The 100 are not material stock. Stale or uncertain market data never produces a supposed current occupancy.

### Set up carrier stock

CMDRHelper can automatically maintain your Fleet Carrier’s private Odyssey stock. It first needs a confirmed starting balance.

On your own Fleet Carrier, open inventory transfer and compare Goods, Assets and Data in turn.

Double-click the Carrier column in CMDRHelper and enter the current carrier quantity for EVERY position. Explicitly confirm ALL empty positions as 0 too.

— = not yet confirmed / unknown
0 = explicitly confirmed empty stock

After completing setup, CMDRHelper tracks transfers between your personal locker and carrier automatically while you are clearly on your own carrier. Personal changes elsewhere do not change carrier stock.

Double-click a Carrier cell at any time to correct or confirm it again.

Open buy orders at the carrier bartender also reserve storage space. In-game occupancy can therefore exceed the sum of existing materials. Bartender activity, especially by other players, can change actual stock. Check and reconfirm the projected balance when needed.

Mining keeps Ship, SRV and Carrier separate. Explicit CargoTransfer events are caught up exactly once across verified journal boundaries; Cargo.json and saved checkpoints receive stricter validation. This is not Odyssey delta tracking. Other players’ trades may require manual reconfirmation. New databases receive the Parent-Hierarchy completion marker after successful initialization, avoiding a false historical migration after first import. Old unmarked databases still require migration, with Elite closed for that historical repair. Chronicle names can be copied with ⧉ and a brief ✓ confirmation. Mission data is loaded more selectively and hidden views avoid unnecessary rebuilds.

## New in version 3.4.6

- More reliable archive imports with large journal collections.
- A more responsive interface during lengthy data processing.
- Improved catch-up of new and expanded journals after imports.
- Faster archive processing and mining refreshes.
- Click the system name in an open Chronicle system view to copy it.
- Fixed tab rendering on Windows in dark mode.

## New in version 3.4.5

- More reliable archive imports with large journal collections.
- A more responsive interface during lengthy data processing.
- Improved catch-up of new and expanded journals after imports.
- Faster archive processing and mining refreshes.
- Click the system name in an open Chronicle system view to copy it.
- Further performance and stability improvements.
- Fixed tab rendering on Windows in dark mode.

## New in version 3.4.4 – Hotfix

- Fixed errors with very large mission IDs so missions are saved reliably.
- After a save failure, journal processing retries with increasing delays without skipping entries.
- Improved startup when no active commander has been detected yet.
- More useful technical diagnostics for these errors without logging actual mission IDs.

## New in version 3.4.3

- Expanded favorites: distance filter and portable ZIP export/import including images.
- Sort Explorer tables and save sorting and column widths separately for each table.
- Mining shows SRV, ship, carrier and total separately; “In stock only” considers all three storage locations.
- Diagnostic packages and privacy-conscious rotating logs for support, with no automatic upload.
- Safe database upgrades directly from older versions; migration backups are retained throughout the release that created them.
- Improved usability, updated help and clearly clickable points on the Chronicle map.

The distance filter starts off (default 500 ly), uses local system coordinates and updates when the system changes. Favorites exports contain favorites.json and available images; duplicates can be skipped, replaced or imported as new entries. The value list and BIO/GEO/MINING tables support natural, numeric and semantic sorting. Installing 3.4.1 first is not required.

## New in version 3.4.1

- Corrects older stored system hierarchies
- Improved display of planets, moons and multiple-star systems
- Safe database update with automatic backup and rollback on errors
- Elite journal files remain unchanged
- Further stability and display improvements

The database update corrects older stored relationships between stars, planets and moons. Journals are only read. Close Elite Dangerous first and make historical journals available where possible. The entire CMDRHelper database is backed up beforehand; errors roll back changes and the backup is restored if necessary. The backup is retained as a safety copy. Cancel lets you postpone the update.

## New in version 3.4 – Mining and inventory

- New Mining area with commodities, reference prices and value classes.
- Ship/SRV stock and manually confirmed carrier stock with automatic transfer tracking.
- Combined search and filters for planetary surface and asteroid/ring mining.
- ABBAU ×N opens the matching Mining overview directly.
- Correct cartography values across session changes.
- Improved help, table styling and usability.

One shared table contains 57 mining commodities with Surface, Asteroid or Both origins. Known reference prices and derived value classes remain fixed guidance values, not live market data.

Verified ship/SRV cargo; double-click to confirm, correct or reset carrier stock to unknown. Only unambiguous CargoTransfer events to/from your own carrier are tracked from a confirmed starting stock. Totals appear only when both amounts are known; unknown remains —.

Combine the in-stock, value-class and origin filters; their states, sorting and column widths are saved. ABBAU ×N automatically selects planetary surface mining. Manual cargo refresh includes status animation and preserves carrier values.

Refined Mining table styling, carrier tooltips and version-independent integrated Mining help. Hand cursors on existing interactive system-map bodies and controls. The A-6-a placeholder fix preserves correct cartography values across sessions.

## New in version 3.3.1 – Bug fixes

- Completed DSS mappings are now reliably detected live.
- Mapping is retained even when the corresponding scan appears later in the current journal.
- Your mapping status, mapping time and probe efficiency are reliably saved.
- Archive imports no longer replace existing scan and mapping values with invalid zeros.
- Affected bodies with complete body data regain correct displayed values when loaded or refreshed.
- Live mapping estimates now include the correct bonuses and truncate fractions of a credit only at the end.
- Sales-based adjustment factors no longer alter regular exploration values.
- Additional regression tests cover mapping across sessions and persistence of mapping data.

## New in version 3.3

- New system analysis based on your personal exploration experience.
- Open / Solo / Private Group game mode directly in the overview.
- Copy system names from Recent systems with one click.
- Clearer historical data and easier-to-understand analysis.
- More reliable journal archive imports when journal files grow later.

The former Jump tip is now Analysis, with System analysis and the existing Historical data. System analysis compares a target with your personal history: the mass code provides the baseline, while region and family refine it cautiously. Potential index 100 represents your personal historical average of damped exploration potential, not a percentage probability. Data basis and evidence strength remain separate from the rating; the final number has no score effect and BIO is currently informational only.

## New in v3.2 compared with v3.1

- Engineering material management: All 146 materials in Raw, Manufactured and Encoded, with grades, capacities and special cases. Commander-specific live stock, search, filters, five subtle row backgrounds and saved column widths/order make browsing easier. Unknown stock remains distinct from zero.

- Odyssey inventory: The fourth material tab contains 223 catalog identities for goods, components, data and consumables. Ship Locker, Backpack and reliable totals remain separate; mission stacks, mission status and engineering uses are visible. Positive stock numbers appear in gold. Missing name translations fall back to English.

- Material trader search (Find trader → Open route planner): On request, Spansh searches Raw, Manufactured and Encoded separately from the current commander system. Carriers are excluded and station details checked. Distance in ly is the direct system distance; community data cannot guarantee access. Sending a result to the route planner only sets the destination system and does not start a route. There is no Odyssey trader search.

- System overview: The new Elite-style view replaces the previous miniature overview and is available in Explorer and Chronicle. Stars and planets form the main structure, with moons branching below; multiple-star systems remain readable. Zoom, scrolling, fit to window and body clicks provide access to details.

- Compact asteroid belts: Belt clusters are grouped into clear belts in the overview and regular Explorer/Chronicle system maps. All individual cluster data is retained.

- Cartography corrected: A later scan after DSS mapping no longer resets unsold exploration values, mapping time or efficiency. Existing incorrect claims are repaired at startup from available journals with clear commander attribution. Missing sources leave the repair pending; deleting the database is unnecessary.

- Improved route planner: The current system follows your location automatically until you enter a manual start; clearing the start field restores automatic tracking. Ships and carriers use exactly validated ID64 system addresses instead of similar names. “Unable to find route” is explained as no route found; check destinations, range and route settings.

- Better update information: The Yes/No window shows installed and available versions plus up to six highlights when a summary is available. Long lists scroll while actions remain accessible. This display ships with v3.2; an unchanged v3.1 client does not show it yet.

## v3.1 (v3.0.3 → v3.1)

- BIO progress is compact: 1/3 yellow, 2/3 blue and 3/3 green; the completed state “Done” is also green. Under “auto show”, GEO has its own saved switch: BIO alone, GEO alone or both together are supported. Manually adjusted column widths in the shared Explorer BIO / GEO / ABBAU table survive reopening and application restarts. Saved popup column widths are restored more robustly; invalid values fall back to safe defaults.

- Discovery and mapping are separate and refer to your scan time: “Already discovered at your scan” and “Already mapped at your scan”. Missing information remains Unknown. First Discovery and First Mapping candidates refer only to scan time; historical No values do not prove that a body is still undiscovered or unmapped today. Your own mapping does not confirm an official first claim. Being known to EDSM remains separate.

- “EDSM status HUD” under “auto show” is OFF by default. After entering a system, a brief message appears over Elite for about 2.5 seconds. “EDSM: KNOWN” means a valid EDSM match for the system. “EDSM: UNKNOWN” means a valid EDSM response without a system match. “EDSM: NO RESPONSE” means a network, HTTP or timeout error, or an invalid response, never a confirmed absence of a match. Being known to EDSM is not the same as official discovery in Elite; no first discoverer or first reporter names are promised. The message works independently of the navigation and cargo HUDs.

- Visit history includes Location, FSDJump and CarrierJump during live journal updates. Multiple location events during one uninterrupted stay count as one visit: A → A → A counts once. A genuine return is preserved: A → B → C → A counts as four visits.

- Completing your own DSS mapping now reliably saves the mapping time, probes used and efficiency target. Later scan events no longer cause existing details to be lost.

- The cargo window automatically adjusts its height to its contents. With many entries, height is capped and the table scrolls; your chosen width and window position are preserved. The existing “Cargo HUD” switch is now under “auto show”, with no additional switch in the cargo window.

- For existing installations, the usual steps are simply: install the update → start CMDRHelper. Necessary historical corrections to BIO data, visit history and DSS metadata run automatically; a database backup is created before data repairs write changes. Repairs are versioned and idempotent: successful revisions are not fully rerun at every start. Reconstruction requires Elite journals that still exist, are readable and can be unambiguously assigned to a commander. Missing sources are not invented or treated as success; pending repairs are retried at the next start. Database deletion, manual scripts and reimport are normally unnecessary.

## Explorer

The Explorer presents the current system in three views:

- **System map:** a graphical display of known stars, planets and moons. Click a body to open its details. “Show all” opens the system overview.
- **Value list:** The value list shows estimates based on the stored scan state, not guaranteed outstanding payouts. First bonuses remain unconfirmed. Tooltips in the map and list and the body details use the same time-qualified states.
- **BIO / GEO / ABBAU:** biological and geological signals, planetary mining sites and confirmed personal finds.

The analysis distinguishes reported signals from actual personal finds. **BIO ×N** is the reported signal count, not confirmation of fully analysed species. **MINING ×N** counts planetary mining sites without revealing their individual commodity contents. Personally mined commodities, secondary materials collected while mining and a body's general material composition remain separate.

The Explorer also shows estimated BIO values, progress of personal analyses and unsold cartographic and BIO data. Values are based on available journal and body information; missing data is not presented as personal discoveries. Additional EDSM data must be distinguished from personal finds as external information.

Body details include available physical properties, atmosphere, rings, materials and discovery information. Body displays use suitable textures and animations for certain special astronomical objects. The Cargo area shows the known load and capacity of the currently used ship or SRV; for the Rhino, cargo and personal mining finds remain different figures.

Select “Navigation” on the left. The “★ Favorites” and “Planet navigation” tabs appear on the right, with “★ Favorites” selected by default. “Navigation → ★ Favorites” manages systems, planets/moons and surface locations for the active commander; “Navigation → Planet navigation” displays planetary navigation in the same main area.

## Planetary navigation

The planetary navigator exclusively helps you fly to a specific **latitude/longitude on a planet or moon**. A separate route planner is available for travel between star systems.

### Enter a target and fly

Select the target body or use the current body, detected automatically where possible. Enter latitude and longitude and, optionally, a target name. You do not need to enter technical details such as BodyID or SystemAddress. **0.0** is also a valid coordinate.

As soon as Elite provides valid planetary position data for the matching body, the compass activates automatically. Without matching data, the navigator displays a waiting state. You can set a new coordinate target on the same body at any time; it replaces the previous target.

### Display during approach

| Target distance | Display |
| --- | --- |
| **More than 380 km** | Planetary globe with your position as a white circle and the target as a small dot. The target is orange on the visible side and red on the hidden far side. The player's position stays fixed in the display; planet and target are shown relative to it. |
| **Up to and including 380 km** | Automatic switch to a tilted perspective grid with **50-km distance spacing** and the target position plotted within it for the continued approach. |

The globe and perspective grid scale proportionally to the available space. In a narrow or short main window, scroll to reach the contents. Switching pages or tabs preserves filters and the navigation target.

### Understanding navigation values

- **Target coordinates:** the target's saved latitude and longitude.
- **Current coordinates:** your most recent valid planetary position.
- **Target distance / Surface distance:** the calculated distance to the target over the spherical surface; the large target distance and detailed value show the same distance with different rounding.
- **Bearing:** the absolute direction from your current position to the target.
- **Heading:** your current orientation as reported by Elite.
- **Relative direction:** the difference between heading and bearing, such as “23° right”, “left” or “straight ahead”.
- **Target course:** the absolute course you can turn to in the Elite HUD. It equals the bearing and is not an additional relative turn angle.

Example: **Heading 051° → Target course 074° = 23° right**.

Navigation depends on the game's status data; updates may arrive with a delay depending on the game state. Surface distance is not a terrain or road route. Obstacles and terrain elevations along the route are not considered.

## Navigation HUD

On the left, under **auto show → Navigation HUD**, you can enable an optional additional display directly over Elite. During valid planetary navigation, it shows:

- relative direction,
- absolute target course,
- distance.

The HUD is transparent, click-through and focus-neutral: it takes neither your mouse clicks nor input focus away from the game. Without valid navigation, it automatically becomes invisible; the sidebar checkbox may remain enabled. The normal navigator works independently of the HUD.

The HUD has been tested in-game under **Linux/X11** and **Windows 11 with Elite**. On Windows, multiple monitors are matched using their geometry and the position of the Elite window, not matching monitor names.

## Favorites

Select “Navigation” on the left. The “★ Favorites” and “Planet navigation” tabs appear on the right, with “★ Favorites” selected by default. “Navigation → ★ Favorites” manages systems, planets/moons and surface locations for the active commander; “Navigation → Planet navigation” displays planetary navigation in the same main area. Favorites belong to the **active commander**. Switching commanders updates the view; the commander selection in the chronicle does not extend the favorites list.

### Save three types

The top action row offers:

| Action | Saved favorite |
| --- | --- |
| **★ Save current system** | The current system, without surface coordinates. |
| **★ Save planet / moon** | A selected known planet or moon in the current system, without surface coordinates. |
| **★ Save current location** | A surface location with the current system, body, latitude and longitude. |

The location button always remains visible and is available only with valid current planetary position data and an active commander. **Clicking freezes the commander, system, body and coordinates before the edit dialog appears.** Subsequent movement in the game does not change this position. The same save workflow is also available in the planetary navigator. Known internal IDs are carried over automatically; no coordinates are invented.

Choose a name and exactly one category: **Bio, Geo, Mining, View, Landing site, Interesting or Other**. A note and an image are optional.

### Find, view and edit

The scrollable list, sorted alphabetically by name, shows name, type, system, body and coordinates where applicable, category and a small image preview. **Free-text search, type and category filters** can be combined. The search covers name, system, body and note.

**Open / View** shows saved information, the note and a larger image preview. **Show in Explorer** uses the existing system overview or body detail view if the favorite belongs to the current Explorer system and matching data is available. For other systems, the saved favorite information remains available.

**Edit** changes name, category, note and image. System, body and saved coordinates are not replaced by live values. For a different position, create a new surface favorite.

**Delete** requires confirmation and removes only the favorite record and its internal image copy. Explorer, journal and body data are preserved.

### Favorite images and latest screenshot

Favorite images are **completely separate from the normal Images area**. CMDRHelper manages its own internal copy in the favorite image folder (`data/favorites/images/` in the standard data layout). The original is neither moved nor modified.

- **Choose image …** accepts PNG, JPEG or WebP and shows a preview. The internal copy is created only when saving.
- **Use latest screenshot** freshly scans the actual screenshot source folder on every click. It also considers matching converted Elite screenshots in the active commander's folder within the configured conversion destination. A new screenshot therefore remains available if automatic conversion has already deleted its BMP.
- Readable files with matching Elite or conversion names are offered, not arbitrary images from general image folders. Ordering uses an unambiguous capture time in the filename, otherwise the file time. For converted images, the capture time saved in the name is used, not the conversion time.
- Before accepting a found screenshot, you see its filename, capture time and a freshly loaded preview. Confirm with **Use this image**. If no suitable screenshot is found, manual image selection remains available. CMDRHelper does not trigger screenshots itself.

An image can later be replaced or removed. Internal copies no longer needed are removed when saving or deleting the favorite. **Favorite actions never delete the original screenshot or a selected original image.** If an internal image file is missing, the favorite remains usable without a preview.

### Surface favorite as a target

**▶ Go to target** passes the saved body, latitude, longitude and favorite name to the existing planetary navigator and replaces its previous target. Favorites have no navigation logic of their own. Matching valid planetary data starts navigation; otherwise the navigator waits as usual.

Other commanders' favorites cannot be used as your own targets. Switching commanders stops a target still managed as the previous commander's favorite target. System and body favorites display existing information; they do not provide their own route planning.

## Chronicle

The chronicle is your saved travel and discovery history. Its **3D travel map** shows visited systems and commander routes. System and body details help you find known BIO, GEO, material, Codex and mining information again.

### Combined filters

**Apply** or **Enter in the free-text field** runs all configured filters together:

- free text,
- optional **From** and **To**,
- **Planetary mining sites** and **At least**,
- **My mining finds** and **Commodity**.

A term from **Search help / Legend** is entered into the search field and executed together with the already configured period and mining filters.

### Period in UTC

From and To are each enabled with their checkbox. A single bound is also possible; without an enabled checkbox, there is no time restriction on that side. **From** includes the beginning of the selected UTC calendar day. **To** includes the entire selected UTC day. UTC is the shared time basis, not your local calendar time.

**Actual system visits** are decisive: at least one saved visit must fall within the period. A system merely becoming known for the first or last time does not replace a visit. With an active period, visit count, first visit and last visit in the map view refer to the filtered visits.

The period filters visits, not individual discovery, BIO, GEO or mining events. Known discovery information and personal mining quantities remain saved **totals**. **“Copper 56 t” with an active period does not automatically mean “56 t during this period”.** If From is later than To, an error message appears; no database query starts.

### Commander and refresh

The **map's commander selection** determines the displayed commander routes. Personal free-text and mining searches, however, refer to the viewed or active commander. Map checkboxes do not automatically extend personal searches to multiple commanders.

**Refresh Chronicle** reloads the data and reruns the active filters. **Current position** first applies the current filter state and centres on the current system only if it is included in the resulting map. Otherwise, a message appears; the filters remain active.

**Reset** clears free text, disables From/To and resets their visible date fields. Mining checkboxes are cleared, the minimum count becomes 0 and the commodity becomes All. Commander selection is preserved; the normal chronicle is then loaded.

With **no matches**, the map and routes are cleared, the results list is cleared and hidden, the detail display is reset and any open chronicle system detail window is closed. Old results do not remain visible.

### Map controls

- Drag with the left mouse button: rotate.
- Drag with the right mouse button: pan.
- Drag with the middle mouse button: draw a zoom rectangle.
- Mouse wheel: zoom.
- **Align:** reset orientation to the galactic top view; pan and zoom are preserved.

## Images and automatic screenshot conversion

In the **Images** area, configure the Elite screenshot source folder and conversion destination. Automatic conversion processes newly arriving BMP screenshots into **PNG or JPEG**. Adjustable brightening is available. BMPs already present at startup are not automatically converted retroactively simply by enabling monitoring; manual conversion is available for them.

Converted filenames include capture time, commander and system information, and files are stored by commander. Automatic assignment follows the active journal commander. A different gallery selection does not change this active commander.

The option to **delete the original BMP after successful conversion** belongs exclusively to this conversion and has its own setting. It is independent of favorite image management.

The gallery shows the matching converted images with previews. It is freshly scanned when shown again; refreshing also considers the current files. Selection and large preview are updated together. If the selected image disappears, another existing image is selected or the preview is cleared. The Images area also has its own image selection and deletion function with confirmation.

## Other views

- **Overview:** active commander, ship, location, journal detection, open missions and online status.
- **Missions:** persistently saved open missions with known targets, progress and completion state. Missing details are not filled in or invented.
- **CMDR:** wealth, ranks, statistics, MercCoins, ships/fleet and known Fleet Carrier location. MercCoins are shown as totals reported by Frontier, not as a self-calculated balance.
- **Route planner:** separate planning for ships and Fleet Carriers using Spansh. Calculated carrier routes can be exported as CSV for CTSVision. Calculation requires a connection to the external service.

## Commander, local data and online services

CMDRHelper identifies the active commander by the Frontier ID from the current journal session. Personal exploration, missions, wealth, favorites and online credentials are stored separately. Simply viewing another commander changes neither the live commander nor their upload assignment.

The local SQLite database preserves known systems, bodies and personal history across restarts. New complete journal entries are processed during play; saved read positions avoid unnecessary rereading. If location or commander is wrong, first check journal detection and the journal folder in settings.

**EDSM** can provide additional system data. Supported journal data can be uploaded to **EDSM and Inara** when the service is configured and enabled with the active commander's own credentials. One commander does not automatically use another's API key. Local storage works independently of an available online connection.

## Languages and contextual help

The interface supports **12 languages**: **DE, EN, FR, IT, NO, SV, FI, PL, NL, ES, TR, EL** – German, English, French, Italian, Norwegian, Swedish, Finnish, Polish, Dutch, Spanish, Turkish and Greek.

There are currently **937 UI-i18n keys per language**. **? Help** provides **10 detailed contextual help topics in all 12 languages**. Favorites are part of Explorer help; planetary navigation has its own topic, accessible directly from the navigator. Help uses the current interface language and retains German as a fallback for a missing catalog or entry.

## Requirements

| Platform | Python |
| --- | --- |
| **Windows** | **Python 3.10 or newer, x64 required.** No artificial upper limit for existing versions. Actual package and import checks are decisive afterwards. |
| **Linux** | **Python 3.10 or newer**, 64-bit recommended. The venv module matching the Python version must be available. |

The required packages are listed in `requirements.txt`:

```text
PySide6>=6.7,<7
numpy
Pillow>=10.0
```

Installation downloads these dependencies. The local Elite files must be accessible for journal processing and planetary navigation. On Linux, Elite can run through Steam/Proton; configure the actual journal and screenshot paths in CMDRHelper. The Linux HUD support described above refers to X11.

## Installation on Linux

Extract the complete project or release and run in the project folder:

```bash
./install.sh
./start.sh
```

The scripts use only this installation's local `venv`. They resolve symbolic script links, check Python and pip and can repair a damaged local environment without touching personal data or Elite journals. Missing system packages are not installed automatically; the installer reports a missing venv module. The existing Linux installation workflow remains unchanged.

## Installation on Windows

1. Extract the complete ZIP into its own folder.
2. Run **install.bat**. It calls the included **install-windows.ps1**.
3. After successful installation, start CMDRHelper with **start.bat**.

Existing **Python 3.10 or newer x64** is accepted without an artificial version ceiling. A future Python version is not rejected solely because of its version number. A suitable existing Python or usable local venv prevents unnecessary automatic Python installation.

If no suitable Python is available, the installer offers automatic installation through **winget** after consent. The fixed **Python 3.14 x64** version series is deliberately selected for this; this choice is separate from the open-ended rule for existing Python versions. If automatic installation is not possible, the installer reports the error.

The installer creates, checks or repairs only the **local venv of this CMDRHelper copy**, installs the requirements and runs **pip check** and import checks for **PySide6, PySide6.QtWidgets, numpy and PIL**. Only these actual checks determine whether the environment is usable. If they fail, installation stops with an understandable error message. Other virtual environments are not repaired or replaced.

## Diagnostics and release packages

If problems occur, journal and online status indicators and log files in the `logs` folder can help. Personal data is stored locally; backing up favorites requires their internal image copies as well as the database.

Use `./create_release.sh` to create your own release package. The application version is managed centrally in `cmdrhelper/version.py` and read by the release script. The package contains application code and assets, but no personal database, venv, Git or cache files.

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

## AI Assistance

CMDRHelper is developed by Faber38. AI tools are used to assist with
development, code analysis, testing, translations and graphical assets.
The results are reviewed and tested before publication.

Some of the graphical assets used in the application were created with
generative AI.

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
