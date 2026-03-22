"""Example queries demonstrating each access pattern."""

import boto3
from boto3.dynamodb.conditions import Key

ENDPOINT = "http://localhost:8000"
TABLE = "card-transactions"

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=ENDPOINT,
    region_name="us-east-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
)

table = dynamodb.Table(TABLE)


def print_items(title, items):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if not items:
        print("  (no results)")
    for item in items:
        print(
            f"  {item.get('event_type', '?'):10s} | "
            f"{item.get('timestamp', '?'):25s} | "
            f"{item.get('amount_cents', 0):>8} cents | "
            f"{item.get('status', '?'):10s} | "
            f"{item.get('merchant_name', '?')}"
        )


# -------------------------------------------------------
# Access Pattern 1: Get full lifecycle of a transaction
# -------------------------------------------------------
def get_transaction_lifecycle(txn_token: str):
    resp = table.query(
        KeyConditionExpression=Key("PK").eq(f"TXN#{txn_token}")
    )
    print_items(
        f"Lifecycle for {txn_token}",
        resp["Items"],
    )


# -------------------------------------------------------
# Access Pattern 2: Get a specific event
# -------------------------------------------------------
def get_specific_event(txn_token: str, timestamp: str, event_token: str):
    resp = table.get_item(
        Key={
            "PK": f"TXN#{txn_token}",
            "SK": f"EVENT#{timestamp}#{event_token}",
        }
    )
    item = resp.get("Item")
    print_items(
        f"Specific event: {event_token}",
        [item] if item else [],
    )


# -------------------------------------------------------
# Access Pattern 3: Transactions by merchant + time range
# -------------------------------------------------------
def get_merchant_transactions(merchant_id: str, start: str, end: str):
    resp = table.query(
        IndexName="GSI1-MerchantIndex",
        KeyConditionExpression=(
            Key("GSI1PK").eq(f"MERCHANT#{merchant_id}")
            & Key("GSI1SK").between(start, end)
        ),
    )
    print_items(
        f"Merchant {merchant_id} [{start} → {end}]",
        resp["Items"],
    )


# -------------------------------------------------------
# Access Pattern 4: Transactions by card + time range
# -------------------------------------------------------
def get_card_transactions(card_hash: str, start: str, end: str):
    resp = table.query(
        IndexName="GSI2-CardIndex",
        KeyConditionExpression=(
            Key("GSI2PK").eq(f"CARD#{card_hash}")
            & Key("GSI2SK").between(start, end)
        ),
    )
    print_items(
        f"Card {card_hash} [{start} → {end}]",
        resp["Items"],
    )


if __name__ == "__main__":
    print("\n*** ACCESS PATTERN 1: Transaction lifecycle ***")
    get_transaction_lifecycle("txn_coffee_001")
    get_transaction_lifecycle("txn_electronics_002")

    print("\n\n*** ACCESS PATTERN 2: Specific event ***")
    get_specific_event("txn_coffee_001", "2026-03-21T08:15:00Z", "evt_c001")

    print("\n\n*** ACCESS PATTERN 3: Merchant transactions ***")
    get_merchant_transactions("MERCH_COFFEE", "2026-03-01", "2026-03-31")

    print("\n\n*** ACCESS PATTERN 4: Card transactions ***")
    get_card_transactions("hash_card_alice", "2026-03-01", "2026-03-31")
    get_card_transactions("hash_card_bob", "2026-03-01", "2026-03-31")
