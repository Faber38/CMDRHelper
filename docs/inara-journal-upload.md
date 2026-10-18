# Automatic Inara journal upload

CMDRHelper queues only newly processed, newline-complete journal events while
Inara is enabled. Existing journal history is not backfilled. Disabling Inara
also disables collection; events produced while disabled are not uploaded
later.

API keys remain in local `QSettings`. Each known journal FID has an independent
configuration below `inara/commanders/<FID>/` containing its enabled flag,
commander name, API key and optional last test result. The settings page selects
and identifies the Commander/FID being edited. A queued event is uploaded only
with the configuration whose FID exactly matches the active journal session;
the separately viewed commander never participates in that decision. Legacy
global Inara settings migrate only with explicit matching stored/live FIDs;
existing destination settings and rejected legacy settings are retained.

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
After the first failure the existing exponential delay is 60 seconds, doubling
up to one hour; after eight failures an entry is no longer retried automatically.
For HTTP 429, Retry-After accepts nonnegative integer seconds or a timezone-aware
HTTP date. Invalid/missing values retain the normal delay; longer valid server
waits take precedence without the one-hour backoff cap. A technical retry deadline
is stored in the existing last_error field (legacy plain text remains readable).
This pause survives restart and also blocks new events for the same commander.
No schema or journal-offset change is involved, and there is no new retry timer.

Each in-flight request reserves its original FID and generation until completion.
A commander switch cancels workers that have not started sending. Responses to
already sent requests may finish only their original outbox entries. Before
sending and atomically before updating, database FID, row owner, source identity,
event contents and retry state must match the captured request. Returning to the
same commander cannot start a duplicate request while that request is outstanding.

The [official Inara documentation](https://inara.cz/elite/inara-api-docs/) specifies
integer eventCustomID values echoed from requests (and ordered replies). We send
an ID for every event and pair replies strictly by ID. Missing, duplicate, foreign
or non-integer IDs reject the entire response, even if some statuses look successful.
Missing events likewise give no acknowledgement. A complete, structurally valid
response can confirm some events and reject others; only rejected events retry.
Status text and response bodies are never copied into diagnostics or error storage.

New diagnostics use allowlisted, type-checked technical fields only. The existing
privacy filter is unchanged except for dedicated Inara error-code and retry-delay
fields. A timeout or process crash after server acceptance still cannot guarantee
exactly-once delivery: an event with no recorded acknowledgement may be retried.
No historical outbox records are reset, deleted or requeued by this change.
