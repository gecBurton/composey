# Composey docker-compose to terraform compiler

## Goal

Provide a PaaS-like deployment experience where application engineers deploy an annotated Docker Compose file into an Environment.

The compiler is responsible for inferring AWS infrastructure and generating Terraform JSON.

The engineer never writes Terraform.

---

# Non-goals (v1)

* Multi-cloud
* Kubernetes
* Arbitrary Terraform generation
* Every Compose feature
* Every AWS service
* Runtime reconciliation

---

# Inputs

## Application

```
docker-compose.yml
```

Optional extensions:

```
x-platform:
```

---

## Environment

```
production.yaml
```

Owned exclusively by the platform team.

Describes:

* ECS Cluster
* VPC
* Subnets
* Domains
* Default service sizes
* Default database sizes
* Logging
* Tags
* Shared resources

---

# Output

```
terraform/
    main.tf.json
    variables.tf.json
    outputs.tf.json
```

Must be deterministic.

---

# Compiler stages

```
Compose
↓
Parse
↓
Normalize
↓
Infer
↓
Application Model
↓
Terraform JSON
```

Each stage should be testable independently.

---

# Semantic model

The semantic model must not contain AWS concepts.

Good:

```
Application
Service
Database
Cache
Ingress
Storage
Queue
```

Bad:

```
Security Group
Target Group
Subnet
Task Definition
ECS Cluster
```

---

# Managed capabilities

Initially support only:

```
Container
Postgres
Redis
S3
Secret
Public HTTP
Worker
```

Everything else is an error.

---

# Inference rules

Examples:

```
postgres image
      ↓
Managed Postgres
```

```
redis image
      ↓
Managed Redis
```

```
ports
      ↓
Public ingress
```

```
depends_on
      ↓
Security Group rules
```

---

# Environment responsibilities

Environment owns:

* VPC
* ECS Cluster
* ALBs
* ACM
* Route53
* CloudMap
* Logging
* IAM defaults
* Network defaults
* Tagging
* Naming conventions

Applications cannot override these.

---

# Application responsibilities

Application owns:

* Images
* Environment variables
* Dependencies
* Health checks
* Scaling profile
* Secrets required
* Managed capabilities required

---

# Compiler guarantees

The compiler must be deterministic.

Equivalent Compose files must generate byte-identical Terraform.

This implies:

* sorted output
* stable resource naming
* canonical JSON
* canonical ordering

---

# Testing

## Golden tests

```
compose.yml
↓
terraform/
```

Directory comparison.

---

## Validation tests

```
terraform validate
```

Must succeed.

---

## Integration tests

```
terraform apply
      ↓
LocalStack
      ↓
Assertions
```

---

## Acceptance tests

Nightly:

```
Terraform
      ↓
AWS sandbox
      ↓
Smoke tests
```

---

# Repository layout

```
compiler/
environment/
backend/
terraform/
model/
tests/
fixtures/
```

---

# Design principles

1. Compose is the application DSL.
2. Environment is the infrastructure DSL.
3. Terraform is a compilation target.
4. AWS is an implementation detail.
5. The semantic model is cloud agnostic.
6. Deterministic output is a feature.
7. Platform defaults are preferred over application configuration.
8. Developers describe intent, not infrastructure.
9. The compiler is stateless.
10. Every compiler stage is independently testable.

---

## The one requirement I'd add above all the others

I'd write this at the top of the design document:

> **Every feature must reduce the amount of AWS knowledge required by an application engineer.**

That's a surprisingly powerful filter. Whenever you're considering adding an annotation or exposing another AWS option, ask: *"Does this make the application engineer think more about AWS, or less?"*

If it's the former, the feature probably belongs in the **Environment** or the compiler, not in the application manifest.

I think that's the principle that will keep your platform elegant as it grows. It's also why I like the architecture we've converged on:

* **Compose** describes the application.
* **Environment** describes where it runs.
* **Compiler** decides how to realize it on AWS.
* **Terraform** is just the implementation artifact.

That's a clean separation of concerns, and one that should scale well as you add more capabilities over time.
Jot something down