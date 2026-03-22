# Infrastructure Setup — DynamoDB Local

This guide walks you through setting up a **free, local DynamoDB instance** using DynamoDB Local. No AWS account or billing required.

---

## Option A: Docker (Recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Steps

```bash
# 1. Pull the official DynamoDB Local image
docker pull amazon/dynamodb-local

# 2. Run it on port 8000
docker run -d \
  --name dynamodb-local \
  -p 8000:8000 \
  amazon/dynamodb-local \
  -jar DynamoDBLocal.jar -sharedDb

# 3. Verify it's running
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

> The `-sharedDb` flag makes all clients share a single database file regardless of region/credentials.

### Stop / Start / Remove

```bash
docker stop dynamodb-local
docker start dynamodb-local
docker rm dynamodb-local        # removes the container (data lost)
```

---

## Option B: Direct JAR Download

### Prerequisites
- Java 11+ installed (`java -version`)

### Steps

```bash
# 1. Download
curl -O https://d1ni2b6xgvw0s0.cloudfront.net/v2.x/dynamodb_local_latest.tar.gz

# 2. Extract
mkdir dynamodb-local && tar -xzf dynamodb_local_latest.tar.gz -C dynamodb-local

# 3. Run
cd dynamodb-local
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb -port 8000
```

---

## Configure AWS CLI for Local

DynamoDB Local still expects AWS credentials (any dummy values work):

```bash
# Set dummy credentials (only needed once)
aws configure set aws_access_key_id dummy
aws configure set aws_secret_access_key dummy
aws configure set region us-east-1

# Always pass --endpoint-url for local operations
aws dynamodb list-tables --endpoint-url http://localhost:8000
```

Or set an alias to save typing:

```bash
alias ddb='aws dynamodb --endpoint-url http://localhost:8000'

# Now use:
ddb list-tables
```

---

## Install NoSQL Workbench (Optional, but great for visual exploration)

[Download NoSQL Workbench](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.settingup.html) — a free GUI tool from AWS. Connect it to `http://localhost:8000` to visualize tables and run queries.

---

## Create a Table

Once DynamoDB Local is running, pick an example and create its table:

```bash
pip install boto3

# Card transactions example
python examples/card-transactions/create_table.py

# Instagram feed example
python examples/instagram-feed/create_table.py
```

See each example's `DESIGN.md` for table design details.

---

## Verify Setup

```bash
# List tables
aws dynamodb list-tables --endpoint-url http://localhost:8000

# Describe a table
aws dynamodb describe-table \
  --table-name card-transactions \
  --endpoint-url http://localhost:8000
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Could not connect to the endpoint URL` | Make sure DynamoDB Local is running on port 8000 |
| `Unable to locate credentials` | Run `aws configure` with dummy values |
| `Table already exists` | Drop it first: `aws dynamodb delete-table --table-name card-transactions --endpoint-url http://localhost:8000` |
| Docker port conflict | Change the host port: `-p 8001:8000` and update endpoint URLs |
