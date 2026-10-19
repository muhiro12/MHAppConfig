"""Validate exact configuration snapshots with MHPlatform's owning decoder."""

import argparse
from pathlib import Path
import subprocess
import tempfile


def git(*arguments):
    return subprocess.check_output(["git", *arguments])


def commit(reference):
    return git("rev-parse", "--verify", "--end-of-options", reference + "^{commit}").decode().strip()


def paths(reference):
    if reference:
        names = git("ls-tree", "-rz", "--name-only", reference)
    else:
        names = git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return {name.decode() for name in names.split(b"\0") if name.endswith(b"/app.json")}


def contents(reference, path):
    return git("show", reference + ":" + path) if reference else Path(path).read_bytes()


def run_validator(validator, candidate, previous=None):
    arguments = [validator, str(candidate)]
    if previous:
        arguments.append(str(previous))
    return subprocess.run(arguments, capture_output=True, text=True, check=False)


def validate_history(validator, base, path, current, previous):
    # Compare every readable published policy so recovery cannot reuse a revision after a bad revert.
    history = [base, *git("log", "--first-parent", "--format=%H", base, "--", path).decode().splitlines()]
    for reference in dict.fromkeys(history):
        if path not in paths(reference):
            continue
        previous.write_bytes(contents(reference, path))
        if run_validator(validator, previous).returncode:
            print("Unreadable historical policy at " + reference + ": " + path, flush=True)
            continue
        result = run_validator(validator, current, previous)
        if result.returncode:
            raise ValueError(path + " conflicts with published policy " + reference + ": " + result.stderr.strip())


def verify(validator, base, candidate):
    if git("rev-parse", "--is-shallow-repository").strip() != b"false":
        raise ValueError("Complete Git history is required for published revision checks")
    current_paths = paths(candidate)
    old_paths = paths(base) if base else set()
    deleted = old_paths - current_paths
    if deleted:
        raise ValueError("Published endpoints cannot be deleted: " + ", ".join(sorted(deleted)))
    if not current_paths:
        raise ValueError("No app configuration found")
    with tempfile.TemporaryDirectory(prefix="mhappconfig-") as directory:
        current = Path(directory, "candidate.json")
        previous = Path(directory, "previous.json")
        for path in sorted(current_paths):
            current.write_bytes(contents(candidate, path))
            result = run_validator(validator, current)
            if result.returncode:
                raise ValueError(path + ": " + result.stderr.strip())
            if base:
                validate_history(validator, base, path, current, previous)
            print(path + ": " + result.stdout.strip(), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validator", required=True)
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--candidate")
    arguments = parser.parse_args()
    base = None if set(arguments.base) == {"0"} else commit(arguments.base)
    candidate = commit(arguments.candidate) if arguments.candidate else None
    verify(arguments.validator, base, candidate)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit("Configuration validation failed: " + str(error)) from error
