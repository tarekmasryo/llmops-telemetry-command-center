from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    """Run pytest with external plugin autoload disabled.

    Keeping this logic in Python makes the test command portable across
    PowerShell, Command Prompt, Git Bash, Linux, and macOS shells.
    """

    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return subprocess.call([sys.executable, "-m", "pytest", "-q"], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
