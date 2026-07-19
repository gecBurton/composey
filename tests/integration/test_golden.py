import json
import os

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


def get_examples():
    """Finds all subdirectories in examples/"""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    examples_dir = os.path.join(root_dir, "examples")
    return [
        d
        for d in os.listdir(examples_dir)
        if os.path.isdir(os.path.join(examples_dir, d))
    ]


@pytest.mark.parametrize("example_name", get_examples())
def test_golden_examples(example_name):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    example_path = os.path.join(root_dir, "examples", example_name)
    compose_path = os.path.join(example_path, "compose.yml")
    expected_path = os.path.join(example_path, "expected", "main.tf.json")

    # Run the compiler
    actual_tf_json = compile_to_terraform(compose_path, FIXED_ENV, example_name)

    # Update logic: If the expected file doesn't exist, create it
    if not os.path.exists(expected_path):
        os.makedirs(os.path.dirname(expected_path), exist_ok=True)
        with open(expected_path, "w") as f:
            f.write(actual_tf_json)
        pytest.skip(
            f"Generated expected file for example: {example_name}. Review and commit it."
        )

    with open(expected_path, "r") as f:
        expected_tf_json = f.read()

    assert json.loads(actual_tf_json) == json.loads(expected_tf_json)
