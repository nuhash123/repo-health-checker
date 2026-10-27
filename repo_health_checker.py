"""Repo Health Checker

Scan a folder (e.g. a cloned GitHub repo) and report:
  - README / LICENSE present?
  - test files present?
  - number of Python files, total lines, code lines
  - functions without a docstring
  - an overall health score (0-100)

Usage:
    python repo_health_checker.py <folder>
    python repo_health_checker.py <folder> --json
"""

import argparse
import ast
import json
import sys
from pathlib import Path

# Folders we never want to scan
IGNORE_DIRS = {".git", ".venv", "venv", "env", "node_modules",
               "__pycache__", ".pytest_cache", ".mypy_cache", "build", "dist"}


def has_file_starting_with(root, prefix):
    """True if root has a file whose name starts with prefix (case-insensitive)."""
    for p in root.iterdir():
        if p.is_file() and p.name.lower().startswith(prefix):
            return True
    return False


def find_python_files(root):
    """Return all .py files under root, skipping folders in IGNORE_DIRS."""
    files = []
    for p in root.rglob("*.py"):
        parts = p.relative_to(root).parts  # folder names after root
        if not any(part in IGNORE_DIRS for part in parts):
            files.append(p)
    return files


def find_test_files(root, py_files):
    """Return files that look like tests: test_*.py, *_test.py, or inside tests/."""
    tests = []
    for p in py_files:
        folders = p.relative_to(root).parts[:-1]
        in_test_folder = any(f in ("tests", "test") for f in folders)
        if p.name.startswith("test_") or p.name.endswith("_test.py") or in_test_folder:
            tests.append(p)
    return tests


def count_lines(path):
    """Return (total_lines, code_lines) for one file."""
    total = 0
    code = 0
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            total += 1
            s = line.strip()
            if s != "" and not s.startswith("#"):
                code += 1
    return total, code


def analyze_functions(path):
    """Return (total_functions, [(name, line), ...] without docstring)."""
    with open(path, encoding="utf-8", errors="ignore") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0, []  # broken file: skip, don't crash
    total = 0
    missing = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total += 1
            if ast.get_docstring(node) is None:
                missing.append((node.name, node.lineno))
    return total, missing


def calculate_score(readme, license_, tests, total_funcs, missing_count):
    """Health score out of 100: README 20, LICENSE 10, tests 30, docstrings 40."""
    score = 0
    if readme:
        score += 20
    if license_:
        score += 10
    if tests:
        score += 30
    if total_funcs > 0:
        documented = total_funcs - missing_count
        score += round(40 * documented / total_funcs)
    return score


def analyze(root):
    """Run every check and return one dictionary with all results."""
    py_files = find_python_files(root)
    test_files = find_test_files(root, py_files)

    total_lines = 0
    code_lines = 0
    total_funcs = 0
    missing = []
    for p in py_files:
        t, c = count_lines(p)
        total_lines += t
        code_lines += c
        n, miss = analyze_functions(p)
        total_funcs += n
        for name, lineno in miss:
            missing.append({"file": str(p.relative_to(root)),
                            "function": name, "line": lineno})

    readme = has_file_starting_with(root, "readme")
    license_ = has_file_starting_with(root, "license")
    gitignore = has_file_starting_with(root, ".gitignore")
    return {
        "repo": str(root),
        "has_readme": readme,
        "has_license": license_,
        "has_gitignore": gitignore,
        "test_files": len(test_files),
        "python_files": len(py_files),
        "total_lines": total_lines,
        "code_lines": code_lines,
        "total_functions": total_funcs,
        "missing_docstrings": missing,
        "score": calculate_score(readme, license_, len(test_files) > 0,
                                 total_funcs, len(missing)),
    }


def print_report(r):
    """Print a human-readable report."""
    yn = lambda b: "YES" if b else "NO"
    print("Checking:", r["repo"])
    print("README present   :", yn(r["has_readme"]))
    print("LICENSE present  :", yn(r["has_license"]))
    print(".gitignore present:", yn(r["has_gitignore"]))
    print("Test files       :", r["test_files"])
    print("Python files     :", r["python_files"])
    print("Lines (total/code):", r["total_lines"], "/", r["code_lines"])
    print("Functions        :", r["total_functions"])
    print("Missing docstring:", len(r["missing_docstrings"]))
    for m in r["missing_docstrings"]:
        print("  -", m["file"], "line", m["line"], m["function"] + "()")
    print("HEALTH SCORE     :", r["score"], "/ 100")


def main():
    """Read command-line arguments, run the analysis, print the result."""
    parser = argparse.ArgumentParser(description="Check the health of a repo folder.")
    parser.add_argument("folder", help="path to the repo folder")
    parser.add_argument("--json", action="store_true", help="print JSON instead")
    args = parser.parse_args()

    root = Path(args.folder)
    if not root.is_dir():
        print("Error: not a folder:", root)
        sys.exit(1)

    result = analyze(root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)


if __name__ == "__main__":
    main()