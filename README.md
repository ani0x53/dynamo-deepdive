# DynamoDB Deep Dive — Card Transactions

A hands-on project to learn DynamoDB data modelling using a **card payment transactions** domain. Run everything locally for free using DynamoDB Local.

---

## Domain: Card Transaction Lifecycle

A card transaction moves through lifecycle events:

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
- `event-token` — unique to each individual lifecycle event (auth, clearing, reversal each get their own)

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

## Table Design: Keys & Access Patterns

### Base Table

| Key | Format | Purpose |
|---|---|---|
| **PK** | `TXN#<transaction-token>` | Groups all lifecycle events for one transaction |
| **SK** | `EVENT#<timestamp>#<event-token>` | Orders events chronologically within a transaction |

**Access pattern →** Get all events for a transaction (Query on PK)

```
PK = "TXN#txn_abc123"
```

Returns: AUTH at 10:30, CLEARING at 14:00 — in order.

---

### GSI1 — Merchant Index

| Key | Format |
|---|---|
| **GSI1PK** | `MERCHANT#<merchant-id>` |
| **GSI1SK** | `<timestamp>` |

**Access pattern →** Get all transactions for a merchant in a time range

```
GSI1PK = "MERCHANT#MERCH_555"
GSI1SK BETWEEN "2026-03-01" AND "2026-03-31"
```

---

### GSI2 — Card Index

| Key | Format |
|---|---|
| **GSI2PK** | `CARD#<card-hash>` |
| **GSI2SK** | `<timestamp>` |

**Access pattern →** Get all transactions for a specific card

```
GSI2PK = "CARD#hash_xyzabc"
GSI2SK BETWEEN "2026-03-01" AND "2026-03-31"
```

---

## Access Pattern Summary

| # | Access Pattern | Key Condition | Index |
|---|---|---|---|
| 1 | Get full lifecycle of a transaction | `PK = TXN#<token>` | Base table |
| 2 | Get a specific event | `PK = TXN#<token>` AND `SK = EVENT#<ts>#<evt>` | Base table |
| 3 | Transactions by merchant + time range | `GSI1PK = MERCHANT#<id>` AND `GSI1SK BETWEEN ...` | GSI1 |
| 4 | Transactions by card + time range | `GSI2PK = CARD#<hash>` AND `GSI2SK BETWEEN ...` | GSI2 |

---

## Getting Started

### 1. Set up DynamoDB Local

See [INFRA_SETUP.md](./INFRA_SETUP.md) for full instructions.

```bash
# Quick start with Docker
docker run -d --name dynamodb-local -p 8000:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb
```

### 2. Create the table

```bash
./scripts/create-table.sh
# or
python scripts/create_table.py
```

### 3. Load sample data

```bash
python scripts/seed_data.py
```

### 4. Run queries

```bash
python scripts/query_examples.py
```

---

## Project Structure

```
dynamo-deepdive/
├── README.md              # You are here — table design & domain context
├── INFRA_SETUP.md         # How to set up DynamoDB Local
└── scripts/
    ├── create-table.sh    # AWS CLI table creation
    ├── create_table.py    # Python (boto3) table creation
    ├── seed_data.py       # Insert sample card transactions
    └── query_examples.py  # Example queries for each access pattern
```

---

## Prerequisites

- Docker (or Java 11+)
- AWS CLI v2
- Python 3.9+ with `boto3` (`pip install boto3`)
