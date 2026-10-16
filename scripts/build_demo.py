"""Build the theme, copy it into example/, and render the demo with SmallDocs."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
name = json.loads((ROOT / "src/theme.json").read_text())["name"]
subprocess.run([sys.executable, str(ROOT / "scripts/build.py")], check=True)
dest = ROOT / "example/_extensions" / name
if dest.exists():
    shutil.rmtree(dest)
shutil.copytree(ROOT / "_extensions" / name, dest)
subprocess.run([sys.executable, "-m", "smalldocs.cli", "render", "example", "--strict"], cwd=ROOT, check=True)
