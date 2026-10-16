"""Checks a Python file for syntax errors without running it.

Run: python pycheck.py SCRIPT.py
Exit code: 0 = no syntax error found, 1 = syntax error, 2 = could not read.
"""
import ast
import sys
import stat
from pathlib import Path


def safe_input(value, directory=False):
    path = Path(value).absolute()
    if '..' in path.parts:
        raise OSError('Parent-traversal paths are unsupported.')
    for part in [*reversed(path.parents), path]:
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise OSError('Links/reparse points are unsupported.')
    info = path.lstat()
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise NotADirectoryError('Expected an ordinary directory.')
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise OSError('Expected an ordinary singly linked file.')
    return path







def check(path):
    with open(safe_input(path), "rb") as f:
        source = f.read()
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as e:
        return {"error": {"line": e.lineno, "column": e.offset, "text": e.text,
                          "message": e.msg, "kind": type(e).__name__}}
    except ValueError as e:
        return {"error": {"line": None, "column": None, "text": None,
                          "message": str(e), "kind": "ValueError"}}
    imports = set()
    functions = classes = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
        elif isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module.split(".")[0])
    return {"error": None, "lines": len(source.splitlines()),
            "functions": functions, "classes": classes, "imports": sorted(imports)}


def report(r):
    e = r["error"]
    if e:
        where = f" on line {e['line']}" if e["line"] else ""
        print(f"Could not parse: {e['kind']}{where}")
        print("Message:", e["message"])
        if e["text"] and e["line"]:
            line = e["text"].rstrip("\r\n")
            print(f"  {e['line']} | {line}")
            if e["column"] and e["column"] > 0:
                print(" " * (5 + len(str(e["line"]))) + " " * (e["column"] - 1) + "^")
        print("Only the first problem is shown. Fix it and run again.")
        return 1
    print("Lines:", r["lines"])
    print("Functions:", r["functions"], " Classes:", r["classes"])
    print("Imports:", ", ".join(r["imports"]) if r["imports"] else "none")
    print("No syntax errors found. The code was not run.")
    print("Imports are listed, not checked.")
    return 0


def main(argv):
    if len(argv) != 2:
        print("Usage: python pycheck.py SCRIPT.py")
        return 2
    try:
        result = check(argv[1])
    except OSError as e:
        print("Could not read the file:", e)
        return 2
    return report(result)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
