# Card Transactions — DynamoDB Design

A single-table design for card payment transaction lifecycle tracking. Each transaction moves through lifecycle events (AUTH → CLEARING or AUTH → REVERSAL), and we need to query by transaction, merchant, or card.

---

## Domain: Card Transaction Lifecycle

```
AUTH  ──►  CLEARING  ──►  (done)
  │
  └──►  REVERSAL   ──►  (done)
```

| Event | Description |
|---|---|
| **AUTH** | Authorization — merchant requests a hold on cardholder funds |
| **CLEARING** | Settlement — the actual money movement after auth |
| **REVERSAL** | Cancellation of a previous auth (full or partial) |

**Key identifiers:**
- `transaction-token` — stays the same across the entire lifecycle of one transaction
- `event-token` — unique to each individual lifecycle event

---

## Access Patterns

| # | Access Pattern | Key Condition | Index |
|---|---|---|---|
| 1 | Get full lifecycle of a transaction | `PK = TXN#<token>` | Base table |
| 2 | Get a specific event | `PK = TXN#<token>` AND `SK = EVENT#<ts>#<evt>` | Base table |
| 3 | Transactions by merchant + time range | `GSI1PK = MERCHANT#<id>` AND `GSI1SK BETWEEN ...` | GSI1 |
| 4 | Transactions by card + time range | `GSI2PK = CARD#<hash>` AND `GSI2SK BETWEEN ...` | GSI2 |

---

## Key Design

### Base Table

| Key | Format | Purpose |
|---|---|---|
| **PK** | `TXN#<transaction-token>` | Groups all lifecycle events for one transaction |
| **SK** | `EVENT#<timestamp>#<event-token>` | Orders events chronologically within a transaction |

### GSI1 — Merchant Index

| Key | Format |
|---|---|
| **GSI1PK** | `MERCHANT#<merchant-id>` |
| **GSI1SK** | `<timestamp>` |

### GSI2 — Card Index

| Key | Format |
|---|---|
| **GSI2PK** | `CARD#<card-hash>` |
| **GSI2SK** | `<timestamp>` |

---

## Item Schema

Each DynamoDB item represents a **single lifecycle event**:

| Attribute | Type | Description | Example |
|---|---|---|---|
| `PK` | String | Partition key | `TXN#txn_abc123` |
| `SK` | String | Sort key | `EVENT#2026-03-21T10:30:00Z#evt_001` |
| `transaction_token` | String | Unique ID for the transaction | `txn_abc123` |
| `event_token` | String | Unique ID for this lifecycle event | `evt_001` |
| `event_type` | String | `AUTH`, `CLEARING`, `REVERSAL` | `AUTH` |
| `amount_cents` | Number | Transaction amount in cents | `5000` |
| `currency` | String | ISO 4217 currency code | `USD` |
| `timestamp` | String | ISO 8601 event timestamp | `2026-03-21T10:30:00Z` |
| `rrn` | String | Retrieval Reference Number (network trace) | `430112345678` |
| `auth_code` | String | Authorization approval code | `A12345` |
| `card_last_four` | String | Last 4 digits of PAN | `4242` |
| `card_hash` | String | Tokenized/hashed card number | `hash_xyzabc` |
| `acceptor_id` | String | Card acceptor / terminal ID | `ACPT_00987` |
| `merchant_id` | String | Merchant identifier | `MERCH_555` |
| `merchant_name` | String | Human-readable merchant name | `Coffee Corner` |
| `mcc` | String | Merchant Category Code | `5411` |
| `response_code` | String | Network response code | `00` (approved) |
| `network` | String | Card network | `VISA` |
| `status` | String | Current event status | `APPROVED`, `DECLINED`, `REVERSED` |
| `GSI1PK` | String | GSI1 partition key | `MERCHANT#MERCH_555` |
| `GSI1SK` | String | GSI1 sort key | `2026-03-21T10:30:00Z` |
| `GSI2PK` | String | GSI2 partition key | `CARD#hash_xyzabc` |
| `GSI2SK` | String | GSI2 sort key | `2026-03-21T10:30:00Z` |

---

## How Do You Prevent Duplicate or Invalid Events?

