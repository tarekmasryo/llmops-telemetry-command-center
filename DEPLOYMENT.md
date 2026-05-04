# Deployment Guide

This repository runs as a self-contained Streamlit command center with bundled synthetic telemetry and notebook-generated artifacts.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Docker run

CI validates the Docker image by building it, starting the container, and polling the Streamlit health endpoint:

```bash
python scripts/docker_smoke_test.py --image llmops-telemetry-command-center:ci --build
```

Build the image:

```bash
docker build -t llmops-telemetry-command-center .
```

Run the app:

```bash
docker run --rm -p 8501:8501 llmops-telemetry-command-center
```

Or use Docker Compose:

```bash
docker compose up --build
```

## GitHub publishing checklist

Before pushing the release branch:

```bash
python -m ruff check app.py src tests scripts
python -m ruff format --check app.py src tests scripts
python -m compileall app.py src tests scripts
python scripts/run_tests.py
```

If Docker is available locally, also run the same container smoke gate used by CI:

```bash
python scripts/docker_smoke_test.py --image llmops-telemetry-command-center:ci --build
```

Then create the repository and push:

```bash
git init
git add .
git commit -m "feat: release LLMOps Telemetry Command Center v1.0.0"
git branch -M main
git remote add origin https://github.com/tarekmasryo/llmops-telemetry-command-center.git
git push -u origin main
```

## Streamlit Community Cloud

Use:

```text
Main file path: app.py
Python version: 3.11+
```

The bundled data and artifacts are already included in the repository.

## Hugging Face Spaces

For a Hugging Face Space, add this front matter to the Space README only:

```yaml
---
title: LLMOps Telemetry Command Center
emoji: 🛰️
colorFrom: slate
colorTo: blue
sdk: streamlit
sdk_version: "1.51.0"
python_version: "3.11"
app_file: app.py
pinned: false
license: mit
---
```

Keep the GitHub README without Hugging Face front matter unless the repository is dedicated to Spaces.

## Runtime assumptions

- Included CSV/JSON artifacts are synthetic and small enough to ship with the repository.
- `load_bundle()` validates required schemas and cross-table references at startup.
- The app fails fast when required data or artifacts are missing, empty, or structurally invalid.
- Streamlit is the dashboard runtime.
