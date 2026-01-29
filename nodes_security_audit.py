"""Security Audit Node for ComfyUI Process Isolation"""

from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)

_TRACE_FILE = "/home/johnj/audit_trace.log"

# Overwrite trace file ONLY in host on first load
if os.environ.get('PYISOLATE_CHILD') != '1':
    try:
        with open(_TRACE_FILE, "w") as f:
            f.write(f"[{os.getpid()}] HOST START\n")
    except:
        pass

def _trace(msg):
    try:
        with open(_TRACE_FILE, "a") as f:
            f.write(f"[{os.getpid()}] {msg}\n")
            f.flush()
    except:
        pass

_trace("LINE 17: module start")

import os

_trace("LINE 20: os imported")


_trace("LINE 24: subprocess imported")


_trace("LINE 28: sys imported")

_trace(f"LINE 30: PYISOLATE_CHILD={os.environ.get('PYISOLATE_CHILD')}")

from comfy_api.latest import io

_trace("LINE 34: io imported")


class SecurityAudit(io.ComfyNode):
    _trace("LINE 36: class body start")
    """Execute security audit."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        _trace("LINE 41: define_schema called")
        result = io.Schema(
            node_id="SecurityAudit",
            category="security_audit",
            display_name="Security Audit",
            inputs=[],
            outputs=[io.String.Output("report", display_name="Audit Report")],
        )
        _trace("LINE 49: define_schema returning")
        return result

    @classmethod
    def execute(cls) -> io.NodeOutput:
        _trace("LINE 54: execute() START")

        _trace("LINE 56: creating lines list")
        lines = []

        _trace("LINE 59: creating results list")
        results = []

        _trace("LINE 62: appending TEST 1 header")
        lines.append("TEST 1: INJECT CRASH BOMB")

        _trace("LINE 65: appending command lines")
        lines.append("$ import sys")
        lines.append("$ exec_module = sys.modules['execution']")
        lines.append("$ exec_module.PromptExecutor.execute = crash_bomb")

        _trace("LINE 70: entering try block")
        logger.info("SecurityAudit: entering try block")
        try:
            _trace("LINE 72: importing sys")
            logger.info("SecurityAudit: importing sys")
            import sys

            _trace(f"LINE 75: sys imported, {len(sys.modules)} modules loaded")
            logger.info(f"SecurityAudit: sys imported, {len(sys.modules)} modules loaded")

            _trace("LINE 77: importing random")
            logger.info("SecurityAudit: importing random")
            import random

            _trace("LINE 80: random imported")
            logger.info("SecurityAudit: random imported")

            _trace(f"LINE 82: checking 'execution' in sys.modules: {'execution' in sys.modules}")
            logger.info(f"SecurityAudit: checking 'execution' in sys.modules: {'execution' in sys.modules}")

            if 'execution' not in sys.modules:
                _trace("LINE 85: execution NOT in sys.modules, importing...")
                logger.info("SecurityAudit: execution NOT in sys.modules, importing...")
                _trace("LINE 87: execution import completed")
                logger.info("SecurityAudit: execution import completed")
            else:
                _trace("LINE 89: execution already in sys.modules")
                logger.info("SecurityAudit: execution already in sys.modules")

            _trace("LINE 91: getting exec_module from sys.modules")
            logger.info("SecurityAudit: getting exec_module from sys.modules")
            exec_module = sys.modules['execution']

            _trace(f"LINE 94: exec_module = {exec_module}")
            logger.info(f"SecurityAudit: exec_module = {exec_module}")
            _trace(f"LINE 95: type(exec_module) = {type(exec_module)}")
            logger.info(f"SecurityAudit: type(exec_module) = {type(exec_module)}")

            _trace("LINE 97: checking PromptExecutor attribute")
            logger.info("SecurityAudit: checking PromptExecutor attribute")
            pe = exec_module.PromptExecutor
            _trace(f"LINE 99: PromptExecutor = {pe}")
            logger.info(f"SecurityAudit: PromptExecutor = {pe}")

            _trace("LINE 101: checking PromptExecutor.execute attribute")
            logger.info("SecurityAudit: checking PromptExecutor.execute attribute")
            pe_execute = pe.execute
            _trace(f"LINE 103: PromptExecutor.execute = {pe_execute}")
            logger.info(f"SecurityAudit: PromptExecutor.execute = {pe_execute}")

            _trace("LINE 105: checking _crash_bomb_installed attribute")
            logger.info("SecurityAudit: checking _crash_bomb_installed attribute")
            already_installed = hasattr(pe_execute, '_crash_bomb_installed')
            _trace(f"LINE 107: already_installed = {already_installed}")
            logger.info(f"SecurityAudit: already_installed = {already_installed}")

            if already_installed:
                _trace("LINE 110: bomb already installed")
                logger.info("SecurityAudit: bomb already installed")
                lines.append("Result: Already installed")
                results.append(("crash_bomb", True))
            else:
                _trace("LINE 114: bomb not installed, patching...")
                logger.info("SecurityAudit: bomb not installed, patching...")

                _trace("LINE 116: storing original_execute")
                logger.info("SecurityAudit: storing original_execute")
                original_execute = pe_execute

                _trace(f"LINE 119: original_execute = {original_execute}")
                logger.info(f"SecurityAudit: original_execute = {original_execute}")

                _trace("LINE 121: defining crash_bomb_execute")
                def crash_bomb_execute(self, *args, **kwargs):
                    if random.random() < 0.25:
                        os._exit(1)
                    return original_execute(self, *args, **kwargs)

                _trace("LINE 127: setting _crash_bomb_installed attribute")
                crash_bomb_execute._crash_bomb_installed = True

                _trace("LINE 130: setting _original attribute")
                crash_bomb_execute._original = original_execute

                _trace("LINE 133: patching PromptExecutor.execute")
                exec_module.PromptExecutor.execute = crash_bomb_execute

                _trace("LINE 136: patch complete")

                _trace("LINE 138: appending result")
                lines.append("Result: INSTALLED - 25% crash rate active")
                results.append(("crash_bomb", True))

                _trace("LINE 142: result appended")

        except Exception as e:
            _trace(f"LINE 145: EXCEPTION caught: {type(e).__name__}: {e}")
            import traceback
            _trace(f"LINE 147: traceback: {traceback.format_exc()}")
            lines.append(f"Result: BLOCKED - {e}")
            results.append(("crash_bomb", False))
            _trace("LINE 150: exception handled")

        _trace("LINE 152: building summary")
        lines.append("")

        _trace("LINE 155: counting vulnerable")
        vulnerable = sum(1 for r in results if r[1])

        _trace(f"LINE 158: vulnerable = {vulnerable}")
        lines.append(f"Attacks succeeded: {vulnerable}/{len(results)}")

        _trace("LINE 161: checking verdict")
        if vulnerable > 0:
            lines.append("VERDICT: VULNERABLE")
        else:
            lines.append("VERDICT: PROTECTED")

        _trace("LINE 167: joining report")
        report = "\n".join(lines)

        _trace(f"LINE 170: report length = {len(report)}")
        _trace("LINE 171: execute() END, returning")
        return io.NodeOutput(report)

_trace("LINE 174: module load complete")
