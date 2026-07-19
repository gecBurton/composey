import json
import subprocess

from models.compose import Application as DockerApplication


def parse(file_path: str, level=2) -> DockerApplication:
    result = subprocess.run(
        ["docker", "compose", "-f", file_path, "config", "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    raw = json.loads(result.stdout)
    return DockerApplication.model_validate(raw)
