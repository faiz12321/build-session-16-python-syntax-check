# Check a Python script for syntax errors without running it

A small read-only Python tool built step by step. Give it a Python file and it asks Python's own parser (the `ast` module) to read it. If the file has a syntax error, it shows the line, the message and a caret. If not, it lists how many functions and classes it found and the module names that are imported. It never runs the code in the file and has no code that writes to a file.

## Run it

    python make_sample.py                  # makes made-up scripts in sample/
    python pycheck.py sample/colon.py      # report on one script
    python -m unittest -v                  # twenty-two automated tests

On Windows, if `python` is not found, use `py`.

## Files

- `pycheck.py` - the tool
- `make_sample.py` - makes three made-up scripts: a good one, one with a missing colon, one with a wrong indent
- `test_pycheck.py` - tests

## Notes

- It checks syntax only. A script that passes can still crash when run, use a name that does not exist, or import a module that is not installed. Imports are listed, not checked.
- It checks the file with the Python you run it with. A script written for a different Python version may be judged differently.
- Only the first syntax error is shown, because the parser stops there. Fix it and run again.
- The wording of the message comes from Python and may differ between versions. The tests check line numbers, not message text.
- A test checks that checking a script containing a statement that would create a file does not create it. A second test checks that one small script keeps the same bytes and modified time.
- Imports are listed by the first part of the module name. Relative imports are not listed.
- "No syntax errors found" only means the parser accepted the file.
- Tested only on small made-up scripts. Python 3.10 and 3.12 on Linux, and, by GitHub Actions, Python 3.12 on Windows and Ubuntu. Not tested on a Windows 10 or 11 desktop.
- Educational example, no warranty. Use at your own risk.
- Code is MIT licensed (see LICENSE). Python is a separate project with its own license; this repository does not include it.
