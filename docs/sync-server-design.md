# OpsCollector-CLI Centralized Sync Server — Design & API Contract

> Single source of truth for the server-side implementation of the OpsCollector-CLI sync plane.
> Audience: backend engineering, platform ops, QA/release. Tone: document-driven, stage-gated (PRD → Architecture → UI-UX → Release Candidate).

---

## 1. Overview

### Purpose
The sync server is a single, always-reachable consolidation point for operational data produced by offline-first OpsCollector-CLI clients. It enables multiple field/remote operators using `opscollector-cli` to push local changes and pull global updates without requiring continuous connectivity.

### Offline-first guarantees
- **Client queue-first**: clients never block on network state. Every local create/update/delete is persisted immediately to the local SQLite store and mirrored into `sync_log`.
- **Lazy sync**: `sync_once` runs only when the server is reachable. If unreachable, the client continues working offline and retries later.
- **Late / out-of-order arrival**: the server accepts push batches in any order and does not require monotonic `version` across clients. It stores all change records and applies deterministic conflict rules.

### Responsibility split
| Layer | Responsibility |
|---|---|
| Client | Local persistence, change capture, resilient `push`/`pull`, retry/back-off, offline UX. |
| Server | Authoritative central store, schema validation, conflict resolution, schema-version gating, audit/change-feed, auth. |

---

## 2. Architecture

### Recommended stack
- **API**: FastAPI + Pydantic v2.
- **ORM / data layer**: SQLAlchemy 2.x with asyncpg.
- **Database**: **PostgreSQL**, recommended from day one for multi-client operational data.

### DB choice rationale
- SQLite is acceptable for single-device/personal pilots, but it has limited concurrency, no native row-level locking, and risky behavior under WAL + multiple writers from sync processes. OpsCollector-CLI already runs locally on SQLite; making the *server* SQLite doubles down on the wrong boundary for multi-client write consolidation.
- PostgreSQL gives us serializable-ish safety via row locks, rich JSON handling, and a single authoritative source for client-generated primary keys. This is the default recommendation until a user explicitly constrains hosting to SQLite.

### Deployment shape
- Single host or single primary/replica pair behind an internal load balancer.
- Stateless API workers: no in-memory session; all state in PostgreSQL.
- TLS termination at the edge/proxy; API expects HTTPS only.
- No client affinity required.

---

## 3. Data model on server

Server tables mirror client entities and add ownership fields. All server `updated_at` values are server-side.

### Core table pattern

```text
<entity>
  id            PK/string — client-generated local row id (stringified int/UUID as supplied by client)
  client_id     str        — originating client
  payload       JSONB      — full entity payload from client
  created_at    datetime   — server ingest timestamp
  updated_at    datetime   — server ingest timestamp
  version       int        — monotonically increasing per row for LWW
  is_conflict   bool       — flagged when merge produced an unresolved divergence
  schema_version int       — client-reported schema version at time of last change
  deleted       bool       — soft delete flag; pulls exclude by default
```

Entities: `objective`, `key_result`, `pic`, `department`, `status`, `bau`, `incident`, `change`, `evidence`.

### Sync / change-feed tables

```text
sync_log
  id             PK/serial
  entity         str
  row_id         str
  op             str          # create | update | delete
  client_id      str
  version        int
  payload        JSONB
  schema_version int
  received_at    datetime     # server receive time
  processed      bool
  error_message  str | null
```

---

## 4. API contract

Base URL: `https://sync.example.com/api/v1`
Auth: `Authorization: Bearer <api_token>` on every endpoint except `/health`.

### 4.1 POST /api/v1/push
Upload a batch of local changes for server application.

Request JSON:
```json
{
  "changes": [
    {
      "entity": "bau",
      "row_id": "17",
      "op": "update",
      "client_id": "c3b1e2f4-0000-0000-0000-000000000001",
      "version": 3,
      "payload": { "id": 17, "name": "BAU-114", "status": "In Progress", "owner_id": 5 },
      "base_schema_version": 2
    }
  ]
}
```

Success 200:
```json
{
  "accepted": ["bau:17"],
  "rejected": [],
  "processed_at": "2026-07-09T12:34:56Z"
}
```

Partial accept 207 / 200 with `rejected` populated:
```json
{
  "accepted": [],
  "rejected": [
    { "entity": "bau", "row_id": "17", "reason": "schema_version 1 < server minimum 2" }
  ],
  "processed_at": "2026-07-09T12:34:56Z"
}
```

Error responses:
- `401` missing/invalid token.
- `403` token not associated with any registered client.
- `409` for recoverable merge conflicts that were not auto-resolved; returns `{ "accepted": [], "rejected": [...], "conflicts": [...] }`.
- `422` malformed payload / schema validation failure.
- `503` database unreachable; client MUST treat as transient and retry later.

Idempotency: retries repeatable because client submits explicit `entity + row_id + version`. Server ignores exact duplicate `(client_id, entity, row_id, version, op)` pairs already marked `processed=true`.

### 4.2 GET /api/v1/pull
Return changes after a client-supplied watermark.

Query params:
- `since` — ISO 8601 datetime; required for delta pulls; omitted = full feed.
- `schema_version` — last known schema version; required for schema gate.

