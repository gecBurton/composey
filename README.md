# Composey: Docker Compose to Terraform Compiler

> [!CAUTION]
> **Project Status: PRE-ALPHA**
> This project is in early development. APIs, models, and generated infrastructure are subject to breaking changes. Not recommended for production use yet.

Composey provides a PaaS-like deployment experience where application engineers deploy an annotated Docker Compose file into an established Environment. The compiler is responsible for inferring AWS infrastructure and generating deterministic Terraform JSON.

**The engineer describes intent; the compiler handles the infrastructure.**

---

## 🚀 Progress & Goals Tracker

### Compiler Pipeline
- [x] **Parse**: Sanitize and load Compose files via `docker compose config`.
- [x] **Normalize**: Transform Compose into a cloud-agnostic semantic model.
- [x] **Infer**: Map semantic intent + environment context to AWS resources.
- [x] **Generate**: Produce deterministic, canonical Terraform JSON.

### Managed Capabilities (v1)
- [x] **Container**: Standard ECS Fargate task deployment.
- [x] **Public HTTP**: Automatic ALB ingress routing for services on port 80/443.
- [x] **Secrets**: Automatic mapping of Compose `secrets` to AWS Secrets Manager.
- [x] **Storage**: Automatic mapping of `volumes` to AWS S3 Buckets.
- [ ] **Managed Postgres**: Infer RDS instance from `postgres` image. *(In Progress)*
- [ ] **Managed Redis**: Infer ElastiCache from `redis` image. *(Pending)*
- [x] **Worker**: Support for background services without public ports.

### Quality & Guarantees
- [x] **Determinism**: Byte-identical output for equivalent inputs (canonical JSON/sorting).
- [x] **Isolation**: Full application-level network and identity isolation.
- [x] **Golden Testing**: Regression protection via example snapshots.
- [x] **Terraform Validation**: CI verification using `terraform validate`.
- [x] **Cloud Fidelity**: Integration testing via `LocalStack`.
- [ ] **Acceptance Testing**: Automated nightly runs in a real AWS sandbox. *(Pending)*

---

## 🛠 Design Principles

1. **Compose is the application DSL.**
2. **Environment is the infrastructure DSL.** (Owned by the Platform Team).
3. **Terraform is a compilation target.**
4. **AWS is an implementation detail.**
5. **The semantic model is cloud-agnostic.**
6. **Deterministic output is a feature.**
7. **Platform defaults are preferred over application configuration.**
8. **Developers describe intent, not infrastructure.**
9. **The compiler is stateless.**
10. **Every compiler stage is independently testable.**

> **Core Philosophy:** Every feature must reduce the amount of AWS knowledge required by an application engineer.

---

## 📦 Usage (Development)

### Requirements
- Python 3.12+
- `uv` (recommended)
- Docker & Docker Compose v2
- Terraform CLI

### Running Tests
The test suite includes unit tests, snapshot comparisons, and local cloud deployment verification.

```bash
make test
```

### Repository Structure
- `src/compiler/`: The logic for each compilation stage.
- `src/models/`: Pydantic schemas for Compose, Semantic, AWS, and Environment models.
- `examples/`: End-to-end examples that serve as documentation and "Golden" test snapshots.
- `tests/`: High-fidelity test suite (Unit, Integration, LocalStack).
