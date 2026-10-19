"""Run with Python 3.11 or 3.12: python setup_project.py."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def main():
    os.chdir(ROOT)
    if sys.version_info[:2] not in {(3, 11), (3, 12)}:
        raise SystemExit("Use Python 3.11 or 3.12 (on Windows: py -3.11 setup_project.py).")
    if not shutil.which("ollama"):
        raise SystemExit("Install and start Ollama from https://ollama.com first.")
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        venv.create(ROOT / ".venv", with_pip=True)
    subprocess.run([str(python), "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    if not (ROOT / "data/documents.jsonl").exists():
        subprocess.run([str(python), "corpus.py"], check=True)
    subprocess.run([str(python), "build_index.py"], check=True)
    subprocess.run(["ollama", "pull", os.getenv("CHAT_MODEL", "qwen2.5:3b")], check=True)
    subprocess.run([str(python), "-c", "from search import Search; Search()"], check=True)
    print("Ready. Run: python run.py")


if __name__ == "__main__":
    main()
