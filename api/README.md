# OpenAPI-First Development

This directory contains the single source of truth for our API specification.

## Setup

### 1. Install pre-commit hooks
```bash
pip install pre-commit
pre-commit install
```

### 2. Install code generation tools
```bash
# OpenAPI Generator (Java)
npm install -g @openapitools/openapi-generator-cli

# Python client generator
pip install openapi-python-client

# TypeScript generator
npm install -g openapi-typescript
```

### 3. Generate clients
```bash
./api/scripts/gen-all.sh
```

## Pre-commit Validation

The OpenAPI spec is automatically validated before every commit using Redocly's OpenAPI CLI.

To run validation manually:
```bash
pre-commit run -a
```

## Architecture

- **Single Source of Truth**: `api/openapi.yaml`
- **No Hand-written DTOs**: All models are generated from the OpenAPI spec
- **Immutable Records**: Java uses records for DTOs (immutable by default)
- **Type Safety**: TypeScript client provides full type safety for the web client

## Generated Clients

- **Java Spring Boot**: `services/spring-api/generated/`
- **Python Services**: `services/*/client/`
- **TypeScript Web Client**: `web-client/src/api.ts`

## Development Workflow

1. Modify `api/openapi.yaml`
2. Run `./api/scripts/gen-all.sh` to regenerate clients
3. Update service implementations to use generated models
4. Commit changes (pre-commit hooks will validate the spec)
