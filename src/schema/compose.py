from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
import os


class Port(BaseModel):
    mode: Literal["ingress", "egress"] = "ingress"
    target: int
    published: Optional[int] = None
    protocol: Literal["tcp", "udp"] = "tcp"


class Build(BaseModel):
    """
    docker-compose build
    """

    context: str = Field(description="context")

    @field_validator("context")
    @classmethod
    def make_relative(cls, v: str) -> str:
        if os.path.isabs(v):
            return os.path.basename(v)
        return v


class Dependency(BaseModel):
    condition: str = Field(description="condition")
    required: bool = Field(description="required", default=True)


class Service(BaseModel):
    """
    docker-compose service
    """

    model_config = {"extra": "ignore"}

    build: Optional[Build] = Field(description="build", default=None)
    ports: Optional[list[Port]] = Field(description="ports", default=None)
    image: Optional[str] = Field(description="image", default=None)
    environment: dict[str, Optional[str]] = Field(
        description="environment", default_factory=dict
    )
    depends_on: dict[str, Dependency] = Field(default_factory=dict)


class Application(BaseModel):
    model_config = {"extra": "ignore"}

    services: dict[str, Service]
