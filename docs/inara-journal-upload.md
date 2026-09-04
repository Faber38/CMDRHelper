# Automatic Inara journal upload

CMDRHelper queues only newly processed, newline-complete journal events while
Inara is enabled. Existing journal history is not backfilled. Disabling Inara
also disables collection; events produced while disabled are not uploaded
later.

The API key remains in local `QSettings`. The key is bound to the active
commander's journal FID when the online settings are saved. A queued event is
uploaded only when its `commander_id`, journal-derived commander name and FID
match that binding. This prevents events from one commander being sent with a
different commander's credentials.

## Supported mappings

| Journal event | Inara event |
| --- | --- |
| `FSDJump` | `addCommanderTravelFSDJump` |
| `Docked` | `addCommanderTravelDock` |
| `Touchdown` | `addCommanderTravelLand` |
| `CarrierJump` | `addCommanderTravelCarrierJump` |
| `Location` | `setCommanderTravelLocation` |
| `MissionAccepted` | `addCommanderMission` |
| `MissionCompleted` | `setCommanderMissionCompleted` |
| `MissionFailed` | `setCommanderMissionFailed` |
| `MissionAbandoned` | `setCommanderMissionAbandoned` |
| `ShipyardNew` | `addCommanderShip` |
| `ShipyardSell` | `delCommanderShip` |

`Location` never generates a synthetic dock event.

## Deliberately unsupported

Credits/assets, cargo, materials, ship-locker contents, ship loadouts,
incremental cargo changes, exobiology data, surface-mining history and unknown
Frontier events are not uploaded. CMDRHelper does not currently have a safe,
complete snapshot or an unambiguous documented mapping for these values.

## Delivery

The SQLite `inara_outbox` is written in the same transaction as the local
journal delta and its committed byte offset. Network delivery is separate.
Batches contain at most 25 events for one commander. Successful events are
marked individually; rejected events and transport failures remain retryable.
Retry delays start at 30 seconds, double up to one hour and stop automatically
after eight failed attempts. A later journal refresh/start retries eligible
entries. No confirmed event is sent again.
