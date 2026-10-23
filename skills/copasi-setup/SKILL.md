---
name: copasi-setup
description: Creates the Python virtual environment with copasi-basico for COPASI/SBML work. Use before any copasi-timecourse, copasi-steadystate, or copasi-optimization run when `.venv` is missing or `import basico` fails.
---

# COPASI environment setup

Run once per project:

```
python scripts/setup_env.py
```

The script creates `.venv`, installs `copasi-basico` and `pandas`, and prints the venv Python path. Run all later COPASI scripts with that interpreter.

Install `copasi-basico`, not `basico`: the latter is an unrelated package. If `import basico` has no `load_model`, run `pip uninstall basico` and then `pip install copasi-basico`.

Done when `.venv/Scripts/python -c "import basico; basico.load_model"` (Linux/macOS: `.venv/bin/python`) exits 0.
