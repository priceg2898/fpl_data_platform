# Recommended Architecture

```text
GitHub Actions
    ↓
OIDC federation to AWS IAM (no long-lived secrets)
    ↓
Build image with BuildKit/buildx
    ↓
Run tests + security scans
    ↓
Push immutable image to ECR
    ↓
Deploy by digest (not mutable tag)
```

---

# 1. Use GitHub OIDC Instead of AWS Keys

Do **NOT** store:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

in GitHub secrets unless absolutely necessary.

Instead:

- configure GitHub OIDC trust with AWS IAM
- allow GitHub Actions to assume a role temporarily

This is now the standard secure pattern.

Useful docs:

- https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html

---

# 2. Separate Build and Deploy Concerns

A common mistake is:

```text
build + push + deploy
```

all in one workflow/job.

Better:

## CI workflow

Triggered on:

- PRs
- pushes to `main`

Responsibilities:

- lint
- test
- build image
- optionally push dev image

## CD workflow

Triggered by:

- release
- tag
- manual approval
- environment promotion

Responsibilities:

- pull immutable image
- deploy existing digest

This prevents rebuilding different artifacts during deployment.

---

# 3. Tag Images Correctly

Avoid:

```text
latest
```

as your only tag.

Best practice is multiple tags:

```text
my-app:git-sha
my-app:branch-name
my-app:v1.8.2
my-app:latest   # optional convenience tag
```

Most important:

- always deploy by digest

Example:

```text
123456789.dkr.ecr.us-east-1.amazonaws.com/my-app@sha256:abc123...
```

Why:

- immutable
- auditable
- reproducible rollback

---

# 4. Use Multi-Stage Docker Builds

Typical pattern:

```dockerfile
FROM node:22 AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app

COPY --from=builder /app/dist ./dist

CMD ["node", "dist/index.js"]
```

Benefits:

- smaller images
- fewer vulnerabilities
- faster pulls
- cleaner runtime

---

# 5. Enable Layer Caching

Without caching, CI gets expensive and slow.

Use Docker Buildx cache.

Example:

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

This can reduce builds from minutes to seconds.

---

# 6. Scan Images Before Push or Deploy

At minimum:

- vulnerability scanning
- dependency scanning

Common tooling:

- Trivy
- Grype
- ECR enhanced scanning

Recommended:

- fail builds on critical vulns

Example:

```yaml
- uses: aquasecurity/trivy-action@master
```

---

# 7. Keep Runtime Images Minimal

Prefer:

- alpine
- distroless
- slim images

Avoid:

- full Ubuntu images unless needed

Examples:

- `node:22-alpine`
- `python:3.12-slim`

Distroless images:

- https://github.com/GoogleContainerTools/distroless

---

# 8. Never Bake Secrets Into Images

Do **NOT** do this:

```dockerfile
ENV DATABASE_PASSWORD=...
```

Use instead:

- ECS task secrets
- Kubernetes secrets
- AWS Secrets Manager
- SSM Parameter Store

Images should be environment-agnostic.

---

# 9. Use Least-Privilege IAM

Your GitHub deploy role should only allow:

- ECR push/pull
- specific repo access
- maybe ECS/EKS deployment

Avoid:

```json
"Action": "*"
```

---

# 10. Use a Reusable Workflow

In larger orgs:

```text
.github/workflows/
    docker-build.yml
    deploy.yml
```

Then reuse with:

```yaml
uses: org/repo/.github/workflows/docker-build.yml@main
```

This standardizes:

- security
- tagging
- scanning
- caching

---

# Example “Good” GitHub Actions Workflow

```yaml
name: build-and-push

on:
  push:
    branches:
      - main

permissions:
  id-token: write
  contents: read

jobs:
  docker:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-ecr
          aws-region: us-east-1

      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:${{ github.sha }}
            123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

# 11. Promote Images Instead of Rebuilding

This is one of the biggest maturity indicators.

Bad:

```text
build separately for staging and prod
```

Good:

```text
build once
promote same digest across environments
```

Example progression:

```text
dev → staging → prod
```

using the exact same image digest.

---

# 12. Add Supply Chain Security

Modern best practices increasingly include:

- SBOM generation
- image signing
- provenance attestation

Tools:

- cosign
- syft
- GitHub artifact attestations

Example stack:

- Syft → SBOM
- Cosign → sign image
- Verify signature during deploy

Docs:

- https://docs.sigstore.dev/cosign/overview/

---

# 13. Keep ECR Repositories Organized

Typical layout:

```text
my-app-dev
my-app-staging
my-app-prod
```

or:

```text
platform/my-app
platform/api
platform/worker
```

Enable:

- lifecycle policies
- image scanning
- encryption

Lifecycle rules matter a lot for cost control.

---

# 14. Recommended Tagging Strategy

A clean pattern:

```text
sha-<commit>
main
vX.Y.Z
```

Example:

```text
sha-a1b2c3d
v2.4.1
latest
```

Then deploy:

```text
@sha256:...
```

---

# 15. Common Anti-Patterns

Avoid:

## Rebuilding on Deploy

Creates drift.

## Using `latest` Everywhere

Breaks reproducibility.

## Long-Lived AWS Keys

Security risk.

## Huge Docker Contexts

Use `.dockerignore`.

## Running as Root

Use:

```dockerfile
USER node
```

## Single-Stage Builds

Bloated images.

---

# A Mature Production Setup Usually Includes

- GitHub Actions
- OIDC federation
- BuildKit/buildx
- cached multi-stage builds
- Trivy scanning
- immutable SHA tagging
- digest-based deploys
- signed images
- environment promotion
- reusable workflows

That’s the general “gold standard” pattern teams converge toward today.