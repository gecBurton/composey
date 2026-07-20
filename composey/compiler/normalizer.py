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

        # Infer capability from image name
        capability = "container"
        image_lower = (docker_service.image or "").lower()

        # Database detection: starts with or matches specific library images
        db_images = ["postgres", "mysql", "mariadb"]
        if any(
            image_lower.startswith(db) or f"/{db}" in image_lower for db in db_images
        ):
            capability = "database"
        # Cache detection
        elif any(
            image_lower.startswith(c) or f"/{c}" in image_lower
            for c in ["redis", "valkey"]
        ):
            capability = "cache"
        # Storage detection
        elif any(
            image_lower.startswith(s) or f"/{s}" in image_lower for s in ["minio"]
        ):
            capability = "object-storage"

        # Extract x-composey size/resource hints
        size = "small"
        cpu = None
        memory = None
        min_scale = 1
        max_scale = 1
        schedule = None

        x_composey = docker_service.x_composey
        if "size" in x_composey:
            size = x_composey["size"]
        if "cpu" in x_composey:
            cpu = int(x_composey["cpu"])
        if "memory" in x_composey:
            memory = int(x_composey["memory"])
        if "min_scale" in x_composey:
            min_scale = int(x_composey["min_scale"])
        if "max_scale" in x_composey:
            max_scale = int(x_composey["max_scale"])
        if "schedule" in x_composey:
            schedule = x_composey["schedule"]

        semantic_services.append(
            SemanticService(
                name=s_name,
                image=docker_service.image or "placeholder",
                capability=capability,
                size=size,
                cpu=cpu,
                memory=memory,
                port=primary_port,
                min_scale=min_scale,
                max_scale=max_scale,
                schedule=schedule,
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
