#!/usr/bin/env bash

set -euo pipefail

# Java Spring Boot API server
openapi-generator-cli generate -i api/openapi.yaml -g spring \
  -o services/spring-api/generated --skip-validate-spec

# Python FastAPI server models - generate Pydantic models for each service
openapi-generator-cli generate -i api/openapi.yaml -g python-fastapi \
  -o services/py-genai/generated --skip-validate-spec \
  --additional-properties=packageName=niche_explorer_models

openapi-generator-cli generate -i api/openapi.yaml -g python-fastapi \
  -o services/py-fetcher/generated --skip-validate-spec \
  --additional-properties=packageName=niche_explorer_models

openapi-generator-cli generate -i api/openapi.yaml -g python-fastapi \
  -o services/py-topics/generated --skip-validate-spec \
  --additional-properties=packageName=niche_explorer_models

# TypeScript client for web app (Axios-based)
npx openapi-generator-cli generate -i api/openapi.yaml -g typescript-axios \
  -o web-client/src/generated/api --skip-validate-spec --additional-properties=supportsES6=true,useSingleRequestParameter=true,withSeparateModelsAndApi=true,apiPackage=apis,modelPackage=models
