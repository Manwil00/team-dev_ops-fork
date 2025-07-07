import pytest
import os
import docker
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs


# Fixture to build the image once and then run the container
@pytest.fixture(scope="module")
def genai_service_container():
    # We need to find the root of the git repo to build the Dockerfile path correctly
    git_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    genai_path = os.path.join(git_root, "services/py-genai")
    image_tag = "test-py-genai-topics:latest"

    # 1. Build the image using the docker SDK
    client = docker.from_env()
    buildargs = {}
    if os.getenv("GOOGLE_API_KEY"):
        buildargs["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

    print(f"Building Docker image {image_tag} from path {genai_path}...")
    try:
        client.images.build(
            path=genai_path,
            tag=image_tag,
            rm=True,  # Remove intermediate containers
            buildargs=buildargs,
        )
        print("Image built successfully.")
    except docker.errors.BuildError as e:
        print("Docker build failed:")
        for line in e.build_log:
            if "stream" in line:
                print(line["stream"].strip())
        pytest.fail("Docker image build failed.", pytrace=False)

    # 2. Run the container with the newly built image, passing the key at runtime
    container = DockerContainer(image=image_tag)
    if os.getenv("GOOGLE_API_KEY"):
        container = container.with_env("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))

    container = container.with_exposed_ports(8000)

    with container as genai:
        wait_for_logs(genai, r"Uvicorn running on http://0.0.0.0:8000")
        host = genai.get_container_host_ip()
        port = genai.get_exposed_port(8000)
        yield f"http://{host}:{port}"


# Fixture to override the GENAI_BASE_URL environment variable for the tests
@pytest.fixture(autouse=True)
def override_genai_url(genai_service_container, monkeypatch):
    monkeypatch.setenv("GENAI_BASE_URL", genai_service_container)
