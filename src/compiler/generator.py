import json

from models.aws import AWSResources
from models.environment import Environment
from models.terraform import TerraformManifest


def generate(resources: AWSResources, env: Environment) -> str:
    # Build provider configuration
    aws_provider = {"region": "us-east-1"}

    if env.aws_endpoint:
        aws_provider.update(
            {
                "access_key": "test",
                "secret_key": "test",
                "skip_credentials_validation": True,
                "skip_metadata_api_check": True,
                "skip_requesting_account_id": True,
                "s3_use_path_style": True,
                "endpoints": {
                    "s3": env.aws_endpoint,
                    "ecs": env.aws_endpoint,
                    "ec2": env.aws_endpoint,
                    "secretsmanager": env.aws_endpoint,
                    "iam": env.aws_endpoint,
                    "elasticloadbalancing": env.aws_endpoint,
                    "cloudwatch": env.aws_endpoint,
                    "logs": env.aws_endpoint,
                },
            }
        )

    manifest = TerraformManifest(
        terraform={
            "required_providers": {
                "aws": {"source": "hashicorp/aws", "version": "~> 5.0"}
            }
        },
        provider={"aws": aws_provider},
        resource=resources,
    )

    # Use model_dump to get a dict, then sort keys for determinism
    data = manifest.model_dump(exclude_none=True, by_alias=True)

    # Cleanup: Remove empty resource type dictionaries
    # Terraform JSON fails if a resource type block (like "aws_s3_bucket") is empty.
    if "resource" in data:
        data["resource"] = {k: v for k, v in data["resource"].items() if v}

    return json.dumps(data, indent=2, sort_keys=True)
