# AI-SGP

AI-SGP is an open source AI Security Governance Platform for tracking AI systems through a secure SDLC lifecycle and generating examination-ready evidence packages.

## Architecture

```text
Browser -> Nginx -> React frontend
              |-> FastAPI backend -> PostgreSQL
                                |-> Redis
                                |-> MinIO
                                |-> Keycloak JWKS/OIDC
```

## Prerequisites

- Docker Desktop or Docker Engine with Compose v2
- Git
- Make, or Python 3.11 for the cross-platform scripts
- Recommended: 8 GB RAM and 10 GB free disk

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost`.

Default local services:

- Frontend: `http://localhost`
- API docs: `http://localhost/api/v1/docs`
- Keycloak: `http://localhost/auth`
- MinIO console: `http://localhost:9001`
- Mailhog: `http://localhost:8025`

Demo credentials are seeded for local development through Keycloak realm import. Change all secrets before deploying anywhere beyond a laptop.

## Environment

All configuration is provided through environment variables. See `.env.example` for the complete reference.

## Development

```bash
make dev
make test
```

On Windows without Make:

```bash
python scripts/health_check.py
python scripts/generate_secret.py
```

## Cloud Deployment

```bash
helm upgrade --install ai-sgp helm/ai-sgp -n ai-sgp --create-namespace
```

Override image tags, ingress, TLS, and managed service credentials in `helm/ai-sgp/values.production.yaml`.

## Repository Settings

Recommended GitHub settings:

- Protect `main`: require PRs, status checks, signed commits, and no force pushes.
- Enable secret scanning, Dependabot, CodeQL, and GitHub Pages.
- Configure `CODECOV_TOKEN` for coverage upload.
- Add staging and production environments before release automation.

## License

Apache-2.0.