Success 200:
```json
{
  "schema_version": 3,
  "min_required_schema_version": 2,
  "changes": [
    {
      "id": "bau:17",
      "entity": "bau",
      "row_id": "17",
      "op": "update",
      "payload": { "id": 17, "name": "BAU-114", "status": "Closed" },
      "received_at": "2026-07-09T12:34:56Z"
    }
  ],
  "cutoff": "2026-07-09T12:30:00Z"
}
```

Schema-version gate error `426/409`:
```json
{ "error": "schema_too_old", "min_required_schema_version": 2, "documentation_url": "https://..." }
```

Error responses:
- `401` missing/invalid token.
- `503` database unreachable.

### 4.3 GET /api/v1/health
```json
{ "status": "ok", "db": "ok", "timestamp": "2026-07-09T12:35:00Z" }
```

### 4.4 POST /api/v1/register
Create/confirm client identity and token.

Request body (optional on first call):
```json
{ "client_id": "c3b1e2f4-0000-0000-0000-000000000001", "display_name": "Field iPad #3" }
```

Success 200/201:
```json
{ "client_id": "c3b1e2f4-0000-0000-0000-000000000001", "api_token": "ocs_...", "created": true }
```

Token stored as SHA-256(`api_token`) server-side; plaintext never persisted. On repeat registration, returns existing token if `client_id` matches; otherwise error.

### 4.5 Read endpoints for bootstrap/resync
- `GET /api/v1/entities/{entity}?limit=&offset=` — list latest central rows.
- `GET /api/v1/entities/{entity}/{row_id}` — single row by client/id combination.

---

## 5. Conflict resolution

### Policy
Start with **last-write-wins (LWW)** by `updated_at`. The most recent server-ingested `updated_at` for a given `(entity, row_id)` wins. The losing side is recorded but not deleted.

### Divergence handling
When two clients edit the same row offline and both push diverging versions for the same server-side row:
1. Server detects that both arrive with the same base identity but different `payload`.
2. If payloads are identical after parsing, both accepted, last ingested time wins.
3. If payloads diverge:
   - Keep the LWW version as the live row.
   - Insert the overwritten payload into a **conflict_events** table with `status=open`, assign to a human reviewer.
4. Pull response may include a `conflict_id` for the losing client so UI/sync_client can surface a warning.

### Version vector extension (future)
- Add `version_vector = {"client_id": version, ...}` payload field for multi-master tracking.
- Detect true concurrent edits even when server timestamps are similar.
- Resolve without human review only when vectors are causally unrelated and fields do not overlap.

---

## 6. Schema versioning & migration gate

- `schema_version` is a positive integer, incremented only by server-side migration.
- Each push batch includes `base_schema_version`. Each server entity row stores the highest schema version seen for that payload.
- Server maintains `server_schema_version` in settings/config table.
- `/pull` rejects clients whose supplied `schema_version < server_schema_version - allowed_drift` with `426` and the required value. Default `allowed_drift = 0`.
- Migration discipline:
  - Backward-compatible additions only: new optional fields, new tables.
  - Renames = new field + deprecated old field + server-side mapping.
  - Deprecations: mark field deprecated in docs; remove only after one full release cycle flagged to clients.

---

## 7. Auth & security

- **Bearer token**: `Authorization: Bearer <api_token>`.
- **TLS required**: enforce HTTPS including internal calls; no HTTP endpoint for API traffic.
- **Rate limiting**: per-client token bucket; reject with `429` on exhaustion.
- **Data model**: shared dataset. All registered clients read and write the same global operational dataset unless a future PRD explicitly requires per-client partitioning.
- **Sensitive treatment**: tokens treated as credentials; logged only in masked form.

---

## 8. Sync protocol flow

1. **Push pending**: client selects unsynced rows from local `sync_log` and POST `/api/v1/push`.
2. **Server apply**: validates auth + schema_version + payload schema; writes to entity tables + `sync_log`; returns accepted/rejected.
3. **Mark local**: if server returned 200, client marks `synced=1`, updates `last_push`.
4. **Pull changes**: client GET `/api/v1/pull?since=<last_pull>&schema_version=<...>`.
5. **Upsert local**: for every returned change, upsert into local DB; mark `last_pull = now`.
6. **Repeat**: on timer or manual trigger.

### Offline behavior
Client never raises on network failure. Failed push/pull returns `None`/`False`; client keeps local rows queued and retries later with exponential back-off.

### Idempotency & retry
Push is idempotent on `(client_id, entity, row_id, version, op)`. Retries are safe because the server deduplicates processed log entries before applying.

---

## 9. Resolved decisions (2026-07-09, user: Pak Reza)

| # | Decision area | Resolution |
|---|---|---|
| 1 | Server DB | **PostgreSQL** (not SQLite hosting) |
| 2 | Data model | **Shared dataset** — all registered clients read/write one global operational pool |
| 3 | Token lifecycle | **Rotation** policy (revoke + scheduled rotation); rotation mechanics TBD at impl |
| 4 | Auto-sync interval | **3 minutes** default (manual trigger also available) |
| 5 | Conflict resolution owner | **admin / manager**, surfaced via **CLI** (not web UI) |
| 6 | schema_version owner | **Coordinator (Evelyn)** owns orchestrating bumps |

All prior open questions are resolved; implementation tasks may proceed against this contract.

--- 

Document version: 0.1 — pending PM/backend sign-off before implementation.
