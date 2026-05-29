import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def ensure_mpremote():
    result = subprocess.run(
        [sys.executable, "-m", "mpremote", "--help"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        print("mpremote is not installed for this Python.")
        print("Install it once:")
        print(f"  {sys.executable} -m pip install mpremote")
        raise SystemExit(1)


def main():
    ensure_mpremote()
    cmd = [sys.executable, "-m", "mpremote", "run", "pico/fps_test.py"]
    raise SystemExit(subprocess.run(cmd, cwd=ROOT).returncode)


if __name__ == "__main__":
    main()

