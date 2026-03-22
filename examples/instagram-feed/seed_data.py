"""Seed sample Instagram feed and story data into DynamoDB Local.

Scenario:
  - Alice (user_alice) follows Bob and Charlie.
  - When Bob or Charlie post, a precompiled feed entry is written
    into Alice's feed partition.
  - Bob and Charlie also post stories (24h TTL).
"""

import boto3
from decimal import Decimal

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

# TTL: 24 hours from post time (epoch seconds)
# 2026-03-21T08:00:00Z = 1774252800
STORY_TTL_24H = 1774252800 + 86400  # expires 2026-03-22T08:00:00Z

ITEMS = [
    # ---- Alice's precompiled feed (posts from people she follows) ----
    {
        "PK": "USER#user_alice",
        "SK": "FEED#2026-03-21T09:00:00Z#post_bob_001",
        "author_id": "user_bob",
        "author_username": "bob_photos",
        "post_id": "post_bob_001",
        "image_url": "s3://insta-media/bob/sunset.jpg",
        "caption": "Amazing sunset at the beach!",
        "like_count": Decimal("142"),
        "comment_count": Decimal("12"),
        "timestamp": "2026-03-21T09:00:00Z",
    },
    {
        "PK": "USER#user_alice",
        "SK": "FEED#2026-03-21T10:30:00Z#post_charlie_001",
        "author_id": "user_charlie",
        "author_username": "charlie_eats",
        "post_id": "post_charlie_001",
        "image_url": "s3://insta-media/charlie/ramen.jpg",
        "caption": "Best ramen in town",
        "like_count": Decimal("89"),
        "comment_count": Decimal("7"),
        "timestamp": "2026-03-21T10:30:00Z",
    },
    {
        "PK": "USER#user_alice",
        "SK": "FEED#2026-03-21T12:00:00Z#post_bob_002",
        "author_id": "user_bob",
        "author_username": "bob_photos",
        "post_id": "post_bob_002",
        "image_url": "s3://insta-media/bob/mountains.jpg",
        "caption": "Hiking vibes",
        "like_count": Decimal("230"),
        "comment_count": Decimal("19"),
        "timestamp": "2026-03-21T12:00:00Z",
    },
    {
        "PK": "USER#user_alice",
        "SK": "FEED#2026-03-21T14:15:00Z#post_charlie_002",
        "author_id": "user_charlie",
        "author_username": "charlie_eats",
        "post_id": "post_charlie_002",
        "image_url": "s3://insta-media/charlie/coffee.jpg",
        "caption": "Afternoon espresso",
        "like_count": Decimal("56"),
        "comment_count": Decimal("3"),
        "timestamp": "2026-03-21T14:15:00Z",
    },

    # ---- Alice's stories feed (stories from people she follows) ----
    {
        "PK": "USER#user_alice",
        "SK": "STORY#2026-03-21T08:00:00Z#story_bob_001",
        "author_id": "user_bob",
        "author_username": "bob_photos",
        "story_id": "story_bob_001",
        "media_url": "s3://insta-media/bob/morning_story.jpg",
        "media_type": "IMAGE",
        "timestamp": "2026-03-21T08:00:00Z",
        "expires_at": STORY_TTL_24H,
    },
    {
        "PK": "USER#user_alice",
        "SK": "STORY#2026-03-21T11:00:00Z#story_charlie_001",
        "author_id": "user_charlie",
        "author_username": "charlie_eats",
        "story_id": "story_charlie_001",
        "media_url": "s3://insta-media/charlie/cooking_story.mp4",
        "media_type": "VIDEO",
        "timestamp": "2026-03-21T11:00:00Z",
        "expires_at": STORY_TTL_24H,
    },

    # ---- Bob's precompiled feed (posts from people he follows) ----
    {
        "PK": "USER#user_bob",
        "SK": "FEED#2026-03-21T10:30:00Z#post_charlie_001",
        "author_id": "user_charlie",
        "author_username": "charlie_eats",
        "post_id": "post_charlie_001",
        "image_url": "s3://insta-media/charlie/ramen.jpg",
        "caption": "Best ramen in town",
        "like_count": Decimal("89"),
        "comment_count": Decimal("7"),
        "timestamp": "2026-03-21T10:30:00Z",
    },
]


def seed():
    with table.batch_writer() as batch:
        for item in ITEMS:
            batch.put_item(Item=item)
    print(f"Seeded {len(ITEMS)} items into '{TABLE}'.")


if __name__ == "__main__":
    seed()
