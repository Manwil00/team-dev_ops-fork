"""
services/py-genai/tests/conftest.py
----------------------------------

This file is imported by pytest BEFORE it starts collecting tests.
That lets us:

1.  Spin-up a pgvector-enabled Postgres test-container for integration tests.
2.  Patch things so *unit* tests that fully mock psycopg2 don’t crash when
    pgvector’s `register_vector()` runs inside `EmbeddingService.__init__`.

"""

import os
import psycopg2
import pytest

# Third-party helpers
from testcontainers.postgres import PostgresContainer  # Docker wrapper
from pgvector.psycopg2 import register_vector  # Real function


# ---------------------------------------------------------------------------
# 1. START THE REAL POSTGRES TEST-CONTAINER  (needed for integration tests)
# ---------------------------------------------------------------------------

_pg = PostgresContainer("ankane/pgvector:latest")  # image has pgvector pre-installed
_pg.start()

host = _pg.get_container_host_ip()
port = _pg.get_exposed_port(5432)
dbname = _pg.dbname
user = _pg.username
password = _pg.password

# Make the running service discoverable by application code
os.environ.update(
    POSTGRES_HOST=host,
    POSTGRES_PORT=str(port),
    POSTGRES_DB=dbname,
    POSTGRES_USER=user,
    POSTGRES_PASSWORD=password,
)

# One-time DB bootstrap: enable extension & create minimal table
conn = psycopg2.connect(
    host=host, port=port, dbname=dbname, user=user, password=password
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS article (
        external_id TEXT PRIMARY KEY,
        embedding   vector(768)
    );
    """
)
cur.close()
register_vector(conn)  # register vector type with *real* connection
conn.close()


# ---------------------------------------------------------------------------
# 3.  Ensure the container is stopped when the entire test session ends
# ---------------------------------------------------------------------------


def pytest_sessionfinish(session, exitstatus):
    _pg.stop()


# ---------------------------------------------------------------------------
# 4.  Dummy autouse fixture (makes it obvious tests depend on this file)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _ensure_pgvector_container():
    """Keep the container alive for the whole test run."""
    yield
