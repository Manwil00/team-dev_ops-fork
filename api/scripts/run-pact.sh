#!/bin/bash
set -e

echo "Running All Pact Contract Tests"

# Step 1: Run all consumer tests to generate pact files
echo "--> Running all Java consumer tests to generate pacts..."
cd services/spring-api
chmod +x gradlew
./gradlew test --tests "*ConsumerTest"
cd ../.. # Back to project root

# Step 2: Verify all pact files were generated (simple, no loops)
echo "--> Verifying pact file generation..."
PACT_DIR="services/spring-api/build/pacts"

if [ ! -f "$PACT_DIR/api-server-py-fetcher.json" ]; then
    echo "Error: Pact file for py-fetcher not generated"
    exit 1
fi
echo "Verified: api-server-py-fetcher.json"

if [ ! -f "$PACT_DIR/api-server-py-genai.json" ]; then
    echo "Error: Pact file for py-genai not generated"
    exit 1
fi
echo "Verified: api-server-py-genai.json"

if [ ! -f "$PACT_DIR/api-server-py-topics.json" ]; then
    echo "Error: Pact file for py-topics not generated"
    exit 1
fi
echo "Verified: api-server-py-topics.json"
echo "All pact files generated successfully."

# Step 3: Run provider tests to verify contracts
echo "--> Running all Python provider tests..."

# --- Provider: py-fetcher ---
echo "--- Verifying py-fetcher ---"
cd services/py-fetcher
python -m pip install -q -r requirements.txt -r test_requirements.txt ./generated
PYTHONPATH=src python -m pytest tests/pact/test_pact_provider.py -v
cd ../..

# --- Provider: py-genai ---
echo "--- Verifying py-genai ---"
cd services/py-genai
python -m pip install -q -r requirements.txt -r test_requirements.txt ./generated
PYTHONPATH=src python -m pytest tests/pact/test_pact_provider.py -v
cd ../..

# --- Provider: py-topics ---
echo "--- Verifying py-topics ---"
cd services/py-topics
python -m pip install -q -r requirements.txt -r test_requirements.txt ./generated
PYTHONPATH=src python -m pytest tests/pact/test_pact_provider.py -v
cd ../..

echo "All contract tests completed successfully!" 