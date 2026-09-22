"""English content for contextual help."""


HELP_TOPICS = {
    "materials": (
        'Materials',
        """<h2>Materials</h2>
<h3>CMDRHelper</h3>
<p>Engineering material management: All 146 materials in Raw, Manufactured and Encoded, with grades, capacities and special cases. Commander-specific live stock, search, filters, five subtle row backgrounds and saved column widths/order make browsing easier. Unknown stock remains distinct from zero.</p>
<p>Odyssey inventory: The fourth material tab contains 223 catalog identities for goods, assets, data and consumables. Ship Locker, Backpack and reliable totals remain separate; mission stacks, mission status and engineering uses are visible. Positive stock numbers appear in gold. Missing name translations fall back to English.</p>
<p>Material trader search (Find trader → Open route planner): On request, Spansh searches Raw, Manufactured and Encoded separately from the current commander system. Carriers are excluded and station details checked. Distance in ly is the direct system distance; community data cannot guarantee access. Sending a result to the route planner only sets the destination system and does not start a route. There is no Odyssey trader search.</p>
<p>This main area shows the engineering materials of the commander currently being viewed. The selection in the CMDR view also applies here; other commanders' data remains separate.</p>
<h3>Three categories</h3>
<p>The Raw materials, Manufactured materials and Encoded data tabs contain all 146 catalog materials, including Guardian and Thargoid materials. The list is sorted by grade and alphabetically within each grade.</p>
<h3>Stock and bars</h3>
<p>The numbers show stock / maximum, for example Vanadium 244 / 250. The corresponding bar shows 97.6 %. Materials you have never owned also appear with 0 when the stock is reliably known.</p>
<p>Empty stocks are marked in muted red, low stocks in yellow/orange and nearly full or full stocks in green. The numbers remain visible regardless of the colors.</p>
<h3>Search and filters</h3>
<p>The search matches the displayed and English material names. It can be combined with all filters: All, Empty (0), Low (more than 0 up to 20 %), Nearly full (from 80 % to below 100 %) and Full (100 %). Values between 20 % and 80 % appear only under All. Tabs and filters are restored on the next start.</p>
<h3>Unknown values</h3>
<p>Without a reliable complete inventory, the display shows, for example, ? / 250. If the maximum is unknown, it may show 12 / ?. In both cases there is no percentage or bar; these materials appear only under All. An unknown grade appears in a separate group at the end of the list.</p>
<h3>Live updates</h3>
<p>New journal events update the stock automatically, including after material trades, engineering, synthesis or material rewards. A loading message appears during the initial read. Newly collected material is briefly highlighted with a label such as Vanadium +1; consumption does not produce a collection notification.</p>
<h3>Material names</h3>
<p>If a material name is not yet available in the selected language, its English display name is used. Internal journal symbols do not replace existing display names.</p>
<h3>Odyssey</h3>
<p>The fourth tab under Materials contains Goods, Assets, Data and Consumables. Ship locker and Backpack show personal stock. Carrier ✎ shows manually confirmed private stock on your own carrier for goods, assets and data. Double-click to confirm, correct or set to unknown. — means unknown; 0 must be explicitly confirmed. Total includes locker, backpack and carrier only when the required values are known and coherent. With multiple stacks, carrier stock appears once in the summary; individual stacks remain separate. Consumables retain the personal total without carrier stock. FCMaterials is not a complete carrier inventory and is not used as one. The locker limit of 1000 applies per category, not per item. Carrier stock is projected from the last confirmed balance. Locker changes are offset only while clearly on your own carrier, after subtracting explicit personal transactions. Purchases and sales through the carrier bartender, especially by other players, may change actual stock and may not be captured automatically. Double-click to confirm again when needed. Total uses the projection from the last confirmed carrier balance, not a guaranteed live query. Private Odyssey carrier storage shares 1,000 spaces across goods, assets and data. The stock sum is fully known only when all catalog positions and additional recorded materials are confirmed, including zero. Otherwise a minimum is shown. If the limit is exceeded, entries are retained and Total becomes unknown. Locker, backpack and market reservations are not private carrier material stock.<br><b>! – Set up carrier stock</b><br>Double-click the Carrier column in CMDRHelper and enter the current carrier quantity for EVERY position. Explicitly confirm ALL empty positions as 0 too.<br>— = not yet confirmed / unknown<br>0 = explicitly confirmed empty stock</p>
<p>Open buy orders at the carrier bartender reserve storage capacity. In-game occupancy may therefore exceed existing material stock. Reservations are not material stock and do not enter material totals. Without suitably current market data, occupancy remains unknown. Market snapshots may change through other players’ trades.</p>
<p>Usage shows the item's usage labels. Mission refers to a mission assignment of the specific inventory stack, not to the item type in general. Normal and mission-bound stacks remain separate. Even after mission completion, an item remains marked while the journal still lists it in the inventory; completion does not automatically remove it. The tooltip shows the mission number and known status. Engineering means that the static Odyssey catalog knows at least one confirmed use: a suit upgrade, weapon upgrade, suit modification, weapon modification or engineer unlock. The individual uses appear in the tooltip. A missing label does not mean the item is useless or only tradable. Powerplay and other special items may also be displayed.</p>
<p>The search matches the displayed local and English material/item names. The six Odyssey filters are All (all items), Mission (mission-assigned stacks), Engineering (items with confirmed engineering use), Backpack (backpack stock greater than zero), Ship locker (locker stock greater than zero) and Stock 0 (reliably known total stock of 0). Unknown stock — is not 0 and is excluded from Stock 0. Missing name translations fall back to English, so individual names may still appear in English in the selected language. This is intentional and is not a translation error in the inventory logic.</p>
<p>The personal inventory is updated automatically in the background. Confirmed new pickups may be highlighted briefly. When switching commanders, old stocks are removed immediately. Subtabs, filters, column widths and column order are saved separately for Odyssey.</p>
<h3>Mining</h3>
<p>Materials → Mining is the central overview of 57 currently known tradable mining commodities, separate from engineering materials. One table covers planetary surface mining and asteroid/ring mining. Fixed reference prices are for guidance only, not live market prices.</p>
<p><b>Columns</b><br><b>Commodity:</b> the commodity or resource name.<br><b>SRV:</b> verified stock in the SRV.<br><b>Ship:</b> verified stock in the ship.<br><b>Carrier:</b> stock on your own carrier; Elite does not supply a complete personal inventory, so the initial stock must be confirmed manually.<br><b>Total:</b> SRV + Ship + Carrier, only when all three balances are known. Otherwise —; unknown is not zero.<br><b>Avg price Cr/t:</b> a fixed reference value, not a guaranteed current selling price. Missing reference prices remain unknown.<br><b>Value class:</b> HIGH from 100,000 Cr/t; MEDIUM at 25,000–99,999 Cr/t; LOW below 25,000 Cr/t. An unknown price has no value class.</p>
<p><b>Confirming carrier stock</b><br>Elite Dangerous does not provide CMDRHelper with a complete personal carrier inventory. Establish a known starting point for a commodity: 1. Double-click its carrier cell. 2. Enter the current stock as a whole number of 0 or more. 3. Apply the value to confirm it manually. 4. CMDRHelper then automatically tracks unambiguous CargoTransfer events between your ship and your own carrier. The tooltip shows the manual confirmation and any subsequent tracking.</p>
<p><b>— = stock unknown</b><br>Without a confirmed starting stock, individual transfers cannot establish a reliable absolute carrier stock. Double-click at any time to change, correct or reset a value to unknown. If a transfer would produce a contradictory or negative result, the stock becomes unknown again and must be manually reconfirmed.</p>
<p><b>Ship and SRV</b><br>SRV and ship stocks are reconstructed separately from verified cargo data. Missing balances remain —. Complete cargo snapshots take precedence over calculated changes.</p>
<p><b>↻ Refresh</b><br>SRV stock and ship stock are refreshed separately using verified data. Confirmed carrier stock is preserved independently. Normal live updates continue automatically. Green means ready or successful, the colour animation indicates an update in progress, and red indicates a failed attempt. Missing or unverifiable data is not reported as empty stock.</p>
<p><b>Combining filters</b><br>Resource search filters by name. Value class offers All, HIGH, MEDIUM and LOW; origin offers All, Planetary mining and Asteroids/Rings. “In stock only” shows a commodity when at least one known balance in the SRV, ship or carrier is positive. Unknown balances are not treated as 0 and do not hide a known positive balance at another location. Search, value class, origin and stock filters can be combined.</p>
<p><b>ABBAU ×N in Explorer</b><br>Clicking opens Materials → Mining and automatically sets the origin filter to Planetary mining. There is no second mining table in Explorer.</p>
<p><b>Sorting and widths</b><br>Click column headings to sort ascending or descending. Stock and prices sort numerically, with unknown values last. Drag column boundaries with the mouse to adjust widths. Sorting, column widths and the value class, origin and In stock only filter states are saved.</p>
<p><b>Origin</b><br>Surface means planetary surface mining; Asteroid means asteroid/ring mining. Some commodities come from both sources (Both) and appear in both matching origin filters.</p>""",
    ),'overview': ('Overview',
              '<h2>Overview</h2>\n'
              '<p>The overview is the home page of CMDRHelper. It summarizes the most important '
              'information about the currently active commander and shows at a glance whether the '
              'journal, location and online services are correctly recognized.</p>\n'
              '\n'
              '<h3>Commander & ship</h3>\n'
              '<p>The commander recognized from the Elite Dangerous Journal and the ship currently '
              'in use are displayed here.</p>\n'
              '<p>CMDRHelper assigns personal data to the respective commander based on the '
              'Frontier ID (FID). This keeps data from different commanders separate from each '
              'other.</p>\n'
              '<p>When changing the commander, the saved information associated with the new '
              'commander is loaded.</p>\n'
              '\n'
              '<p>CMDRHelper shows the game mode last reported by Elite. Open, Solo and Private Group are recognized from LoadGame. For private groups, the group name reported by Elite is displayed unchanged. This does not mean that Elite is currently running.</p>\n'
              '<h3>journal</h3>\n'
              "<p>CMDRHelper uses Elite Dangerous's journal files as its main data source.</p>\n"
              '<p>The journal display informs whether journal files have been found and assigned '
              'to the active commander. New complete journal entries are automatically processed '
              'during gameplay.</p>\n'
              '<p>Journal areas that have already been processed are saved so that CMDRHelper does '
              'not have to fully evaluate each journal again the next time it is started.</p>\n'
              '\n'
              '<h3>Current location</h3>\n'
              '<p>Shows the currently known star system and - as far as known from the journal - '
              'the exact location of the commander.</p>\n'
              '<p>The location is updated by events such as jumps, docking and other position '
              'reports and stored on a commander-by-command basis.</p>\n'
              '\n'
              '<h3>Missions</h3>\n'
              '<p>This area shows the number of currently known open missions.</p>\n'
              '<p>The “Missions” button or menu item takes you to the full mission view with the '
              'known mission objectives and status information.</p>\n'
              '\n'
              '<h3>Last Stand</h3>\n'
              '<p>“Last state” summarizes the last known persistent commander state. This allows '
              'important information to be restored even after restarting Elite Dangerous or '
              'CMDRHelper.</p>\n'
              '\n'
              '<h3>Final systems</h3>\n'
              '<p>Systems recently visited or recognized from the journal are displayed here.</p>\n'
              "<p>The list serves as a quick overview of the Commander's recent journey.</p>\n"
              '<p>Visit history includes Location, FSDJump and CarrierJump during live journal updates. Multiple location events during one uninterrupted stay count as one visit: A → A → A counts once. A genuine return is preserved: A → B → C → A counts as four visits.</p>\n\n'
              '<h3>Online status</h3>\n'
              '<p>There are additional status indicators at the top of the main window:</p>\n'
              '<ul>\n'
              '<li><b>Journal recognized</b>– CMDRHelper detected a valid journal source and '
              'commander identity.</li>\n'
              '<li><b>EDSM</b>– shows the current status of the EDSM transmission for the active '
              'journal FID.</li>\n'
              '<li><b>INARA</b>– shows the current status of the Inara transmission for the active '
              'journal FID.</li>\n'
              '</ul>\n'
              '<p>Online access data is managed separately for each commander. A commander never '
              "automatically uses another commander's API-Key.</p>\n"
              '\n'
              '<h3>Important for multiple commanders</h3>\n'
              '<p>The live data always depends on the commander who was clearly identified by the '
              'current Elite Dangerous journal session.</p>\n'
              '<p>Merely displaying a different commander in a view does not change the active '
              'live commander or affect any EDSM or Inara broadcast.</p>\n'
              '\n'
              '<h3>Tip</h3>\n'
              '<p>If the commander, ship or location does not match the current state of the game, '
              'first check the journal display at the top and then check the journal folder set '
              'under “Settings”.</p>'
              '<p>Open is red, Solo gold and Private Group green, with the reported group name for private groups. The mode is reconstructed from available journals and updated with new LoadGame entries.</p>\n<p>A single click on an entry in Recent systems copies the system name to the clipboard. “✓ Copied: &lt;System&gt;” appears briefly.</p>\n'),
 'missions': (
        'Missions & Rewards',
        """<h2>Missions &amp; Rewards</h2>
<p>This main page shows missions and observed rewards for the currently active journal Commander. Selecting another Commander in the separate CMDR view does not change this page. Each Commander's data stays separate.</p>

<h3>Using this page</h3>
<ol>
<li>Open “Missions &amp; Rewards” and select a mission in the list.</li>
<li>Check “Status” and “MISSION DETAILS”. Use “Next step” for guidance.</li>
<li>If needed, use “Refresh journal” to read the available journal data again.</li>
<li>Consider mission rewards, “Bounties” and “Combat bonds” separately.</li>
</ol>

<h3>List and details</h3>
<p>The list contains confirmed open missions and detected provisional encounter offers. It shows the mission, system, planet / location, status, next step, reward and deadline. Selecting an entry displays the available destination and progress details. Missing journal information remains unknown; provisional offers have an unknown deadline.</p>

<h3>Mission status</h3>
<p>Status follows the available mission, location and progress information. Not every mission type provides all intermediate stages.</p>
<ul>
<li><b>Mission accepted / En route:</b> The mission is known; arrival at its destination has not yet been detected.</li>
<li><b>In target system:</b> You are in the target system, but not yet at the detected mission destination.</li>
<li><b>At mission destination:</b> The matching destination station or body has been reached.</li>
<li><b>Destination changed:</b> A new mission destination has been reported.</li>
<li><b>Cargo collected:</b> Collection of mission cargo has been detected.</li>
<li><b>Delivery in progress:</b> A delivery has been recorded; known quantity progress is shown.</li>
<li><b>Task completed / Data received:</b> The task or data collection is done. The mission may still be open, for example with “Return to mission terminal”. This does not yet confirm payment.</li>
</ul>
<p>Detected completions, failures and abandonments remove the affected mission from the open list. A complete new mission snapshot may identify older entries as no longer active.</p>

<h3>Total reward</h3>
<p>“Total reward” adds up the known credit rewards of confirmed open missions. It is not a balance already paid out. Provisional encounter offers, bounties and combat bonds are excluded.</p>

<h3>Encounter missions</h3>
<p>Supported space encounters can appear as provisional “Encounter assignment” entries before a final MissionID is available. “Reward offer” is therefore not yet a confirmed open mission reward and is excluded from the total reward.</p>
<p>If later journal information unambiguously links an offer to a mission, the two are merged. Ambiguous offers remain provisional. Unconfirmed offers disappear locally after 24 hours; this does not indicate an in-game mission deadline.</p>

<h3>Bounties</h3>
<p>This area shows locally observed bounties with a total and amounts by faction. It only knows captured data, not a reliably complete in-game balance. “Recording from now on.” marks the start of capture; gaps are indicated by “Not fully synchronized: some events may be missing.”.</p>
<p>A detected bounty redemption or death clears the entire local bounty balance. This is independent of mission status.</p>

<h3>Combat bonds</h3>
<p>This area lists observed combat bonds by faction that have not been detected as redeemed. Any balance from before capture began is missing. Uncertainty is shown as “Observed amount” with “Balance not fully verified.”.</p>
<p>An unambiguously attributed redemption clears the observed amount for the named faction; other factions remain unchanged. If attribution is unclear, amounts remain and “Redemption detected – check balance.” appears. A detected death clears observed combat bonds.</p>

<h3>Resetting locally</h3>
<p>“Reset…” in a reward area clears only that area's local balance for the active Commander after confirmation. <b>This changes no values in Elite Dangerous.</b> Bounties and combat bonds are reset separately; missions are neither cleaned up nor completed.</p>

<h3>Updates and restarts</h3>
<p>Known open missions and local reward balances survive Helper restarts. A new journal session without a mission list does not automatically remove open missions. Capture gaps can leave reward balances incomplete in particular. “Refresh journal” can only read existing information, not create missing game data.</p>
<p>The local mission display needs no Inara connection. With an enabled connection configured for the active Commander, supported mission events can also be uploaded.</p>""",
    ),
 'explorer': ('Explorer',
              '<h2>Explorer</h2>\n<h3>CMDRHelper</h3>\n<p>System overview: The new Elite-style view replaces the previous miniature overview and is available in Explorer and Chronicle. Stars and planets form the main structure, with moons branching below; multiple-star systems remain readable. Zoom, scrolling, fit to window and body clicks provide access to details.</p>\n<p>Compact asteroid belts: Belt clusters are grouped into clear belts in the overview and regular Explorer/Chronicle system maps. All individual cluster data is retained.</p>\n<p>Cartography corrected: A later scan after DSS mapping no longer resets unsold exploration values, mapping time or efficiency. Existing incorrect claims are repaired at startup from available journals with clear commander attribution. Missing sources leave the repair pending; deleting the database is unnecessary.</p>\n'
              '<p>The Explorer evaluates the systems and celestial bodies discovered and scanned '
              'by the active commander. It combines your own Elite Dangerous journal data with '
              'already available additional information and displays exploration, cartography, '
              'biological/geological signals and surface mining data together.</p>\n'
              '\n'
              '<h3>Current system</h3>\n'
              '<p>The current level of knowledge about the system is summarized in the upper '
              'area.</p>\n'
              '<p>These include, among others:</p>\n'
              '<ul>\n'
              '<li>well-known and even recorded bodies in the journal</li>\n'
              '<li>existing signals</li>\n'
              '<li>Scan values</li>\n'
              '<li>cartography value already achieved</li>\n'
              '<li>possible total value if fully mapped</li>\n'
              '<li>BIO status and estimated BIO values</li>\n'
              '<li>Cartography and BIO data that have not yet been submitted</li>\n'
              '</ul>\n'
              '<p>The values \u200b\u200bshown are based on the actually available data. Missing '
              'information is not presented as a separate discovery.</p>\n'
              '\n'
              '<h3>System map</h3>\n'
              '<p>The system map graphically represents stars, planets, moons and other known '
              'bodies in the current system.</p>\n'
              '<p>A body can be clicked to open its detailed view.</p>\n'
              '<p>The display shows, among other things, body type, distance and – if available – '
              'scan and cartography values \u200b\u200bas well as special exploration '
              'properties.</p>\n'
              '\n'
              '<p>“Automatically fit to window” is enabled by default and remembers your choice across restarts. It fits each new overview to the window once; enabling it in an open window also fits once. Afterwards you can still zoom and pan manually. “Fit to window” remains available to fit the view again manually.</p>\n'
              '\n'
              '<h3>Stations and facilities</h3>\n'
              '<p>The “STATIONS (N)” tab shows known stations and facilities in the current Explorer system as expandable cards. The tab count includes all known entries, even those hidden by filters. This is not a complete directory of every station in the galaxy.</p>\n'
              '<p>The starting point is locally known Elite journal observations. With Spansh supplementation enabled, the separate station cache adds station information. Sources can be “Journal”, “Spansh” or “Journal + Spansh”; journal information takes precedence where facts conflict. Spansh does not add Fleet Carriers here. A locally known carrier belonging to you can appear.</p>\n'
              '\n'
              '<h3>Station search, filters and sorting</h3>\n'
              '<p>“Search station name…” immediately searches station names or parts of names, ignoring case. An empty search does not restrict names. The search and both filters must all match.</p>\n'
              '<ul>\n'
              '<li><b>Type:</b> Limits the list to orbital stations, outposts, surface stations, settlements, megaships, Fleet Carriers or other facilities. “All types” removes the type restriction.</li>\n'
              '<li><b>Parent body:</b> Selects a known associated body. “All bodies” allows all locations; “Unknown” appears when entries cannot be safely assigned to a known body.</li>\n'
              '<li><b>Sort by:</b> Initially alphabetical by “Name”. Alternatively sort ascending by “Type”, “Parent body” or “Distance to arrival”. Distance is sorted numerically; unknown distances or bodies appear last when sorting by that field.</li>\n'
              '</ul>\n'
              '<p>There are no station column headers to click. The selectors sort the cards. Search, filters and sorting do not make network requests. Changing systems clears the search and type/body filters. An empty display distinguishes no known entries from entries that do not match the filters.</p>\n'
              '\n'
              '<h3>Station details and services</h3>\n'
              '<p>Click a station card header to expand or collapse its details. Where known, these show name, type, system, associated body, MarketID, last update and source. Double-clicking the preview image opens the image viewer.</p>\n'
              '<p>Spansh can add distance to arrival in light seconds, allegiance, government, controlling faction, economy information and counts of large, medium and small landing pads. Station update, system update and retrieval times are shown separately where available; a new retrieval does not guarantee newer station information.</p>\n'
              '<p>Known “Services” appear as labelled fields, such as “Market”, “Shipyard”, “Outfitting”, “Repair”, “Refuel” or “Material Trader”. The card header shows up to three services and, when applicable, the number of further entries; expanding shows all services recognised by CMDRHelper. Missing information is not guessed and does not prove that a facility is absent.</p>\n'
              '\n'
              '<h3>Stations on the map and refreshing</h3>\n'
              '<p>The system map and “System overview” use the same known station information. Facilities with a confirmed body association appear beside that body; others appear under “Other facilities”. Clicking opens station details, or a selection list first for groups.</p>\n'
              '<p>In “System overview”, “Refresh Spansh data” refreshes Spansh station information for the system displayed in that window. Spansh station information must be enabled and the system identity known. The status line reports running requests, success, failure or an update already performed today. On failure, local information and usable cached data remain available. Settings help explains automatic requests, caching and manual refresh rules.</p>\n'
              '\n'
              '<h3>BIO ×N</h3>\n'
              '<p>BIO ×N denotes the number of biological signals of a body reported by the '
              'game.</p>\n'
              '<p>The number initially only indicates how many biological signals or genera were '
              'reported. It does not automatically mean that all biological species have already '
              'been found or analyzed.</p>\n'
              '<p>Actual own organic discoveries are kept separately.</p>\n'
              '\n'
              '<h3>GEO ×N</h3>\n'
              '<p>GEO ×N shows the number of geological signals of a body reported by the '
              'game.</p>\n'
              '<p>These can include, for example, geological features such as fumaroles or '
              'geysers. CMDRHelper only displays the information that appears from the existing '
              'journal/body data.</p>\n'
              '\n'
              '<h3>ABBAU ×N</h3>\n'
              '<p>ABBAU ×N shows the number of planetary mining sites of a body reported by Elite '
              'Dangerous.</p>\n'
              '<p>Example:</p>\n'
              '<p><b>ABBAU ×12</b></p>\n'
              '<p>means that 12 planetary mining sites have been reported for this body.</p>\n'
              '<p>The number does not say which raw material can be extracted at a single '
              'location.</p>\n'
              '\n'
              '<h3>Own mining finds</h3>\n'
              '<p>If the commander has actually carried out surface mining with the Rhino, the '
              'CMDRHelper stores the personal findings documented separately.</p>\n'
              '<p>A distinction is made between:</p>\n'
              '<ul>\n'
              '<li>actually obtained commodities, e.g. B. Copper in tons</li>\n'
              '<li>secondary materials collected during mining</li>\n'
              '<li>general surface materials of the body</li>\n'
              '</ul>\n'
              '<p>An example of a personal find would be:</p>\n'
              '<p><b>Copper – 40 t</b></p>\n'
              '<p>This information means that this commander actually extracted 40 t of copper '
              'there.</p>\n'
              '<p>The personal mining finds are saved for each commander and are not mixed with '
              'the finds of other commanders.</p>\n'
              '\n'
              '<h3>Body surface materials</h3>\n'
              '<p><code>Scan.Materials</code>describes the general surface material composition of '
              'a body.</p>\n'
              '<p>For example, iron, nickel, sulfur or other materials can be displayed with '
              'percentage values.</p>\n'
              '<p>These values \u200b\u200bshould not be confused with the raw materials of a '
              'planetary mining depot. Frontier does not provide any documented direct association '
              'between these general body materials and the contents of an individual mining site '
              'in the Journal.</p>\n'
              '\n'
              '<h3>Terraforming</h3>\n'
              '<p>The symbol or label for terraforming shows that a body is considered a '
              'terraforming candidate based on the available data.</p>\n'
              '\n'
              '<h3>First discovery</h3>\n'
              '<p>“Already discovered at your scan” describes the state before your scan at that time. Yes means previously discovered, No means not yet discovered then; missing information remains Unknown. ★ marks a First Discovery candidate at scan time, not a guaranteed official first claim still available today.</p>\n<p>A historical WasDiscovered=false or WasMapped=false does not mean the body is still undiscovered or unmapped today. These observations remain historical after data sales or revisits. Being known to EDSM is separate information and does not prove official discovery in Elite. No official first discoverer is inferred from it.</p>\n'
              '\n'
              '<h3>First mapping</h3>\n'
              '<p>CMDRHelper distinguishes between:</p>\n'
              '<ul>\n'
              '<li>◉ First Mapping candidate at scan time: not yet mapped when you scanned it</li>\n<li>◎ Mapped by you: your own DSS completion is recorded</li>\n<li>◉✓ Candidate at scan time and your own mapping recorded; official first claim unconfirmed</li>\n'
              '</ul>\n'
              '<p>“Already mapped at your scan” is evaluated separately from discovery. Missing information remains Unknown. An already discovered body may have been unmapped when you scanned it. Your own mapping does not confirm an official First Mapping tag; across multiple visits, its order relative to the stored scan is not always established either.</p>\n<p>Completing your own DSS mapping now reliably saves the mapping time, probes used and efficiency target. Later scan events no longer cause existing details to be lost.</p>\n'
              '\n'
              '<h3>Landable</h3>\n'
              '<p>The landability indicator identifies bodies on which, according to known data, '
              'landing is possible.</p>\n'
              '\n'
              '<h3>Gold frames / valuable bodies</h3>\n'
              '<p>Particularly valuable bodies can be highlighted in the explorer display.</p>\n'
              '<p>The gold border marks a mapping estimate above the configured threshold. It is not a First Discovery marker and confirms neither unsold data nor first-discovery or first-mapping bonuses still available today.</p>\n'
              "<p>It does not replace the detailed display of the body's value.</p>\n"
              '\n'
              '<h3>List of values</h3>\n'
              '<p>The value list shows estimates based on the stored scan state, not guaranteed outstanding payouts. First bonuses remain unconfirmed. Tooltips in the map and list and the body details use the same time-qualified states.</p>\n'
              '<p>It is particularly suitable for quickly comparing interesting or valuable bodies '
              'in a system.</p>\n'
              '\n'
              '<h3>BIO / GEO / ABBAU</h3>\n'
              '<p>This view groups bodies with biological, geological or planetary mining signals.</p>\n'
              '<p>This means that interesting bodies do not have to be searched for individually '
              'in the complete system map.</p>\n'
              '<p>If you have your own surface mining data, your personal mining finds can also be '
              'visible.</p>\n'
              '<p>Manually adjusted column widths in the shared Explorer BIO / GEO / ABBAU table survive reopening and application restarts. Saved popup column widths are restored more robustly; invalid values fall back to safe defaults.</p>\n\n'
              '<h3>Using the tables</h3>\n<p>In the value list and BIO / GEO / ABBAU, click a column heading to '
              'sort; click it again to reverse the direction. Drag column boundaries with the mouse to resize '
              'them. Sorting and column widths are saved separately for each table. Body names use natural '
              'ordering, for example A 2 before A 10. Distances, credits and counts sort numerically. Status, '
              'analysis and visited columns sort by their meaning rather than alphabetically.</p>\n\n<h3>Body '
              'detail</h3>\n'
              '<p>Clicking on a body opens the detailed view.</p>\n'
              '<p>As far as is known, the following can appear there:</p>\n'
              '<ul>\n'
              '<li>Body Type</li>\n'
              '<li>mass</li>\n'
              '<li>distance</li>\n'
              '<li>Gravity</li>\n'
              '<li>atmosphere</li>\n'
              '<li>Landability</li>\n'
              '<li>Terraforming status</li>\n'
              '<li>BIO/GEO signals</li>\n'
              '<li>planetary mining sites</li>\n'
              '<li>Surface materials</li>\n'
              '<li>own mining finds</li>\n'
              '<li>Scan value</li>\n'
              '<li>cartography value</li>\n'
              '<li>current value</li>\n'
              '</ul>\n'
              '<p>Not every body has all the information.</p>\n'
              '\n'
              '<h3>BIO forecasts</h3>\n'
              '<p>CMDRHelper can estimate possible biological discoveries based on the existing '
              'data on suitable bodies.</p>\n'
              '<p>Predictions are not a guarantee that a particular species will actually be '
              'present. They serve as a decision-making aid for exploration.</p>\n'
              '<p>Estimated BIO values \u200b\u200bare also predictions and are treated separately '
              'from actual confirmed findings.</p>\n'
              '\n'
              '<h3>Not yet submitted</h3>\n'
              '<p>CMDRHelper maintains commander-related known cartography and BIO data that has '
              'not yet been submitted.</p>\n'
              '<p>Cartography sales and biological royalties are accounted for using the '
              'corresponding journal events.</p>\n'
              '<p>Cartography data that has already been sold should not appear as open again '
              'after reconstruction.</p>\n'
              '\n'
              '<h3>Auto show</h3>\n'
              '<p>Supported live information such as Valuable Bodies, BIO Finds or Cargo can be '
              'automatically displayed using the switches in the left sidebar.</p>\n'
              '<p>These small live windows serve as additional hints while playing and do not '
              'replace the full Explorer view.</p>\n'
              '<p>“Cargo” shows the confirmed inventory of the Ship or SRV determined by the active Journal FID. SRV Cargo is never adopted as Ship Cargo; Limpets count towards the total load and are displayed separately in the Name | Quantity table.</p>\n'
              '<p>BIO progress is compact: 1/3 yellow, 2/3 blue and 3/3 green; the completed state “Done” is also green. Under “auto show”, GEO has its own saved switch: BIO alone, GEO alone or both together are supported.</p>\n<p>The cargo window automatically adjusts its height to its contents. With many entries, height is capped and the table scrolls; your chosen width and window position are preserved. The existing “Cargo HUD” switch is now under “auto show”, with no additional switch in the cargo window.</p>\n\n'
              '<h3>Several commanders</h3>\n'
              '<p>Personal exploration results, cartography, BIO finds and own surface mining '
              'finds are assigned to the respective commander.</p>\n'
              '<p>Global astronomical properties of a body - for example the number of known '
              'planetary mining sites - remain properties of the body itself.</p>\n'
              '\n'
              '<h3>Tip</h3>\n'
              "<p>If you have an interesting body, it's worth clicking on the detailed view. This "
              'is the best place to differentiate between general body data, possible exploration '
              'results and actual finds documented by your own commander.</p>'
              """

<h3>★ Favorites</h3>
<p>The “★ Favorites” button at the top of the Explorer opens a separate, reusable favorites window. Here you save systems, planets/moons and surface locations for the active commander.</p>
<p>The scrollable list, sorted alphabetically by name, shows the name, type, system, body and latitude/longitude where applicable, category and a small image preview. Free-text search, type and category filters can be used together. The search covers the name, system, body and note.</p>
<p>“Open / View” shows the saved information, note and a larger image preview. “Show in Explorer” opens the existing system overview or body detail view if the favorite belongs to the current Explorer system and matching data is available. For other systems, the saved favorite data remains visible; no system route is calculated.</p>

<h3>Distance filter</h3>
<p>“Distance filter” is off by default. “Max. distance:” defaults to 500 ly, with a range of 1 to 100,000 ly. Distance is measured from the currently known system using locally available system coordinates. No live query is made just for this filter.</p>
<p>Favorites with known distances beyond the limit are hidden. Favorites with unknown distances remain visible. If the current system’s coordinates are missing, the distance filter hides no entries. Search, type and category filters still apply. Filtering updates automatically after a system change. The switch and maximum distance are saved.</p>

<h3>Exporting favorites</h3>
<p>“Export” creates a portable ZIP containing all favorites of the active commander, not just entries visible through search, type, category or distance filters. favorites.json contains the structured favorite data; available favorite images are included under images/. The package can be transferred between Linux and Windows.</p>
<p>Existing favorites and original images are not changed. Identical image contents are stored only once in the package. Missing or damaged images do not prevent exporting favorite data. Import and export allow up to 32 MiB per file and 256 MiB in total for the uncompressed package contents.</p>

<h3>Importing favorites</h3>
<p>“Import” first checks the ZIP and shows a summary of new and existing favorites before making changes. Imported favorites belong to the currently active commander. Duplicates are identified by type, category, name and location: known system/body IDs and coordinates, otherwise system/body names. Duplicates within the package are also considered.</p>
<p>One choice applies to all detected duplicates: “Skip” is the default and keeps existing entries unchanged; “Replace existing favorite” applies the imported data to the existing favorite; “Import as a new entry” creates an additional entry. Cancelling imports nothing.</p>
<p>Invalid favorite data prevents the entire import. If an import error occurs, database changes are rolled back to avoid a partial import. Missing or damaged images do not prevent importing valid favorite data; those favorites are imported without an image. Imported images are managed locally by CMDRHelper.</p>

<h3>Save a system, planet or current location</h3>
<ul>
<li>“★ Save current system” saves the current system without surface coordinates.</li>
<li>“★ Save planet / moon” lets you select a known planet or moon in the current system. This favorite also receives no surface coordinates.</li>
<li>“★ Save current location” is at the top of the favorites window beside the other two save options and is also available in the planetary navigator. In the favorites window, the button always remains visible and is disabled without valid current planetary position data and an active commander. Clicking it freezes the commander, system, body, latitude and longitude. Subsequent movement in the game does not change these values in the open dialog.</li>
</ul>
<p>Enter a name of your choice and select exactly one category: Bio, Geo, Mining, View, Landing site, Interesting or Other. A note and an image are optional. Known technical IDs are carried over internally; you do not need to enter them. Latitude or longitude 0.0 are also valid coordinates.</p>
<p>“Edit” changes the name, category, note and image. The system, body and saved coordinates are preserved. To save a different surface location, create a new favorite at that position.</p>

<h3>Quick favorite without the mouse</h3>
<p>Under “Settings → Quick favorite”, you can freely set, change or remove a global hotkey. After installation, it is “Not assigned” by default: CMDRHelper does not register any key without being asked. The binding is saved. If a combination is already in use or unavailable on your system, an error message appears; any previously working binding is retained.</p>
<p>On Linux/X11 and Windows, the hotkey also works while Elite has focus – on foot, in the SRV and in the ship. Pressing it immediately saves the current surface location for the active commander, without a dialog or mouse interaction. The commander, system, body and current Latitude/Longitude values are frozen at that moment. Nothing is saved without valid current planetary coordinates; earlier coordinates are not reused.</p>
<p>The favorite receives a unique provisional name such as “Marker 07.09.2026 06:32:15” and the “Other” category. In the normal favorites window, you can later rename it, assign it to another category, add a note or add an image. No screenshot is automatically taken or imported.</p>
<p>For approximately two seconds, “★ FAVORITE SAVED” appears directly over the active Elite window with the body and coordinates; if the location is unavailable, “⚠ NO PLANETARY COORDINATES” appears briefly. The display does not take focus or intercept input. It also works with the navigation HUD switched off and then disappears completely. With the HUD switched on, the normal navigation display remains afterwards. The saved HUD switch setting is not changed. The display uses the same overlay infrastructure and platform requirements as the navigation HUD.</p>

<h3>Favorite images</h3>
<p>Favorite images are separate from the Images area. “Choose image …” allows PNG, JPEG and WebP. Only when saving does CMDRHelper copy the selected image into its own favorite image folder. The original file is neither moved nor modified.</p>
<p>“Use latest screenshot” rescans the configured screenshot source folder on every click and looks for readable screenshots with typical Elite filenames. Without a configured folder, the usual Elite screenshot directories on Windows or Steam/Proton are considered. The folder belonging to the active commander in the configured conversion destination is also searched for matching converted Elite screenshots. A converted screenshot can therefore still be found if its original BMP has been deleted. The newest capture is determined by an unambiguous timestamp in the filename, otherwise by the file time; for converted images, the capture time stored in the name counts instead of the conversion time. CMDRHelper does not trigger screenshots itself or search arbitrary image folders.</p>
<p>Before use, the filename, capture time and a freshly loaded preview are displayed. Confirm with “Use this image”. If no suitable screenshot is found, you can still use “Choose image …”. Elite BMP screenshots are saved as an internal PNG copy.</p>
<p>An image can be replaced in the edit dialog or deselected with “Remove image”. Saving removes the internal copy that is no longer used. If an image file is missing, the favorite remains usable without a preview.</p>
<p>Favorite images can be included in exports and are copied locally on import. Shared internal image copies are retained while another favorite still needs them. When an import replaces favorites, old image files are currently retained as a precaution.</p>

<h3>Favorite target and commander</h3>
<p>“▶ To route” sets the favorite’s known system as the destination in the route planner. The start follows the existing behavior using the current AppState; a manually entered start is preserved. No route is calculated automatically. “◎ To coordinates” starts the existing planetary navigation to the surface location with the existing navigation HUD when a system, body and valid coordinates are saved. Traveling to the system and surface navigation are two separate steps, with no automatic travel sequence. Without surface coordinates, only the route action is available; actions with missing required data are hidden.</p>
<p>For surface locations, “◎ To coordinates” passes the saved body, latitude, longitude and favorite name to the existing planetary navigator. The new target replaces the previous target. Favorites have no navigation logic of their own. The navigator continues to decide for itself: matching valid planetary data activates navigation; otherwise it waits for that data.</p>
<p>Favorites belong exclusively to the active commander. Switching commanders updates the list and discards an open edit dialog. A target still managed as the previous commander's favorite target is stopped. The commander selection in the chronicle does not extend this favorites list.</p>
<p>“Delete” requires confirmation and removes only the favorite record and its internal image copy. The original screenshot or selected original image and all Explorer, journal and body data are preserved.</p>"""),
 'chronicle': (
        'Chronicle',
        """<h2>Chronicle</h2>
<h3>CMDRHelper</h3>
<p>System overview: The new Elite-style view replaces the previous miniature overview and is available in Explorer and Chronicle. Stars and planets form the main structure, with moons branching below; multiple-star systems remain readable. Zoom, scrolling, fit to window and body clicks provide access to details.</p>
<p>Compact asteroid belts: Belt clusters are grouped into clear belts in the overview and regular Explorer/Chronicle system maps. All individual cluster data is retained.</p>
<p>The chronicle is the commander's personal travel and discovery history. It uses the permanently stored journal information to find systems that have already been visited, to spatially represent them and to search for known discoveries.</p>

<h3>Systems visited</h3>
<p>The Chronicle shows the systems visited and their locations in the galaxy known to the Commander.</p>
<p>If available, the first and last visit as well as known body information are taken into account.</p>
<p>With an active period, the visit count, first visit and last visit in the map view refer to the filtered actual system visits.</p>
<p>The chronicle is therefore not just a map, but also a tool for finding previous travel destinations and discoveries.</p>

<h3>3D map</h3>
<p>The systems visited are spatially represented using their galactic X/Y/Z coordinates.</p>
<p>The operating instructions are located directly above the map:</p>
<ul>
<li>Hold down the left mouse button → rotate view</li>
<li>hold and drag the middle mouse button → draw a zoom rectangle</li>
<li>Hold down the right mouse button → move view</li>
</ul>
<p>The small axis display helps with orientation in space.</p>

<p>Use the mouse wheel to zoom in or out without a modifier key.</p>
<p>Double-click empty map space to restore the initial tilted view, reset panning and fit all currently displayed systems into the window. Filters and the selected system are retained.</p>
<p>When you start rotating with the left mouse button, the clicked system becomes the pivot. In empty space, the point beneath the pointer on the galactic plane is used; with a nearly horizontal view, the map centre on that plane is used instead. Align also rotates around the current pivot.</p>
<p>Click a system to open its detail window. There, left-click the system name at the top or the adjacent copy icon ⧉ to copy only the system name to the clipboard. A brief ✓ confirms the copy.</p>

<h3>Current position</h3>
<p>With “Current Position” the map view can be aligned or returned to the currently known location of the active commander.</p>
<p>The current filter settings are applied first. The view is centred on the current system only if it is included in the resulting map.</p>
<p>Otherwise, “The current system is not included in this filter selection.” is displayed. This does not remove the filters.</p>

<h3>Align</h3>
<p>“Align” resets the orientation to a top-down view of the galactic plane. Panning and zoom are preserved.</p>
<p>This is useful if extensive rotation has made the map difficult to follow.</p>

<h3>Refresh Chronicle</h3>
<p>“Refresh Chronicle” reloads the chronicle data using the current combined filter settings and updates the display. Free text, enabled date bounds and mining filters are evaluated together again; active filters are not ignored.</p>
<p>The function does not change journal files or create new exploration data. It simply updates the history display based on the existing CMDRHelper data.</p>

<h3>Free-text search</h3>
<p>Already known content can be searched using the “Search chronicle …” field.</p>
<p>The search takes into account – if available in the database – among other things:</p>
<ul>
<li>System names</li>
<li>Body features</li>
<li>biological data</li>
<li>Materials</li>
<li>Codex data</li>
</ul>
<p>Free text, period and mining share a single filter area. “Apply” evaluates the configured filters together. Enter in the free-text field starts the same combined filtering as “Apply”.</p>

<h3>From/To period (UTC)</h3>
<p>Enable “From” and “To” using their respective checkboxes and select the desired date. You can also use just one bound. Without an enabled checkbox, there is no time restriction on that side; with neither checkbox enabled, no period restriction applies.</p>
<ul>
<li><b>From:</b> From the start of the selected UTC calendar day, inclusive.</li>
<li><b>To:</b> The entire selected UTC calendar day is included, up to immediately before the start of the following day.</li>
</ul>
<p>UTC is Coordinated Universal Time. The date bounds refer to UTC calendar days, not calendar days in your local time zone.</p>
<p>The filter uses actual system visits from <code>system_visits</code>. An actual visit by the respective commander within the period is required. The stored values <code>first_seen</code> and <code>last_seen</code> do not replace a real visit: a period merely lying between an earlier first visit and a later last visit is not sufficient.</p>
<p>The period filters visits, not individual discovery, BIO, GEO or mining events. Known findings and mining quantities remain stored totals. From/To can be used on their own or together with free text and mining.</p>
<p>If From is after To, “The From date must not be after the To date.” is displayed. No database query is started. Correct the date bounds and apply the filters again.</p>

<h3>Search results</h3>
<p>Results are displayed in the existing results list below the chronicle map.</p>
<p>Depending on the type of hit, system and body as well as additional information may appear.</p>
<p>A hit can be used to find the corresponding system or body that is already known and to open the existing detailed information.</p>

<h3>No results</h3>
<p>If valid combined filtering finds no matches, the map and routes are cleared. The results list is cleared and hidden, the detail display is reset and any open chronicle system detail window is closed.</p>
<p>Old results do not remain visible. In this case, check the combination of search text, period and mining filters, as well as the commander used for the respective view.</p>

<h3>Planetary mining sites</h3>
<p>The filter “Planetary mining sites” can be used to specifically search for known bodies for which Elite Dangerous has reported planetary mining sites.</p>
<p>The underlying display corresponds to that known from Explorer:</p>
<p><b>ABBAU ×N</b></p>
<p>The number belongs to the body itself and is not related to the commander.</p>

<h3>At least</h3>
<p>Using “At least” you can specify the minimum number of planetary mining locations a body should have.</p>
<p>Example:</p>
<p><b>At least 20</b></p>
<p>only shows known bodies with at least:</p>
<p><b>ABBAU ×20</b></p>
<p>This makes it possible to specifically locate particularly extensive mining areas.</p>

<h3>My mining finds</h3>
<p>“My mining finds” limits the search to bodies where the viewed commander has demonstrably carried out surface mining.</p>
<p>This information comes from personal surface mining history and is strictly separated by commander.</p>
<p>A body can therefore have global ABBAU ×N signals without the commander having mined anything there.</p>

<h3>Commodity</h3>
<p>When “My mining finds” is enabled, the “Commodity” selection is also available.</p>
<p>The list contains only commodities that the viewed commander has actually extracted through surface mining.</p>
<p>This is not a theoretical list of all possible mining raw materials.</p>
<p>For EXAMPLE, the selection might contain:</p>
<ul>
<li>All</li>
<li>copper</li>
</ul>
<p>If additional raw materials are actually mined later, they will automatically appear in your personal selection.</p>

<h3>Targeted search for raw materials</h3>
<p>For example, if “Copper” is selected and then “Apply” is pressed, the history will only show bodies on which the commander in question has demonstrably mined copper.</p>
<p>Example:</p>
<p><b>Example System / 2 — ABBAU ×12 — copper 40 t</b></p>
<p>This means that the chronicle can be used as a personal location database: a raw material that has already been mined can be found again later.</p>

<h3>All raw materials</h3>
<p>“Commodity: All” includes all matching personal surface mining finds.</p>
<p>If several commodities are known on a body, they can be displayed together with the commander’s own quantities mined so far.</p>
<p>Example:</p>
<p><b>ABBAU ×12 — Helium-3 10 t, copper 40 t</b></p>
<p>The quantities are the respective commander’s personal mined quantities actually recorded in journal events.</p>
<p>Even with an active period, personal mining quantities remain stored totals. <b>Copper 40 t</b> does not automatically mean <b>40 t in the selected period</b>. The period requires a matching system visit, but does not restrict the displayed mined quantity to that period.</p>

<h3>Combine filters</h3>
<p>Free text, enabled From/To bounds and mining filters can be combined. A match must satisfy the configured conditions together.</p>
<p>For example:</p>
<ul>
<li>Planetary mining sites active</li>
<li>At least 20</li>
<li>My mining finds active</li>
<li>Commodity copper</li>
</ul>
<p>searches for known bodies with at least 20 planetary mining sites where the commander in question has already mined copper himself.</p>
<p>Any additional search text is also taken into account. If a period is also set, the viewed commander must actually have visited the corresponding system during that period; the copper mining itself need not have occurred during that period.</p>

<h3>Apply</h3>
<p>“Apply” runs combined filtering with all currently configured search, period and mining filters:</p>
<ul>
<li>Free text</li>
<li>From, if enabled</li>
<li>To, if enabled</li>
<li>Planetary mining sites</li>
<li>Minimum count</li>
<li>My mining finds</li>
<li>Commodity, if “My mining finds” is enabled</li>
</ul>
<p>Enter in the free-text field runs exactly the same combined filtering. Without free text and mining filters, the normal map is loaded for the checked map commanders, restricted by From/To if applicable.</p>

<h3>Reset</h3>
<p>“Reset” restores the shared filter area to its initial state:</p>
<ul>
<li>Free text is cleared.</li>
<li>From and To are disabled; the date fields show today's date again and are disabled.</li>
<li>Planetary mining sites is disabled.</li>
<li>The minimum count is set to 0.</li>
<li>My mining finds is disabled.</li>
<li>Commodity is reset to “All”.</li>
</ul>
<p>The commander selection is preserved. The normal chronicle is then reloaded for that map selection; previous search results and detail displays are reset.</p>

<h3>Commander selection</h3>
<p>The chronicle can display data from different known commanders.</p>
<p>There are two separate selection concepts:</p>
<ul>
<li><b>Map commander selection:</b> The commander checkboxes determine which commander routes appear in the normal map without a free-text/mining search. An enabled period is taken into account.</li>
<li><b>Viewed commander:</b> Personal free-text/mining searches use the viewed commander (<code>viewed_commander_id</code>), falling back to the active commander. Personal commodity lists also follow that commander.</li>
</ul>
<p>However, personal information such as your own mining finds and raw material lists are always evaluated separately for the commander actually being viewed.</p>
<p>A commander does not see any mining discoveries in his raw material selection that belong exclusively to another commander.</p>

<h3>All commanders</h3>
<p>The map/chronicle display can take multiple commanders into account.</p>
<p>“All commanders” refers to the map commander selection. The commander checkboxes do not automatically extend personal free-text/mining searches to multiple commanders.</p>
<p>This does not change the personal assignment of commander-related data. Global astronomical properties of a system or body remain shared, personal findings remain separate.</p>

<h3>Search aid / legend</h3>
<p>Additional information about the chronicle search and the meaning of the display can be accessed via “Search help / legend”.</p>
<p>Clicking a search term places it in the search field and runs it together with the period/mining filters already configured.</p>
<p>This context-related main help supplements the short operating instructions available there.</p>

<h3>Tip</h3>
<p>The chronicle is particularly suitable for finding interesting places that were discovered during a longer trip.</p>
<p>For surface mining, for example, it can answer:</p>
<p>“On which planet have I ever mined copper?”</p>
<p>or:</p>
<p>“Which of my known planets have a particularly high number of mining sites?”</p>""",
    ),
 'jump_tip': (
        'Analysis',
        """
<h2>Analysis</h2>
<p>Analysis uses your personal exploration history. System analysis evaluates an entered procedural system name; Historical data retains the previous code analysis with historical hits and Re-evaluate. Both are decision aids, not guarantees of discoveries.</p>
<h3>Comparison basis</h3>
<p>The mass code provides the baseline. Region and family refine it cautiously. Small local samples are smoothed towards the larger evidence base. Limited data means uncertainty, not a poor rating. Insufficiently investigated systems do not count as negative hits.</p>
<h3>Potential index</h3>
<p>Potential index 100 represents your personal historical average of damped exploration potential. The index is not a percentage probability. A uniform mapping scenario and damped outliers enable comparison; the median and smoothed potential are estimated credits, not guaranteed earnings.</p>
<h3>Notable finds</h3>
<p>The final system number is not rated: Plio Aip KN-B d13-201 belongs to family Plio Aip KN-B d13. BIO is informational and does not contribute to the main rating. Missing analyses do not establish zero values.</p>
<h3>System analysis</h3>
<p>Enter a system name and choose Analyse or press Enter. Use current system takes the name from the existing game state. Analysis is recalculated only on user action. Comparison basis and historical results identify their level; without local comparisons, parent-level experience is used. Evidence quality is shown separately from the recommendation.</p>
<p>The “System” field accepts a typed name. “Use current system” only fills the field; then use “Analyse” or Enter. The name is checked locally against the supported procedural naming pattern. There is no online system lookup or list for resolving ambiguous names here.</p>
<p>An empty entry, unsupported name, missing qualified comparison data or an error replaces the previous result with a message. A successful analysis shows the recommendation, potential index and local data basis. The comparison table lists mass code, region and family with system counts and data basis; historical values and known special finds appear below.</p>
<h3>Historical data</h3>
<p>Historical hits by system code. These values describe your exploration experience so far and are not a direct prediction for an individual target system. Data basis and evidence strength describe the reliability of the comparison data, based on the available sample and its distribution across sectors.</p>
<p>In “Historical data”, choose a type of find under “Target”, rather than a destination: for example an exploration target, BIO genus or BIO species. The initial evaluation runs when the view is built. After changing the target or minimum count, the previous ranking remains until you press “Re-evaluate”.</p>
<p>The number field beside the target selector sets the minimum sample per code: 1 to 50 surveyed systems, initially 3. Codes with fewer systems or no historical hit for the selected type of find are excluded from the ranking.</p>
<p>The “Historical patterns” table shows up to 50 codes with rank, past success (hit systems / surveyed systems), hit rate and strength of evidence. Ordering follows the smoothed historical assessment, not just hit rate. Both tables have a fixed order without column sorting or detail actions. No matching patterns produces an empty-results message; an evaluation error clears the ranking and shows an error message. Analysis does not calculate a travel route.</p>
""",
    ),
 'route_planner': ('Route planner',
                   """<h2>Route planner</h2>
<h3>Overview</h3>
<p>The planner calculates routes between systems through Spansh. Select “Ship route” or “Fleet Carrier / CTSVision”. A network connection is required; CMDRHelper does not control your ship or carrier.</p>

<h3>Start and destination</h3>
<p>“Start system” follows the active commander’s known current system until you enter your own start. Clearing the field restores this default behaviour. Enter the full “Destination system”; a route target taken from favourites prepares the ship route without calculating it.</p>
<p>Start and destination must resolve unambiguously before calculation. Similar names are not substituted. Unknown or ambiguous names produce a message; correct the entry.</p>

<h3>Ship route</h3>
<p>There is no ship selector here: known active-ship data prefill the technical fields. Edited values remain manual overrides. “Apply ship data” reapplies available ship data. Check the indication for complete, incomplete, stale or unknown FSD data.</p>
<p>Check “Main tank capacity”, “Current cargo”, “Base mass”, “Reserve tank capacity”, “Reserve fuel”, “FSD optimal mass”, “Maximum FSD fuel per jump”, “Fuel power”, “Fuel multiplier” and “Range boost”. Jump capability follows from these inputs; there is no single normal ship jump-range field. Cargo or equipment changes can alter achievable range.</p>

<h3>Ship options and calculation</h3>
<p>“Routing algorithm” offers optimistic, pessimistic, fuel, fuel_jumps and guided. The selection is sent to Spansh.</p>
<p>Options are “Use supercharge/neutron stars”, “Ship starts already supercharged”, “Use FSD injections”, “Exclude secondary stars” and “Refuel at every scoopable star”: neutron assistance, an already boosted start, FSD injections, secondary stars and refuelling stops. Start with “Calculate ship route with Spansh”.</p>

<h3>Carrier route</h3>
<p>“Fleet Carrier / CTSVision” plans a carrier route without selecting or controlling a particular carrier. Enter “Tritium in tank” and “Tritium in carrier storage”, at most 25,000 t combined. “Calculated carrier mass” shows 25,000 t plus those two amounts.</p>
<p>“Maximum jump range” accepts 1 to 500 ly, defaulting to 500 ly. “Calculate route with Spansh” starts calculation. The carrier calculation button is disabled while that request runs.</p>

<h3>Spansh and waiting</h3>
<p>The actual route calculation runs in the background through Spansh. Status reports the request followed by success or failure. This calculates routes, not trade prices or station information. There is no cancel button for an ongoing calculation in this view.</p>

<h3>Route results</h3>
<p>The list follows the fixed route order: number, system, jump distance and remaining distance. It is not freely sortable. Ship routes also show fuel used, fuel in tank, neutron and refuelling indications; carrier routes show tritium used.</p>
<p>Totals below show distance, jump count and fuel consumption or estimated tritium. Missing values remain “–”. Compare the plan with the actual in-game state.</p>

<h3>Progress and next target</h3>
<p>A successfully calculated ship route is adopted automatically. “Current system”, “Next destination” and “Route status” show position, next route step and state. The list remains; completed steps do not receive additional checkmarks.</p>
<p>A recognised ship jump to the next or a later route system advances progress and automatically copies the following system name to the clipboard. Repeated location reports and carrier jumps do not count as these progress jumps.</p>
<p>Loading the route does not automatically copy a name. Use “Copy next destination” initially or later while a next target exists. Only the system name is copied: no automatic pasting or control of Elite.</p>

<h3>Deviation and completion</h3>
<p>A jump outside the remaining route shows “Current system is off route”. The route and previous next target remain; there is no automatic recalculation. A later matching forward jump can resume the route. Alternatively, deliberately calculate a new route.</p>
<p>At the last route system, “Route complete” appears. “Next destination” becomes “–”, the copy button is disabled and no further name is copied. The existing clipboard content is not cleared. The results remain displayed.</p>

<h3>CTSVision export</h3>
<p>Only carrier routes offer “Export for CTSVision”. After successful calculation, choose a new CSV file. It contains the route sequence and available distance, fuel, tritium and restocking information for subsequent use in CTSVision.</p>
<p>This is a file export, not a direct connection or automatic carrier control. Existing files are not overwritten. Cancelling the file dialog creates no file; write failures are reported.</p>

<h3>Errors and advice</h3>
<p>Missing systems, incomplete or invalid ship parameters and excessive tritium are reported. Required tank, mass and FSD values must be positive; reserve fuel must not exceed reserve tank capacity.</p>
<p>No route found, network problems, excessive waiting or an unusable Spansh response also produce a message instead of an invented result. Check system names, ship data and options, then calculate again as needed.</p>

<h3>Analysis and commander context</h3>
<p>“Analysis”, with “System analysis” and “Historical data”, assesses systems and existing experience. The route planner calculates the actual journey between start and destination.</p>
<p>Defaults use the active commander and ship. Merely viewing another commander in CMDR view does not change that basis.</p>"""),
 'images': ('Pictures',
            '<h2>Pictures</h2>\n'
            '<p>The “Images” section manages the screenshots taken with Elite Dangerous. '
            'CMDRHelper can automatically recognize new recordings, process them and store them in '
            'a gallery based on the commander.</p>\n'
            '\n'
            '<h3>Source folder</h3>\n'
            '<p>The source folder is the folder where Elite Dangerous saves its screenshots in BMP '
            'format.</p>\n'
            '<p>CMDRHelper can monitor this folder for new BMP files. For automatic processing to '
            'work, the correct screenshot folder must be set.</p>\n'
            '\n'
            '<h3>Destination folder</h3>\n'
            '<p>The destination folder is the common root folder for the images processed by '
            'CMDRHelper.</p>\n'
            '<p>The user sets this root folder. CMDRHelper automatically creates the required '
            'commander-related subfolders during processing.</p>\n'
            '\n'
            '<h3>Automatic processing</h3>\n'
            '<p>If “Automatically convert” is activated and valid source and destination folders '
            'are set, CMDRHelper regularly checks the source folder for new BMP screenshots.</p>\n'
            '<p>When activated, existing BMP files are initially marked as known and are not '
            'automatically converted without being asked. The separate function for converting '
            'existing BMPs is available for this.</p>\n'
            '<p>A new file is not enqueued until it has the same non-zero size in two consecutive '
            'checks. As a result, a write operation that is still in progress is not processed '
            'immediately.</p>\n'
            '\n'
            '<h3>Image conversion</h3>\n'
            '<p>As a source, CMDRHelper processes BMP files. “PNG” or “JPG” can be selected as the '
            'target format.</p>\n'
            '<p>JPG files are saved at quality level 95. PNG files are saved in an optimized '
            'manner.</p>\n'
            '<p>By default, the original BMP file is retained. If “Delete BMP after conversion” is '
            'activated, the source BMP will only be deleted after the target image has been '
            'successfully saved.</p>\n'
            '\n'
            '<h3>Brighten image</h3>\n'
            '<p>The brightening is adjusted from 0 to 50 percent using a slider and a linked '
            'number field. The setting is saved.</p>\n'
            '<p>It is automatically applied during every conversion started thereafter - both for '
            'newly monitored and manually initiated existing BMP files. 0 percent takes over the '
            'original brightness; higher values \u200b\u200bincrease the brightness of the '
            'generated PNG or JPG image accordingly.</p>\n'
            '<p>The function is not a pure preview and is not subsequently applied to an image '
            'selected in the gallery. The changed brightness is saved in the new target file.</p>\n'
            '<p>The source BMP remains unchanged unless deletion of the BMP file is also '
            'activated. Journal, commander and exploration data are not changed.</p>\n'
            '\n'
            '<h3>Commander related storage</h3>\n'
            '<p>New screenshots are assigned to the actual playing Commander based on the journal '
            'identity present in the active live AppState.</p>\n'
            '<p>The folder structure contains commander name and Frontier ID, for example:</p>\n'
            '<p><b>EXAMPLE_F12345678/</b></p>\n'
            '<p>The FID keeps the assignment clear even with multiple commanders. This allows two '
            'commanders with the same name to be distinguished.</p>\n'
            '\n'
            '<h3>filenames</h3>\n'
            '<p>New processed images receive a name with the time of capture, commander name and - '
            'if available - the star system known when queuing.</p>\n'
            '<p>Example:</p>\n'
            '<p><b>2026-09-04_13-18-22_EXAMPLE_Sol.png</b></p>\n'
            '<p>The FID is in the commander-related folder name, not again in the image file '
            'name.</p>\n'
            '\n'
            '<h3>Secure filenames</h3>\n'
            '<p>CMDRHelper sanitizes commander and system names for use as file and folder '
            'components.</p>\n'
            '<p>Illegal control and Windows characters are replaced, whitespace is unified, '
            'problematic periods or trailing spaces are removed, and reserved Windows names such '
            'as CON or NUL are secured.</p>\n'
            '\n'
            '<h3>Recording time</h3>\n'
            '<p>For naming, CMDRHelper uses the modification time of the stable recognized BMP '
            'file. Only if this cannot be read will the current time be used.</p>\n'
            '<p>This means that the name usually depends on the source file and not on the '
            'subsequent conversion time.</p>\n'
            '\n'
            '<h3>Multiple images in the same second</h3>\n'
            '<p>If the intended file name already exists or is reserved for an ongoing conversion, '
            'CMDRHelper continuously adds it<code>_2</code>,<code>_3</code>,<code>_4</code>and so '
            'forth.</p>\n'
            '<p>This means that another screenshot with the same timestamp will not overwrite an '
            'existing target image.</p>\n'
            '\n'
            '<h3>Commander change during processing</h3>\n'
            '<p>Commander, FID and system are captured together when queuing a screenshot.</p>\n'
            '<p>A later change of commander does not change the assignment of this already waiting '
            'image. This means that a screenshot of EXAMPLE is not subsequently written to the '
            'folder of another commander.</p>\n'
            '\n'
            '<h3>gallery</h3>\n'
            '<p>The gallery shows PNG, JPG and JPEG files from the directories associated with the '
            'selected filter. New, deleted or moved images are regularly detected.</p>\n'
            '<p>The gallery filter does not change the storage location or commander assignment of '
            'the files.</p>\n'
            '\n'
            '<h3>Current commander</h3>\n'
            '<p>The Current Commander filter shows images from the folder of the commander '
            'currently viewed in the CMDR view.</p>\n'
            '<p>The commander in question only determines the gallery display. On the other hand, '
            'assigning a new live screenshot uses the journal identity active when enqueuing.</p>\n'
            '\n'
            '<h3>All commanders</h3>\n'
            '<p>The “All Commanders” filter shows the images from the valid subfolders of all '
            'known commanders together. The special folder for recordings without recognized '
            'identity is also taken into account.</p>\n'
            '<p>The files are not moved or merged.</p>\n'
            '\n'
            '<h3>Not assigned</h3>\n'
            '<p>The Unassigned filter shows supported image files located directly in the shared '
            'target root folder.</p>\n'
            '<p>In particular, older images without commander-related subfolders remain visible. '
            "CMDRHelper doesn't try to guess their affiliation after the fact.</p>\n"
            '\n'
            '<h3>Existing images</h3>\n'
            '<p>Existing images in the root folder are not automatically moved or renamed.</p>\n'
            '<p>They remain accessible via “Unassigned” as long as they are available as PNG, JPG '
            'or JPEG.</p>\n'
            '\n'
            '<h3>Select and view image</h3>\n'
            '<p>A simple click on a preview image shows the image scaled in the preview area and '
            'displays its file name.</p>\n'
            '<p>A double click opens the file with the operating system application set for '
            'images.</p>\n'
            '<p>Multiple images can be marked at the same time. When you change the window size, '
            'the preview of the current image is rescaled to fit.</p>\n'
            '\n'
            '<h3>Delete image</h3>\n'
            '<p>Marked images can be deleted using “Delete selected” or the Delete key. Before '
            'deleting, a security query appears; Without a selection, the necessary selection is '
            'first pointed out.</p>\n'
            '<p>Only the selected PNG/JPG/JPEG target files are deleted from the directories of '
            'the current gallery filter. The original BMP source file is not affected.</p>\n'
            '\n'
            '<h3>Open target folder</h3>\n'
            '<p>“Open target folder” opens the storage location in the file manager and creates '
            'the shared root folder if necessary.</p>\n'
            '<p>The “Current Commander” filter opens its existing Commander subfolder. If it does '
            'not yet exist or another filter is active, the shared root folder will be '
            'opened.</p>\n'
            '\n'
            '<h3>Security of image paths</h3>\n'
            '<p>Before deleting, CMDRHelper checks the canonical path of each file. It must be '
            'within the configured target folder and directly in a directory permitted by the '
            'current gallery filter.</p>\n'
            '<p>Symbolic links are not used as commander folders or gallery images and are not '
            'deleted via the gallery. Paths outside the target area and traversal paths are '
            'rejected.</p>\n'
            '\n'
            '<h3>If no commander was detected</h3>\n'
            '<p>If Commander and FID are missing when queuing a new recording, the file will not '
            'be put on hold and will not be assigned to a known Commander.</p>\n'
            '<p>It will be in the subfolder<b>UNKNOWN_UNKNOWN/</b>processed; the file name also '
            'used for the Commander<b>UNKNOWN</b>. This folder can be viewed through All '
            'Commanders, not through the Unallocated root folder filter.</p>\n'
            '\n'
            '<h3>Several commanders</h3>\n'
            '<p>Two separate rules apply to image management:</p>\n'
            '<ul>\n'
            '<li><b>Save new images:</b>The active journal identity with Commander and FID when '
            'enqueued determines the destination folder.</li>\n'
            '<li><b>View images:</b>The commander viewed or the selected gallery filter determines '
            'the visible images.</li>\n'
            '</ul>\n'
            '<p>This means that the gallery of another commander can be viewed while EXAMPLE is '
            'being played without new screenshots ending up in the folder of the commander in '
            'question.</p>\n'
            '\n'
            '<h3>Tip</h3>\n'
            '<p>A shared screenshot root folder is sufficient. CMDRHelper automatically separates '
            'newly processed images into Commander and FID.</p>\n'
            '<p>With "Current Commander", "All Commanders" and "Unassigned" you can switch between '
            'personal gallery, the subfolders of all commanders and older images in the root '
            'folder.</p>\n'
            '<p>Higher brightness can help with dark photos; it affects the newly created target '
            'image during the conversion.</p>'),
 'commander_view': (
        'CMDR view',
        """<h2>CMDR view</h2>
<h3>Choosing a commander</h3>
<p>The selector at the top determines whose saved data you view. ● Live active identifies the active journal commander; View only identifies another saved profile. Selecting a commander does not make them the active journal commander: the main “Missions &amp; Rewards” page still uses the commander actually playing. Personal data remains separate by FID, even for identical names. Viewing a profile does not start an online upload.</p>

<h3>Overview, wealth and MercCoins</h3>
<p>“Overview” shows name, FID, status, first and last records, visited systems, biological/geological finds, Codex entries and cartography sales, location, open missions, ship, carrier and unsold biological/cartographic data with known estimates. “Wealth” is the last saved credit balance. “Mercenary credits” displays Frontier’s reported values: “Current”, “Total spent”, “Engineering”, “Gear” and “Reported by Frontier: total earned”. These counters need not balance mathematically; CMDRHelper neither corrects them nor invents a transaction history. Unknown values remain “–”.</p>

<h3>Missions and exploration</h3>
<p>“Missions” shows the viewed commander’s saved open missions with status, mission name, destination, expiry and reward. This table is for viewing; it has no mission details or mission actions like the main page. “Exploration” shows unsold biological/cartographic data, biological finds, First Footfalls, personally and efficiently mapped bodies, and visited systems. “Chronicle” is a placeholder here; open the full chronicle from the main menu.</p>

<h3>Fleet and ship details</h3>
<p>“Ships” shows the current or last-used ship at the top, followed by this commander’s saved fleet. Click a ship card’s header to expand its details. Sort ascending or descending by use, name, type, jump range, cargo capacity, unladen mass, location or time; filter all ships or those with vehicle/fighter hangars. Green identifies the live ship; other colours group known locations. Details include identification, ShipID, location, timestamps, FSD/Guardian booster, range, mass, cargo/fuel capacities and loadout status (complete, incomplete or stale). Available module data adds hangars, shields and reinforcements, weapons and passenger cabins. Missing values remain “–”.</p>

<h3>Your own fleet carrier</h3>
<p>“Owned Fleet Carrier” shows the saved carrier’s name, callsign, CarrierID, last location and last update. These are details of your own carrier, not trade offers or mining stocks.</p>

<h3>Personal ship and carrier images</h3>
<p>Use “Choose ship image…” in expanded ship details or “Select carrier image…” for the carrier. PNG, JPG/JPEG and WEBP are supported. CMDRHelper stores its own local copy, separated by commander and ship or carrier, which survives restarts. Choosing another image replaces this copy. “Remove personal image” removes the copy and its association; the original image file is preserved. Without a personal image, an available standard preview or a placeholder appears. Image selection is disabled when the carrier cannot be identified unambiguously. Screenshots are not assigned automatically.</p>

<h3>Image viewer</h3>
<p>Double-click an available ship or carrier image to open the separate viewer using the image file rather than just the thumbnail. The image scales proportionally to the window. You can enlarge or maximise the window and close it with Esc or the window’s close button. There is no image navigation or zoom control here. The main “Images” section instead manages screenshots.</p>

<h3>Deleting a ship</h3>
<p>“Delete ship…” requires explicit confirmation; Cancel is selected by default. It removes the local ship record, including saved loadout data and the personal image copy. The current or last-used ship and an identified live ship are protected; deletion is blocked while rereading. A local deletion marker prevents old journal data from immediately bringing the ship back. A new unambiguous active-ship report in the live journal after deletion can restore it. Confirmed rereading can also clear the marker. Neither restores the deleted personal image copy.</p>

<h3>Rereading all ships</h3>
<p>“Reread all ships…” is useful for recovering fleet information from existing journals or finding locally removed ships again. After confirmation, known journal files and files in the configured journal folder are read again for the viewed commander, for fleet data only. Elite does not need to be running. Newer saved information and ships absent from the available journals are retained; recognised sales are taken into account. On success, this commander’s manual deletion markers are cleared. Existing personal images are kept; deleted ones stay deleted. Other commanders are unaffected. If reading or applying the data fails, markers remain: check journal access and try again.</p>

<h3>Local data and safety</h3>
<p>Saved information can be viewed offline and after a restart; it represents the last known state. Images, deletion and rereading affect CMDRHelper only. They do not change ships, carriers or credits in Elite Dangerous or rewrite journals.</p>""",
    ),
 'settings': ('Settings',
              '<h2>Settings</h2>\n<h3>CMDRHelper</h3>\n<p>Better update information: The Yes/No window shows installed and available versions plus up to six highlights when a summary is available. Long lists scroll while actions remain accessible.</p>\n'
              '<p>The “Settings” area determines how CMDRHelper works with Elite Dangerous, '
              'journal files, database, online services, interface and updates.</p>\n'
              '<p>Changes to credentials and paths should be made carefully. Commander-related '
              'settings are managed separately by Frontier ID if necessary.</p>\n'
              '\n'
              '<h3>journal</h3>\n'
              '<p>The journal folder is one of the most important settings. It must point to the '
              'folder where Elite Dangerous the<code>Journal*.log</code>files of the Windows or '
              'Proton profile used.</p>\n'
              '<p>The journals provide, among other things:</p>\n'
              '<ul>\n'
              '<li>Commander identity, location and travel</li>\n'
              '<li>Missions, ships and assets</li>\n'
              '<li>Exploration, cartography and BIO data</li>\n'
              '<li>Surface mining, mercenary coins and other supported states</li>\n'
              '</ul>\n'
              '\n'
              '<h3>Journal display and operation</h3>\n'
              '<p>The journal group shows the folder set, the number of journals found, the oldest '
              'and newest journals, the name of the newest file and the time of the last read '
              'entry.</p>\n'
              '<p>“Select journal folder” changes the folder. “Read now” triggers the normal '
              'update immediately.</p>\n'
              '<p>Clearly identifiable sessions are assigned using FID. New complete entries are '
              'processed incrementally; Secure reading positions prevent each journal from being '
              'unnecessarily reread in its entirety the next time it is started.</p>\n'
              '\n'
              '<h3>database</h3>\n'
              '<p>CMDRHelper permanently stores required data in a local SQLite database. This '
              'includes global system and body data as well as information explicitly assigned to '
              'a commander.</p>\n'
              '<p>The settings page shows statistics about the saved data. The database should not '
              'be edited manually while CMDRHelper is running.</p>\n'
              '\n'
              '<h3>Import journal archive</h3>\n'
              '<p>“Import journal archive” completely compares the journal files of the set '
              'journal folder with the database. Already known journal areas are taken into '
              'account based on the saved import information and are not blindly duplicated as new '
              'data.</p>\n'
              '<p>During a manually visible import, the progress, number and currently processed '
              'file are displayed. After completion, CMDRHelper reports imported or already known '
              'data or an error.</p>\n'
              '<p>The archive import also serves to relearn supported historical information from '
              'clearly assigned journals.</p>\n'
              '\n'
              '<h3>Commander related data</h3>\n'
              '<p>CMDRHelper separates personal information based on the FID and the associated '
              'internal Commander ID. These include, but are not limited to, missions, assets, '
              'MercCoins, personal exploration and online access.</p>\n'
              '<p>An unknown or ambiguous journal session may not be arbitrarily assigned to a '
              'commander.</p>\n'
              '\n'
              '<h3>Online Services</h3>\n'
              '<p>CMDRHelper supports EDSM and Inara. Both accesses are processed and saved '
              'separately for each known commander or each FID.</p>\n'
              '<p>The selection in the settings only determines whose access is currently being '
              'edited or tested. Only the commander clearly identified by the active journal '
              'session is allowed to send live.</p>\n'
              '\n'
              '<h3>Spansh station information</h3>\n'
              '<p>Under “ONLINE SERVICES”, “Add Spansh station information” enables optional station and facility information in Explorer and system views. It is off by default. Only the public system identifier is sent, not commander information; no personal API key is needed. This option does not control trade market searches.</p>\n'
              '<p>When disabled, only local journal information is shown and no new Spansh station requests are started; manual refresh is also disabled. Existing station cache data is not deleted, but is not added to the display. Enabling makes existing cached data available again without itself making a network request.</p>\n'
              '\n'
              '<h3>Automatic station requests and cache</h3>\n'
              '<p>Automatic checks occur only on a newly detected live entry of the active journal commander into another system, for example after a ship jump, carrier jump or new confirmed location report. Startup, commander changes, archive imports and simply opening Explorer or a system view do not start automatic requests.</p>\n'
              '<p>The separate station cache survives Helper restarts. A retrieval less than 7 days old is considered fresh and avoids another automatic network request. Missing or older data may be refreshed on the next qualifying live system entry. At most one automatic attempt per system per local calendar day is allowed; failures count, including across restarts. There is no continuous background refresh of all stored systems. Older usable cached data may still be displayed, including offline.</p>\n'
              '<p>This cache contains supplementary station information, not trade market prices. Spansh community market data for selling, buying and recommendations has its own temporary RAM search cache. Trade market snapshots personally observed in Elite are stored separately again: they survive a restart but are valid only while less than 24 hours old.</p>\n'
              '\n'
              '<h3>Refreshing station data manually</h3>\n'
              '<p>Open “System overview” and choose “Refresh Spansh data”. This refreshes only Spansh station information for the system shown in that window, not every stored system or trade market prices. The option must be enabled; while a request for that system is running, the action is disabled.</p>\n'
              '<p>Manual refresh can bypass the 7-day freshness period and a failed automatic attempt that day. If the system was already retrieved successfully today by the local calendar, no new request is made: “Spansh data has already been updated today.” A successful retrieval renews the station cache. On failure, existing local and usable cached information remains available and the status line reports the failure. A failed manual attempt can be retried.</p>\n'
              '\n'
              '<h3>EDSM access for</h3>\n'
              '<p>“EDSM access for:” selects the commander to be edited. The selection will show '
              '“set up” or “not set up” depending on whether a API-Key is stored.</p>\n'
              '<p>Visible are commander name, hidden API-Key field, “Use EDSM”, a connection test '
              'and its last test status.</p>\n'
              '<p>Each commander needs their own appropriate EDSM access. The selection does not '
              'switch the live uploader to this commander.</p>\n'
              '\n'
              '<h3>Use and test EDSM</h3>\n'
              '<p>“Use EDSM” enables or disables the service for the selected FID. Missing or '
              'deactivated credentials do not affect local journal processing.</p>\n'
              '<p>“Test EDSM connection” checks the access data currently visible in the form. A '
              'successful test confirms the connection, but does not change the active journal FID '
              'or live commander.</p>\n'
              '\n'
              '<h3>Inara access for</h3>\n'
              '<p>“Inara Access for:” follows the same multi-CMDR principle. Activation, Inara '
              'commander name and API-Key are saved separately for each FID.</p>\n'
              '<p>Here too, the selection shows “set up” or “not set up”. A key from one commander '
              'is not automatically used for another commander.</p>\n'
              '\n'
              '<h3>Use and test Inara</h3>\n'
              '<p>With Inara set up and enabled for the active journal FID, CMDRHelper can '
              'transmit the supported travel, location, mission and ship events. Not every journal '
              'event is sent to Inara.</p>\n'
              '<p>“Test Inara connection” checks the currently visible access data without '
              'changing the live commander.</p>\n'
              '\n'
              '<h3>Inara outbox</h3>\n'
              '<p>Supported Inara events are persistently flagged in an outbox before network '
              'transmission.</p>\n'
              '<p>Temporary errors allow these entries to be preserved for later attempts. The '
              'worker only processes the outbox of the uniquely active journal FID; Entries from '
              'other commanders are not included.</p>\n'
              '\n'
              '<h3>Online status in the header</h3>\n'
              '<p>EDSM currently shows:</p>\n'
              '<ul>\n'
              '<li><b>EDSM</b>– cannot be used or deactivated for the active FID</li>\n'
              '<li><b>EDSM is waiting</b>– set up and without ongoing transmission</li>\n'
              '<li><b>EDSM transmission</b>– the last EDSM processing run ended without errors; '
              'The tooltip states whether events were sent, journal data was processed or no new '
              'data was found</li>\n'
              '<li><b>EDSM error</b>– the last transmission status is incorrect</li>\n'
              '</ul>\n'
              '<p>There is currently no additional, separately labeled state “EDSM active” for '
              'EDSM.</p>\n'
              '<p>Inara distinguishes more precisely:</p>\n'
              '<ul>\n'
              '<li><b>INARA out</b>– disabled for the active journal FID</li>\n'
              '<li><b>INARA ready</b>– set up, but still without confirmed transmission in this '
              'session</li>\n'
              '<li><b>INARA transmission</b>– the worker is currently sending</li>\n'
              '<li><b>INARA active</b>– the last actual transfer was successfully confirmed</li>\n'
              '<li><b>INARA error</b>– the last transfer attempt failed</li>\n'
              '</ul>\n'
              '\n'
              '<h3>API-Key security</h3>\n'
              '<p>API-Keys are personal credentials. The input fields are hidden; They are stored '
              'commander-related in the application settings and not in the CMDRHelper '
              'database.</p>\n'
              '<p>Keys should not be published, shared in screenshots, or added to public '
              'repositories.</p>\n'
              '\n'
              '<h3>Images/Screenshots</h3>\n'
              '<p>Source Folder, Destination Folder, PNG/JPG, Auto Processing, BMP Delete, and '
              'Brightening from 0 to 50 percent are located exclusively in the main Images menu, '
              'not on the Settings page.</p>\n'
              '<p>The “Images” context-sensitive help describes these options in detail.</p>\n'
              '\n'
              '<h3>surface</h3>\n'
              '<p>The interface group includes the appearance, language, font, font size, and '
              'value threshold for valuable explorer bodies.</p>\n'
              '\n'
              '<h3>Dark and light mode</h3>\n'
              '<p>You can switch directly between dark and light appearance. The theme is '
              'immediately applied to the interface and existing system and history cards and '
              'saved.</p>\n'
              '\n'
              '<h3>Language</h3>\n'
              '<p>The interface offers twelve languages \u200b\u200bto choose from. “Save '
              'Language” saves the selection; A restart of CMDRHelper is then required for a '
              'completely uniform conversion of existing widgets.</p>\n'
              '\n'
              '<h3>Font and font size</h3>\n'
              '<p>Font family and font size from 7 to 24 pt can be selected and saved.</p>\n'
              '<p>Both changes will only take full effect after a restart. The interface '
              'explicitly indicates this.</p>\n'
              '\n'
              '<h3>Value threshold</h3>\n'
              '<p>The Explorer value threshold determines the estimated credit value from which '
              'bodies are highlighted as particularly valuable. The change is saved immediately '
              'and updates the corresponding Explorer display.</p>\n'
              '\n'
              '<h3>Auto-hide</h3>\n'
              '<p>“Precious Bodies”, “BIO Finds” and “Cargo” are firmly located in the left sidebar, not '
              'within the Settings page.</p>\n'
              '<p>The switches are saved and control the supported small live hint windows during '
              'exploration. The value threshold for Valuable Bodies is set in the interface '
              'settings.</p>\n'
              '<p>The Cargo window exclusively uses the Cargo snapshot confirmed for the active Journal FID. The commander viewed in CMDR View and viewed_commander_id do not affect this live window. For a Ship it shows occupied / maximum · free; if CargoCapacity is unknown, no value is estimated.</p>\n'
              '<p>“EDSM status HUD” under “auto show” is OFF by default. After entering a system, a brief message appears over Elite for about 2.5 seconds. Repeated Location events during the same stay do not produce duplicate messages; a genuine return may be checked again.</p>\n<p>“EDSM: KNOWN” means a valid EDSM match for the system. “EDSM: UNKNOWN” means a valid EDSM response without a system match. “EDSM: NO RESPONSE” means a network, HTTP or timeout error, or an invalid response, never a confirmed absence of a match. Being known to EDSM is not the same as official discovery in Elite; no first discoverer or first reporter names are promised.</p>\n<p>The message works independently of the navigation and cargo HUDs. Persistent HUD displays and quick-favorite messages are preserved. The request does not block the interface; late responses for systems already left are discarded.</p>\n\n'
              '<h3>Updates</h3>\n'
              '<p>The update group shows installed version and GitHub status. Check Now manually '
              'checks for a new scheduled CMDRHelper version; In addition, a delayed automatic '
              'check takes place after the start.</p>\n'
              '<p>If a new version is available, CMDRHelper will ask before downloading and '
              'installing. An announced database update is shown separately in this dialog.</p>\n'
              '<p>For existing installations, the usual steps are simply: install the update → start CMDRHelper. Necessary historical corrections to BIO data, visit history and DSS metadata run automatically; a database backup is created before data repairs write changes. Repairs are versioned and idempotent: successful revisions are not fully rerun at every start. Reconstruction requires Elite journals that still exist, are readable and can be unambiguously assigned to a commander. Missing sources are not invented or treated as success; pending repairs are retried at the next start. Database deletion, manual scripts and reimport are normally unnecessary.</p>\n\n'
              '<h3>Download progress</h3>\n'
              '<p>The download runs in the background. If the total size is known, CMDRHelper '
              'shows file name, received and total MiB, percent, transfer rate and estimated '
              'remaining time.</p>\n'
              '<p>Without a known total size, the progress bar works in busy mode and continues to '
              'show the amount of data received and - if determinable - the rate. Before '
              'installation, the downloaded ZIP is checked.</p>\n'
              '\n'
              '<h3>Cancel update</h3>\n'
              '<p>“Cancel download” ends an ongoing download in a controlled manner. An aborted, '
              'incomplete or invalid download will not be installed.</p>\n'
              '\n'
              '<h3>Update on Windows</h3>\n'
              '<p>On Windows, the actual update process continues regardless of the original start '
              'console. A console shutdown should therefore not unintentionally end it.</p>\n'
              '<p>If an error occurs after file changes have begun, the existing rollback backup '
              'attempts to restore the previous version.</p>\n'
              '\n'
              '<h3>Restart after update</h3>\n'
              '<p>After successful installation, the updater CMDRHelper restarts via the intended '
              'start path and briefly checks whether the new process is running stably.</p>\n'
              '<p>If a release requires a one-time database update, the journal archive will also '
              'be reevaluated after the restart.</p>\n'
              '\n'
              '<h3>Several commanders</h3>\n'
              '<p><b>Settings selection = Whose online access am I editing?</b></p>\n'
              '<p><b>Active Journal-FID = Who is allowed to broadcast live?</b></p>\n'
              '<p>Neither the online account selection nor the CMDR view is allowed to switch a '
              'live uploader to a viewed-only commander.</p>\n'
              '\n'
              '<h3>Help</h3>\n'
              '<p>"? Help" is located in the left sidebar above "auto show" and opens the help of '
              'the currently visible main menu area.</p>\n'
              '<p>In the “Settings” area, the button opens this settings help directly.</p>\n'
              '\n'
              '<h3>Tip</h3>\n'
              '<p>If you are reinstalling or have problems, check first:</p>\n'
              '<ul>\n'
              '<li>correct journal folder and recognized commander identity</li>\n'
              '<li>desired language, theme, font and explorer value threshold</li>\n'
              '<li>Online access to the correct FID</li>\n'
              '<li>In case of image problems, source and target folders in the “Images” main '
              'menu</li>\n'
              '</ul>\n'
              '<p>If there are several commanders, always pay attention to which FID the visible '
              'online access data applies to.</p>'),
    "planet_navigation": (
        'Planet navigation',
        """<h2>Planet navigation</h2>
<p>The planet navigator helps you exclusively to fly to a specific latitude/longitude on a planet or moon. You specify a coordinate target and receive the distance and direction to it.</p>
<p>It is not an interstellar route planner and does not handle system or jump navigation. You fly your ship yourself.</p>

<h3>Opening the navigator and entering a target</h3>
<p>Open “Planet navigation” in Explorer and select “Manual input…”. You can open the navigator and enter a target before a current surface position is available.</p>
<ul>
<li><b>Body:</b> Select the target planet or moon from the list or use the body already detected. You can also enter the body name yourself if it is not yet listed. If in doubt, use the full name including the system name.</li>
<li><b>Latitude:</b> Enter the target latitude between −90° and +90°.</li>
<li><b>Longitude:</b> Enter the target longitude between −180° and +180°. Pay attention to the sign of both coordinates.</li>
<li><b>Target name:</b> You can optionally enter a label to make your target easier to recognise.</li>
</ul>
<p>Use “Set target” to confirm your entry. You do not need to enter technical IDs such as BodyID and SystemAddress; they are not normal user inputs.</p>

<h3>When does the compass start?</h3>
<p>Once a target is set and Elite provides valid planetary position data for the matching body, navigation becomes active automatically. You do not need to press a separate start button.</p>
<p>If this data is still missing or belongs to a different body, the navigator waits with “Waiting for planetary coordinates …”. You can enter a target even before this data arrives.</p>

<p>Active navigation requires valid coordinates, body name, heading and planet radius from Elite for the target body. Landing is not required: suitable data can arrive during approach. Without a valid position, or on another body, the navigator waits rather than inventing a position.</p>

<h3>Save current location</h3>
<p>“★ Save current location” saves your confirmed current position, not the entered navigation target. A valid Elite position, an identified commander and a known system are required. Otherwise the action is disabled or a message appears.</p>
<p>System, body and coordinates are captured when invoked. In the favourites dialog, edit the name, category and note and optionally attach an image. Only “Save” stores the record locally for that commander; cancelling saves nothing. Later movement does not change the captured position.</p>

<h3>Use saved positions</h3>
<p>Open “★ Favorites” in Explorer. Select a saved surface location and “◎ To coordinates” to adopt its body, coordinates and name as the navigation target. This replaces any previous target; on another body the navigator waits for matching position data.</p>
<p>“Edit” changes the name, category and note. “Delete” removes the favourite only after confirmation, without removing Elite data. Favourites survive Helper restarts and are separated by commander; the current navigation target itself lasts only for the session.</p>

<h3>Planet globe: more than 380 km</h3>
<p>When the target distance is greater than 380 km, the navigator displays the planet globe.</p>
<ul>
<li>The <b>white circle</b> marks your own position.</li>
<li>The <b>small target dot</b> is orange when the target is on the visible side of the planet.</li>
<li>If the target is on the hidden far side, the target dot is shown in red.</li>
<li>Your position stays fixed in the display. The planet and target are shown relative to your position and orientation.</li>
</ul>
<p>The white arrow points forwards; the yellow arrow points in the relative target direction. The globe is a schematic orientation aid, not a geographically accurate terrain view. A red dot means the far side of the globe, not automatically “behind your ship”.</p>

<h3>Perspective grid: up to and including 380 km</h3>
<p>At a target distance of up to and including 380 km, the display automatically switches to a tilted perspective grid. If the distance increases beyond 380 km again, the globe reappears.</p>
<p>The crosslines form a <b>50-km distance grid</b>. The target dot is plotted within the grid according to distance and relative direction. The perspective helps you continue your approach; the tilt makes the spacing appear tighter towards the back. For the actual course to steer, also watch the target course and relative direction.</p>

<h3>Reading the navigation values correctly</h3>
<ul>
<li><b>Target distance:</b> The large display shows the remaining distance to the target along the idealised planetary surface.</li>
<li><b>Target coordinates:</b> The coordinate pair entered for the target, latitude first, then longitude. It stays unchanged as you move.</li>
<li><b>Current coordinates:</b> Your last confirmed coordinate pair from Elite, also latitude / longitude.</li>
<li><b>Distance along surface:</b> The same surface distance as the target distance, potentially rounded more precisely in the detail display. This is not a second route or a direct spatial distance through the air.</li>
<li><b>Bearing:</b> The absolute direction to the target from your current position, as a compass angle: 000° is north, 090° east, 180° south and 270° west.</li>
<li><b>Heading:</b> Your current orientation as provided by Elite. It shows where you are currently pointing and does not necessarily match the bearing yet.</li>
<li><b>Relative direction:</b> The difference between your orientation and the bearing, for example “23° right”, “10° left” or “Straight ahead”. At 180°, the target is behind you.</li>
<li><b>Target course:</b> The prominently displayed bearing as an absolute course you can turn to in the Elite HUD. It is not an additional turning angle.</li>
</ul>
<p>Example: With heading 051° and target course 074°, turn 23° to the right until your Elite compass shows approximately 074°. As you continue flying, the bearing and target course may change; follow the updated values.</p>
<p>At the same position as the target, at a pole or at the exact opposite point on the planet, the direction may be undefined. The navigator then shows the corresponding message instead of an invented course.</p>

<h3>Window size</h3>
<p>The navigator window can be freely resized. The globe or perspective grid adjusts proportionally to the available space. The minimum size keeps the detailed values readable; the globe stays round. The window position and size are saved.</p>

<h3>Enabling the navigation HUD</h3>
<p>On the left of the main window, tick the box under <b>auto show → Navigation HUD</b>. With valid planetary navigation, the HUD appears directly over the visible Elite window in the foreground.</p>
<p>It shows three lines:</p>
<ul>
<li>relative direction</li>
<li>target course</li>
<li>distance</li>
</ul>
<p>The HUD is transparent, click-through and focus-neutral: it does not cover the game with an opaque area, intercept mouse clicks or take input focus away from Elite when it appears automatically.</p>
<p>Without valid navigation or an unambiguous direction, it automatically becomes invisible. It is also hidden when Elite is minimised or not in the foreground. The sidebar box can remain ticked; it represents your preference for automatic display, not its current visibility.</p>
<p>The HUD is only an additional display. The normal navigator works independently of it, even when the HUD is switched off or unavailable.</p>

<h3>Setting a new target</h3>
<p>On the same body, you can reopen “Manual input…” at any time and set different coordinates. The new target replaces the previous navigation target. With matching position data, the compass updates immediately.</p>
<p>“Stop navigation” removes the current target. Simply set a new target for another approach.</p>

<p>Closing the navigator window does not end the target. An enabled navigation HUD can continue; “Stop navigation” removes the target. Leaving the matching body or losing position data pauses navigation and hides the navigation HUD.</p>

<h3>Data freshness and limitations</h3>
<p>Navigation is based on the status data provided by Elite. Updates may arrive with a delay depending on the game state. The age display in the navigator shows how much time has passed since the last confirmed status message.</p>
<p>The surface distance describes the shortest arc on an idealised sphere. It is not a terrain or road route. The navigator does not know about obstacles or terrain heights along the route; flight altitude, safe speed and obstacle avoidance remain your responsibility.</p>

<p>The current position comes from Status.json; the journal supplements body and system associations. The window and enabled navigation HUD keep updates active as needed. The display depends on available Elite data and does not guarantee accuracy in metres.</p>

<h3>Tip</h3>
<p>Before approaching, check the body name and the signs of the target coordinates. Then align with the target course on the Elite compass and watch the relative direction and distance. If the navigator is waiting, check whether Elite is already providing planetary coordinates for the target body.</p>""",
    ),
}

