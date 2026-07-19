import os
import shutil
import subprocess
import tempfile

import pytest
from utils import get_examples

from compiler import compile_to_terraform


@pytest.mark.parametrize("example_name", get_examples())
def test_terraform_validate(example_name, terraform_base, mock_prod_env):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    example_path = os.path.join(root_dir, "examples", example_name)
    compose_path = os.path.join(example_path, "compose.yml")

    # 1. Compile
    tf_json = compile_to_terraform(compose_path, mock_prod_env, example_name)

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
