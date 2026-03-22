"""Example queries for the Instagram precompiled feed."""

import boto3
from boto3.dynamodb.conditions import Key

ENDPOINT = "http://localhost:8000"
TABLE = "instagram-feed"

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
            f"  @{item.get('author_username', '?'):16s} | "
            f"{item.get('timestamp', '?'):25s} | "
            f"{item.get('caption', item.get('media_type', '?'))}"
        )


# -------------------------------------------------------
# Access Pattern 1: Get user's feed (latest N posts)
# -------------------------------------------------------
def get_feed(user_id: str, limit: int = 10):
    """Fetch the latest N posts in a user's precompiled feed."""
    resp = table.query(
        KeyConditionExpression=(
            Key("PK").eq(f"USER#{user_id}")
            & Key("SK").begins_with("FEED#")
        ),
        ScanIndexForward=False,  # newest first
        Limit=limit,
    )
    print_items(f"Feed for {user_id} (last {limit})", resp["Items"])


# -------------------------------------------------------
# Access Pattern 2: Get user's active stories
# -------------------------------------------------------
def get_stories(user_id: str):
    """Fetch active stories in a user's feed.

    Stories older than 24h are auto-deleted by DynamoDB TTL,
    so whatever is here is still active.
    """
    resp = table.query(
        KeyConditionExpression=(
            Key("PK").eq(f"USER#{user_id}")
            & Key("SK").begins_with("STORY#")
        ),
        ScanIndexForward=False,
    )
    print_items(f"Stories for {user_id}", resp["Items"])


# -------------------------------------------------------
# Access Pattern 3: Paginated feed (cursor-based)
# -------------------------------------------------------
def get_feed_page(user_id: str, page_size: int = 2, last_key=None):
    """Fetch a page of the feed, using ExclusiveStartKey for pagination."""
    kwargs = {
        "KeyConditionExpression": (
            Key("PK").eq(f"USER#{user_id}")
            & Key("SK").begins_with("FEED#")
        ),
        "ScanIndexForward": False,
        "Limit": page_size,
    }
    if last_key:
        kwargs["ExclusiveStartKey"] = last_key

    resp = table.query(**kwargs)
    items = resp["Items"]
    next_key = resp.get("LastEvaluatedKey")

    print_items(
        f"Feed page for {user_id} (size={page_size})",
        items,
    )
    if next_key:
        print(f"  → more pages available (LastEvaluatedKey set)")
    else:
        print(f"  → end of feed")

    return next_key


if __name__ == "__main__":
    print("\n*** ACCESS PATTERN 1: Get user feed (latest posts) ***")
    get_feed("user_alice", limit=10)

    print("\n\n*** ACCESS PATTERN 2: Get active stories ***")
    get_stories("user_alice")

    print("\n\n*** ACCESS PATTERN 3: Paginated feed ***")
    cursor = get_feed_page("user_alice", page_size=2)
    if cursor:
        get_feed_page("user_alice", page_size=2, last_key=cursor)
