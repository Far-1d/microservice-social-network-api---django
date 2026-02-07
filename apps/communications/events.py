import json, os
import redis
from dotenv import load_dotenv
from apps.users.models import User

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", None)
redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)

class UserEventManager:
    def __init__(self):
        self.redis = redis_client

    def publish(self, event_type: str, user: User):
        data = {
            "id": str(user.id),
            "username": user.username,
            "slug": user.slug,
            "email": user.email,
        }

        self.redis.publish(
            f'user_events',
            json.dumps({
                "type": event_type,
                "data": data
            })
        )
