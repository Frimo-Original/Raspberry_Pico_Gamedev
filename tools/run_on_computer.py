import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    raise SystemExit(subprocess.run([sys.executable, "run_tkinter.py"], cwd=ROOT).returncode)


if __name__ == "__main__":
    main()

