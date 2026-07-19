from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from .aws import AWSResources


class TerraformManifest(BaseModel):
    """
    The root structure of a terraform.tf.json file.
    """

    model_config = ConfigDict(extra="ignore")

    terraform: Optional[Dict[str, Any]] = Field(default=None)
    provider: Optional[Dict[str, Any]] = Field(default=None)
    variable: Optional[Dict[str, Any]] = Field(default=None)
    resource: AWSResources = Field(default_factory=AWSResources)
    output: Optional[Dict[str, Any]] = Field(default=None)
