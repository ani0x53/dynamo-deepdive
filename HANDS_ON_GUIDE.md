# Hands-On Guide — DynamoDB Local CLI & Python

Everything you need to install, run, create tables, and query DynamoDB locally.

---

## 1. Install & Run

### Docker (one command)

```bash
docker pull amazon/dynamodb-local
docker run -d --name dynamodb-local -p 8000:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb
```

### Credentials

DynamoDB Local requires credentials but **accepts any dummy values**:

```bash
# Option A: Set env vars (per session)
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy
export AWS_DEFAULT_REGION=us-east-1

# Option B: Configure AWS CLI (persists)
aws configure
# Access Key ID:     dummy
# Secret Access Key: dummy
# Region:            us-east-1
# Output format:     json
```

> These are not real AWS credentials. DynamoDB Local doesn't validate them — it just requires they're present.

### Python (boto3)

```bash
pip install boto3
```

In Python, pass dummy creds directly:

```python
import boto3

dynamodb = boto3.client(
    "dynamodb",
    endpoint_url="http://localhost:8000",
    region_name="us-east-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
)
```

**Always pass `endpoint_url="http://localhost:8000"`** — without it, boto3 tries to connect to real AWS.

---

## 2. Create a Table

### CLI

```bash
aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name my-table \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

### Python

```python
dynamodb.create_table(
    TableName="my-table",
    AttributeDefinitions=[
        {"AttributeName": "PK", "AttributeType": "S"},
        {"AttributeName": "SK", "AttributeType": "S"},
    ],
    KeySchema=[
        {"AttributeName": "PK", "KeyType": "HASH"},
        {"AttributeName": "SK", "KeyType": "RANGE"},
    ],
    ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
)
```

### Attribute Types

| Code | Type |
|---|---|
| `S` | String |
| `N` | Number |
| `B` | Binary |

> You only define attributes used in keys (PK, SK, GSI keys). All other attributes are schemaless — just include them when you write items.

---

## 3. List & Describe Tables

```bash
# List all tables
aws dynamodb list-tables --endpoint-url http://localhost:8000

# Describe a specific table
aws dynamodb describe-table \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions
```

---

## 4. Write Items

### CLI — PutItem

```bash
aws dynamodb put-item \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions \
  --item '{
    "PK": {"S": "TXN#txn_test_99"},
    "SK": {"S": "EVENT#2026-03-21T12:00:00Z#evt_t001"},
    "event_type": {"S": "AUTH"},
    "amount_cents": {"N": "999"},
    "merchant_name": {"S": "Test Shop"},
    "GSI1PK": {"S": "MERCHANT#MERCH_TEST"},
    "GSI1SK": {"S": "2026-03-21T12:00:00Z"},
    "GSI2PK": {"S": "CARD#hash_card_test"},
    "GSI2SK": {"S": "2026-03-21T12:00:00Z"}
  }'
```

> Note: CLI uses `{"S": "value"}` / `{"N": "123"}` format (DynamoDB JSON). Numbers are passed as strings in this format.

### Python — PutItem (simpler)

```python
table = boto3.resource(
    "dynamodb",
    endpoint_url="http://localhost:8000",
    region_name="us-east-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
).Table("card-transactions")

table.put_item(Item={
    "PK": "TXN#txn_test_99",
    "SK": "EVENT#2026-03-21T12:00:00Z#evt_t001",
    "event_type": "AUTH",
    "amount_cents": 999,
    "merchant_name": "Test Shop",
    "GSI1PK": "MERCHANT#MERCH_TEST",
    "GSI1SK": "2026-03-21T12:00:00Z",
    "GSI2PK": "CARD#hash_card_test",
    "GSI2SK": "2026-03-21T12:00:00Z",
})
```

### Batch Write (multiple items)

```python
with table.batch_writer() as batch:
    batch.put_item(Item={...})
    batch.put_item(Item={...})
```

---

## 5. Query (Single Partition — Fast)

Query always requires a **partition key** (equality) and optionally a **sort key** condition.

### CLI — Get all events for a transaction

```bash
aws dynamodb query \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values '{":pk": {"S": "TXN#txn_coffee_001"}}'
```

### CLI — Query with sort key range

```bash
aws dynamodb query \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions \
  --key-condition-expression "PK = :pk AND SK BETWEEN :start AND :end" \
  --expression-attribute-values '{
    ":pk": {"S": "TXN#txn_coffee_001"},
    ":start": {"S": "EVENT#2026-03-21T00:00:00Z"},
    ":end": {"S": "EVENT#2026-03-21T23:59:59Z"}
  }'
