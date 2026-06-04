# Perplexity Thread/History Management API

Documented from network traffic analysis of `https://www.perplexity.ai/library`.

---

## Endpoints

### 1. List Threads (History)

**Endpoint:** `POST /rest/thread/list_ask_threads`

**Query Parameters:**
- `version=2.18`
- `source=default`

**Request Body:**
```json
{
  "limit": 20,
  "offset": 0,
  "search_term": "",
  "ascending": false,
  "exclude_asi": false,
  "include_assets": true
}
```

**Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | `20` | Number of threads to fetch |
| `offset` | integer | `0` | Pagination offset |
| `search_term` | string | `""` | Filter by search term (searches titles/queries) |
| `ascending` | boolean | `false` | Sort order. `false` = newest first, `true` = oldest first |
| `exclude_asi` | boolean | `false` | Exclude ASI (computer agent) threads |
| `include_assets` | boolean | `true` | Include asset attachment info |

**Response:** Array of thread objects (see Thread Schema below).

---

### 2. List Recent Threads

**Endpoint:** `GET /rest/thread/list_recent`

**Query Parameters:**
- `exclude_asi=false` — Exclude ASI threads
- `version=2.18`
- `source=default`

**Response:** Array of simplified thread objects:

```json
[
  {
    "uuid": "...",
    "title": "Thread Title",
    "link": "/search/{uuid}",
    "variant": "thread",
    "unread": true,
    "status": "completed",
    "context_uuid": "...",
    "task_description": null,
    "answer_preview": null,
    "mode_type": 2
  }
]
```

---

### 3. List Pinned Threads

**Endpoint:** `POST /rest/thread/list_pinned_ask_threads`

**Query Parameters:**
- `version=2.18`
- `source=default`

**Request Body:**
```json
{
  "include_assets": true,
  "search_term": "",
  "send_last_entry": true,
  "thread_type_filter": "asi",
  "with_temporary_threads": false
}
```

**Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `include_assets` | boolean | `true` | Include asset info |
| `search_term` | string | `""` | Filter term |
| `send_last_entry` | boolean | `true` | Include last entry data |
| `thread_type_filter` | string | `"asi"` | Filter by thread type |
| `with_temporary_threads` | boolean | `false` | Include temporary threads |

**Response:** Array of thread objects (full schema).

---

### 4. Get Thread Details

**Endpoint:** `GET /rest/thread/{slug}`

**Query Parameters:**
- `with_parent_info=true`
- `with_schematized_response=true`
- `version=2.18`
- `source=default`
- `limit=100`
- `offset=0`
- `from_first=true`

**Response:** Full thread data with entries array.

---

### 5. Rename Thread

**Endpoint:** `POST /rest/thread/set_thread_title`

**Query Parameters:**
- `version=2.18`
- `source=default`

**Request Body:**
```json
{
  "context_uuid": "3059fb29-5916-4d19-8de5-6c58bddcc4ad",
  "title": "New Thread Title",
  "read_write_token": "f4a52279-0d0f-4b98-ae24-96f5b5ab49bb"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context_uuid` | string | Yes | Thread's context UUID |
| `title` | string | Yes | New title for the thread |
| `read_write_token` | string | No | Auth token from thread data |

**Response:** `204 No Content` on success.

---

### 6. Delete Thread(s)

**Endpoint:** `DELETE /rest/thread`

**Query Parameters:**
- `version=2.18`
- `source=default`

**Request Body:**
```json
{
  "entry_uuids": [],
  "context_uuids": [
    "5553523f-cbce-4e89-8ded-3ad4a424365e",
    "0c88a071-8a0f-4434-9270-36c1ff142fb3"
  ],
  "read_write_token": ""
}
```

**Parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `entry_uuids` | array | Specific entry UUIDs to delete (can be empty) |
| `context_uuids` | array | Thread context UUIDs to delete entirely |
| `read_write_token` | string | Optional auth token |

**Response:**
```json
{"status": "success"}
```

---

## Thread Schema

### Full Thread Object (`list_ask_threads` response)