DIALOG_TITLE = 'Help – {area}'
CLOSE_LABEL = 'Close'


# Database update guidance; help itself remains version independent.
HELP_TOPICS["overview"] = (HELP_TOPICS["overview"][0], HELP_TOPICS["overview"][1] + '<h3>Database update required</h3><p>The database update corrects older stored relationships between stars, planets and moons. Journals are only read. Close Elite Dangerous first and make historical journals available where possible. The entire CMDRHelper database is backed up beforehand; errors roll back changes and the backup is restored if necessary. The backup is retained as a safety copy. Cancel lets you postpone the update.</p>')

HELP_TOPICS["settings"] = (HELP_TOPICS["settings"][0], HELP_TOPICS["settings"][1] + '<h3>Diagnostics and logs</h3><p>In Settings → Diagnostics and logs, open the log file or create a diagnostic package. Logs are in the installation folder under logs/ (cmdrhelper.log and up to four rotations). The ZIP contains sanitized technical logs, system_info.json and diagnose_summary.txt; no journals, database, FID/commander data, credentials, favorites or images. Personal paths are replaced with placeholders. Contents of older logs that predate privacy filtering are omitted. Choose where to save the ZIP and share it with support if needed; it is never sent automatically.</p>')

HELP_TOPICS["trade"] = (
    'Trade',
    """<h2>Trade</h2>
<h3>Trading at a glance</h3>
<p>“Sell” finds markets that buy your commodity. “Buy” finds a specific commodity to purchase. “Recommendations” shows what you can buy at your current station and sell elsewhere for a profit within your requirements.</p>

<h3>Market data and age</h3>
<p>Selling and buying automatically combine valid saved observations of your own markets with community market data through Spansh. Recommendations buy exclusively from your current observed Elite market; destinations normally come from your observations and Spansh. Community results are held temporarily in memory only.</p>
<p>All market data is a snapshot, including your own observations. Prices, supply and demand can change before arrival. Check the data age: neither availability nor profit is guaranteed.</p>
<p>If the same market is known from your own observation and the community, CMDRHelper uses the newer valid snapshot.</p>

<h3>Selecting a commodity</h3>
<p>Click “Commodity”, search by displayed name, English name or symbol, then select the commodity. German names come from the maintained German commodity catalogue. If no maintained translation exists, the English catalogue name or a readable name is shown.</p>

<h3>Sell</h3>
<p>The search uses both valid observations of your own markets and community market data. Select a commodity, “Quantity (t)” and filters, then “Find best sale”. The search finds buying offers with enough demand for the entered quantity. “Price / t” is the price you receive when selling. “Potential revenue” = price × entered quantity. The starting point is your Commander's current system. The highest selling price appears first by default.</p>

<h3>Buy</h3>
<p>The search uses both valid observations of your own markets and community market data. Select a commodity, desired quantity and filters, then “Find cheapest purchase”. The reported “Supply” must cover the entire quantity. “Price / t” is your purchase price; “Total cost” = price × desired quantity. The starting point is your current system. The lowest purchase price appears first by default. This searches for a specific commodity, not a profitable trade.</p>

<h3>Filters and result tables</h3>
<ul>
<li><b>Radius (ly):</b> maximum distance from the starting system to the destination system.</li>
<li><b>Maximum market data age / Destination data age:</b> maximum permitted age of the market data; for recommendations, this applies to the destination.</li>
<li><b>Pad size:</b> minimum required landing pad size, not an exact station size. “Medium” also permits large pads; “Any” imposes no restriction.</li>
<li><b>Include Fleet Carriers:</b> allow or exclude carriers.</li>
<li><b>Max. arrival distance (Ls):</b> maximum distance from the arrival star to the station. Leave blank for no restriction. A destination with unknown arrival distance cannot satisfy this filter.</li>
</ul>
<p>Own and community results use the same filters for data age, radius, landing pad, carriers and arrival distance. Missing information is not estimated. Destinations with unknown system distance or without evidence that they meet an enabled restriction are excluded. For observed markets, this particularly affects missing pad and arrival data; when carriers are excluded, a destination must be known not to be a carrier.</p>
<p>Click column headings to sort: numbers by numeric value, data age by actual age and pads by size class. Selling and buying show at most 100 results. “There are more results. Narrow the filters.” indicates a limited search. Available own and community results are sorted together by price before the list is limited. Because of the community service’s search limits, these are not guaranteed to be the best offers overall.</p>
<p>If the community search fails when selling or buying, matching own results remain usable. CMDRHelper marks the search as incomplete: better community offers may be missing.</p>

<h3>Your observed markets</h3>
<p>Open the commodity market in Elite while docked. While CMDRHelper is running, it captures the market automatically if it can safely match it to the current station. No manual import is needed. Opening it again updates the snapshot.</p>
<p>One current snapshot is kept per market and Commander, less than 24 hours old. Older snapshots are removed automatically; there is no permanent price history. Valid observations survive a Helper restart. “Own market data: X stations” counts the active Commander's valid observed station markets. The selected maximum market data age also applies to own results.</p>
<ul>
<li><b>✓ Captured:</b> Recommendations has a valid observed snapshot for the current station.</li>
<li><b>Open commodity market:</b> No usable observed snapshot is available for this station.</li>
<li><b>Market data outdated:</b> A previously displayed snapshot is no longer valid. Open the market again.</li>
</ul>
<p>If an old snapshot was removed before opening the view, “Open commodity market” also appears. In flight, no positive status is shown for the previous station.</p>

<h3>Recommendations</h3>
<p>You need a current station, a valid observed snapshot for it and a known current ship with reliably known free cargo space. Occupied space is deducted. With unknown or full cargo space, a new search cannot start; quantities are not invented. After departure, no new calculation uses your former location.</p>
<p>Set “Minimum profit”: 10 % includes only opportunities with at least a 10 % margin. The search checks locally available commodities. The buying station itself is not a destination. For the same destination station (same MarketID), the newer valid snapshot is used. Each commodity shows the checked destination with the highest “Potential profit” under your filters, not necessarily the best destination in the galaxy. The table starts with the highest possible profit; “Source” shows “Elite local” or “Spansh”, and “Destination data age” shows the destination snapshot's age.</p>

<h3>Only my observed markets</h3>
<p>This checkbox is available only under Recommendations. Selling and buying automatically use both sources. This checkbox limits recommendations to valid destination markets you have observed yourself. No community query is made; Spansh is not needed for this search. Radius, the additional destination age limit, minimum profit, pad, carrier and arrival filters still apply and must be satisfied using available information. Deliberately omitting the community search is not an error and does not make the search incomplete. This lets you search quickly between previously visited stations.</p>

<h3>Possible profit and quantity</h3>
<ul>
<li><b>Profit / t:</b> selling price at the destination − purchase price here. “Profit %” = profit per tonne ÷ purchase price × 100.</li>
<li><b>Quantity (t):</b> the smallest of free cargo space, supply at the buying market and demand at the destination.</li>
<li><b>Potential profit:</b> profit per tonne × possible quantity; an estimate based on the known snapshots.</li>
</ul>
<p>Example: 280 t free, 150 t supply, 20,000 t demand → 150 t possible quantity. Not every commodity can automatically fill all free cargo space.</p>

<h3>Remembered trade flight</h3>
<p>Use the checkbox to remember exactly one recommendation. Selecting another replaces it. The separate note shows the commodity, destination station, destination system and “Potential profit” at the time of selection. It is a reminder, not a continuously recalculated recommendation.</p>
<p>It survives purchases, cargo changes, departure, system changes, docking and opening a market. It disappears with “Remove” or clearing the checkbox, when a new recommendation search actually starts, when switching Commander and when quitting Helper. It is not saved across restarts.</p>
<p>“Copy system” copies only the destination system name to the clipboard. The station stays visible in the note; no route is created.</p>

<h3>Search, progress and cancellation</h3>
<p>Start searches manually. Recommendations check multiple commodities and may take longer. Once the search scope is known, the progress bar and “Checking commodities: x of y …” show the commodities actually checked. “Cancel” is available only during a cancellable search; a pending network response may delay cancellation. Switching tabs cancels the running search; the shared selling/buying filters are retained.</p>
<p>If individual community queries fail or search limits are reached, valid checked recommendations may remain visible. “Incomplete search” means the displayed results apply to the checked data, but not all commodities or destinations were fully checked. Read the message, narrow the filters when limits are reached or try again later. Manual cancellation discards the current results list.</p>

<h3>Diagnostics for problems</h3>
<p>“Copy diagnostic” copies technical information about the last finished recommendation run for troubleshooting. It contains no Commander/FID data or market prices. Diagnostics stay in memory; no permanent diagnostic file is created and nothing is sent automatically. Share the copied text with support yourself if needed.</p>

<h3>Making a trade run</h3>
<ol>
<li>Dock at a station and open the commodity market in Elite.</li>
<li>Open “Trade” → “Recommendations” and check for “Captured”.</li>
<li>Set minimum profit and filters, then choose “Find recommendations”.</li>
<li>Tick the recommendation you want to remember and buy the commodity in Elite.</li>
<li>Use “Copy system” if needed and fly to the destination; the station remains visible in the note.</li>
<li>Sell in Elite. Open the market there to update your own observations of the new market too.</li>
</ol>""",
)
