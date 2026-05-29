import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_mpremote(*args):
    cmd = [sys.executable, "-m", "mpremote", *args]
    try:
        return subprocess.run(cmd, cwd=ROOT, check=True)
    except ModuleNotFoundError:
        raise
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode)


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


def remove_cache_dirs():
    for cache_dir in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache_dir)


def main():
    ensure_mpremote()
    remove_cache_dirs()

    print("Uploading game files to Pico...")
    run_mpremote("fs", "cp", "-r", "api", ":")
    run_mpremote("fs", "cp", "-r", "game_core", ":")
    run_mpremote("fs", "cp", "-r", "backends", ":")
    run_mpremote("fs", "cp", "-r", "examples", ":")
    run_mpremote("fs", "cp", "-r", "assets", ":")
    run_mpremote("fs", "cp", "pico/main.py", ":main.py")

    print("Resetting Pico...")
    run_mpremote("reset")
    print("Done. Pico should start main.py now.")


if __name__ == "__main__":
    main()
