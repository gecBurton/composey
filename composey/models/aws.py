from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class TerraformLifecycle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    create_before_destroy: Optional[bool] = None
    prevent_destroy: Optional[bool] = None
    ignore_changes: Optional[List[str]] = None


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
    tags: Optional[Dict[str, str]] = None


class EcsService(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    cluster: str
    task_definition: str
    desired_count: int = 1
    launch_type: Literal["EC2", "FARGATE", "EXTERNAL"] = "FARGATE"

    network_configuration: Dict[str, Any]  # Subnets and SGs
    load_balancer: List[Dict[str, Any]] = Field(default_factory=list)
    tags: Optional[Dict[str, str]] = None


class SecurityGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    vpc_id: str
    description: str
    tags: Optional[Dict[str, str]] = None


class S3Bucket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bucket: str
    force_destroy: bool = True
    tags: Optional[Dict[str, str]] = None


class IamRole(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    assume_role_policy: str
    tags: Optional[Dict[str, str]] = None


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
    tags: Optional[Dict[str, str]] = None


class DbSubnetGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    subnet_ids: List[str]
    tags: Optional[Dict[str, str]] = None


class ElastiCacheCluster(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cluster_id: str
    engine: Literal["redis", "memcached"]
    node_type: str
    num_cache_nodes: int
    subnet_group_name: str
    security_group_ids: List[str]
    tags: Optional[Dict[str, str]] = None


class ElastiCacheSubnetGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    subnet_ids: List[str]
    tags: Optional[Dict[str, str]] = None


class LbTargetGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    port: int
    protocol: Literal["HTTP", "HTTPS", "TCP", "TLS", "UDP", "TCP_UDP", "GENEVE"]
    vpc_id: str
    target_type: Literal["instance", "ip", "lambda", "alb"]
    health_check: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None


class LbListenerRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    listener_arn: str
    priority: int
    action: List[Dict[str, Any]]
    condition: List[Dict[str, Any]]
    tags: Optional[Dict[str, str]] = None


class SecretsManagerSecret(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class SecretsManagerSecretVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    secret_id: str
    secret_string: str
    lifecycle: Optional[TerraformLifecycle] = None


class RandomPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")

    length: int = 16
    special: bool = False


class CloudWatchLogGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    retention_in_days: int = 7
    tags: Optional[Dict[str, str]] = None


class AppAutoscalingTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_capacity: int
    min_capacity: int
    resource_id: str
    scalable_dimension: str = "ecs:service:DesiredCount"
    service_namespace: str = "ecs"


class AppAutoscalingPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    policy_type: str = "TargetTrackingScaling"
    resource_id: str
    scalable_dimension: str = "ecs:service:DesiredCount"
    service_namespace: str = "ecs"
    target_tracking_scaling_policy_configuration: Dict[str, Any]


class AWSResources(BaseModel):
    """
    A registry of the AWS resources our compiler supports.
    """

    aws_ecs_task_definition: Dict[str, EcsTaskDefinition] = Field(default_factory=dict)
    aws_ecs_service: Dict[str, EcsService] = Field(default_factory=dict)
    aws_appautoscaling_target: Dict[str, AppAutoscalingTarget] = Field(
        default_factory=dict
    )
    aws_appautoscaling_policy: Dict[str, AppAutoscalingPolicy] = Field(
        default_factory=dict
    )
    aws_security_group: Dict[str, SecurityGroup] = Field(default_factory=dict)
    aws_security_group_rule: Dict[str, SecurityGroupRule] = Field(default_factory=dict)
    aws_cloudwatch_log_group: Dict[str, CloudWatchLogGroup] = Field(
        default_factory=dict
    )
    aws_lb_target_group: Dict[str, LbTargetGroup] = Field(default_factory=dict)
    aws_lb_listener_rule: Dict[str, LbListenerRule] = Field(default_factory=dict)
    aws_secretsmanager_secret: Dict[str, SecretsManagerSecret] = Field(
        default_factory=dict
    )
    aws_secretsmanager_secret_version: Dict[str, SecretsManagerSecretVersion] = Field(
        default_factory=dict
    )
    random_password: Dict[str, RandomPassword] = Field(default_factory=dict)
    aws_s3_bucket: Dict[str, S3Bucket] = Field(default_factory=dict)
    aws_iam_role: Dict[str, IamRole] = Field(default_factory=dict)
    aws_iam_role_policy: Dict[str, IamRolePolicy] = Field(default_factory=dict)
    aws_db_instance: Dict[str, DbInstance] = Field(default_factory=dict)
    aws_elasticache_cluster: Dict[str, ElastiCacheCluster] = Field(default_factory=dict)
    aws_db_subnet_group: Dict[str, DbSubnetGroup] = Field(default_factory=dict)
    aws_elasticache_subnet_group: Dict[str, ElastiCacheSubnetGroup] = Field(
        default_factory=dict
    )
