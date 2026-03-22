#!/usr/bin/env bash
# Creates the card-transactions table on DynamoDB Local

ENDPOINT="http://localhost:8000"

echo "Creating card-transactions table..."

aws dynamodb create-table \
  --endpoint-url "$ENDPOINT" \
  --table-name card-transactions \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S \
    AttributeName=GSI1SK,AttributeType=S \
    AttributeName=GSI2PK,AttributeType=S \
    AttributeName=GSI2SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --global-secondary-indexes \
    '[
      {
        "IndexName": "GSI1-MerchantIndex",
        "KeySchema": [
          {"AttributeName": "GSI1PK", "KeyType": "HASH"},
          {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
        ],
        "Projection": {"ProjectionType": "ALL"},
        "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
      },
      {
        "IndexName": "GSI2-CardIndex",
        "KeySchema": [
          {"AttributeName": "GSI2PK", "KeyType": "HASH"},
          {"AttributeName": "GSI2SK", "KeyType": "RANGE"}
        ],
        "Projection": {"ProjectionType": "ALL"},
        "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
      }
    ]' \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

echo ""
echo "Verifying..."
aws dynamodb describe-table \
  --endpoint-url "$ENDPOINT" \
  --table-name card-transactions \
  --query 'Table.{Name:TableName,Status:TableStatus,ItemCount:ItemCount,Keys:KeySchema,GSIs:GlobalSecondaryIndexes[*].IndexName}' \
  --output table

echo ""
echo "Done! Table 'card-transactions' created."
