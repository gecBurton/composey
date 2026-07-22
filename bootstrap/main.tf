terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.region

  # LocalStack support: point every service at the same custom endpoint.
  dynamic "endpoints" {
    for_each = var.aws_endpoint == null ? [] : [var.aws_endpoint]

    content {
      ec2            = endpoints.value
      ecs            = endpoints.value
      elbv2          = endpoints.value
      iam            = endpoints.value
      sts            = endpoints.value
      logs           = endpoints.value
      s3             = endpoints.value
      secretsmanager = endpoints.value
    }
  }
}

locals {
  tags = merge(var.tags, { Environment = var.name })

  # Split the VPC into /20s: the first az_count blocks are public, the next are private.
  public_cidrs  = [for i in range(var.az_count) : cidrsubnet(var.vpc_cidr, 4, i)]
  private_cidrs = [for i in range(var.az_count) : cidrsubnet(var.vpc_cidr, 4, i + var.az_count)]

  listener_port     = var.certificate_arn == null ? 80 : 443
  listener_protocol = var.certificate_arn == null ? "HTTP" : "HTTPS"
}

data "aws_availability_zones" "available" {
  state = "available"
}

# --- Network ----------------------------------------------------------------

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.tags, { Name = var.name })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.tags, { Name = var.name })
}

resource "aws_subnet" "public" {
  count = var.az_count

  vpc_id                  = aws_vpc.this.id
  cidr_block              = local.public_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.tags, { Name = "${var.name}-public-${count.index}" })
}

resource "aws_subnet" "private" {
  count = var.az_count

  vpc_id            = aws_vpc.this.id
  cidr_block        = local.private_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.tags, { Name = "${var.name}-private-${count.index}" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(local.tags, { Name = "${var.name}-public" })
}

resource "aws_route_table_association" "public" {
  count = var.az_count

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# One NAT gateway per AZ so a single AZ failure cannot take out egress for the rest.
resource "aws_eip" "nat" {
  count = var.az_count

  domain = "vpc"
  tags   = merge(local.tags, { Name = "${var.name}-nat-${count.index}" })
}

resource "aws_nat_gateway" "this" {
  count = var.az_count

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  depends_on = [aws_internet_gateway.this]

  tags = merge(local.tags, { Name = "${var.name}-${count.index}" })
}

resource "aws_route_table" "private" {
  count = var.az_count

  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.this[count.index].id
  }

  tags = merge(local.tags, { Name = "${var.name}-private-${count.index}" })
}

resource "aws_route_table_association" "private" {
  count = var.az_count

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# --- Compute ----------------------------------------------------------------

resource "aws_ecs_cluster" "this" {
  name = var.name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.tags
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  cluster_name       = aws_ecs_cluster.this.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

# --- Shared load balancer ---------------------------------------------------

resource "aws_security_group" "alb" {
  count = var.create_alb ? 1 : 0

  name        = "${var.name}-alb"
  description = "Ingress to the shared ALB for ${var.name}"
  vpc_id      = aws_vpc.this.id

  ingress {
    from_port   = local.listener_port
    to_port     = local.listener_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

resource "aws_lb" "this" {
  count = var.create_alb ? 1 : 0

  name               = "${var.name}-alb"
  load_balancer_type = "application"
  subnets            = aws_subnet.public[*].id
  security_groups    = [aws_security_group.alb[0].id]

  tags = local.tags
}

# Default action is a hard 404: composey adds per-service rules onto this listener.
resource "aws_lb_listener" "this" {
  count = var.create_alb ? 1 : 0

  load_balancer_arn = aws_lb.this[0].arn
  port              = local.listener_port
  protocol          = local.listener_protocol
  ssl_policy        = var.certificate_arn == null ? null : "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }

  tags = local.tags
}
