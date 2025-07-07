"""
Pact provider test for py-fetcher service.

This test verifies that py-fetcher can satisfy the contracts
defined by the api-server consumer test.
"""

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
    "../../../spring-api/build/pacts/api-server-py-fetcher.json",
)


class TestPyFetcherProvider:
    """
    Provider test that verifies py-fetcher satisfies the contract
    from api-server consumer test.
    """

    @pytest.fixture(scope="module")
    def provider_service(self):
        """
        Spins up the py-fetcher service as a separate process for the Verifier to use.
        """
        process = subprocess.Popen(
            [
                "python",
                "-m",
                "uvicorn",
                "src.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8200",  # As defined for py-fetcher
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        def _wait_for_service(url, timeout=30):
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print("Provider service started successfully.")
                        return
                except requests.exceptions.ConnectionError:
                    time.sleep(1)
            # If the loop finishes, the service did not start
            stdout, stderr = process.communicate()
            raise Exception(
                f"Provider service at {url} did not start within {timeout} seconds.\\n"
                f"STDOUT: {stdout.decode()}\\n"
                f"STDERR: {stderr.decode()}"
            )

        # Use the health check endpoint to wait for the service
        _wait_for_service("http://127.0.0.1:8200/health")
        yield "http://127.0.0.1:8200"

        print("Terminating provider service...")
        process.terminate()
        process.wait()

    def test_against_api_server_contract(self, provider_service, mocker):
        """
        Validates that the py-fetcher provider meets the contract defined by the api-server consumer.
        """
        if not os.path.exists(PACT_FILE):
            pytest.fail(
                f"Pact file not found at {os.path.abspath(PACT_FILE)}. "
                "Please run the consumer test in 'spring-api' first to generate it."
            )

        # Mock the internal service to avoid real calls to arXiv during verification
        mock_fetch_service = mocker.patch(
            "src.main.arxiv_fetcher", new_callable=MagicMock
        )

        def fetcher_is_ready_to_serve_articles():
            """Provider state: the fetcher is ready."""
            # This state is simple, but we can configure mock returns here
            mock_fetch_service.fetch = AsyncMock(
                return_value=[MagicMock(id="123", title="Mocked Paper", source="arxiv")]
            )
            return True

        def fetcher_has_arxiv_categories():
            """Provider state: the fetcher has categories available."""
            # No mock needed as this endpoint returns static data.
            return True

        provider_states = {
            "the article fetcher is ready to serve articles for source arxiv": fetcher_is_ready_to_serve_articles,
            "the article fetcher has categories available for source arxiv": fetcher_has_arxiv_categories,
        }

        verifier = Verifier(provider="py-fetcher", provider_base_url=provider_service)

        success, logs = verifier.verify_pacts(
            PACT_FILE,
            provider_states=provider_states,
            verbose=True,
        )

        assert success, f"Provider verification failed. Logs:\\n{logs}"