```

### CLI — Query a GSI (merchant transactions)

```bash
aws dynamodb query \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions \
  --index-name GSI1-MerchantIndex \
  --key-condition-expression "GSI1PK = :pk AND GSI1SK BETWEEN :start AND :end" \
  --expression-attribute-values '{
    ":pk": {"S": "MERCHANT#MERCH_COFFEE"},
    ":start": {"S": "2026-03-01"},
    ":end": {"S": "2026-03-31"}
  }'
```

### CLI — Query GSI2 (card/customer transactions)

```bash
aws dynamodb query \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions \
  --index-name GSI2-CardIndex \
  --key-condition-expression "GSI2PK = :pk AND GSI2SK >= :since" \
  --expression-attribute-values '{
    ":pk": {"S": "CARD#hash_card_alice"},
    ":since": {"S": "2026-03-11T00:00:00Z"}
  }'
```

### Python — Query

```python
from boto3.dynamodb.conditions import Key

# Base table — transaction lifecycle
response = table.query(
    KeyConditionExpression=Key("PK").eq("TXN#txn_coffee_001")
)
items = response["Items"]

# GSI — merchant transactions in March
response = table.query(
    IndexName="GSI1-MerchantIndex",
    KeyConditionExpression=(
        Key("GSI1PK").eq("MERCHANT#MERCH_COFFEE")
        & Key("GSI1SK").between("2026-03-01", "2026-03-31")
    ),
)

# GSI — card transactions last 10 days
response = table.query(
    IndexName="GSI2-CardIndex",
    KeyConditionExpression=(
        Key("GSI2PK").eq("CARD#hash_card_alice")
        & Key("GSI2SK").gte("2026-03-11T00:00:00Z")
    ),
)
```

---

## 6. GetItem (Direct Lookup — Fastest)

When you know both PK and SK exactly:

```bash
aws dynamodb get-item \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions \
  --key '{
    "PK": {"S": "TXN#txn_coffee_001"},
    "SK": {"S": "EVENT#2026-03-21T08:15:00Z#evt_c001"}
  }'
```

```python
response = table.get_item(Key={
    "PK": "TXN#txn_coffee_001",
    "SK": "EVENT#2026-03-21T08:15:00Z#evt_c001",
})
item = response["Item"]
```

---

## 7. Scan (Full Table — Avoid in Production)

```bash
aws dynamodb scan \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions
```

```python
response = table.scan()
items = response["Items"]
```

> Scan reads **every item** in the table. Fine for local dev, expensive at scale. Always prefer Query.

---

## 8. Filter Expressions (Post-Query Filtering)

Filters run **after** the query reads data — they don't reduce read capacity, just trim results.

```bash
aws dynamodb query \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions \
  --key-condition-expression "PK = :pk" \
  --filter-expression "event_type = :type" \
  --expression-attribute-values '{
    ":pk": {"S": "TXN#txn_coffee_001"},
    ":type": {"S": "AUTH"}
  }'
```

```python
from boto3.dynamodb.conditions import Key, Attr

response = table.query(
    KeyConditionExpression=Key("PK").eq("TXN#txn_coffee_001"),
    FilterExpression=Attr("event_type").eq("AUTH"),
)
```

> **Important**: Filters do NOT save read costs. DynamoDB reads first, filters second. Design your keys so queries return exactly what you need.

---

## 9. Delete Items & Tables

```bash
# Delete one item
aws dynamodb delete-item \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions \
  --key '{
    "PK": {"S": "TXN#txn_test_99"},
    "SK": {"S": "EVENT#2026-03-21T12:00:00Z#evt_t001"}
  }'

# Delete entire table
aws dynamodb delete-table \
  --endpoint-url http://localhost:8000 \
  --table-name card-transactions
```

---

## 10. Useful Sort Key Operators

| Operator | Example | Use |
|---|---|---|
| `=` | `SK = "EVENT#..."` | Exact match |
| `begins_with` | `SK begins_with "EVENT#2026-03"` | Prefix match (all events in March) |
| `BETWEEN` | `SK BETWEEN :a AND :b` | Range |
| `<`, `<=`, `>`, `>=` | `SK >= "EVENT#2026-03-11"` | One-sided range (last 10 days) |

---

## Quick Reference: CLI Alias

Save typing by setting up an alias:

```bash
alias ddb='aws dynamodb --endpoint-url http://localhost:8000'

# Then use:
ddb list-tables
ddb query --table-name card-transactions --key-condition-expression "PK = :pk" ...
```
