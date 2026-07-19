import json

from models.aws import AWSResources
from models.terraform import TerraformManifest


def generate(resources: AWSResources) -> str:
    manifest = TerraformManifest(resource=resources)

    # Use model_dump to get a dict, then sort keys for determinism
    data = manifest.model_dump(exclude_none=True, by_alias=True)

    return json.dumps(data, indent=2, sort_keys=True)
