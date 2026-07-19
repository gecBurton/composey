import os

from ..models.compose import Application as DockerApplication
from ..models.semantic import (
    Application as SemanticApplication,
)
from ..models.semantic import (
    Relationship,
)
from ..models.semantic import (
    Service as SemanticService,
)


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

        # Resolve secrets to names
        secret_names = []
        if docker_service.secrets:
            for s in docker_service.secrets:
                if isinstance(s, str):
                    secret_names.append(s)
                else:
                    secret_names.append(s.source)

        # Resolve volumes to names
        storage_names = []
        if docker_service.volumes:
            for v in docker_service.volumes:
                source = None
                if isinstance(v, str):
                    # handle simple string format source:target
                    source = v.split(":")[0]
                elif v.source:
                    source = v.source

                if source:
                    # If it's an absolute path, only use the filename/basename
                    # This prevents local workstation paths from leaking into TF
                    if os.path.isabs(source):
                        source = os.path.basename(source)
                    storage_names.append(source)

        semantic_services.append(
            SemanticService(
                name=s_name,
                image=docker_service.image or "placeholder",
                port=primary_port,
                env=docker_service.environment,
                secrets=secret_names,
                storage=storage_names,
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
