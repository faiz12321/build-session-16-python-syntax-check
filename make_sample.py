"""Makes three small made-up Python scripts to practise on.

Run: python make_sample.py
"""
from pathlib import Path

FILES = {
    "good.py": 'import json\nfrom pathlib import Path\n\n\ndef total(items):\n    result = 0\n    for item in items:\n        result += item\n    return result\n\n\nclass Cart:\n    pass\n\n\nprint(total([1, 2, 3]))\n',
    "colon.py": 'import os\n\n\ndef greet(name)\n    return "Hello " + name\n',
    "indent.py": 'def total(items):\n    result = 0\n    for item in items:\n        result += item\n      return result\n',
}


def make(folder):
    folder = Path(folder)
    folder.mkdir(exist_ok=True)
    for name, data in FILES.items():
        (folder / name).write_bytes(data.encode("utf-8"))
    return folder


if __name__ == "__main__":
    make("sample")
    print("Made sample/good.py, colon.py and indent.py")
