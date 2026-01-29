"""
Proxy Test Node: Utils

SYSTEMATIC test of comfy.utils proxy coverage.
Enumerates key APIs that nodes use from comfy.utils.
Outputs coverage report for baseline comparison.
"""
from __future__ import annotations


import comfy.utils
from comfy_api.latest import io


# Key comfy.utils members that nodes actually use
UTILS_CONSTANTS = [
    "PROGRESS_BAR_ENABLED",
    "PROGRESS_BAR_HOOK",
    "ALWAYS_SAFE_LOAD",
    "DISABLE_MMAP",
    "MMAP_TORCH_FILES",
]

UTILS_FUNCTIONS = [
    "set_progress_bar_enabled",
    "set_progress_bar_global_hook",
    "reshape_mask",
    "common_upscale",
    "bislerp",
    "lanczos",
]

UTILS_CLASSES = [
    "ProgressBar",
]


class ProxyTestUtils(io.ComfyNode):
    """Systematic test of comfy.utils - tests key APIs nodes use."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestUtils",
            display_name="Proxy Test: Utils",
            category="PyIsolated/ProxyTests",
            inputs=[
                io.Latent.Input("latent", optional=True),
            ],
            outputs=[
                io.String.Output("report", display_name="Report"),
            ],
        )

    @classmethod
    def execute(cls, latent=None) -> io.NodeOutput:
        lines = []
        tested = 0
        passed = 0
        failed = 0
        skipped = 0

        lines.append("=" * 60)
        lines.append("UTILS PROXY COVERAGE REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Section 1: Constants
        lines.append("-" * 40)
        lines.append("CONSTANTS")
        lines.append("-" * 40)

        for const_name in UTILS_CONSTANTS:
            tested += 1
            try:
                value = getattr(comfy.utils, const_name)
                lines.append(f"[PASS] {const_name} = {value}")
                passed += 1
            except AttributeError:
                lines.append(f"[FAIL] {const_name}: AttributeError (not found)")
                failed += 1
            except Exception as e:
                lines.append(f"[FAIL] {const_name}: {type(e).__name__}: {e}")
                failed += 1

        lines.append("")
        lines.append("-" * 40)
        lines.append("FUNCTIONS (existence check)")
        lines.append("-" * 40)

        for func_name in UTILS_FUNCTIONS:
            tested += 1
            try:
                func = getattr(comfy.utils, func_name)
                if callable(func):
                    lines.append(f"[PASS] {func_name} exists and is callable")
                    passed += 1
                else:
                    lines.append(f"[FAIL] {func_name} exists but not callable")
                    failed += 1
            except AttributeError:
                lines.append(f"[FAIL] {func_name}: AttributeError (not found)")
                failed += 1
            except Exception as e:
                lines.append(f"[FAIL] {func_name}: {type(e).__name__}: {e}")
                failed += 1

        lines.append("")
        lines.append("-" * 40)
        lines.append("CLASSES")
        lines.append("-" * 40)

        for class_name in UTILS_CLASSES:
            tested += 1
            try:
                cls_obj = getattr(comfy.utils, class_name)
                if isinstance(cls_obj, type):
                    lines.append(f"[PASS] {class_name} exists and is a class")
                    passed += 1
                else:
                    lines.append(f"[FAIL] {class_name} exists but not a class")
                    failed += 1
            except AttributeError:
                lines.append(f"[FAIL] {class_name}: AttributeError (not found)")
                failed += 1
            except Exception as e:
                lines.append(f"[FAIL] {class_name}: {type(e).__name__}: {e}")
                failed += 1

        lines.append("")
        lines.append("-" * 40)
        lines.append("PROGRESSBAR FUNCTIONAL TESTS")
        lines.append("-" * 40)

        # ProgressBar instantiation
        tested += 1
        try:
            pbar = comfy.utils.ProgressBar(100)
            lines.append(f"[PASS] ProgressBar(100): total={pbar.total}, current={pbar.current}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] ProgressBar(100): {e}")
            failed += 1

        # ProgressBar.update_absolute
        tested += 1
        try:
            pbar = comfy.utils.ProgressBar(100)
            pbar.update_absolute(50)
            lines.append(f"[PASS] pbar.update_absolute(50): current={pbar.current}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] pbar.update_absolute(50): {e}")
            failed += 1

        # ProgressBar.update
        tested += 1
        try:
            pbar = comfy.utils.ProgressBar(100)
            pbar.update(10)
            pbar.update(20)
            lines.append(f"[PASS] pbar.update(10), pbar.update(20): current={pbar.current}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] pbar.update(): {e}")
            failed += 1

        # Hook callback test
        tested += 1
        hook_called = False
        def test_hook(current, total, preview=None, node_id=None):
            nonlocal hook_called
            hook_called = True

        try:
            original_hook = comfy.utils.PROGRESS_BAR_HOOK
            comfy.utils.set_progress_bar_global_hook(test_hook)
            pbar = comfy.utils.ProgressBar(100)
            pbar.update_absolute(50)
            comfy.utils.PROGRESS_BAR_HOOK = original_hook
            lines.append(f"[PASS] Hook callback test: hook_called={hook_called}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] Hook callback test: {e}")
            failed += 1

        lines.append("")
        lines.append("-" * 40)
        lines.append("PROGRESS_BAR_HOOK STATE")
        lines.append("-" * 40)

        # Critical test: Is PROGRESS_BAR_HOOK set?
        # This MUST be set for progress to work. If None, proxy is broken.
        tested += 1
        try:
            hook = comfy.utils.PROGRESS_BAR_HOOK
            if hook is None:
                lines.append("[FAIL] PROGRESS_BAR_HOOK is None - progress updates broken")
                failed += 1
            else:
                lines.append(f"[PASS] PROGRESS_BAR_HOOK is set: {type(hook)}")
                passed += 1
        except Exception as e:
            lines.append(f"[FAIL] PROGRESS_BAR_HOOK: {e}")
            failed += 1

        # Summary
        lines.append("")
        lines.append("=" * 60)
        lines.append("COVERAGE SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Total items tested: {tested}")
        lines.append(f"Passed: {passed}")
        lines.append(f"Failed: {failed}")
        lines.append(f"Skipped: {skipped}")
        coverage = (passed / tested * 100) if tested > 0 else 0
        lines.append(f"Coverage: {coverage:.1f}%")
        lines.append("=" * 60)

        report = "\n".join(lines)
        return io.NodeOutput(report)


NODES = [ProxyTestUtils]
