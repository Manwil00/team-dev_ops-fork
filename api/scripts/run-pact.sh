#!/bin/bash
set -e

echo "Running Pact contract tests"

# Step 1: Run consumer test to generate pact file
echo "Step 1: Running Java consumer test"
cd services/spring-api
./gradlew test --tests "com.nicheexplorer.apiserver.pact.ArticleFetcherConsumerTest"

# Verify pact file was generated
if [ ! -f "build/pacts/api-server-py-fetcher.json" ]; then
    echo "Error: Pact file not generated"
    exit 1
fi
echo "Pact file generated successfully"

# Step 2: Run provider test to verify contract
echo "Step 2: Running Python provider test"
cd ../py-fetcher
pip install -r requirements.txt
pip install -r test_requirements.txt
python -m pytest tests/test_pact_provider.py::TestPyFetcherProvider::test_against_api_server_contract -v

echo "Contract tests completed successfully" 