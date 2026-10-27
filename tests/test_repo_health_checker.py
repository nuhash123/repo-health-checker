"""Tests for repo_health_checker."""

import sys
from pathlib import Path

# Make the project root importable when pytest runs from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import repo_health_checker as rhc


def make_repo(tmp_path):
    """Create a tiny fake repo and return its path."""
    (tmp_path / "README.md").write_text("# Demo")
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n\n"
        "def sub(a, b):\n    \"\"\"Subtract.\"\"\"\n    return a - b\n"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_calc.py").write_text("def test_x():\n    pass\n")
    return tmp_path


def test_readme_detected(tmp_path):
    """README is found, LICENSE is not."""
    repo = make_repo(tmp_path)
    assert rhc.has_file_starting_with(repo, "readme")
    assert not rhc.has_file_starting_with(repo, "license")


def test_missing_docstrings(tmp_path):
    """Only add() and test_x() lack docstrings; sub() has one."""
    repo = make_repo(tmp_path)
    result = rhc.analyze(repo)
    names = {m["function"] for m in result["missing_docstrings"]}
    assert names == {"add", "test_x"}
    assert result["total_functions"] == 3


def test_ignored_folders_are_skipped(tmp_path):
    """Files inside venv/ must not be counted."""
    repo = make_repo(tmp_path)
    (repo / "venv").mkdir()
    (repo / "venv" / "hidden.py").write_text("def hidden():\n    pass\n")
    assert rhc.analyze(repo)["python_files"] == 2


def test_syntax_error_does_not_crash(tmp_path):
    """A broken file is skipped instead of crashing the tool."""
    repo = make_repo(tmp_path)
    (repo / "bad.py").write_text("def broken(:\n")
    assert rhc.analyze(repo)["python_files"] == 3


def test_score_range(tmp_path):
    """Score is always between 0 and 100."""
    result = rhc.analyze(make_repo(tmp_path))
    assert 0 <= result["score"] <= 100


def test_gitignore_detected(tmp_path):
    """has_gitignore is False first, True after we create the file."""
    repo = make_repo(tmp_path)
    assert rhc.analyze(repo)["has_gitignore"] is False
    (repo / ".gitignore").write_text("venv/\n")
    assert rhc.analyze(repo)["has_gitignore"] is True