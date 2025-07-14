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


## Kubernetes Deployment

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
- Create two namespaces on the cluster:
    - niche-explorer: This is where the application will be hosted.
    - monitoring: This is where Grafana and Prometheus will run.
- Setup secrets on the cluster:
    - Using [kubectl](https://kubernetes.io/de/docs/reference/kubectl/):
     ```bash
        kubectl create secret generic my-app-credentials \
                    --from-literal=CHAIR_API_KEY="<YOUR_ACTUAL_CHAIR_API_KEY>" \
                    --from-literal=GOOGLE_API_KEY="<YOUR_ACTUAL_GOOGLE_API_KEY>" \
                    --from-literal=POSTGRES_DB="<YOUR_ACTUAL_POSTGRES_DB_NAME>" \
                    --from-literal=POSTGRES_PASSWORD="<YOUR_ACTUAL_POSTGRES_PASSWORD>" \
                    --from-literal=POSTGRES_USER="<YOUR_ACTUAL_POSTGRES_USER>" \
                    --namespace <namespace>
     ```
    where:
    - CHAIR_API_KEY: Key to an LLM
    - GOOGLE_API_KEY: Key of [Google AI Studio](https://aistudio.google.com/)
    - POSTGRES_DB: Name of the database
    - POSTGRES_PASSWORD: Password for the database
    - POSTGRES_USER: Username for the database
    - namespace: Namespace you want to deploy to.

  
- Configure Ingress address in `values.yml`
- Create two namespaces in the project and configure the .kube/config file to point to the cluster:
    - niche-explorer: Namespace for the main project
    - monitoring: Namespace for the monitoring services.
- Deploy the two Helm charts from the project root:
    - niche-explorer (main application):
        - Run `helm upgrade --install -n niche-explorer <Deployment Name> infra/helm/niche_explorer/`
    - monitoring-stack (i.e. Grafana and Prometheus):
        - Run `bash deploy-monitoring-stack.sh`
    - alternatively the application and the monitoring stack can be deployed running this command `bash infra/helm/deploy.sh `.
    - Wait around 5 minutes before accessing the application to ensure all services are up and running.
- To uninstall / undeploy these two, run `bash infra/helm/undeploy.sh`.

## AWS Deployment

### Prerequisits

Before beginning, ensure the following are installed and configured:

*   **[Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli)**
*   **[Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)**
*   **[AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)**
*   An **AWS account** with permissions to create EC2 instances and related resources.
*   A **GitHub Personal Access Token (PAT)** with `read:packages` scope to pull images from the GitHub Container Registry (ghcr.io).
*   If Docker images are not pushed to the standard project ghcr.io, update the paths in `infra/compose.aws.yml`.

---
Manually create EC2 Instance:
1.  Log in to the **AWS Management Console** and navigate to the **EC2** service.
2.  Click **Launch instances**.
3.  Configure the new instance with the following settings:
    *   **Name:** Choose a descriptive name (e.g., `my-app-server`).
    *   **Application and OS Images (AMI):** Select **Ubuntu**.
    *   **Instance type*** Use an instance with at least 8 GiB RAM, like `t3.large`
    *   **Key pair (login):** Choose `vockey`as key pair. The corresponding `.pem` file will be needed later.
    *   **Network settings:** Ensure **HTTPS** and **HTTP** are enabled.
    *   **Configure storage:** Increase the root volume size to at least **25 GiB**.
4.  Click **Launch instance**.
5.  Once the instance is running, copy its **Public IPv4 address** and **Instance ID**, as they will be needed later.


### Local AWS Deployment

#### Terraform 

1.  Configure the local AWS credentials so Terraform can authenticate. They can typically be found in the AWS account details for the AWS CLI. Copy them into the local credentials file:
    ```sh
    # Location of the AWS credentials file
    ~/.aws/credentials
    ```

2.  Navigate to the Terraform directory (from project root folder):
    ```sh
    cd infra/terraform/
    ```

3.  Create or update the `terraform.tfvars` file with the details from the created EC2 instance:
    ```hcl
    # infra/terraform/terraform.tfvars

    instance_id = "i-xxx"  # <-- Replace with your Instance ID
    public_ip   = "xxx.xxx.xxx.xxx"         # <-- Replace with your Public IPv4 address
    ```

4.  Initialize, plan, and apply the Terraform configuration:
    ```sh
    # Initialize the Terraform workspace
    terraform init

    # (Optional) Preview the changes that will be made
    terraform plan

    # Apply the changes to create the Elastic IP
    terraform apply -auto-approve
    ```

#### Deploy using Ansible: 

This installs Docker, logs in to the container registry, and starts the application.

0. Update the `DOMAIN` variable in .env to the obtained public IP.

1.  Navigate to the Ansible directory:
    ```sh
    cd infra/ansible/  # From project root folder

    cd ../ansible      # From the terraform folder
    ```

2.  Place the private key file (`labsuser.pem`, obtained earlier) into this directory.

3.  Set the correct permissions for the private key file.
    ```sh
    chmod 400 labsuser.pem
    ```

4.  Open the `inventory.yml` file and update the `ansible_host` with the instance's public IP address.
    ```yaml
    # infra/ansible/inventory.yml

    all:
      hosts:
        aws_instance:
          ansible_host: xxx.xxx.xxx.xxx  # <-- Replace with Public IPv4 address
          # ...
    ```

5.  Run the Ansible playbook to deploy the application, providing the GitHub username and Personal Access Token as extra variables (May take 5-10 minutes).

    ```sh
    ansible-playbook playbook.yml --extra-vars "ghcr_username=<GITHUB_USERNAME> ghcr_token=<GITHUB_TOKEN>"
    ```

The application should now be deployed and accessible at the public IP address of the EC2 instance.
---

In rare cases, the AWS public IP address changes seemingly at random. Hence, if the above fails with an SSH error, consider updating the IP address.


#### GH-Action AWS Deployment


### Database Schema

The application uses PostgreSQL with pgvector. Class Diagram:
![Class Diagram](docs/Product%20backlog%20%26%20architecture/assets/Class_Diagram.png)


### Use Case Diagram 

<img src="docs/Product backlog & architecture/assets/use-case.png" width="600">