from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Sequence

DEFAULT_IMAGE = "llmops-telemetry-command-center:ci"
CONTAINER_NAME_PREFIX = "llmops-telemetry-command-center-smoke"


def run(command: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a Docker CLI command and stream output to the current terminal."""

    return subprocess.run(list(command), check=check, text=True)


def find_free_port() -> int:
    """Ask the OS for an available localhost port for the smoke test."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_health(url: str, *, timeout_seconds: int) -> None:
    """Poll the Streamlit health endpoint until it responds or the timeout expires."""

    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if 200 <= response.status < 500:
                    response.read()
                    return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
        time.sleep(2)

    raise TimeoutError(
        f"Docker smoke test did not reach {url!r} within {timeout_seconds}s. Last error: {last_error}"
    )


def print_container_logs(container_name: str) -> None:
    """Print container logs to make CI failures diagnosable."""

    print("\n--- Docker container logs ---", file=sys.stderr)
    run(["docker", "logs", container_name], check=False)
    print("--- End Docker container logs ---\n", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and smoke-test the Streamlit Docker image.")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Docker image tag to build/run.")
    parser.add_argument("--build", action="store_true", help="Build the image before running the smoke test.")
    parser.add_argument(
        "--port", type=int, default=0, help="Host port to bind. Defaults to a free localhost port."
    )
    parser.add_argument("--timeout", type=int, default=90, help="Health-check timeout in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    image = args.image
    host_port = args.port or find_free_port()
    container_name = f"{CONTAINER_NAME_PREFIX}-{os.getpid()}"
    health_url = f"http://127.0.0.1:{host_port}/_stcore/health"
    container_started = False

    if shutil.which("docker") is None:
        print(
            "Docker CLI was not found. Install Docker or run this command in CI with Docker available.",
            file=sys.stderr,
        )
        return 127

    try:
        if args.build:
            run(["docker", "build", "--pull", "-t", image, "."])

        run(
            [
                "docker",
                "run",
                "--detach",
                "--name",
                container_name,
                "--publish",
                f"127.0.0.1:{host_port}:8501",
                image,
            ]
        )
        container_started = True
        wait_for_health(health_url, timeout_seconds=args.timeout)
        print(f"Docker smoke test passed: {health_url}")
        return 0
    except Exception as exc:  # noqa: BLE001 - CI diagnostics should preserve the original failure.
        print(f"Docker smoke test failed: {exc}", file=sys.stderr)
        if container_started:
            print_container_logs(container_name)
        return 1
    finally:
        if container_started:
            run(["docker", "rm", "-f", container_name], check=False)


if __name__ == "__main__":
    raise SystemExit(main())
