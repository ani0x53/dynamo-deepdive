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
