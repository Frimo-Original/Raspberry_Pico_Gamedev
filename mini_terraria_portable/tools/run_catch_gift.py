import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    code = "from backends.tkinter_backend import run; from examples.catch_gift import CatchGiftGame; run(CatchGiftGame())"
    raise SystemExit(subprocess.run([sys.executable, "-c", code], cwd=ROOT).returncode)


if __name__ == "__main__":
    main()
