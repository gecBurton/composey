import json

from models.aws import (
    AWSResources,
    ContainerDefinition,
    EcsService,
    EcsTaskDefinition,
    SecurityGroup,
    SecurityGroupRule,
)
from models.environment import Environment
from models.semantic import Application as SemanticApp


def infer(app: SemanticApp, env: Environment) -> AWSResources:
    resources = AWSResources()

    # Naming convention helper: [env]-[app]-[resource]
    def get_name(resource_name: str) -> str:
        return f"{env.name}-{app.name}-{resource_name}"

    # 1. Create a shared Security Group for the whole application
    app_sg_key = "app_sg"
    resources.aws_security_group[app_sg_key] = SecurityGroup(
        name=get_name("sg"),
        vpc_id=env.vpc_id,
        description=f"Security group for {app.name} in {env.name}",
    )

    # 2. Map each Semantic Service to ECS Fargate resources
    for service in app.services:
        # Resolve storage to S3 buckets and IAM policies
        for bucket_name in service.storage:
            # Sanitize for Terraform identifier (alphanumeric and underscore)
            # Remove characters like / or . which often appear in path-based volume names
            safe_id = "".join(c if c.isalnum() else "_" for c in bucket_name).strip("_")
            bucket_key = f"{service.name}_{safe_id}_bucket"

            resources.aws_s3_bucket[bucket_key] = {
                # S3 bucket name: lowercase, alphanumeric and hyphens only
                "bucket": get_name(f"{service.name}-{safe_id}")
                .lower()
                .replace("_", "-")[:63],
                "force_destroy": True,
            }

            policy_key = f"{service.name}_{safe_id}_policy"
            resources.aws_iam_role_policy[policy_key] = {
                "name": get_name(f"{service.name}-{safe_id}-policy"),
                "role": "execution_role_placeholder",
                "policy": json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": ["s3:*"],
                                "Resource": [
                                    f"${{aws_s3_bucket.{bucket_key}.arn}}",
                                    f"${{aws_s3_bucket.{bucket_key}.arn}}/*",
                                ],
                            }
                        ],
                    }
                ),
            }

        # Resolve secrets to AWS Secrets Manager references
        container_secrets = []
        for secret_name in service.secrets:
            secret_key = f"{service.name}_{secret_name}_secret"
            resources.aws_secretsmanager_secret[secret_key] = {
                "name": get_name(f"{service.name}-{secret_name}"),
                "description": f"Secret {secret_name} for {app.name} service {service.name}",
            }
            container_secrets.append(
                {
                    "name": secret_name.upper().replace("-", "_"),
                    "valueFrom": f"${{aws_secretsmanager_secret.{secret_key}.arn}}",
                }
            )

        # Container Definition
        container = ContainerDefinition(
            name=service.name,
            image=service.image,
            portMappings=[
                {
                    "containerPort": service.port,
                    "hostPort": service.port,
                    "protocol": "tcp",
                }
            ]
            if service.port
            else [],
            environment=[{"name": k, "value": v} for k, v in service.env.items()],
            secrets=container_secrets,
        )

        # Task Definition
        task_def_key = f"{service.name}_td"
        resources.aws_ecs_task_definition[task_def_key] = EcsTaskDefinition(
            family=get_name(service.name),
            cpu=str(service.cpu),
            memory=str(service.memory),
            container_definitions=json.dumps([container.model_dump(exclude_none=True)]),
            execution_role_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
        )

        # ECS Service
        service_key = f"{service.name}_service"
        ecs_service = EcsService(
            name=get_name(service.name),
            cluster=env.ecs_cluster_arn,
            task_definition=f"${{aws_ecs_task_definition.{task_def_key}.arn}}",
            network_configuration={
                "subnets": env.private_subnets,
                "security_groups": [f"${{aws_security_group.{app_sg_key}.id}}"],
                "assign_public_ip": False,
            },
        )

        # 4. Handle Public Ingress (ALB integration)
        if app.public_service == service.name and env.alb_arn:
            tg_key = f"{service.name}_tg"
            resources.aws_lb_target_group[tg_key] = {
                "name": get_name(f"{service.name}-tg"),
                "port": service.port or 80,
                "protocol": "HTTP",
                "vpc_id": env.vpc_id,
                "target_type": "ip",
                "health_check": {"enabled": True, "path": "/", "matcher": "200-399"},
            }

            if env.alb_listener_arn:
                rule_key = f"{service.name}_listener_rule"
                resources.aws_lb_listener_rule[rule_key] = {
                    "listener_arn": env.alb_listener_arn,
                    "priority": 100,
                    "action": [
                        {
                            "type": "forward",
                            "target_group_arn": f"${{aws_lb_target_group.{tg_key}.arn}}",
                        }
                    ],
                    "condition": [{"path_pattern": {"values": ["/*"]}}],
                }

            ecs_service.load_balancer = [
                {
                    "target_group_arn": f"${{aws_lb_target_group.{tg_key}.arn}}",
                    "container_name": service.name,
                    "container_port": service.port or 80,
                }
            ]

            # Add SG rule to allow ALB to talk to the shared app SG on this service's port
            alb_ingress_rule_key = f"alb_to_{service.name}_rule"
            resources.aws_security_group_rule[alb_ingress_rule_key] = SecurityGroupRule(
                type="ingress",
                from_port=service.port or 80,
                to_port=service.port or 80,
                protocol="tcp",
                security_group_id=f"${{aws_security_group.{app_sg_key}.id}}",
                cidr_blocks=["0.0.0.0/0"],
                description=f"Allow ALB to talk to {service.name}",
            )

        resources.aws_ecs_service[service_key] = ecs_service

    # 3. Infer Security Group Rules from Relationships
    for rel in app.relationships:
        rule_key = f"{rel.client}_to_{rel.server}_rule"

        server_service = next((s for s in app.services if s.name == rel.server), None)
        port = rel.port or (
            server_service.port if server_service and server_service.port else 80
        )

        # Since it's a shared SG, the rule allows traffic from the SG to itself
        resources.aws_security_group_rule[rule_key] = SecurityGroupRule(
            type="ingress",
            from_port=port,
            to_port=port,
            protocol="tcp",
            security_group_id=f"${{aws_security_group.{app_sg_key}.id}}",
            source_security_group_id=f"${{aws_security_group.{app_sg_key}.id}}",
            description=f"Allow {rel.client} to talk to {rel.server}",
        )

    return resources
