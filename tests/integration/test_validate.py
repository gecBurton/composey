import json
import os
import shutil
import subprocess
import tempfile

import pytest

from compiler import compile_to_terraform
from models.environment import Environment

# Mock environment for testing
FIXED_ENV = Environment(
    name="prod",
    vpc_id="vpc-123",
    public_subnets=["subnet-1", "subnet-2"],
    private_subnets=["subnet-3", "subnet-4"],
    ecs_cluster_arn="arn:aws:ecs:us-east-1:123456789012:cluster/prod-cluster",
    alb_arn="arn:aws:lb:us-east-1:123456789012:loadbalancer/app/shared-alb/123",
    alb_listener_arn="arn:aws:lb:us-east-1:123456789012:listener/app/shared-alb/123/456",
)


@pytest.fixture(scope="session")
def terraform_base():
    """
    Initializes a shared Terraform directory with the AWS provider.
    Each test will copy the .terraform folder from here to stay fast.
    """
    if shutil.which("terraform") is None:
        pytest.skip("terraform CLI not found")

    base_dir = tempfile.mkdtemp()

    # Create a dummy manifest just to init the provider
    dummy_manifest = {
        "terraform": {
            "required_providers": {
                "aws": {"source": "hashicorp/aws", "version": "~> 5.0"}
            }
        }
    }

    with open(os.path.join(base_dir, "main.tf.json"), "w") as f:
        json.dump(dummy_manifest, f)

    # Optimization: Use a shared plugin cache to avoid downloading AWS provider every time
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    cache_dir = os.path.abspath(os.path.join(root_dir, ".terraform_cache"))
    os.makedirs(cache_dir, exist_ok=True)

    env_vars = os.environ.copy()
    env_vars["TF_PLUGIN_CACHE_DIR"] = cache_dir

    # Init once for the session
    result = subprocess.run(
        ["terraform", "init", "-backend=false", "-input=false"],
        cwd=base_dir,
        capture_output=True,
        text=True,
        env=env_vars,
    )

    if result.returncode != 0:
        shutil.rmtree(base_dir)
        pytest.skip(f"Terraform init failed during session setup: {result.stderr}")

    yield base_dir
    shutil.rmtree(base_dir)


def get_examples():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    examples_dir = os.path.join(root_dir, "examples")
    if not os.path.exists(examples_dir):
        return []
    return [
        d
        for d in os.listdir(examples_dir)
        if os.path.isdir(os.path.join(examples_dir, d))
    ]


@pytest.mark.parametrize("example_name", get_examples())
def test_terraform_validate(example_name, terraform_base):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    example_path = os.path.join(root_dir, "examples", example_name)
    compose_path = os.path.join(example_path, "compose.yml")

    # 1. Compile
    tf_json = compile_to_terraform(compose_path, FIXED_ENV, example_name)

    # 2. Run terraform validate in a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy the pre-initialized .terraform folder (instantly skip init)
        shutil.copytree(
            os.path.join(terraform_base, ".terraform"),
            os.path.join(tmpdir, ".terraform"),
        )
        shutil.copy(
            os.path.join(terraform_base, ".terraform.lock.hcl"),
            os.path.join(tmpdir, ".terraform.lock.hcl"),
        )

        json_path = os.path.join(tmpdir, "main.tf.json")
        with open(json_path, "w") as f:
            f.write(tf_json)

        # Validate (No init needed!)
        result = subprocess.run(
            ["terraform", "validate", "-json", "-no-color"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.fail(
                f"Terraform validation failed for {example_name}: {result.stdout}"
            )
