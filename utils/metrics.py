from prometheus_client import (
    Counter, 
    Histogram, 
    Gauge,
)


new_users_total = Counter(
    "new_users_total",
    "Total number of new users registrations",
)

users_deleted_total = Counter(
    "users_deleted_total",
    "Total number of users deletions",
)

password_reset_requests_total = Counter(
    "password_reset_requests_total",
    "Total number of password reset requests",
)

login_attempts_total = Counter(
    "login_attempts_total",
    "Total number of login attempts",
    ["status"]  # success or fail
)

interactions_total = Counter(
    "interactions_total",
    "Total number of user interactions with each other",
)

follow_request_total = Gauge(
    "follow_request_total",
    "Total number of follow requests",
)

follow_total = Gauge(
    "follow_total",
    "Total number of follow relationships",
)

blocks_total = Gauge(
    "blocks_total",
    "Total number of active block",
)

user_event_rate = Histogram(
    'user_event_rate',
    "user events per time",
    ['timestamp'],
)

api_requests_by_version = Counter(
    'api_requests_by_version',
    "requests by api version",
    ['version'],
)


response_time_ms = Histogram(
    "response_time_ms",
    "Average response time by endpoint",
    ['endpoint'],
    unit='ms',
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
)

response_codes_total = Counter(
    "response_codes_total",
    "number of response codes",
    ['status_code'],
)

