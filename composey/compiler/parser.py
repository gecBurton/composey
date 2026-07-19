import json
import subprocess

import yaml

from ..models.compose import Application as DockerApplication


def parse(file_path: str, level=2) -> DockerApplication:
    # 1. Use docker compose config to handle interpolation and normalization
    result = subprocess.run(
        ["docker", "compose", "-f", file_path, "config", "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    raw = json.loads(result.stdout)

    # 2. Extract x-composey extensions from raw YAML (docker-compose strips them)
    with open(file_path, "r") as f:
        raw_yaml = yaml.safe_load(f)

    if "services" in raw_yaml:
        for s_name, s_data in raw_yaml["services"].items():
            if "x-composey" in s_data and s_name in raw["services"]:
                raw["services"][s_name]["x-composey"] = s_data["x-composey"]

    # print(json.dumps(raw, indent=2)) # Debug

    return DockerApplication.model_validate(raw)