What happens if the network retries and your system receives the same AUTH twice? Or a CLEARING comes in for a transaction that was already reversed? Or someone tries to reverse the same transaction twice?

DynamoDB has no traditional row locks. Instead, it provides **conditional writes** — you attach a condition to your write, and DynamoDB atomically checks the condition and applies the write. If the condition fails, the write is rejected with a `ConditionalCheckFailedException`.

### Problem 1: Duplicate AUTH (same event processed twice)

The same AUTH event is sent twice due to a network retry. Without protection, you'd insert two identical items.

**Solution:** Use `attribute_not_exists` on PutItem. Since PK + SK must be unique, and the SK contains the event token, the second write fails.

```python
table.put_item(
    Item={
        "PK": "TXN#txn_abc123",
        "SK": "EVENT#2026-03-21T10:30:00Z#evt_001",
        "event_type": "AUTH",
        "status": "APPROVED",
        ...
    },
    ConditionExpression="attribute_not_exists(PK)",
)
# First call: succeeds, item is created
# Second call: ConditionalCheckFailedException — item already exists, write rejected
```

`attribute_not_exists(PK)` means "only write this item if no item with this PK+SK exists yet." This is idempotent — you can safely retry without side effects.

### Problem 2: Double REVERSAL (reversing an already-reversed transaction)

A reversal request comes in, but the transaction was already reversed. Without protection, you'd end up with two REVERSAL events.

**Solution:** Before writing the REVERSAL event, conditionally check that the latest status is still `APPROVED` (not already `REVERSED`). This requires a summary/status item on the transaction.

Add a summary item per transaction that tracks the current state:

```
PK = TXN#txn_abc123
SK = STATUS                     ← summary item
current_status = "APPROVED"
```

Then use a **conditional update** when processing a reversal:

```python
# Step 1: Write the reversal event (idempotent with attribute_not_exists)
table.put_item(
    Item={
        "PK": "TXN#txn_abc123",
        "SK": "EVENT#2026-03-21T16:45:00Z#evt_002",
        "event_type": "REVERSAL",
        ...
    },
    ConditionExpression="attribute_not_exists(PK)",
)

# Step 2: Update the status — only if still APPROVED
table.update_item(
    Key={"PK": "TXN#txn_abc123", "SK": "STATUS"},
    UpdateExpression="SET current_status = :new",
    ConditionExpression="current_status = :expected",
    ExpressionAttributeValues={
        ":new": "REVERSED",
        ":expected": "APPROVED",
    },
)
# If already REVERSED → ConditionalCheckFailedException → reject the duplicate
```

### Problem 3: CLEARING after REVERSAL (invalid state transition)

A clearing arrives for a transaction that was already reversed. This shouldn't be allowed.

**Solution:** Same pattern — the conditional write on the STATUS item enforces valid state transitions:

```python
table.update_item(
    Key={"PK": "TXN#txn_abc123", "SK": "STATUS"},
    UpdateExpression="SET current_status = :new",
    ConditionExpression="current_status = :expected",
    ExpressionAttributeValues={
        ":new": "SETTLED",
        ":expected": "APPROVED",   # can only clear if currently approved
    },
)
# If status is REVERSED → condition fails → clearing is rejected
```

### Valid State Transitions

```
APPROVED  ──►  SETTLED     (via CLEARING)
APPROVED  ──►  REVERSED    (via REVERSAL)
```

The conditional write enforces this state machine at the database level. No application-level locks, no race conditions — DynamoDB guarantees the check-and-update is atomic within a single item.

### Why Not Traditional Locks?

DynamoDB is distributed across many nodes. Holding a pessimistic lock across partitions would kill the performance and availability that DynamoDB is designed for. Optimistic concurrency (try the write, fail if stale) fits the distributed model — you never block other readers or writers, and conflicts are resolved immediately on the conflicting write.

---

## Getting Started

```bash
# 1. Make sure DynamoDB Local is running (see INFRA_SETUP.md in repo root)

# 2. Create the table
python examples/card-transactions/create_table.py

# 3. Seed sample data
python examples/card-transactions/seed_data.py

# 4. Run example queries
python examples/card-transactions/query_examples.py
```
