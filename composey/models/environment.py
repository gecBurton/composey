from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field


class Environment(BaseModel):
    """
    Infrastructure context owned by the platform team.
    Describes the target environment where applications are deployed.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Environment name (e.g., production, staging)")
    vpc_id: str = Field(description="The VPC ID")
    public_subnets: List[str] = Field(description="List of public subnet IDs for ALBs")
    private_subnets: List[str] = Field(
        description="List of private subnet IDs for tasks"
    )
    ecs_cluster_arn: str = Field(description="The ARN of the ECS Cluster")
    region: str = Field(default="us-east-1", description="The AWS region")
    alb_arn: Optional[str] = Field(
        default=None, description="The ARN of the shared Application Load Balancer"
    )
    alb_listener_arn: Optional[str] = Field(
        default=None, description="The ARN of the HTTPS/HTTP listener on the ALB"
    )
    tags: Optional[Dict[str, str]] = Field(
        default=None, description="Default tags for all resources"
    )
    aws_endpoint: Optional[str] = Field(
        default=None,
        description="Optional custom endpoint for AWS services (e.g., for LocalStack)",
    )

    @classmethod
    def from_yaml(cls, path: str) -> "Environment":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
