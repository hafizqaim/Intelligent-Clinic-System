## Intelligent Clinic System

Backend platform for multi-tenant clinic operations, telemetry, and RAG-powered clinical assistance.

## Phase 1: Git Infrastructure

This repository uses a lightweight, team-friendly Git workflow.

### Branching

- `main`: stable branch, only reviewed changes
- `feature/<name>`: feature implementation branches
- `fix/<name>`: bug fixes

### Commit Convention

Use concise conventional commit prefixes:

- `feat:` new functionality
- `fix:` bug fix
- `refactor:` internal restructuring
- `docs:` documentation changes
- `test:` tests
- `chore:` tooling/configuration

Example:

`feat: add tenant-scoped patients endpoint`

### Local Quality Gates

Install and enable pre-commit hooks:

```bash
pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
```

### CI

Pull requests are validated by GitHub Actions (`.github/workflows/ci.yml`) with:

- dependency installation
- Python syntax verification (`compileall`)
- Alembic sanity check (`alembic current`)

## Quick Start

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
docker compose up -d
```

