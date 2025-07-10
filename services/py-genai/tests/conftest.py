import os
import psycopg2
import pytest
from testcontainers.postgres import PostgresContainer
from pgvector.psycopg2 import register_vector

# ---------------------------------------------------------------------------
# Boot a pgvector-enabled Postgres container immediately upon importing this
# conftest module. Pytest imports *all* conftest.py files before it collects
# (and therefore before it imports) any test modules. This guarantees that the
# environment variables are in place and the Postgres service is ready before
# `EmbeddingService` attempts to connect during `src` imports inside the test
# modules.
# ---------------------------------------------------------------------------

_pg_container = PostgresContainer("ankane/pgvector:latest")
_pg_container.start()

host = _pg_container.get_container_host_ip()
port = _pg_container.get_exposed_port(5432)
dbname = _pg_container.dbname
user = _pg_container.username
password = _pg_container.password

# Export connection details so the application picks them up
os.environ.setdefault("POSTGRES_HOST", host)
os.environ.setdefault("POSTGRES_PORT", str(port))
os.environ.setdefault("POSTGRES_DB", dbname)
os.environ.setdefault("POSTGRES_USER", user)
os.environ.setdefault("POSTGRES_PASSWORD", password)

# Prepare schema required for tests
_conn = psycopg2.connect(
    host=host, port=port, dbname=dbname, user=user, password=password
)
_conn.autocommit = True
_register_cur = _conn.cursor()
_register_cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
_register_cur.execute(
    """
    CREATE TABLE IF NOT EXISTS article (
        external_id TEXT PRIMARY KEY,
        embedding vector(768)
    );
    """
)
_register_cur.close()
register_vector(_conn)
_conn.close()

# ---------------------------------------------------------------------------
# Finalizer to ensure the container is stopped once the entire test session is
# finished.
# ---------------------------------------------------------------------------


def pytest_sessionfinish(session, exitstatus):
    _pg_container.stop()


# No additional fixtures are strictly necessary, but we keep a dummy autouse
# fixture to make it explicit that tests rely on the running container. It does
# nothing other than provide clarity in the test output.


@pytest.fixture(scope="session", autouse=True)
def _ensure_pgvector_container():
    yield  # Container lifecycle handled globally
