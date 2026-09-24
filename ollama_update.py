#!/usr/bin/env python3

"""
Ollama Update - Automatically update all local models

Usage:
    ollama_update.py

Description:
    This script fetches the list of all locally installed Ollama models
    and performs an `ollama pull` on each one to ensure they are up to date.

Requirements:
    Requires the `ollama` CLI to be installed and available in the system PATH.
"""

import shutil
import subprocess
import sys
from typing import List, Tuple

from docopt import docopt
from termcolor import colored

# Constants
SUCCESS_MARK = "✓"
ERROR_MARK = "✗"
DEFAULT_TIMEOUT_SECONDS = 300


class OllamaUpdater:
    def _run_command(self, command: List[str], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Tuple[bool, str, str]:
        """Run a shell command and return (success, stdout, stderr)."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout,
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else "Unknown error"
            stdout = exc.stdout.strip() if exc.stdout else ""
            return False, stdout, stderr
        except subprocess.TimeoutExpired as exc:
            stderr = str(exc)
            stdout = exc.stdout.strip() if exc.stdout else ""
            return False, stdout, stderr
        except FileNotFoundError:
            print(
                f"[{colored(ERROR_MARK, 'red')}] Error: 'ollama' command not found. Please ensure Ollama is installed.",
                file=sys.stderr,
            )
            raise

    def get_models(self) -> List[str]:
        """Get the list of local models from 'ollama list'."""
        success, stdout, stderr = self._run_command(["ollama", "list"], timeout=30)
        if not success:
            print(f"[{colored(ERROR_MARK, 'red')}] Failed to list models: {stderr}", file=sys.stderr)
            return []

        models: List[str] = []
        lines = stdout.strip().splitlines()
        if len(lines) < 2:
            return []

        # The first line is usually the header.
        if "NAME" not in lines[0].upper():
            return []

        for line in lines[1:]:
            stripped = line.strip()
            if not stripped:
                continue

            parts = stripped.split()
            if parts:
                models.append(parts[0])

        return models

    def update_all(self) -> None:
        """Update all models found in the list."""
        success_count = 0
        failure_count = 0
        error_count = 0

        try:
            if not shutil.which("ollama"):
                print(
                    f"[{colored(ERROR_MARK, 'red')}] Error: 'ollama' command not found. Please ensure Ollama is installed.",
                    file=sys.stderr,
                )
                error_count = 1
                return

            models = self.get_models()
            if not models:
                print(f"[{colored(ERROR_MARK, 'red')}] No models found to update.")
                print("\nUpdate Summary:")
                print(f"  Successes: {success_count}")
                print(f"  Failures:  {failure_count}")
                print(f"  Errors:    {error_count}")
                return

            print(f"Found {len(models)} models. Starting updates...")

            for model in models:
                print(f"Updating {model}...", end=" ", flush=True)
                try:
                    subprocess.run(
                        ["ollama", "pull", model],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=DEFAULT_TIMEOUT_SECONDS,
                    )
                    print(f"[{colored(SUCCESS_MARK, 'green')}] Done.")
                    success_count += 1
                except subprocess.CalledProcessError as exc:
                    stderr = exc.stderr.strip() if exc.stderr else "Unknown error"
                    print(f"[{colored(ERROR_MARK, 'red')}] Failed.", file=sys.stderr)
                    if stderr:
                        print(f"  Details: {stderr}", file=sys.stderr)
                    failure_count += 1
                except subprocess.TimeoutExpired:
                    print(f"[{colored(ERROR_MARK, 'red')}] Timed out after {DEFAULT_TIMEOUT_SECONDS} seconds.", file=sys.stderr)
                    failure_count += 1
                except FileNotFoundError:
                    print(
                        f"[{colored(ERROR_MARK, 'red')}] Error: 'ollama' command not found.",
                        file=sys.stderr,
                    )
                    error_count += 1
                    return
        finally:
            print("\nUpdate Summary:")
            print(f"  Successes: {success_count}")
            print(f"  Failures:  {failure_count}")
            print(f"  Errors:    {error_count}")


def main() -> None:
    docopt(__doc__, version="0.1")
    updater = OllamaUpdater()
    updater.update_all()


if __name__ == "__main__":
    main()
