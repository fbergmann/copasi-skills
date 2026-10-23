import subprocess
import sys
import venv
from pathlib import Path

venv_dir = Path(".venv")
if not venv_dir.exists():
    venv.create(venv_dir, with_pip=True)

python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
subprocess.check_call([str(python), "-m", "pip", "install", "--upgrade", "pip"])
subprocess.check_call([str(python), "-m", "pip", "install", "copasi-basico", "pandas"])
subprocess.check_call([str(python), "-c", "import basico; basico.load_model"])
print(python.resolve())
