.PHONY: run test lint format-check compile check docker-build docker-smoke docker-check docker-run clean

PYTHON ?= python

run:
	$(PYTHON) -m streamlit run app.py

test:
	$(PYTHON) scripts/run_tests.py

lint:
	$(PYTHON) -m ruff check app.py src tests scripts

format-check:
	$(PYTHON) -m ruff format --check app.py src tests scripts

compile:
	$(PYTHON) -m compileall app.py src tests scripts

check: lint format-check compile test

docker-build:
	docker build -t llmops-telemetry-command-center .

docker-smoke:
	$(PYTHON) scripts/docker_smoke_test.py --image llmops-telemetry-command-center:ci --build

docker-check: docker-smoke

docker-run:
	docker run --rm -p 8501:8501 llmops-telemetry-command-center

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache', '.ruff_cache', 'dist', 'build']]"
