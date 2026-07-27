# New standalone tool

Create a new standalone Python CLI script in the repo root following existing project conventions.

Requirements:
- Use shebang and `docopt` usage in module docstring
- Keep implementation class-based
- Preserve stderr/non-zero exits on errors
- Keep tool independent (no inter-tool imports)
- Add tests in `tests/*_test.py`
- Update `README.md` and `requirements.txt` if needed

Validation:
- Run `python -m unittest discover -s tests -p '*_test.py' -v`
- Ensure style passes `pre-commit run --all-files`
