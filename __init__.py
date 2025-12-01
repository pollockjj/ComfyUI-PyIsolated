"""PyIsolated - Secure arbitrary Python execution node for ComfyUI.

Executes user-provided Python code in isolated venvs via PyIsolate process isolation.
Solves the exec() security policy violation while enabling safe workflow sharing.

Research: ComfyUI Python Execution Node Design.md (Section 1.2 - Security Crisis)
"""

from __future__ import annotations

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)
LOG_PREFIX = "🔒 [PyIsolated]"


class PyIsolateExecuteNode:
    """Execute arbitrary Python code in isolated sandbox.
    
    Inputs:
        code: Python code to execute (multiline)
        input_text: Simple text input accessible as `input_text` variable
        dependencies: Newline-separated pip packages (optional)
    
    Outputs:
        result: Execution result (value of `result` variable)
        stdout: Captured console output
        exit_code: 0 = success, 1 = error
    
    Security: Process-isolated via PyIsolate (malicious code cannot escape)
    Pattern: Node-RED Exec node (3-output design for debugging)
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict:
        return {
            "required": {
                "code": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "# Simple example\nresult = f'Hello, {input_text}!'\nprint(f'Processing: {input_text}')",
                    },
                ),
                "input_text": (
                    "STRING",
                    {"default": "World"},
                ),
            },
            "optional": {
                "dependencies": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "# One package per line\n# numpy\n# requests",
                    },
                ),
            },
        }
    
    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("result", "stdout", "exit_code")
    FUNCTION = "execute"
    CATEGORY = "pyisolate"
    OUTPUT_NODE = False
    
    def execute(self, code: str, input_text: str, dependencies: str = "") -> Tuple[str, str, int]:
        """Execute user code in isolated environment.
        
        Args:
            code: Python code string
            input_text: Simple input variable
            dependencies: Newline-separated pip packages
        
        Returns:
            Tuple of (result, stdout, exit_code)
        """
        logger.info(f"{LOG_PREFIX}[Execute] Starting code execution")
        
        from .execution_wrapper import run_code_safe
        
        # Parse dependencies (filter comments and empty lines)
        deps = [
            line.strip()
            for line in dependencies.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        
        logger.info(f"{LOG_PREFIX}[Execute] Dependencies: {deps if deps else 'none'}")
        
        try:
            result, stdout, exit_code = run_code_safe(
                code=code,
                inputs={"input_text": input_text},
                dependencies=deps,
            )
            
            logger.info(
                f"{LOG_PREFIX}[Execute] Complete - exit_code={exit_code}, "
                f"result_len={len(result)}, stdout_len={len(stdout)}"
            )
            
            return (result, stdout, exit_code)
        
        except Exception as e:
            logger.error(f"{LOG_PREFIX}[Execute] Fatal error: {e}", exc_info=True)
            error_msg = f"Fatal execution error: {str(e)}"
            return (error_msg, "", 1)


NODE_CLASS_MAPPINGS = {
    "PyIsolated": PyIsolateExecuteNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PyIsolated": "PyIsolate Execute",
}

logger.info(f"{LOG_PREFIX}[Module] PyIsolated node registered")
