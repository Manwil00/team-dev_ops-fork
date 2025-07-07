import pytest
import subprocess
import time
import requests
import os
from pact import Verifier
from dotenv import load_dotenv
from niche_explorer_models.models.classify_response import ClassifyResponse
from niche_explorer_models.models.query_builder_response import QueryBuilderResponse


class TestPyGenAiProvider:
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
                "8000",
            ]
        )
        self._wait_for_service("http://127.0.0.1:8000/health")
        yield "http://127.0.0.1:8000"
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
            "../../../spring-api/build/pacts/api-server-py-genai.json",
        )

        if not os.path.exists(pact_file):
            pytest.fail(
                f"Pact file not found at {os.path.abspath(pact_file)}. "
                "Please run the consumer test first to generate the contract."
            )

        verifier = Verifier(provider="py-genai", provider_base_url=provider_service)

        def genai_service_available_for_classification():
            """Setup for POST /classify"""
            mock_response = ClassifyResponse(
                source="arxiv", source_type="research", suggested_category="cs.AI"
            )
            mocker.patch(
                "src.services.openweb_client.OpenWebClient.classify_source",
                return_value=mock_response,
            )
            return True

        def genai_service_available_for_embeddings():
            """Setup for POST /embeddings"""
            mock_response = {"vectors": [[0.1, 0.2, 0.3]], "cached_count": 0}
            mocker.patch(
                "src.services.embedding_service.embedding_service.embed_batch_with_cache",
                return_value=mock_response,
            )
            return True

        def genai_service_has_existing_embeddings():
            """Setup for GET /embeddings"""
            mock_response = {"embeddings": [[0.1, 0.2, 0.3]], "found_count": 1}
            mocker.patch(
                "src.services.embedding_service.embedding_service.get_embeddings_by_ids",
                return_value=mock_response,
            )
            return True

        def genai_service_available_for_query_building():
            """Setup for POST /query/build/{source}"""
            mock_response = QueryBuilderResponse(
                query='all:"test query"+AND+cat:cs.AI',
                description="Advanced arXiv search for 'test query' in category cs.AI",
                source="arxiv",
            )
            mocker.patch(
                "src.services.query_generation_service.query_service.build_advanced_query",
                return_value=mock_response.query,
            )
            return True

        def genai_service_receives_an_invalid_classification_request():
            """Setup for POST /classify with bad data. No mock needed as FastAPI should handle it."""
            return True

        provider_states = {
            "genai service is available for classification": genai_service_available_for_classification,
            "genai service is available for embeddings": genai_service_available_for_embeddings,
            "genai service has existing embeddings": genai_service_has_existing_embeddings,
            "genai service is available for query building": genai_service_available_for_query_building,
            "genai service receives an invalid classification request": genai_service_receives_an_invalid_classification_request,
        }

        success, logs = verifier.verify_pacts(
            pact_file,
            provider_states=provider_states,
            verbose=True,
            enable_pending=False,
        )

        assert success, f"Provider verification failed: {logs}"
