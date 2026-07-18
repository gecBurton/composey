from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Service(BaseModel):
    """
    A logical unit of compute. Cloud-agnostic representation of a containerized process.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Unique identifier for the service")
    image: str = Field(description="Docker image URI")
    cpu: int = Field(default=256, description="CPU units (1024 = 1 vCPU)")
    memory: int = Field(default=512, description="Memory in MiB")
    port: Optional[int] = Field(
        default=None, description="The internal port the service listens on"
    )
    env: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
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
