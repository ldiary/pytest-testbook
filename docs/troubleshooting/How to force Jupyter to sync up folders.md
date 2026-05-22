Sometimes Jupyter will refuse to load `pw_start()` because it can not find the newer version of `pytest_testbook`. In which case we need the nuclear option:

```python
import sys
from pathlib import Path

# 1. Dynamically find the root directory of your project
current_dir = Path().resolve()

# 2. Check if the notebook is in a subfolder (like 'tests/') or the root
if (current_dir.parent / 'pytest_testbook').exists():
    project_root = str(current_dir.parent)
elif (current_dir / 'pytest_testbook').exists():
    project_root = str(current_dir)
else:
    raise FileNotFoundError("Could not locate the 'pytest_testbook' directory.")

# 3. Force this exact path to the very front of Python's brain
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"Forcing Python to load package from: {project_root}")

# 4. Import and run!
from pytest_testbook import pw_start, pw_execute, pw_stop
pw_start(False)
print("Playwright successfully initialized!")
```