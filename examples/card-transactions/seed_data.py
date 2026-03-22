"""Seed sample card transactions into DynamoDB Local."""

import boto3

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

# Sample transactions — two full lifecycles + one declined auth

ITEMS = [
    # --- Transaction 1: Coffee purchase (AUTH → CLEARING) ---
    {
        "PK": "TXN#txn_coffee_001",
        "SK": "EVENT#2026-03-21T08:15:00Z#evt_c001",
        "transaction_token": "txn_coffee_001",
        "event_token": "evt_c001",
        "event_type": "AUTH",
        "amount_cents": 450,
        "currency": "USD",
        "timestamp": "2026-03-21T08:15:00Z",
        "rrn": "602112340001",
        "auth_code": "A10001",
        "card_last_four": "4242",
        "card_hash": "hash_card_alice",
        "acceptor_id": "ACPT_COFFEE_01",
        "merchant_id": "MERCH_COFFEE",
        "merchant_name": "Morning Brew Cafe",
        "mcc": "5812",
        "response_code": "00",
        "network": "VISA",
        "status": "APPROVED",
        "GSI1PK": "MERCHANT#MERCH_COFFEE",
        "GSI1SK": "2026-03-21T08:15:00Z",
        "GSI2PK": "CARD#hash_card_alice",
        "GSI2SK": "2026-03-21T08:15:00Z",
    },
    {
        "PK": "TXN#txn_coffee_001",
        "SK": "EVENT#2026-03-21T14:00:00Z#evt_c002",
        "transaction_token": "txn_coffee_001",
        "event_token": "evt_c002",
        "event_type": "CLEARING",
        "amount_cents": 450,
        "currency": "USD",
        "timestamp": "2026-03-21T14:00:00Z",
        "rrn": "602112340001",
        "auth_code": "A10001",
        "card_last_four": "4242",
        "card_hash": "hash_card_alice",
        "acceptor_id": "ACPT_COFFEE_01",
        "merchant_id": "MERCH_COFFEE",
        "merchant_name": "Morning Brew Cafe",
        "mcc": "5812",
        "response_code": "00",
        "network": "VISA",
        "status": "SETTLED",
        "GSI1PK": "MERCHANT#MERCH_COFFEE",
        "GSI1SK": "2026-03-21T14:00:00Z",
        "GSI2PK": "CARD#hash_card_alice",
        "GSI2SK": "2026-03-21T14:00:00Z",
    },
    # --- Transaction 2: Electronics purchase (AUTH → REVERSAL) ---
    {
        "PK": "TXN#txn_electronics_002",
        "SK": "EVENT#2026-03-20T16:30:00Z#evt_e001",
        "transaction_token": "txn_electronics_002",
        "event_token": "evt_e001",
        "event_type": "AUTH",
        "amount_cents": 129900,
        "currency": "USD",
        "timestamp": "2026-03-20T16:30:00Z",
        "rrn": "602112340002",
        "auth_code": "A20001",
        "card_last_four": "8888",
        "card_hash": "hash_card_bob",
        "acceptor_id": "ACPT_ELEC_01",
        "merchant_id": "MERCH_TECHMART",
        "merchant_name": "TechMart Electronics",
        "mcc": "5732",
        "response_code": "00",
        "network": "MASTERCARD",
        "status": "APPROVED",
        "GSI1PK": "MERCHANT#MERCH_TECHMART",
        "GSI1SK": "2026-03-20T16:30:00Z",
        "GSI2PK": "CARD#hash_card_bob",
        "GSI2SK": "2026-03-20T16:30:00Z",
    },
    {
        "PK": "TXN#txn_electronics_002",
        "SK": "EVENT#2026-03-20T16:45:00Z#evt_e002",
        "transaction_token": "txn_electronics_002",
        "event_token": "evt_e002",
        "event_type": "REVERSAL",
        "amount_cents": 129900,
        "currency": "USD",
        "timestamp": "2026-03-20T16:45:00Z",
        "rrn": "602112340002",
        "auth_code": "A20001",
        "card_last_four": "8888",
        "card_hash": "hash_card_bob",
        "acceptor_id": "ACPT_ELEC_01",
        "merchant_id": "MERCH_TECHMART",
        "merchant_name": "TechMart Electronics",
        "mcc": "5732",
        "response_code": "00",
        "network": "MASTERCARD",
        "status": "REVERSED",
        "GSI1PK": "MERCHANT#MERCH_TECHMART",
        "GSI1SK": "2026-03-20T16:45:00Z",
        "GSI2PK": "CARD#hash_card_bob",
        "GSI2SK": "2026-03-20T16:45:00Z",
    },
    # --- Transaction 3: Declined auth ---
    {
        "PK": "TXN#txn_grocery_003",
        "SK": "EVENT#2026-03-21T09:00:00Z#evt_g001",
        "transaction_token": "txn_grocery_003",
        "event_token": "evt_g001",
        "event_type": "AUTH",
        "amount_cents": 8725,
        "currency": "USD",
        "timestamp": "2026-03-21T09:00:00Z",
        "rrn": "602112340003",
        "auth_code": "",
        "card_last_four": "4242",
        "card_hash": "hash_card_alice",
        "acceptor_id": "ACPT_GROC_01",
        "merchant_id": "MERCH_FRESHMART",
        "merchant_name": "FreshMart Grocery",
        "mcc": "5411",
        "response_code": "51",
        "network": "VISA",
        "status": "DECLINED",
        "GSI1PK": "MERCHANT#MERCH_FRESHMART",
        "GSI1SK": "2026-03-21T09:00:00Z",
        "GSI2PK": "CARD#hash_card_alice",
        "GSI2SK": "2026-03-21T09:00:00Z",
    },
    # --- Transaction 4: Another coffee shop, same merchant, different card ---
    {
        "PK": "TXN#txn_coffee_004",
        "SK": "EVENT#2026-03-21T10:00:00Z#evt_c004",
        "transaction_token": "txn_coffee_004",
        "event_token": "evt_c004",
        "event_type": "AUTH",
        "amount_cents": 625,
        "currency": "USD",
        "timestamp": "2026-03-21T10:00:00Z",
        "rrn": "602112340004",
        "auth_code": "A40001",
        "card_last_four": "8888",
        "card_hash": "hash_card_bob",
        "acceptor_id": "ACPT_COFFEE_01",
        "merchant_id": "MERCH_COFFEE",
        "merchant_name": "Morning Brew Cafe",
        "mcc": "5812",
        "response_code": "00",
        "network": "MASTERCARD",
        "status": "APPROVED",
        "GSI1PK": "MERCHANT#MERCH_COFFEE",
        "GSI1SK": "2026-03-21T10:00:00Z",
        "GSI2PK": "CARD#hash_card_bob",
        "GSI2SK": "2026-03-21T10:00:00Z",
    },
]


def seed():
    with table.batch_writer() as batch:
        for item in ITEMS:
            batch.put_item(Item=item)
    print(f"Seeded {len(ITEMS)} items into '{TABLE}'.")


if __name__ == "__main__":
    seed()
