# Docker

```
docker/
  dev/
    Dockerfile        # uvicorn --reload, source-mounted for hot reload
    compose.yml
  prod/
    Dockerfile        # multi-stage build, uvicorn workers, no source mount
    compose.yml
    compose.postgres.yml  # optional standalone PostgreSQL for prod
  .env.example        # template — copy to .env.dev or .env.prod
  .env.dev            # gitignored, dev values
  .env.prod           # gitignored, prod values
  entrypoint.sh       # runs DB migrations then exec's the server command
  README.md
```

## Env vars

See `.env.example` for the full list with descriptions.

## Volumes

`docker compose down` never removes volumes. Use `docker compose down -v` only to intentionally wipe all data.

| Volume             | Path in container      | Purpose                             |
| ------------------ | ---------------------- | ----------------------------------- |
| `postgres_data`    | `/var/lib/postgresql/data` | PostgreSQL database             |
| `redis_data`       | `/data`                | Redis job queue (dev)               |
| `fireform_uploads` | `/data/uploads` (dev), `/app/data` (prod) | Uploaded templates + generated PDFs |
| `ollama_data`      | `/root/.ollama`        | Ollama model weights                |
| `whisper_models`   | `/data/whisper`        | Whisper model cache                 |
