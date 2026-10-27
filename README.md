# Repo Health Checker

A small Python command-line tool that scans a project folder (for example a cloned
GitHub repository) and reports how healthy it looks.

## What it checks

- README present?
- LICENSE present?
- .gitignore present?
- Test files present?
- Number of Python files, total lines and code lines
- Functions without a docstring (found with Python's `ast` module)
- An overall health score out of 100

## Requirements

- Python 3.8+
- No third-party packages (tests need `pytest`)

## Usage

```bash
python repo_health_checker.py <folder>
python repo_health_checker.py <folder> --json
```

Example output:

```
Checking: demo_repo
README present   : YES
LICENSE present  : NO
.gitignore present: NO
Test files       : 1
Python files     : 2
Lines (total/code): 10 / 8
Functions        : 3
Missing docstring: 2
  - calc.py line 1 add()
  - tests\test_calc.py line 3 test_add()
HEALTH SCORE     : 63 / 100
```

## Scoring

| Check | Points |
|---|---|
| README | 20 |
| LICENSE | 10 |
| Test files | 30 |
| Docstring coverage | up to 40 |

## How it works

1. `find_python_files()` walks the folder with `Path.rglob`, skipping `.git`, `venv`, etc.
2. `count_lines()` counts total and code lines (blank lines and comments excluded).
3. `analyze_functions()` parses each file into an AST and looks for functions
   with no docstring. Files with syntax errors are skipped.
4. `calculate_score()` turns the results into a score.

## Run the tests

```bash
pip install pytest
python -m pytest tests
```

## License

MIT, see [LICENSE](LICENSE).