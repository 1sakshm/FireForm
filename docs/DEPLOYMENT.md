# Deployment Guide

This guide covers deploying FireForm using Docker. By the end, you will have the full FireForm stack (FastAPI server + Ollama AI engine) running on any machine with a single command.

## Prerequisites

| Requirement | Version | Install |
| :--- | :--- | :--- |
| Docker Desktop | 26.x or newer | [docker.com/get-started](https://www.docker.com/get-started/) |
| WSL2 (Windows) | Latest | `wsl --update` |
| Git | Any | [git-scm.com](https://git-scm.com/) |
| Disk space | ~6GB free | For Docker images + LLM model |
| RAM | 8GB min | 16GB recommended |

## Quick Start (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/fireform-core/FireForm
cd FireForm

# 2. First-time setup (creates docker/.env.dev, picks a model)
make init

# 3. Build, start everything and pull the AI model (one-time download)
make fireform

# 4. Open FireForm
#    API + Swagger docs:  http://localhost:8000/docs
#    Frontend:            run the separate fireform-frontend repo (npm run dev)
```

## Production Deployment (Station Intranet)

For deployment on a Linux station server:

1.  **Start services:** `docker compose -f docker/prod/compose.yml --env-file docker/.env.prod up -d`
2.  **Pull model:** `docker compose -f docker/prod/compose.yml --env-file docker/.env.prod exec ollama ollama pull <OLLAMA_MODEL>`
3.  **Access:** The FireForm API is now accessible at `http://<station-server-ip>:8000`

**HTTPS Note:** For HTTPS, point your department's reverse proxy (nginx/Apache) to port 8000.

## Known Limitations

- **PostgreSQL** is the database (`docker/prod/compose.postgres.yml` for a bundled instance).
- **Model download** (~1GB for the default `qwen2.5:1.5b`) is required on first run.
- **CPU inference** is used by default, but Ollama will use CUDA if an NVIDIA GPU is detected.
