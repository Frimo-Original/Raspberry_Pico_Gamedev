import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_RUNTIME_FILES = {".bin"}
ASSET_RUNTIME_NAMES = {"manifest.json"}


def run_mpremote(*args):
    cmd = [sys.executable, "-m", "mpremote", *args]
    try:
        return subprocess.run(cmd, cwd=ROOT, check=True)
    except ModuleNotFoundError:
        raise
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode)


def run_mpremote_optional(*args):
    cmd = [sys.executable, "-m", "mpremote", *args]
    return subprocess.run(cmd, cwd=ROOT)


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


def copy_runtime_assets(target):
    source = ROOT / "assets"
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in ASSET_RUNTIME_FILES and path.name not in ASSET_RUNTIME_NAMES:
            continue
        rel_path = path.relative_to(source)
        out_path = target / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out_path)


def main():
    ensure_mpremote()
    remove_cache_dirs()

    print("Uploading game files to Pico...")
    run_mpremote("fs", "cp", "-r", "api", ":")
    run_mpremote("fs", "cp", "-r", "game_core", ":")
    run_mpremote("fs", "cp", "-r", "backends", ":")
    run_mpremote("fs", "cp", "-r", "examples", ":")
    run_mpremote_optional("fs", "rm", "-r", ":assets")
    with tempfile.TemporaryDirectory() as temp_dir:
        runtime_assets = Path(temp_dir) / "assets"
        copy_runtime_assets(runtime_assets)
        run_mpremote("fs", "cp", "-r", str(runtime_assets), ":")
    run_mpremote("fs", "cp", "pico/main.py", ":main.py")

    print("Resetting Pico...")
    run_mpremote("reset")
    print("Done. Pico should start main.py now.")


if __name__ == "__main__":
    main()
