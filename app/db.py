import logging

from neo4j import GraphDatabase
from neo4j.exceptions import (
    ServiceUnavailable,
    SessionExpired,
    TransientError,
)

from app.config import settings

log = logging.getLogger(__name__)

driver = GraphDatabase.driver(
    settings.neo4j_uri,
    auth=(
        settings.neo4j_username,
        settings.neo4j_password,
    ),
    connection_timeout=30,
    max_transaction_retry_time=30,
    initial_retry_delay=1,
    retry_delay_multiplier=2.0,
    retry_delay_jitter_factor=0.2,
)

RETRYABLE_ERRORS = (
    SessionExpired,
    TransientError,
    ServiceUnavailable,
)


def verify_connection():
    driver.verify_connectivity()


def close_connection():
    driver.close()