"""Create the instagram-feed table on DynamoDB Local."""

import boto3

ENDPOINT = "http://localhost:8000"

dynamodb = boto3.client(
    "dynamodb",
    endpoint_url=ENDPOINT,
    region_name="us-east-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
)


def create_table():
    try:
        dynamodb.create_table(
            TableName="instagram-feed",
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5,
            },
        )
        print("Table 'instagram-feed' created successfully.")
    except dynamodb.exceptions.ResourceInUseException:
        print("Table 'instagram-feed' already exists.")

    # Enable TTL on the 'expires_at' attribute (for stories auto-expiry)
    try:
        dynamodb.update_time_to_live(
            TableName="instagram-feed",
            TimeToLiveSpecification={
                "Enabled": True,
                "AttributeName": "expires_at",
            },
        )
        print("TTL enabled on 'expires_at' attribute.")
    except Exception as e:
        print(f"TTL note: {e}")

    desc = dynamodb.describe_table(TableName="instagram-feed")
    table = desc["Table"]
    print(f"  Status: {table['TableStatus']}")
    print(f"  Keys:   {table['KeySchema']}")


if __name__ == "__main__":
    create_table()
