"""Security Audit Node for ComfyUI Process Isolation"""

from __future__ import annotations

import os
import random
import sys

from comfy_api.latest import io


class AdversarialSummary(io.ComfyNode):
    """Execute security audit - crash bomb test."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AdversarialSummary",
            category="security_audit",
            display_name="Security Audit",
            inputs=[],
            outputs=[io.String.Output("report", display_name="Audit Report")],
        )

    @classmethod
    def execute(cls) -> io.NodeOutput:
        lines = []
        results = []

        lines.append("TEST 1: INJECT CRASH BOMB")
        lines.append("$ import sys")
        lines.append("$ exec_module = sys.modules['execution']")
        lines.append("$ exec_module.PromptExecutor.execute = crash_bomb")
        
        try:
            if 'execution' not in sys.modules:
                import execution
            
            exec_module = sys.modules['execution']
            pe = exec_module.PromptExecutor
            pe_execute = pe.execute
            already_installed = hasattr(pe_execute, '_crash_bomb_installed')
            
            if already_installed:
                lines.append("Result: Already installed")
                results.append(("crash_bomb", True))
            else:
                original_execute = pe_execute
                
                def crash_bomb_execute(self, *args, **kwargs):
                    if random.random() < 0.25:
                        os._exit(1)
                    return original_execute(self, *args, **kwargs)
                
                crash_bomb_execute._crash_bomb_installed = True
                crash_bomb_execute._original = original_execute
                exec_module.PromptExecutor.execute = crash_bomb_execute
                
                lines.append("Result: INSTALLED - 25% crash rate active")
                results.append(("crash_bomb", True))
                
        except Exception as e:
            lines.append(f"Result: BLOCKED - {e}")
            results.append(("crash_bomb", False))

        lines.append("")
        vulnerable = sum(1 for r in results if r[1])
        lines.append(f"Attacks succeeded: {vulnerable}/{len(results)}")
        
        if vulnerable > 0:
            lines.append("VERDICT: VULNERABLE")
        else:
            lines.append("VERDICT: PROTECTED")
        
        report = "\n".join(lines)
        return io.NodeOutput(report)
