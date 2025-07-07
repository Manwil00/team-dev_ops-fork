import pytest
import chromadb
from testcontainers.chroma import ChromaContainer
import os


# Fixture to manage the lifecycle of a ChromaDB container for testing.
# Scope is 'session' to start the container once for the entire test session.
@pytest.fixture(scope="session")
def chroma_container():
    # Set this to a non-existent directory to avoid conflicts with local ChromaDB
    os.environ["CHROMA_DB_PATH"] = "/tmp/chroma_db_test"

    with ChromaContainer(image="chromadb/chroma:0.4.24").with_env(
        "ALLOW_RESET", "TRUE"
    ) as chroma:
        yield chroma


# Fixture to provide a ChromaDB client connected to the test container.
# Scope is 'function' to ensure each test function gets a fresh client
# and a clean database state if needed (by resetting the container).
@pytest.fixture(scope="function")
def chroma_client(chroma_container: ChromaContainer):
    # Get a client configured to connect to the running container
    client = chromadb.HttpClient(
        host=chroma_container.get_container_host_ip(),
        port=chroma_container.get_exposed_port(8000),
    )
    yield client
    # Reset the database after each test function to ensure test isolation
    client.reset()


# Autouse fixture to automatically mock the ChromaDB client for all tests.
# This is the key to redirecting the EmbeddingService to our test container
# without changing its source code.
@pytest.fixture(autouse=True)
def override_chroma_db(monkeypatch, chroma_client: chromadb.HttpClient):
    """
    This fixture is the core of our testing strategy. It intercepts any
    attempt by the application to create a `chromadb.PersistentClient` and
    returns our test-container-backed `HttpClient` instead.
    """
    # We are replacing the class `PersistentClient` with a lambda function.
    # Any code that calls `chromadb.PersistentClient(...)` will now execute
    # this lambda, which simply returns the client connected to our test container.
    # The original arguments to PersistentClient are ignored.
    monkeypatch.setattr(
        chromadb, "PersistentClient", lambda path, settings: chroma_client
    )
