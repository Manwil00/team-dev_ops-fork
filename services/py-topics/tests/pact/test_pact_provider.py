import pytest
import subprocess
import time
import requests
import os
from pact import Verifier
from dotenv import load_dotenv
import httpx
from niche_explorer_models.models.embedding_response import EmbeddingResponse


class TestPyTopicsProvider:
    @pytest.fixture(scope="module")
    def provider_service(self):
        # Load .env from the project root
        dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path=dotenv_path)

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
            ]
        )
        self._wait_for_service("http://127.0.0.1:8100/health")
        yield "http://127.0.0.1:8100"
        process.terminate()
        process.wait()

    def _wait_for_service(self, url, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
        raise Exception(f"Service at {url} did not start within {timeout} seconds")

    def test_against_api_server_contract(self, provider_service, mocker):
        pact_file = os.path.join(
            os.path.dirname(__file__),
            "../../../spring-api/build/pacts/api-server-py-topics.json",
        )

        if not os.path.exists(pact_file):
            pytest.fail(
                f"Pact file not found at {os.path.abspath(pact_file)}. "
                "Please run the consumer test first to generate the contract."
            )

        verifier = Verifier(provider="py-topics", provider_base_url=provider_service)

        def topic_discovery_service_available():
            """
            Set up state for topic discovery. Mocks the HTTP client used to call the
            py-genai service to ensure py-topics is tested in isolation.
            """
            # This is the data the contract expects py-genai to return.
            mock_embedding_data = EmbeddingResponse(
                embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
                cached_count=2,
                found_count=2,
            ).model_dump()

            mock_response = httpx.Response(200, json=mock_embedding_data)

            # The service uses both GET and POST to fetch embeddings. We mock both
            # to return the same valid response, ensuring the topic_service can proceed.
            mocker.patch("httpx.AsyncClient.get", return_value=mock_response)
            mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

            return True

        def topic_discovery_service_receives_an_invalid_request():
            """Setup for POST /api/v1/topics/discover with bad data. No mock needed."""
            return True

        provider_states = {
            "topic discovery service is available": topic_discovery_service_available,
            "topic discovery service receives an invalid request": topic_discovery_service_receives_an_invalid_request,
        }

        success, logs = verifier.verify_pacts(
            pact_file,
            provider_states=provider_states,
            verbose=True,
            enable_pending=False,
        )

        assert success, f"Provider verification failed: {logs}"
