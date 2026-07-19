from models.environment import Environment

from .generator import generate
from .inference import infer
from .normalizer import normalize
from .parser import parse


def compile_to_terraform(compose_file: str, env: Environment, project_name: str) -> str:
    # 1. Parse
    docker_app = parse(compose_file)

    # 2. Normalize
    semantic_app = normalize(docker_app, project_name)

    # 3. Infer
    aws_resources = infer(semantic_app, env)

    # 4. Generate
    return generate(aws_resources)
