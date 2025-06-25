#!/usr/bin/env bash

set -euo pipefail

SPEC_PATH="$(git rev-parse --show-toplevel)/api/openapi.yaml"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Java – Spring Boot stubs
openapi-generator-cli generate \
  -i "$SPEC_PATH" \
  -g spring \
  -o "$PROJECT_ROOT/services/spring-api/generated" \
  --skip-validate-spec

# Python – client
openapi-python-client \
  --path "$SPEC_PATH" \
  --output "$PROJECT_ROOT/services/python-client" \
  --config "$PROJECT_ROOT/api/scripts/py-config.json" || true

# TypeScript SDK for the web client
npx openapi-typescript "$SPEC_PATH" -o "$PROJECT_ROOT/web-client/src/api.ts" 