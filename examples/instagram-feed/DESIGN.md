# Instagram Precompiled Feed — DynamoDB Design

A precompiled (fan-out on write) feed design for an Instagram-like application. When a user posts, a feed entry is written to every follower's partition, making reads a single fast query.

---

## Access Patterns

| # | Access Pattern | Description |
|---|---|---|
| 1 | Get user's feed | Latest N posts from people they follow |
| 2 | Get user's active stories | Stories from the last 24 hours |
| 3 | Paginated feed | Infinite scroll with cursor-based pagination |

---

## Design Option A: Sort by Timestamp (Chronological Feed)

The simplest approach — feed items are sorted by when they were posted.

### Key Design

| Key | Format | Example |
|---|---|---|
| **PK** | `USER#<user_id>` | `USER#user_alice` |
| **SK** | `FEED#<timestamp>#<post_id>` | `FEED#2026-03-21T09:00:00Z#post_bob_001` |
| **SK** | `STORY#<timestamp>#<story_id>` | `STORY#2026-03-21T08:00:00Z#story_bob_001` |

### How It Works

**Feed query (latest 10 posts):**

```
PK = "USER#user_alice"
SK begins_with "FEED#"
ScanIndexForward = False    ← newest first
Limit = 10
```

**Stories query:**

```
PK = "USER#user_alice"
SK begins_with "STORY#"
```

Stories auto-expire via DynamoDB **TTL** on the `expires_at` attribute (set to 24 hours after post time). No cleanup code needed.

**Pagination:** Use `ExclusiveStartKey` (the `LastEvaluatedKey` from the previous page) for cursor-based infinite scroll.

### When to Use

- Purely chronological feed (Twitter-style, early Instagram)
- Simple to implement, no re-ordering needed
- Feed items are write-once, never updated for ordering

### Item Schema

| Attribute | Type | Description |
|---|---|---|
| `PK` | String | `USER#<user_id>` — the feed owner |
| `SK` | String | `FEED#<timestamp>#<post_id>` or `STORY#<timestamp>#<story_id>` |
| `author_id` | String | Who created the post |
| `author_username` | String | Display name of the author |
| `post_id` / `story_id` | String | Unique post/story identifier |
| `image_url` / `media_url` | String | Media location (S3 path) |
| `caption` | String | Post caption (feed items only) |
| `media_type` | String | `IMAGE` or `VIDEO` (stories only) |
| `like_count` | Number | Current like count |
| `comment_count` | Number | Current comment count |
| `timestamp` | String | ISO 8601 when the post was created |
| `expires_at` | Number | Unix epoch TTL — DynamoDB auto-deletes after this (stories only) |

---

## Design Option B: Sort by Rank (ML-Ranked Feed)

When an external ML service assigns a relevance rank to each feed item, bake the rank into the sort key so DynamoDB returns items in ranked order.

### Key Design

| Key | Format | Example |
|---|---|---|
| **PK** | `USER#<user_id>` | `USER#user_alice` |
| **SK** | `FEED#<zero_padded_rank>#<post_id>` | `FEED#00005#post_bob_001` |
| **SK** | `STORY#<zero_padded_rank>#<story_id>` | `STORY#00002#story_bob_001` |

Zero-pad the rank (e.g., `00005`) so that string sorting matches numeric sorting. Lower rank = higher priority.

### How It Works

**Feed query (top 10 ranked posts):**

```
PK = "USER#user_alice"
SK begins_with "FEED#"
ScanIndexForward = True     ← lowest rank (highest priority) first
Limit = 10
```

### Write Flow

1. User Bob creates a post
2. Fan-out service writes a feed entry to each follower's partition
3. ML ranking service assigns a rank to each entry
4. The feed entry is written with rank in the SK: `FEED#00005#post_bob_001`

### Re-Ranking

When the ML service recalculates ranks (e.g., periodically or on new signals), it must:

1. **Delete** the old item (old SK with old rank)
2. **Put** a new item (new SK with new rank)

This is because DynamoDB sort keys are immutable — you can't update a key in place. This is fine for a precompiled feed since the service is already doing batch writes.

```python
# Re-rank: delete old, put new
table.delete_item(Key={"PK": "USER#user_alice", "SK": "FEED#00042#post_bob_001"})
table.put_item(Item={"PK": "USER#user_alice", "SK": "FEED#00005#post_bob_001", ...})
```

### When to Use

- Algorithmic feed (modern Instagram, TikTok-style)
- ML service precomputes relevance scores
- You want DynamoDB to return items in ranked order without client-side sorting

### Trade-offs vs Timestamp Sort

| | Timestamp (Option A) | Rank (Option B) |
|---|---|---|
| **Ordering** | Chronological | ML-determined relevance |
| **Write complexity** | Write once | May need delete + re-put on re-rank |
| **Read complexity** | Simple query | Simple query |
| **Pagination** | Clean cursor-based | Cursors work but may shift on re-rank |
| **Freshness** | Always current | Depends on re-ranking frequency |

---

## No GSI Needed

Both options require **zero GSIs**. The entire design runs on the base table:

- PK groups all feed items for one user
- SK sorts them (by time or by rank)
- `begins_with("FEED#")` and `begins_with("STORY#")` separate the two item types within the same partition

This is the power of a precompiled feed — all the work happens at write time, so reads are as simple as possible.

---

## Fan-Out on Write — How Items Get Into the Feed

This table stores the **read-optimized** view. The write path looks like:

```
Bob posts a photo
    │
    ▼
Get Bob's follower list: [alice, charlie, dave, ...]
    │
    ▼
For each follower:
    Write a feed item into their partition
    PK = USER#<follower_id>
    SK = FEED#<timestamp>#<post_id>   (or FEED#<rank>#<post_id>)
```

For users with millions of followers (celebrities), this fan-out is done asynchronously via queues (SQS/SNS). The feed table itself doesn't care — it just stores the precompiled result.

---

## Getting Started

```bash
# 1. Make sure DynamoDB Local is running (see INFRA_SETUP.md in repo root)

# 2. Create the table
python examples/instagram-feed/create_table.py

# 3. Seed sample data
python examples/instagram-feed/seed_data.py

# 4. Run example queries
python examples/instagram-feed/query_examples.py
```
