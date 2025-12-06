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
from typing import Dict, List, Set, Tuple

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
        return "ComfyUI-PyIsolated"  # Default venv
    
    # Sort for consistency
    deps_sorted = sorted(dependencies)
    dep_string = "\n".join(deps_sorted)
    
    # Hash to get unique identifier
    dep_hash = hashlib.sha256(dep_string.encode()).hexdigest()[:8]
    
    return f"PyIsolated_{dep_hash}"


def get_venv_root() -> Path:
    # Try to find ComfyUI root via folder_paths
    try:
        import folder_paths
        return Path(folder_paths.base_path) / ".pyisolate_venvs"
    except ImportError:
        pass
    
    # Fallback: relative to this file
    current_file = Path(__file__).resolve()
    # Go up: execution_wrapper.py -> ComfyUI-PyIsolated -> custom_nodes -> ComfyUI
    comfy_root = current_file.parent.parent.parent
    return comfy_root / ".pyisolate_venvs"


def get_python_executable(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_pip_executable(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def ensure_venv(venv_name: str, dependencies: List[str], venv_root: Path) -> Path:
    venv_path = venv_root / venv_name
    
    if venv_path.exists():
        logger.info(f"[Venv] Reusing existing venv: {venv_name}")
        return venv_path
    
    logger.info(f"[Venv] Creating new venv: {venv_name}")
    
    # Ensure venv root exists
    venv_root.mkdir(parents=True, exist_ok=True)
    
    # Create venv (stream output)
    print(f"\n{'='*60}")
    print(f"🔨 Creating venv: {venv_name}")
    print(f"{'='*60}")
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_path)],
        check=True
    )
    print(f"✅ Venv created: {venv_path}")
    
    # Install dependencies
    if dependencies:
        pip_path = get_pip_executable(venv_path)
        print(f"\n📦 Installing {len(dependencies)} package(s)...")
        
        for i, dep in enumerate(dependencies, 1):
            print(f"\n[{i}/{len(dependencies)}] Installing: {dep}")
            print(f"{'-'*60}")
            try:
                # Stream output directly to console
                subprocess.run(
                    [str(pip_path), "install", dep],
                    check=True
                )
                print(f"✅ Installed: {dep}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {dep}")
                logger.error(f"[Venv] Failed to install {dep}: {e}")
                raise
        
        print(f"\n{'='*60}")
        print(f"✅ All packages installed in: {venv_name}")
        print(f"{'='*60}\n")
    
    logger.info(f"[Venv] Venv ready: {venv_name}")
    return venv_path


def run_code_in_venv(
    code: str,
    inputs: Dict[str, any],
    venv_path: Path
) -> Tuple[str, str, int]:

    python_path = get_python_executable(venv_path)
    
    # Write code and inputs to temp files to avoid escaping issues
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        code_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(inputs, f)
        inputs_file = f.name
    
    # Execution wrapper script - use raw strings for Windows path compatibility
    wrapper_script = f'''
import sys
import json
from io import StringIO

# Load inputs
with open(r"{inputs_file}", "r") as f:
    inputs = json.load(f)

# Capture stdout
stdout_capture = StringIO()
original_stdout = sys.stdout
sys.stdout = stdout_capture

try:
    # Create namespace
    namespace = inputs.copy()
    namespace["__builtins__"] = __builtins__
    
    # Execute code from file
    with open(r"{code_file}", "r") as f:
        code = f.read()
    
    exec(code, namespace)
    
    # Extract result
    result = namespace.get("result", "")
    exit_code = 0
except Exception as e:
    result = f"Error: {{str(e)}}"
    exit_code = 1
finally:
    sys.stdout = original_stdout

# Get stdout
stdout = stdout_capture.getvalue()

# Output as JSON
output = {{"result": str(result), "stdout": stdout, "exit_code": exit_code}}
print(json.dumps(output))
'''
    
    try:
        # Run wrapper in venv
        proc = subprocess.run(
            [str(python_path), "-c", wrapper_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse output
        try:
            output = json.loads(proc.stdout)
            return (output["result"], output["stdout"], output["exit_code"])
        except json.JSONDecodeError as e:
            logger.error(f"[Venv] Failed to parse output: {e}")
            logger.error(f"[Venv] Raw stdout: {repr(proc.stdout)}")
            logger.error(f"[Venv] Stderr: {proc.stderr}")
            return (f"Error: {proc.stderr or str(e)}", proc.stdout, 1)
    
    except subprocess.TimeoutExpired:
        return ("Error: Execution timeout (30s)", "", 1)
    except Exception as e:
        logger.error(f"[Venv] Execution failed: {e}", exc_info=True)
        return (f"Error: {str(e)}", "", 1)
    finally:
        # Cleanup temp files
        try:
            os.unlink(code_file)
            os.unlink(inputs_file)
        except:
            pass


def run_code_safe(
    code: str,
    inputs: Dict[str, any],
    dependencies: List[str] = None,
) -> Tuple[str, str, int]:

    dependencies = dependencies or []
    
    logger.info(f"[Wrapper] Executing code with {len(dependencies)} dependencies")
    
    # Generate venv name from dependencies
    venv_name = get_venv_name(dependencies)
    logger.info(f"[Wrapper] Target venv: {venv_name}")
    
    # Get platform-agnostic venv root
    venv_root = get_venv_root()
    
    try:
        venv_path = ensure_venv(venv_name, dependencies, venv_root)
    except Exception as e:
        logger.error(f"[Wrapper] Venv creation failed: {e}", exc_info=True)
        return (f"Venv creation error: {str(e)}", "", 1)
    
    # Execute code in the venv
    logger.info(f"[Wrapper] Executing in venv: {venv_path}")
    result, stdout, exit_code = run_code_in_venv(code, inputs, venv_path)
    
    logger.info(
        f"[Wrapper] Complete - venv={venv_name}, exit_code={exit_code}, "
        f"stdout_len={len(stdout)}, result_len={len(result)}"
    )
    
    return (result, stdout, exit_code)


def run_code_direct(code: str, inputs: Dict[str, any], dependencies: List[str] = None) -> Tuple[any, str, int]:
    if dependencies:
        for dep in dependencies:
            # Skip if already installed
            if _is_package_installed(dep):
                sys.__stdout__.write(f"✅ {dep} (already installed)\n")
                sys.__stdout__.flush()
                continue
            
            try:
                sys.__stdout__.write(f"📦 Installing: {dep}...\n")
                sys.__stdout__.flush()
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                # Cache as installed
                base_name = dep.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip()
                _installed_packages.add(base_name.lower())
                sys.__stdout__.write(f"✅ Installed: {dep}\n")
                sys.__stdout__.flush()
            except subprocess.CalledProcessError as e:
                sys.__stdout__.write(f"❌ Failed to install {dep}: {e.stderr}\n")
                sys.__stdout__.flush()
                return (f"Error installing {dep}: {e.stderr}", "", 1)
    
    stdout_capture = StringIO()
    original_stdout = sys.stdout
    
    try:
        sys.stdout = stdout_capture
        
        # Create namespace with inputs
        namespace = inputs.copy()
        namespace["__builtins__"] = __builtins__
        
        # Execute user code
        exec(code, namespace)
        
        # Extract result
        result = namespace.get("result", "")
        stdout = stdout_capture.getvalue()
        return (result, stdout, 0)
        
    except Exception as e:
        stdout = stdout_capture.getvalue()
        logger.error(f"[Direct] Execution error: {e}")
        return (f"Error: {str(e)}", stdout, 1)
    finally:
        sys.stdout = original_stdout
