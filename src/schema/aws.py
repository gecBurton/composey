from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SecurityGroupRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str  # ingress/egress
    from_port: int
    to_port: int
    protocol: str
    cidr_blocks: Optional[List[str]] = None
    source_security_group_id: Optional[str] = None
    security_group_id: str
    description: Optional[str] = None


class ContainerDefinition(BaseModel):
    """
    Partial model for ECS Container Definitions
    """

    name: str
    image: str
    essential: bool = True
    portMappings: List[Dict[str, Any]] = Field(default_factory=list)
    environment: List[Dict[str, str]] = Field(default_factory=list)
    logConfiguration: Optional[Dict[str, Any]] = None


class EcsTaskDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: str
    network_mode: str = "awsvpc"
    requires_compatibilities: List[str] = ["FARGATE"]
    cpu: str
    memory: str
    container_definitions: str  # We usually jsonencode the ContainerDefinition list
    execution_role_arn: str
    task_role_arn: Optional[str] = None


class EcsService(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    cluster: str
    task_definition: str
    desired_count: int = 1
    launch_type: str = "FARGATE"

    network_configuration: Dict[str, Any]  # Subnets and SGs
    load_balancer: List[Dict[str, Any]] = Field(default_factory=list)


class SecurityGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    vpc_id: str
    description: str


class Environment(BaseModel):
    """
    Infrastructure context owned by the platform team.
    Describes the target AWS environment where applications are deployed.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Environment name (e.g., production, staging)")
    vpc_id: str = Field(description="The AWS VPC ID")
    public_subnets: List[str] = Field(description="List of public subnet IDs for ALBs")
    private_subnets: List[str] = Field(
        description="List of private subnet IDs for Fargate tasks"
    )
    ecs_cluster_arn: str = Field(description="The ARN of the ECS Cluster")
    alb_arn: Optional[str] = Field(
        default=None, description="The ARN of the shared Application Load Balancer"
    )
    alb_listener_arn: Optional[str] = Field(
        default=None, description="The ARN of the HTTPS/HTTP listener on the ALB"
    )
    base_domain: Optional[str] = Field(
        default=None,
        description="The base domain for the environment (e.g., example.com)",
    )
    tags: Dict[str, str] = Field(
        default_factory=dict, description="Default tags for all resources"
    )


class AWSResources(BaseModel):
    """
    A registry of the AWS resources our compiler supports.
    """

    aws_ecs_task_definition: Dict[str, EcsTaskDefinition] = Field(default_factory=dict)
    aws_ecs_service: Dict[str, EcsService] = Field(default_factory=dict)
    aws_security_group: Dict[str, SecurityGroup] = Field(default_factory=dict)
    aws_security_group_rule: Dict[str, SecurityGroupRule] = Field(default_factory=dict)
    aws_cloudwatch_log_group: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    aws_lb_target_group: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    aws_lb_listener_rule: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
