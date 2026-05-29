import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_CODE = """
import game
game.init()
game.clear(game.BLUE)
game.rect(20, 20, 40, 30, game.RED)
game.rect(70, 40, 50, 20, game.GREEN)
game.rect(10, 90, 140, 12, game.WHITE)
game.present()
print("ILI9341 test complete")
"""


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
    cmd = [sys.executable, "-m", "mpremote", "exec", TEST_CODE]
    raise SystemExit(subprocess.run(cmd, cwd=ROOT).returncode)


if __name__ == "__main__":
    main()

