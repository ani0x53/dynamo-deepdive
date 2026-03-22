# DynamoDB Deep Dive

A hands-on project to learn DynamoDB data modelling through real-world use cases. Each example in `examples/` is a self-contained design with its own table, seed data, queries, and design doc. Run everything locally for free using DynamoDB Local.

---

## Examples

| Example | Description | Design Doc |
|---|---|---|
| [card-transactions](./examples/card-transactions/) | Card payment lifecycle tracking with merchant and card indexes | [DESIGN.md](./examples/card-transactions/DESIGN.md) |
| [instagram-feed](./examples/instagram-feed/) | Precompiled news feed and stories with TTL, fan-out on write | [DESIGN.md](./examples/instagram-feed/DESIGN.md) |

---

## Getting Started

### 1. Set up DynamoDB Local

See [INFRA_SETUP.md](./INFRA_SETUP.md) for full instructions.

```bash
# Quick start with Docker
docker run -d --name dynamodb-local -p 8000:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb
```

### 2. Pick an example and run it

```bash
# Example: card-transactions
python examples/card-transactions/create_table.py
python examples/card-transactions/seed_data.py
python examples/card-transactions/query_examples.py

# Example: instagram-feed
python examples/instagram-feed/create_table.py
python examples/instagram-feed/seed_data.py
python examples/instagram-feed/query_examples.py
```

### 3. Read the design doc

Each example has a `DESIGN.md` that explains the key design, access patterns, and trade-offs.

---

## Project Structure

```
dynamo-deepdive/
├── README.md                  # You are here
├── INFRA_SETUP.md             # How to set up DynamoDB Local
├── HANDS_ON_GUIDE.md          # DynamoDB CLI & Python reference
└── examples/
    ├── card-transactions/     # Card payment lifecycle
    │   ├── DESIGN.md
    │   ├── create-table.sh
    │   ├── create_table.py
    │   ├── seed_data.py
    │   └── query_examples.py
    └── instagram-feed/        # Precompiled feed & stories
        ├── DESIGN.md
        ├── create_table.py
        ├── seed_data.py
        └── query_examples.py
```

---

## Prerequisites

- Docker (or Java 11+)
- AWS CLI v2
- Python 3.9+ with `boto3` (`pip install boto3`)
