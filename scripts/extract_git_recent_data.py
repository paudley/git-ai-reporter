# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Extracts recent commit data from a Git repository into a JSONL file.

This script is used to generate static test data for the pytest suite, ensuring
that tests run against a consistent and representative set of commit history.
"""

import json
from pathlib import Path

from git import Commit
from git import Repo
from git.exc import GitCommandError
import typer

APP = typer.Typer()


@APP.command()
def extract(
    repo_path: str = typer.Argument(..., help="Path to the source Git repository."),
    output_file: Path = typer.Option(
        "tests/extracts/sample_git_data.jsonl",
        "--output",
        "-o",
        help="Path to the output JSONL file.",
    ),
    num_commits: int = typer.Option(
        250, "--num", "-n", help="Number of recent commits to extract."
    ),
) -> None:
    """Extracts recent commit diffs and metadata to a JSONL file for testing."""
    try:
        repo = Repo(repo_path, search_parent_directories=True)
    except GitCommandError as e:
        typer.echo(f"Error: Not a valid git repository: {repo_path}", err=True)
        raise typer.Exit(code=1) from e

    typer.echo(f"Extracting last {num_commits} commits from {repo.working_dir}...")

    # Ensure the output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    commits = list(repo.iter_commits(max_count=num_commits))
    extracted_count = 0

    with output_file.open("w", encoding="utf-8") as f:
        for commit in reversed(commits):  # Reverse to get chronological order
            if not commit.parents:
                continue  # Skip root commit as it has no parent to diff against

            parent: Commit = commit.parents[0]

            if not (diff := parent.diff(commit, create_patch=True)):
                continue  # Skip empty commits

            commit_data = {
                "hexsha": commit.hexsha,
                "message": commit.message,
                "committed_datetime": commit.committed_datetime.isoformat(),
                "diff": (
                    diff[0].diff.decode("utf-8", "ignore")
                    if diff[0].diff and isinstance(diff[0].diff, bytes)
                    else str(diff[0].diff) if diff[0].diff else ""
                ),
            }
            f.write(json.dumps(commit_data) + "\n")
            extracted_count += 1

    typer.echo(f"Successfully extracted {extracted_count} commits to {output_file}")


if __name__ == "__main__":
    APP()
