# NicheExplorer

[![CI](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/ci.yml/badge.svg)](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/ci.yml)
[![Docs](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/docs.yml/badge.svg)](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Docker](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/build_docker.yml/badge.svg)](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/build_docker.yml)
[![Deploy Helm](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/deploy_helm.yml/badge.svg)](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/deploy_helm.yml)
[![Manual Docker Deploy](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/deploy_docker_manual_input.yml/badge.svg)](https://github.com/AET-DevOps25/team-dev_ops/actions/workflows/deploy_docker_manual_input.yml)

**Catch emerging research trends in seconds.** Type a question, NicheExplorer fetches the latest papers & discussions, clusters them into semantic topics and presents an interactive report.

> 🌐 **Live demo:** _coming soon_ (TODO)

## Demo

> The GIF below shows a complete front-end flow: entering a query, running the pipeline, and browsing the discovered topics.

![NicheExplorer demo](docs/demo.gif)

---


# Quick Start

## Local Development Setup

#### 1. Clone repository & configure environment

```bash
git clone https://github.com/your-org/team-dev_ops.git
cd team-dev_ops

Configure environment
cp .env.example .env
```
#### 2.  Generate OpenAPI client libraries
```bash
bash api/scripts/gen-all.sh 
``` 

#### 3. Local development (uses override with hard-coded localhost rules)
```bash
docker compose --env-file ./.env -f infra/docker-compose.yml -f infra/docker-compose.override.yml up --build -d
```
#### (Optional) Server / production deployment
```bash
docker compose --env-file ./.env -f infra/docker-compose.yml up --build -d
```

## Overview

NicheExplorer is a microservices-based application that leverages machine learning and natural language processing to identify emerging trends in research domains. The system automatically fetches content from multiple sources, performs semantic analysis, and generates insightful reports.

| Service           | Technology Stack       | Port | Purpose                                   |
|------------------|------------------------|------|-------------------------------------------|
| client           | React + Vite + Nginx   | 80   | User interface and interaction [[docs](web-client/README.md)]           |
| api-server       | Spring Boot + Java     | 8080 | Request orchestration and business logic [[docs](services/spring-api/README.md)] |
| genai            | FastAPI + Python       | 8000 | AI/ML processing and embeddings [[docs](services/py-genai/README.md)] |
| topic-discovery  | FastAPI + Python       | 8100 | Content clustering and topic analysis [[docs](services/py-topics/README.md)] |
| article-fetcher  | FastAPI + Python       | 8200 | Content retrieval and RSS processing [[docs](services/py-fetcher/README.md)] |
| db               | PostgreSQL + pgvector  | 5432 | Data persistence and vector search        |

➡️ **Traefik Dashboard**: [http://localhost:8080/dashboard/](http://localhost:8080/dashboard/)

## API Documentation

The complete REST API specification is available in `api/openapi.yaml` and published automatically via GitHub Pages:

| Format | Live link |
| ------ | --------- |
| ReDoc  | https://AET-DevOps25.github.io/team-dev_ops/api.html |
| Swagger UI | https://AET-DevOps25.github.io/team-dev_ops/swagger/ |

The `docs` GitHub Pages site is built by the workflow in `.github/workflows/docs.yml` every time `api/openapi.yaml` changes (or when you trigger the workflow manually).  

### View locally

```bash
# Install once
npm i -g redoc-cli swagger-ui-dist http-server

# Generate docs
redoc-cli bundle api/openapi.yaml -o docs/api.html

# Serve locally at http://localhost:8088
http-server docs -p 8088
```

# Architecture

![Architecture Diagram](docs/Product%20backlog%20%26%20architecture/assets/Architecture.png)

```
team-dev_ops/
├── api/                    # OpenAPI specification and generators
├── services/               # Microservices source code
│   ├── py-genai/          # AI/ML service
│   ├── py-topics/         # Topic discovery service
│   ├── py-fetcher/        # Content fetching service
│   └── spring-api/        # Main API orchestrator
├── web-client/            # React frontend application
├── infra/                 # Infrastructure as code
│   ├── docker-compose.yml # Local development
│   ├── helm/              # Kubernetes charts
│   ├── grafana/           # Grafana configuration
│   ├── prometheus/        # Prometheus configuration
│   ├── traefik/           # Traefik configuration
│   ├── terraform/         # Cloud infrastructure
│   └── ansible/           # Configuration management
└── docs/                  # Documentation and architecture
```


### Kubernetes Deployment

The application is set up to be deployable to a Kubernetes cluster via Helm.

The Helm folder structure is organized as follows:

```
team-dev_ops/infra/helm/
├── monitoring-stack/           # Monitoring deployment
│   ├── grafana/                # All Grafana deployment files
│   ├── prometheus/             # All Prometheus deployment files
│   ├── Chart.yml               # Default Helm chart for deployment
├── niche-explorer/             # Microservices source code
│   ├── templates/              # Contains all Kubernetes resource templates
│   │   ├── deployments/        # Helm templates for Deployments
│   │   ├── services/           # Helm templates for Services
│   │   └── ...                 # Other resource templates (e.g., ingresses, configmaps)
│   ├── Chart.yaml              # Helm chart definition for niche-explorer
│   └── values.yaml             # Configurable values for niche-explorer charts
├── deploy-monitoring-stack.sh  # Script to deploy the monitoring stack
```

Before deploying, ensure the following configurations are in place:
- Create secrets on k8s cluster:
    - Insert the secret name in `values.yml` at `existingSecret: ...` sections
    - CHAIR_API_KEY: Key to an LLM
    - GOOGLE_API_KEY: Key of [text](https://aistudio.google.com/)
    - POSTGRES_DB: Name of the database
    - POSTGRES_PASSWORD: Password for the database
    - POSTGRES_USER: Username for the database
- Configure Ingress address in `values.yml`
- Create two namespaces in the project and configure the .kube/config file to point to the cluster:
    - niche-explorer: Namespace for the main project
    - monitoring: Namespace for the monitoring services.
- Deploy the two Helm charts from the project root:
    - niche-explorer (main application):
        - Run `helm upgrade --install -n niche-explorer <Deployment Name> infra/helm/niche_explorer/`
    - monitoring-stack (i.e. Grafana and Prometheus):
        - Run `bash deploy-monitoring-stack.sh`


### Database Schema

The application uses PostgreSQL with pgvector. Class Diagram:
![Class Diagram](docs/Product%20backlog%20%26%20architecture/assets/Class_Diagram.png)


### Use Case Diagram 

<img src="docs/Product backlog & architecture/assets/use-case.png" width="600">