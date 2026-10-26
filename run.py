"""Use the project's environment without requiring an activation command."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
python = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not python.exists():
    raise SystemExit("Run python setup_project.py first.")
command = sys.argv[1:] or ["app.py"]
raise SystemExit(subprocess.call([str(python), *command], cwd=root))
