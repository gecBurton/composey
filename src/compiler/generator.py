import json

from models.aws import AWSResources
from models.terraform import TerraformManifest


def generate(resources: AWSResources) -> str:
    manifest = TerraformManifest(
        terraform={
            "required_providers": {
                "aws": {"source": "hashicorp/aws", "version": "~> 5.0"}
            }
        },
        provider={"aws": {"region": "us-east-1"}},
        resource=resources,
    )

    # Use model_dump to get a dict, then sort keys for determinism
    data = manifest.model_dump(exclude_none=True, by_alias=True)

    # Cleanup: Remove empty resource type dictionaries
    # Terraform JSON fails if a resource type block (like "aws_s3_bucket") is empty.
    if "resource" in data:
        data["resource"] = {k: v for k, v in data["resource"].items() if v}

    return json.dumps(data, indent=2, sort_keys=True)
