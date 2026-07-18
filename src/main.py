import json
import subprocess

from schema.compose import Application as DockerApplication
from schema.semantic import (
    Application as SemanticApplication,
)
from schema.semantic import (
    Relationship,
)
from schema.semantic import (
    Service as SemanticService,
)


def parse(file_path: str, level=2) -> DockerApplication:
    result = subprocess.run(
        ["docker", "compose", "-f", file_path, "config", "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    raw = json.loads(result.stdout)
    return DockerApplication.model_validate(raw)


def normalize(app: DockerApplication, project_name: str) -> SemanticApplication:
    semantic_services = []
    relationships = []
    public_service = None

    for s_name, docker_service in app.services.items():
        # Identify the public service (first one mapping to port 80 or 443)
        if docker_service.ports:
            for p in docker_service.ports:
                if p.published in [80, 443] and public_service is None:
                    public_service = s_name

        # Handle services without ports safely
        primary_port = docker_service.ports[0].target if docker_service.ports else None

        semantic_services.append(
            SemanticService(
                name=s_name,
                image=docker_service.image or "placeholder",
                port=primary_port,
                env=docker_service.environment,
            )
        )

        # Build relationships
        for dep_name in docker_service.depends_on.keys():
            relationships.append(Relationship(client=s_name, server=dep_name))

    return SemanticApplication(
        name=project_name,
        services=semantic_services,
        relationships=relationships,
        public_service=public_service,
    )
