import json

from ..models.aws import (
    AWSResources,
    ContainerDefinition,
    EcsService,
    EcsTaskDefinition,
    SecurityGroup,
    SecurityGroupRule,
)
from ..models.environment import Environment
from ..models.semantic import Application as SemanticApp


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

    # 2. Map each Semantic Service to AWS resources
    for service in app.services:
        if service.capability == "database":
            # Managed RDS Instance
            engine = "postgres"
            port = 5432
            if "mysql" in service.image.lower():
                engine = "mysql"
                port = 3306
            elif "mariadb" in service.image.lower():
                engine = "mariadb"
                port = 3306

            # 1. Create a secret for the database master password
            db_secret_key = f"{service.name}_db_password"
            resources.aws_secretsmanager_secret[db_secret_key] = {
                "name": get_name(f"{service.name}-db-password"),
                "description": f"Master password for {service.name} RDS",
            }

            sng_key = f"{service.name}_sng"
            resources.aws_db_subnet_group[sng_key] = {
                "name": get_name(f"{service.name}-sng"),
                "subnet_ids": env.private_subnets,
            }

            db_key = f"{service.name}_db"
            resources.aws_db_instance[db_key] = {
                "identifier": get_name(service.name),
                "engine": engine,
                "instance_class": "db.t3.micro",
                "allocated_storage": 20,
                "db_subnet_group_name": f"${{aws_db_subnet_group.{sng_key}.name}}",
                "vpc_security_group_ids": [f"${{aws_security_group.{app_sg_key}.id}}"],
                "skip_final_snapshot": True,
                "publicly_accessible": False,
                "username": "admin",
                "password": f"${{aws_secretsmanager_secret.{db_secret_key}.id}}",  # Placeholder reference
            }
            continue

        if service.capability == "cache":
            # Managed ElastiCache (Redis)
            sng_key = f"{service.name}_sng"
            resources.aws_elasticache_subnet_group[sng_key] = {
                "name": get_name(f"{service.name}-sng"),
                "subnet_ids": env.private_subnets,
            }

            cache_key = f"{service.name}_cache"
            resources.aws_elasticache_cluster[cache_key] = {
                "cluster_id": get_name(service.name),
                "engine": "redis",
                "node_type": "cache.t3.micro",
                "num_cache_nodes": 1,
                "subnet_group_name": f"${{aws_elasticache_subnet_group.{sng_key}.name}}",
                "security_group_ids": [f"${{aws_security_group.{app_sg_key}.id}}"],
            }
            continue

        # Standard Container (ECS Fargate)
        # Create IAM Roles for the service
        task_role_key = f"{service.name}_task_role"
        resources.aws_iam_role[task_role_key] = {
            "name": get_name(f"{service.name}-task-role"),
            "assume_role_policy": json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": "sts:AssumeRole",
                            "Effect": "Allow",
                            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                        }
                    ],
                }
            ),
        }

        exec_role_key = f"{service.name}_exec_role"
        resources.aws_iam_role[exec_role_key] = {
            "name": get_name(f"{service.name}-exec-role"),
            "assume_role_policy": json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": "sts:AssumeRole",
                            "Effect": "Allow",
                            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                        }
                    ],
                }
            ),
        }

        # Resolve storage to S3 buckets and IAM policies
        for bucket_name in service.storage:
            safe_id = "".join(c if c.isalnum() else "_" for c in bucket_name).strip("_")
            bucket_key = f"{service.name}_{safe_id}_bucket"

            resources.aws_s3_bucket[bucket_key] = {
                "bucket": get_name(f"{service.name}-{safe_id}")
                .lower()
                .replace("_", "-")[:63],
                "force_destroy": True,
            }

            policy_key = f"{service.name}_{safe_id}_policy"
            resources.aws_iam_role_policy[policy_key] = {
                "name": get_name(f"{service.name}-{safe_id}-policy"),
                "role": f"${{aws_iam_role.{task_role_key}.name}}",
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

            # Grant Exec Role access to read the secret
            secret_policy_key = f"{service.name}_{secret_name}_policy"
            resources.aws_iam_role_policy[secret_policy_key] = {
                "name": get_name(f"{service.name}-{secret_name}-policy"),
                "role": f"${{aws_iam_role.{exec_role_key}.name}}",
                "policy": json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": ["secretsmanager:GetSecretValue"],
                                "Resource": [
                                    f"${{aws_secretsmanager_secret.{secret_key}.arn}}"
                                ],
                            }
                        ],
                    }
                ),
            }

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
            execution_role_arn=f"${{aws_iam_role.{exec_role_key}.arn}}",
            task_role_arn=f"${{aws_iam_role.{task_role_key}.arn}}",
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

    # 3. Dynamic Link Injection (Service Discovery)
    # If a service depends on a managed capability, inject the connection details
    for service in app.services:
        if service.capability != "container":
            continue

        service_key = f"{service.name}_service"
        # We need to find the ECS task definition for this service
        task_def_key = f"{service.name}_td"
        if task_def_key not in resources.aws_ecs_task_definition:
            continue

        task_def = resources.aws_ecs_task_definition[task_def_key]
        container_defs = json.loads(task_def.container_definitions)
        container = container_defs[0]

        # Check all relationships where this service is the client
        for rel in [r for r in app.relationships if r.client == service.name]:
            server = next((s for s in app.services if s.name == rel.server), None)
            if not server or server.capability == "container":
                continue

            # Server is a managed service (DB or Cache)
            address = ""
            if server.capability == "database":
                db_key = f"{server.name}_db"
                address = f"${{aws_db_instance.{db_key}.address}}"
            elif server.capability == "cache":
                cache_key = f"{server.name}_cache"
                address = (
                    f"${{aws_elasticache_cluster.{cache_key}.cache_nodes[0].address}}"
                )

            # Replace any env vars that were pointing to the local name
            for env_var in container["environment"]:
                if env_var["value"] == server.name:
                    env_var["value"] = address

        task_def.container_definitions = json.dumps(container_defs)

    # 4. Infer Security Group Rules from Relationships
    for rel in app.relationships:
        rule_key = f"{rel.client}_to_{rel.server}_rule"
        server_service = next((s for s in app.services if s.name == rel.server), None)

        # Determine port based on capability if not explicitly provided
        default_port = 80
        if server_service:
            if server_service.capability == "database":
                default_port = (
                    3306
                    if "mysql" in server_service.image.lower()
                    or "mariadb" in server_service.image.lower()
                    else 5432
                )
            elif server_service.capability == "cache":
                default_port = 6379
            elif server_service.port:
                default_port = server_service.port

        port = rel.port or default_port

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
