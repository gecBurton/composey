from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
import json
import os
import subprocess


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


class Service(BaseModel):
    """
    docker-compose service
    """

    name: str = Field(description="name")
    build: Optional[Build] = Field(description="build", default=None)
    ports: Optional[list[Port]] = Field(description="ports", default=None)


class Application(BaseModel):
    services: list[Service]


def parse(file_path: str) -> Application:
    result = subprocess.run(
        ["docker", "compose", "-f", file_path, "config", "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    raw = json.loads(result.stdout)
    raw["services"] = [
        dict(v, name=name) for name, v in raw.get("services", {}).items()
    ]
    return Application.model_validate(raw)
