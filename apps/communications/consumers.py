from kafka import KafkaConsumer, KafkaProducer
import json, os
from apps.users.models import User

import logging
logging.getLogger('kafka').setLevel(logging.ERROR)

def run_consumer():
    consumer = KafkaConsumer(
        bootstrap_servers=os.environ.get('KAFKA_URL', ''),
        key_deserializer=lambda k: str(k).encode(),
        value_deserializer=lambda x: json.loads(x.decode()),
    )
    consumer.subscribe(['request-followers', 'request-blocked-users'])

    producer = Producer()

    for message in consumer:
        topic = str(message.topic)
        print("--------- new message topic: ", topic)
        if topic == 'request-followers':
            producer.handle_followers_request(payload=message.value)
        
        elif topic == 'request-blocked-users':
            producer.handle_blocked_users_request(payload=message.value)
        
class Producer:
    def __init__(self):
        self.response_producer = KafkaProducer(
            bootstrap_servers=os.environ.get('KAFKA_URL', None),
            key_serializer=lambda k: str(k).encode('utf-8'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='gzip'
        )

    def handle_followers_request(self, payload: dict):
        correlation_id = payload["request_id"]
        user_id = payload["user_id"]
        print('message correlation and user_id : ', correlation_id, " ---------- ", user_id)
        try:
            user = User.regular_objects.get(id=user_id)
        except User.DoesNotExist:
            print('user not found !!!')
            self.response_producer.send(
            'response-followers',
            key=correlation_id,
            value={
                "request_id": correlation_id,
                "user_id": user_id,
                "status": "404"
            }
        )

        # only following user and staff can view private profiles followers
        followers = user.followers.all()

        follower_ids = [str(fr.id) for fr in followers]
        print('----- followers are: ', follower_ids)
        self.response_producer.send(
            'response-followers',
            key=correlation_id,
            value={
                "request_id": correlation_id,
                "user_id": user_id,
                "followers": follower_ids,
                "status": "200"
            }
        )

    def handle_blocked_users_request(self, payload: dict):
        correlation_id = payload["request_id"]
        user_id = payload["user_id"]

        try:
            user = User.regular_objects.get(id=user_id)
        except User.DoesNotExist:
            self.response_producer.send(
            'response-blocked-users',
            key=correlation_id,
            value={
                "request_id": correlation_id,
                "user_id": user_id,
                "status": "404"
            }
        )

        blocked_users = user.blocked_users.all()

        blocked_user_ids = [bu.id for bu in blocked_users]

        self.response_producer.send(
            'response-blocked-users',
            key=correlation_id,
            value={
                "request_id": correlation_id,
                "user_id": user_id,
                "blocked_users": blocked_user_ids,
                "status": "200"
            }
        )