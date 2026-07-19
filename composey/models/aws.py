from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SecurityGroupRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["ingress", "egress"]
    from_port: int
    to_port: int
    protocol: Literal["tcp", "udp", "icmp", "all", "-1"]
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
    secrets: List[Dict[str, str]] = Field(default_factory=list)
    logConfiguration: Optional[Dict[str, Any]] = None


class EcsTaskDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: str
    network_mode: Literal["bridge", "host", "awsvpc", "none"] = "awsvpc"
    requires_compatibilities: List[Literal["EC2", "FARGATE", "EXTERNAL"]] = ["FARGATE"]
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
    launch_type: Literal["EC2", "FARGATE", "EXTERNAL"] = "FARGATE"

    network_configuration: Dict[str, Any]  # Subnets and SGs
    load_balancer: List[Dict[str, Any]] = Field(default_factory=list)


class SecurityGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    vpc_id: str
    description: str


class S3Bucket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bucket: str
    force_destroy: bool = True


class IamRole(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    assume_role_policy: str


class IamRolePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    role: str
    policy: str


class DbInstance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifier: str
    engine: Literal["postgres", "mysql", "mariadb"]
    instance_class: str
    allocated_storage: int
    db_subnet_group_name: str
    vpc_security_group_ids: List[str]
    skip_final_snapshot: bool = True
    publicly_accessible: bool = False
    username: Optional[str] = None
    password: Optional[str] = None


class DbSubnetGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    subnet_ids: List[str]


class ElastiCacheCluster(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cluster_id: str
    engine: Literal["redis", "memcached"]
    node_type: str
    num_cache_nodes: int
    subnet_group_name: str
    security_group_ids: List[str]


class ElastiCacheSubnetGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    subnet_ids: List[str]


class LbTargetGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    port: int
    protocol: Literal["HTTP", "HTTPS", "TCP", "TLS", "UDP", "TCP_UDP", "GENEVE"]
    vpc_id: str
    target_type: Literal["instance", "ip", "lambda", "alb"]
    health_check: Optional[Dict[str, Any]] = None


class LbListenerRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    listener_arn: str
    priority: int
    action: List[Dict[str, Any]]
    condition: List[Dict[str, Any]]


class SecretsManagerSecret(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: Optional[str] = None


class AWSResources(BaseModel):
    """
    A registry of the AWS resources our compiler supports.
    """

    aws_ecs_task_definition: Dict[str, EcsTaskDefinition] = Field(default_factory=dict)
    aws_ecs_service: Dict[str, EcsService] = Field(default_factory=dict)
    aws_security_group: Dict[str, SecurityGroup] = Field(default_factory=dict)
    aws_security_group_rule: Dict[str, SecurityGroupRule] = Field(default_factory=dict)
    aws_cloudwatch_log_group: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    aws_lb_target_group: Dict[str, LbTargetGroup] = Field(default_factory=dict)
    aws_lb_listener_rule: Dict[str, LbListenerRule] = Field(default_factory=dict)
    aws_secretsmanager_secret: Dict[str, SecretsManagerSecret] = Field(
        default_factory=dict
    )
    aws_s3_bucket: Dict[str, S3Bucket] = Field(default_factory=dict)
    aws_iam_role: Dict[str, IamRole] = Field(default_factory=dict)
    aws_iam_role_policy: Dict[str, IamRolePolicy] = Field(default_factory=dict)
    aws_db_instance: Dict[str, DbInstance] = Field(default_factory=dict)
    aws_elasticache_cluster: Dict[str, ElastiCacheCluster] = Field(default_factory=dict)
    aws_db_subnet_group: Dict[str, DbSubnetGroup] = Field(default_factory=dict)
    aws_elasticache_subnet_group: Dict[str, ElastiCacheSubnetGroup] = Field(
        default_factory=dict
    )