```json
{
  "thread_number": 0,
  "last_query_datetime": "2026-05-29T12:25:17.955282",
  "mode": "copilot",
  "context_uuid": "e7ebf033-1417-4a4e-919b-bb666c83f6f8",
  "uuid": "9971c10b-7504-4172-9d90-d441399f1775",
  "frontend_uuid": "5d7ad2fd-f485-4e77-804f-334bec48bb00",
  "frontend_context_uuid": "4d03fcba-83bf-46fe-b336-5631c9c2be65",
  "slug": "9971c10b-7504-4172-9d90-d441399f1775",
  "title": "What is quantum computing?",
  "query_str": "What is quantum computing?",
  "first_answer": "{\"answer\":\"...\"}",
  "answer_preview": "Quantum computing is a type of computing...",
  "thread_access": 1,
  "has_next_page": true,
  "status": "COMPLETED",
  "display_model": "gpt54_thinking",
  "expiry_time": null,
  "source": "default",
  "source_metadata": null,
  "thread_status": "completed",
  "thread_status_summary": null,
  "thread_status_summary_enum": null,
  "locked_reason": null,
  "wake_at": null,
  "crons": null,
  "stream_created_at": null,
  "persona_id": null,
  "query_source": null,
  "dream_mode": null,
  "unread": true,
  "query_count": 1,
  "search_focus": "internet",
  "sources": ["web"],
  "featured_images": [],
  "read_write_token": "0856a626-553b-46c5-941e-675c7135ffcc",
  "total_threads": 99,
  "social_info": {
    "view_count": 0,
    "fork_count": 0,
    "like_count": 0,
    "user_likes": false
  },
  "assets": [],
  "num_assets": 0,
  "attachments": []
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `thread_number` | integer | Position in the list |
| `last_query_datetime` | ISO string | Last activity timestamp |
| `mode` | string | `"copilot"` or `"concise"` |
| `context_uuid` | string | **Primary thread identifier** (used for delete/rename) |
| `uuid` | string | Thread UUID (same as slug) |
| `slug` | string | URL-friendly identifier (used for get_thread) |
| `title` | string | Display title |
| `query_str` | string | Original search query |
| `first_answer` | string | JSON-stringified first answer |
| `answer_preview` | string | Truncated answer text |
| `status` / `thread_status` | string | `"COMPLETED"`, `"IN_PROGRESS"` |
| `display_model` | string | Model used (e.g., `gpt54_thinking`, `pplx_alpha`, `pplx_pro`) |
| `unread` | boolean | Whether user has seen this thread |
| `query_count` | integer | Number of messages in thread |
| `total_threads` | integer | Total count across all pages |
| `read_write_token` | string | Token required for some mutations |
| `social_info` | object | View/fork/like counts |
| `sources` | array | Sources used (`web`, `scholar`, etc.) |
| `search_focus` | string | Search focus (`internet`, `collections`) |
| `attachments` | array | File attachments |
| `assets` | array | Generated assets (pages, files) |

---

## Thread Status Values

| Status | Description |
|--------|-------------|
| `"COMPLETED"` | Query finished successfully |
| `"IN_PROGRESS"` | Query still running |
| `"ERROR"` | Query failed |

---

## Display Model Values (Observed)

From the HAR capture, these `display_model` values appear in thread listings:

- `turbo` — Auto mode (free)
- `pplx_pro` — Pro mode default
- `gpt54_thinking` — GPT-5.4 with thinking
- `pplx_alpha` — Deep research mode
- `grok41nonreasoning` — Grok 4.1 standard
- `claude45sonnetthinking` — Claude Sonnet 4.5 thinking
- `claude46opusthinking` — Claude Opus 4.6 thinking
- `gemini31pro_high` — Gemini 3.1 Pro thinking

---

## PPLX CLI Usage

```bash
# List threads from history
pplx threads list
pplx threads list -l 50
pplx threads list -s "quantum"
pplx threads list --ascending

# Recent threads
pplx threads recent
pplx threads recent --exclude-asi

# Pinned threads
pplx threads pinned

# Get thread details
pplx threads get <slug>

# Rename thread
pplx threads rename <context_uuid> "New Title"

# Delete thread(s)
pplx threads delete <context_uuid>
pplx threads delete uuid1,uuid2,uuid3 --force
```

---

## Python API

```python
from pplx import PerplexityClient

client = PerplexityClient()

# List all threads
threads = client.list_threads(limit=20, search_term="quantum")

# Recent sidebar-style list
recent = client.list_recent_threads(exclude_asi=False)

# Pinned/ASI tasks
pinned = client.list_pinned_threads()

# Get full thread with messages
thread = client.get_thread("thread-slug-uuid")

# Rename
client.rename_thread(
    context_uuid="thread-context-uuid",
    title="New Title",
)

# Delete multiple
client.delete_threads(
    context_uuids=["uuid1", "uuid2"]
)
```

---

## Source

Analyzed from HAR captures:
- `debug/network/library.har` — Navigating https://www.perplexity.ai/library
- `debug/network/debug.har` — General browsing session
