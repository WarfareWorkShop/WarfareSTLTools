"""Create a distributable ZIP archive of the Warfare STL Tools add-on."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "warfare_stl_tools"
DEFAULT_OUTPUT = ROOT / f"{PACKAGE_NAME}.zip"


def build_archive(output: Path) -> Path:
    target = output.with_suffix(".zip") if output.suffix != ".zip" else output
    if target.exists():
        target.unlink()

    shutil.make_archive(target.with_suffix(""), "zip", root_dir=ROOT, base_dir=PACKAGE_NAME)
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Destination ZIP file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    archive = build_archive(args.output)
    print(f"Add-on archive created at {archive}")


if __name__ == "__main__":
    main()
