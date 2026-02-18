import sys
import logging
import structlog
from datetime import datetime, timezone

LOG_KEY_ORDER = [
    "timestamp",
    "status_code",
    "logger",
    "event",
    "method",
    "path",
    "api_version",
    "user_id",
    "ip",
    "request_id",
    "duration_ms",
    "level",
]


def order_keys(_, __, event_dict):
    ordered = {}
    # add keys in preferred order
    for key in LOG_KEY_ORDER:
        if key in event_dict:
            ordered[key] = event_dict[key]

    # add any remaining keys not in the list
    for key, value in event_dict.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def setup_logging():
    logging.basicConfig(
        format="-> %(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        logger_factory=structlog.PrintLoggerFactory(),
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.processors.format_exc_info,
            order_keys,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
    )


def get_logger(name: str = __name__):
    return structlog.get_logger(name).bind(logger=name)
