# the actual cross-repo project-detection logic

import subprocess
from pathlib import Path

import typer


def detect_project(explicit: str | None) -> str:
    if explicit:
        return explicit

    try:
        # subprocess.run(..., cwd=Path.cwd()) runs that command
        # as if you'd typed it in your current directory
        # actual mechanism that makes cross-repo detection work:
        # whatever directory you're standing in when you run journal log,
        # git tells us which repo (if any) that is.
        result = subprocess.run(
            # asks git "what's the root folder of the repo I'm currently inside?
            ["git", "rev-parse", "--show-toplevel"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
        )
    # means git itself isn't installed at all;
    except FileNotFoundError:
        typer.secho(
            "git not found - using current folder name as project. Use --project to be precise.",
            fg=typer.colors.YELLOW,
        )

        return Path.cwd().name

    # result.returncode != 0 means git is installed but you're not inside a repo.
    if result.returncode != 0:
        # yellow warning printed
        typer.secho(
            "Not inside a git repo- using current folder name as project. "
            "Use --project to be precise.",
            fg=typer.colors.YELLOW,
        )

        return Path.cwd().name

    repo_root = Path(result.stdout.strip())

    remote_result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    # If we are in a repo, try git remote get-url origin
    # if it succeeds, parse the repo name out of the URL.
    # url.rstrip("/").split("/")[-1] takes the last path segment,
    # which works for both SSH (git@github.com:user/repo.git) and
    # HTTPS (https://github.com/user/repo.git) remote URLs,
    # since both put the repo name last. Then strip a trailing
    # .git if present.
    if remote_result.returncode == 0:
        url = remote_result.stdout.strip()
        name = url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[: -len(".git")]
        return name

    return repo_root.name
