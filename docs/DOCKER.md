# Docker Documentation

FireForm uses Docker to ensure a consistent environment across different machines.

> **New to FireForm?** Start with the [Setup Guide](1.%20SETUP.md) for the complete first-time development setup. This page is a reference for FireForm's Docker environment and commands.

## Container Stack

The dev stack (`docker/dev/compose.yml`) runs:
1.  **`fireform-app`**: Runs the FastAPI server on `http://localhost:8000`.
2.  **`fireform-celery-worker`**: Runs background fill and transcription jobs.
3.  **`fireform-postgres`** and **`fireform-redis`**: Database and job queue.
4.  **`fireform-whisper`**: Speech-to-text.
5.  **`fireform-ollama`**: Runs Ollama for LLM calls (only with `make fireform` / `make up`; `make fireform-native` uses `OLLAMA_HOST` instead).

The frontend is not part of this stack; it lives in the separate [fireform-frontend](https://github.com/fireform-core/fireform-frontend) repository and runs with `npm run dev`.

## Makefile Commands

The `Makefile` simplifies common Docker tasks. You can run these commands from the project root:

| Command | Description |
| :--- | :--- |
| `make fireform` | Build, start all containers and pull the Ollama model |
| `make fireform-native` | Same, without the Ollama container (uses `OLLAMA_HOST`) |
| `make build` | Build Docker images |
| `make up` | Start all containers in the background |
| `make down` | Stop all containers |
| `make logs` | View logs from all containers |
| `make shell` | Open a shell in the app container |
| `make pull-model` | Pull the model set in `OLLAMA_MODEL` into Ollama |
| `make clean` | Stop containers (keeps volumes) |
| `make super-clean` | Stop containers and delete all volumes |
| `make help` | Show all available commands |

## Troubleshooting

- **Logs:** Use `make logs` to see what's happening inside the containers.
- **Port Conflicts:** If port 11434 (Ollama) or 8000 (App) is already in use, you may need to stop the conflicting process or change the mapping in `docker/dev/compose.yml` (or `APP_PORT` in `docker/.env.dev`).
- **Model not found:** If LLM calls fail, ensure you've run `make pull-model`.
