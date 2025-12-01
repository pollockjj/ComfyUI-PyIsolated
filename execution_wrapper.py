"""Execution wrapper for isolated Python code execution.

Captures stdout, handles errors, executes user code in controlled namespace.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)
LOG_PREFIX = "🔒 [PyIsolated]"


def get_venv_name(dependencies: List[str]) -> str:
    """Generate unique venv name based on dependency hash.
    
    Args:
        dependencies: List of pip package specifiers
    
    Returns:
        Venv name like 'PyIsolated_abc12345'
    """
    if not dependencies:
        return "ComfyUI-PyIsolated"  # Default venv
    
    # Sort for consistency
    deps_sorted = sorted(dependencies)
    dep_string = "\n".join(deps_sorted)
    
    # Hash to get unique identifier
    dep_hash = hashlib.sha256(dep_string.encode()).hexdigest()[:8]
    
    return f"PyIsolated_{dep_hash}"


def ensure_venv(venv_name: str, dependencies: List[str], venv_root: Path) -> Path:
    """Ensure venv exists with dependencies installed.
    
    Args:
        venv_name: Name of the venv
        dependencies: List of pip packages to install
        venv_root: Root directory for venvs
    
    Returns:
        Path to the venv directory
    """
    venv_path = venv_root / venv_name
    
    if venv_path.exists():
        logger.info(f"{LOG_PREFIX}[Venv] Reusing existing venv: {venv_name}")
        return venv_path
    
    logger.info(f"{LOG_PREFIX}[Venv] Creating new venv: {venv_name}")
    
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
        pip_path = venv_path / "bin" / "pip"
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
                logger.error(f"{LOG_PREFIX}[Venv] Failed to install {dep}: {e}")
                raise
        
        print(f"\n{'='*60}")
        print(f"✅ All packages installed in: {venv_name}")
        print(f"{'='*60}\n")
    
    logger.info(f"{LOG_PREFIX}[Venv] Venv ready: {venv_name}")
    return venv_path


def run_code_in_venv(
    code: str,
    inputs: Dict[str, any],
    venv_path: Path
) -> Tuple[str, str, int]:
    """Execute code in specific venv via subprocess.
    
    Args:
        code: Python code to execute
        inputs: Input variables
        venv_path: Path to venv to use
    
    Returns:
        Tuple of (result, stdout, exit_code)
    """
    python_path = venv_path / "bin" / "python"
    
    # Write code and inputs to temp files to avoid escaping issues
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        code_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(inputs, f)
        inputs_file = f.name
    
    # Execution wrapper script
    wrapper_script = f"""
import sys
import json
from io import StringIO

# Load inputs
with open('{inputs_file}', 'r') as f:
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
    with open('{code_file}', 'r') as f:
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
"""
    
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
            logger.error(f"{LOG_PREFIX}[Venv] Failed to parse output: {e}")
            logger.error(f"{LOG_PREFIX}[Venv] Raw stdout: {repr(proc.stdout)}")
            logger.error(f"{LOG_PREFIX}[Venv] Stderr: {proc.stderr}")
            return (f"Error: {proc.stderr or str(e)}", proc.stdout, 1)
    
    except subprocess.TimeoutExpired:
        return ("Error: Execution timeout (30s)", "", 1)
    except Exception as e:
        logger.error(f"{LOG_PREFIX}[Venv] Execution failed: {e}", exc_info=True)
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
    """Execute user code safely with dynamic venv per dependency set.
    
    Args:
        code: Python code string to execute
        inputs: Dictionary of input variables (accessible in code)
        dependencies: List of pip packages (creates unique venv per set)
    
    Returns:
        Tuple of (result_string, stdout_string, exit_code)
        exit_code: 0 = success, 1 = error
    
    Security: Runs in isolated venv (managed by PyIsolate infrastructure)
    """
    dependencies = dependencies or []
    
    logger.info(f"{LOG_PREFIX}[Wrapper] Executing code with {len(dependencies)} dependencies")
    
    # Generate venv name from dependencies
    venv_name = get_venv_name(dependencies)
    logger.info(f"{LOG_PREFIX}[Wrapper] Target venv: {venv_name}")
    
    # Ensure venv exists
    venv_root = Path("/mnt/ai/ComfyUI/.pyisolate_venvs")
    try:
        venv_path = ensure_venv(venv_name, dependencies, venv_root)
    except Exception as e:
        logger.error(f"{LOG_PREFIX}[Wrapper] Venv creation failed: {e}", exc_info=True)
        return (f"Venv creation error: {str(e)}", "", 1)
    
    # Execute code in the venv
    logger.info(f"{LOG_PREFIX}[Wrapper] Executing in venv: {venv_path}")
    result, stdout, exit_code = run_code_in_venv(code, inputs, venv_path)
    
    logger.info(
        f"{LOG_PREFIX}[Wrapper] Complete - venv={venv_name}, exit_code={exit_code}, "
        f"stdout_len={len(stdout)}, result_len={len(result)}"
    )
    
    return (result, stdout, exit_code)
