import pytest
import subprocess
import time
import requests
import os
from pact import Verifier
from unittest.mock import MagicMock, AsyncMock

# Define the expected location of the contract file
PACT_FILE = os.path.join(
    os.path.dirname(__file__),
    "../../../spring-api/build/pacts/api-server-py-topics.json",
)


@pytest.fixture
def provider_service(monkeypatch):
    # Mock the GENAI_BASE_URL before the service starts
    monkeypatch.setenv("GENAI_BASE_URL", "http://mock-genai-service")

    service_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    process = subprocess.Popen(
        [
            "python",
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8100",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=service_root,
    )

    def _wait_for_service(url, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if requests.get(url, timeout=5).status_code == 200:
                    print("Provider service started successfully.")
                    return
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        stdout, stderr = process.communicate()
        raise Exception(
            f"Provider service at {url} did not start. Logs:\\n{stderr.decode()}"
        )

    _wait_for_service("http://127.0.0.1:8100/health")
    yield "http://127.0.0.1:8100"

    print("Terminating provider service...")
    process.terminate()
    process.wait()


class TestPyTopicsProvider:
    def test_against_api_server_contract(self, provider_service, mocker):
        if not os.path.exists(PACT_FILE):
            pytest.fail(f"Pact file not found: {os.path.abspath(PACT_FILE)}")

        # Mock the internal TopicDiscoveryService to isolate the provider from its dependency.
        # The service instance in `main.py` is `topic_service`.
        mock_service_instance = mocker.patch(
            "src.main.topic_service", new_callable=MagicMock
        )

        # The `discover_topic` method is async, so we must use an AsyncMock.
        mock_service_instance.discover_topic = AsyncMock()

        # Configure a valid, deterministic response for the contract verification.
        from niche_explorer_models.models.topic_discovery_response import (
            TopicDiscoveryResponse,
        )

        mock_service_instance.discover_topic.return_value = TopicDiscoveryResponse(
            query="pact-test", topics=[], total_articles_processed=0
        )

        def topic_service_is_ready_to_discover_topics():
            # This provider state doesn't require special setup as the mock is already in place.
            return True

        provider_states = {
            "the topic discovery service is ready": topic_service_is_ready_to_discover_topics,
        }

        verifier = Verifier(provider="py-topics", provider_base_url=provider_service)
        success, logs = verifier.verify_pacts(
            PACT_FILE, provider_states=provider_states, verbose=True
        )
        assert success, f"Provider verification failed. Logs:\\n{logs}"
