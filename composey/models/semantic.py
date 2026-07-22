from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Capability = Literal["container", "database", "cache", "object-storage"]


class Service(BaseModel):
    """
    A logical unit of compute or a managed capability.
    Cloud-agnostic representation of a process or stateful service.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Unique identifier for the service")
    image: str = Field(description="Docker image URI")
    capability: Capability = Field(
        default="container",
        description="The nature of the service (Standard container or managed cloud service)",
    )
    size: Literal["small", "medium", "large"] = Field(
        default="small", description="The relative size of the compute resource"
    )
    cpu: Optional[int] = Field(default=None, description="CPU units (1024 = 1 vCPU)")
    memory: Optional[int] = Field(default=None, description="Memory in MiB")
    port: Optional[int] = Field(
        default=None, description="The internal port the service listens on"
    )
    build_context: Optional[str] = Field(
        default=None,
        description="Path (relative to the compose file) to a Docker build context. "
        "When set, the image is built and pushed to ECR instead of pulled.",
    )
    command: Optional[list[str]] = Field(
        default=None, description="Container command override (exec form)"
    )
    health_check_grace_period: Optional[int] = Field(
        default=None,
        description="Seconds ECS ignores ALB health checks after a task starts",
    )
    min_scale: int = Field(default=1, description="Minimum number of instances")
    max_scale: int = Field(default=1, description="Maximum number of instances")
    schedule: Optional[str] = Field(
        default=None, description="Cron expression for scheduled tasks"
    )
    cdn_enabled: bool = Field(
        default=False, description="Whether to enable CDN for this service"
    )
    env: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    secrets: list[str] = Field(
        default_factory=list,
        description="List of secret names required by this service",
    )
    storage: list[str] = Field(
        default_factory=list,
        description="List of storage volume names (buckets) required by this service",
    )


class Relationship(BaseModel):
    """
    Directed connectivity: client -> server.
    This is the single source of truth for network security and service discovery.
    """

    model_config = ConfigDict(extra="forbid")

    client: str = Field(description="The name of the service initiating the connection")
    server: str = Field(description="The name of the service receiving the connection")
    port: Optional[int] = Field(
        default=None,
        description="The specific port for this link. If None, uses the server's default port.",
    )


class Application(BaseModel):
    """
    The complete semantic representation of the application stack.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="The name of the application or environment")
    services: list[Service] = Field(
        default_factory=list, description="All compute nodes in the application"
    )
    relationships: list[Relationship] = Field(
        default_factory=list,
        description="Explicit list of all allowed network connections",
    )
    public_service: Optional[str] = Field(
        default=None,
        description="The name of the service exposed to the internet via the root URL",
    )
