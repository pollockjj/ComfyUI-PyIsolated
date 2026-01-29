from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import os
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

_installed_packages: Set[str] = set()


def _is_package_installed(package_name: str) -> bool:
    base_name = package_name.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
    if base_name.lower() in _installed_packages:
        return True
    spec = importlib.util.find_spec(base_name)
    if spec is not None:
        _installed_packages.add(base_name.lower())
        return True
    return False


def get_venv_name(dependencies: List[str]) -> str:
    if not dependencies:
        return "ComfyUI-PyIsolated"
    deps_sorted = sorted(dependencies)
    dep_hash = hashlib.sha256("\n".join(deps_sorted).encode()).hexdigest()[:8]
    return f"PyIsolated_{dep_hash}"


def get_venv_root() -> Path:
    try:
        import folder_paths
        return Path(folder_paths.base_path) / ".pyisolate_venvs"
    except ImportError:
        pass
    return Path(__file__).resolve().parent.parent.parent / ".pyisolate_venvs"


def get_python_executable(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def get_pip_executable(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "pip.exe"
    return venv_path / "bin" / "pip"


def ensure_venv(venv_name: str, dependencies: List[str], venv_root: Path) -> Path:
    venv_path = venv_root / venv_name
    if venv_path.exists():
        return venv_path

    venv_root.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

    if dependencies:
        pip_path = get_pip_executable(venv_path)
        for dep in dependencies:
            subprocess.run([str(pip_path), "install", dep], check=True, capture_output=True)

    return venv_path


def run_code_in_venv(code: str, inputs: Dict[str, Any], venv_path: Path) -> Tuple[str, str, int]:
    python_path = get_python_executable(venv_path)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        code_file = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(inputs, f)
        inputs_file = f.name

    wrapper_script = f'''
import sys
import json
from io import StringIO

with open(r"{inputs_file}", "r") as f:
    inputs = json.load(f)

stdout_capture = StringIO()
original_stdout = sys.stdout
sys.stdout = stdout_capture

try:
    namespace = inputs.copy()
    namespace["__builtins__"] = __builtins__
    with open(r"{code_file}", "r") as f:
        code = f.read()
    exec(code, namespace)
    result = namespace.get("result", "")
    exit_code = 0
except Exception as e:
    result = f"Error: {{str(e)}}"
    exit_code = 1
finally:
    sys.stdout = original_stdout

stdout = stdout_capture.getvalue()
output = {{"result": str(result), "stdout": stdout, "exit_code": exit_code}}
print(json.dumps(output))
'''

    try:
        proc = subprocess.run(
            [str(python_path), "-c", wrapper_script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        try:
            output = json.loads(proc.stdout)
            return (output["result"], output["stdout"], output["exit_code"])
        except json.JSONDecodeError:
            return (f"Error: {proc.stderr or 'Parse error'}", proc.stdout, 1)
    except subprocess.TimeoutExpired:
        return ("Error: Execution timeout (30s)", "", 1)
    except Exception as e:
        return (f"Error: {str(e)}", "", 1)
    finally:
        try:
            os.unlink(code_file)
            os.unlink(inputs_file)
        except OSError:
            pass


def run_code_safe(
    code: str,
    inputs: Dict[str, Any],
    dependencies: List[str] = None,
) -> Tuple[str, str, int]:
    dependencies = dependencies or []
    venv_name = get_venv_name(dependencies)
    venv_root = get_venv_root()

    try:
        venv_path = ensure_venv(venv_name, dependencies, venv_root)
    except Exception as e:
        return (f"Venv creation error: {str(e)}", "", 1)

    return run_code_in_venv(code, inputs, venv_path)


def run_code_direct(
    code: str,
    inputs: Dict[str, Any],
    dependencies: List[str] = None,
) -> Tuple[Any, str, int]:
    if dependencies:
        for dep in dependencies:
            if _is_package_installed(dep):
                continue
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                base_name = dep.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
                _installed_packages.add(base_name.lower())
            except subprocess.CalledProcessError as e:
                return (f"Error installing {dep}: {e.stderr}", "", 1)

    stdout_capture = StringIO()
    original_stdout = sys.stdout

    try:
        sys.stdout = stdout_capture
        namespace = inputs.copy()
        namespace["__builtins__"] = __builtins__
        exec(code, namespace)  # noqa: S102
        result = namespace.get("result", "")
        stdout = stdout_capture.getvalue()
        return (result, stdout, 0)
    except Exception as e:
        stdout = stdout_capture.getvalue()
        return (f"Error: {str(e)}", stdout, 1)
    finally:
        sys.stdout = original_stdout
