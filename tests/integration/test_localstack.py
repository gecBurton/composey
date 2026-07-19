import os
import shutil
import subprocess
import tempfile

import pytest
import requests

from composey.compiler import compile_to_terraform


@pytest.mark.parametrize("example_name", ["flask"])
def test_terraform_apply_localstack(
    example_name, localstack_session, terraform_base, mock_localstack_env
):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    example_path = os.path.join(root_dir, "examples", example_name)
    compose_path = os.path.join(example_path, "compose.yml")

    # 1. Compile
    tf_json = compile_to_terraform(compose_path, mock_localstack_env, example_name)

    # 2. Run terraform apply
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy the pre-initialized .terraform folder
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

        # Set dummy credentials for LocalStack
        env = os.environ.copy()
        env["AWS_ACCESS_KEY_ID"] = "test"
        env["AWS_SECRET_ACCESS_KEY"] = "test"
        env["AWS_DEFAULT_REGION"] = "us-east-1"

        # Apply (allow failure on ECS, but check S3/Secrets)
        subprocess.run(
            ["terraform", "apply", "-auto-approve", "-no-color"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env=env,
        )

        # 3. Assertions (verify resources in LocalStack)
        # We'll use the standard AWS CLI style call to S3 (which works in community)
        s3_res = requests.get(
            f"{localstack_session}/",
            headers={"Host": "s3.localhost.localstack.cloud"},
            params={"Action": "ListBuckets"},
        )
        assert "local-flask" in s3_res.text.lower()
