import json
import os

import pytest
from utils import get_examples

from composey.compiler import compile_to_terraform


@pytest.mark.parametrize("example_name", get_examples())
def test_golden_examples(example_name, mock_prod_env):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    example_path = os.path.join(root_dir, "examples", example_name)
    compose_path = os.path.join(example_path, "compose.yml")
    expected_path = os.path.join(example_path, "expected", "main.tf.json")

    # Run the compiler
    actual_tf_json = compile_to_terraform(compose_path, mock_prod_env, example_name)

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
