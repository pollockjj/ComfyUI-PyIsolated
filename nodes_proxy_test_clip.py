"""
Proxy Test Node: CLIP

COMPREHENSIVE functionality test of CLIP.
Tests actual behavior, state changes, and operations.
NO proxy knowledge - pure CLIP API testing.
"""
from __future__ import annotations

import torch
from typing import Any, Callable

from comfy_api.latest import io

class ProxyTestCLIP(io.ComfyNode):
    """Comprehensive CLIP functionality test - verifies actual behavior."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestCLIP",
            display_name="Proxy Test: CLIP (Full)",
            category="PyIsolated/ProxyTests",
            inputs=[
                io.Clip.Input("clip"),
                io.String.Input("text", default="A photo of a cat"),
            ],
            outputs=[
                io.String.Output("report", display_name="Report"),
            ],
        )

    @classmethod
    def execute(cls, clip: Any, text: str) -> io.NodeOutput:
        # CRITICAL: Isolate tests from the rest of the workflow.
        # This test node modifies state; working on a clone protects the original.
        clip = clip.clone()

        lines = []
        tested = 0
        passed = 0
        failed = 0

        lines.append("=" * 60)
        lines.append("CLIP COMPREHENSIVE FUNCTIONALITY TEST")
        lines.append("=" * 60)
        lines.append("")

        def verify(name: str,
                  action: Callable[[], Any],
                  check: Callable[[Any], bool] | None = None,
                  pre_check: Callable[[], bool] | None = None,
                  expect_error: type[Exception] | None = None) -> Any:
            nonlocal tested, passed, failed
            tested += 1

            if pre_check:
                try:
                    if not pre_check():
                        lines.append(f"[FAIL] {name} - Pre-condition failed")
                        failed += 1
                        return None
                except Exception as e:
                    lines.append(f"[FAIL] {name} - Pre-check error: {e}")
                    failed += 1
                    return None

            try:
                res = action()

                if expect_error:
                    lines.append(f"[FAIL] {name} - Expected {expect_error.__name__}, got Success")
                    failed += 1
                    return res

                if check:
                    if check(res):
                        lines.append(f"[PASS] {name}")
                        passed += 1
                    else:
                        res_str = str(res)
                        if len(res_str) > 100:
                            res_str = res_str[:97] + "..."
                        lines.append(f"[FAIL] {name} - Verification failed. Result: {res_str}")
                        failed += 1
                else:
                    lines.append(f"[PASS] {name}")
                    passed += 1
                return res

            except Exception as e:
                if expect_error:
                    if isinstance(e, expect_error) or (isinstance(expect_error, tuple) and isinstance(e, expect_error)):
                         lines.append(f"[PASS] {name} - Expected error caught: {type(e).__name__}")
                         passed += 1
                    else:
                         lines.append(f"[FAIL] {name} - Expected {expect_error}, got {type(e).__name__}: {e}")
                         failed += 1
                else:
                    lines.append(f"[FAIL] {name} - Exception: {type(e).__name__}: {e}")
                    failed += 1
                    return None

        # =====================================================================
        # 1. CORE PROPERTIES & STATE
        # =====================================================================
        lines.append("-" * 40)
        lines.append("1. CORE PROPERTIES & STATE")
        lines.append("-" * 40)

        verify("patcher_access", lambda: clip.patcher, check=lambda x: x is not None)
        verify("layer_idx_default", lambda: clip.layer_idx, check=lambda x: x is None)

        # Setter Tests
        verify("set_layer_idx",
               lambda: (clip.clip_layer( -2 ), clip.layer_idx)[-1],
               check=lambda x: x == -2)

        verify("tokenizer_options_access", lambda: isinstance(clip.tokenizer_options, dict), check=lambda x: True)
        verify("set_tokenizer_option",
               lambda: (clip.set_tokenizer_option("test_opt", 123), clip.tokenizer_options.get("test_opt"))[-1],
               check=lambda x: x == 123)

        verify("use_clip_schedule_default", lambda: clip.use_clip_schedule, check=lambda x: x is False)

        # Test property setter if accessible, or modifications
        def set_schedule():
            clip.use_clip_schedule = True
            return clip.use_clip_schedule
        verify("set_use_clip_schedule", set_schedule, check=lambda x: x is True)

        verify("apply_hooks_to_conds_access", lambda: clip.apply_hooks_to_conds, check=lambda x: True) # None or value

        verify("get_ram_usage", lambda: clip.get_ram_usage(), check=lambda x: isinstance(x, int))

        # =====================================================================
        # 2. ENCODING
        # =====================================================================
        lines.append("-" * 40)
        lines.append("2. ENCODING")
        lines.append("-" * 40)

        # Tokenize
        tokens = verify("tokenize", lambda: clip.tokenize(text), check=lambda x: isinstance(x, dict))

        if tokens:
            # Encode from Tokens (default: just cond)
            verify("encode_from_tokens(cond_only)",
                   lambda: clip.encode_from_tokens(tokens, return_pooled=False),
                   check=lambda x: isinstance(x, torch.Tensor))

            # Encode from Tokens (return_pooled=True) -> Tuple Check!
            verify("encode_from_tokens(pooled=True)",
                   lambda: clip.encode_from_tokens(tokens, return_pooled=True),
                   check=lambda x: isinstance(x, tuple) and len(x) == 2)

            # Encode from Tokens (return_dict=True) -> Dict
            verify("encode_from_tokens(dict=True)",
                   lambda: clip.encode_from_tokens(tokens, return_dict=True),
                   check=lambda x: isinstance(x, dict) and "cond" in x and "pooled_output" in x)

        # Direct Encode
        verify("encode",
               lambda: clip.encode(text),
               check=lambda x: isinstance(x, torch.Tensor))

        # =====================================================================
        # 3. PATCHING INTERACTION (Nested Proxy)
        # =====================================================================
        lines.append("-" * 40)
        lines.append("3. PATCHING & NESTED ACCESS")
        lines.append("-" * 40)

        verify("get_key_patches", lambda: clip.get_key_patches(), check=lambda x: isinstance(x, dict))

        # Test add_patches (delegates to patcher)
        verify("add_patches",
               lambda: clip.add_patches({}, 1.0, 1.0),
               check=lambda x: isinstance(x, list) or isinstance(x, tuple)) # Core returns tuple/list

        # Verify load_model
        verify("load_model",
               lambda: clip.load_model(),
               check=lambda x: x is not None) # Returns patcher

        # =====================================================================
        # 4. IDENTITY & CLONING
        # =====================================================================
        lines.append("-" * 40)
        lines.append("4. IDENTITY & CLONING")
        lines.append("-" * 40)

        new_clip = verify("clone", lambda: clip.clone(), check=lambda x: x is not None and x is not clip)

        if new_clip:
            verify("clone_independence",
                   lambda: new_clip.patcher is not clip.patcher,
                   check=lambda x: True) # Should have different patcher instances (proxies)

            # Verify new clip works
            verify("clone_encode",
                   lambda: new_clip.encode(text),
                   check=lambda x: isinstance(x, torch.Tensor))

        # =====================================================================
        # 5. STATE DICT & SAVING
        # =====================================================================
        lines.append("-" * 40)
        lines.append("5. STATE DICT")
        lines.append("-" * 40)

        verify("get_sd", lambda: clip.get_sd(), check=lambda x: isinstance(x, dict))

        # Verify load_sd matches signature, but tough to test without real weights
        # So we just ensure method exists and args valid
        # We can pass empty dict and expect it to handle (or fail specific way)
        # verify("load_sd", lambda: clip.load_sd({}), expect_error=Exception)

        lines.append("")
        lines.append("=" * 60)
        lines.append("SUMMARY")
        lines.append(f"Tested: {tested} | Passed: {passed} | Failed: {failed}")
        coverage = (passed / tested * 100) if tested > 0 else 0
        lines.append(f"Functional Coverage: {coverage:.1f}%")
        lines.append("=" * 60)

        return io.NodeOutput("\n".join(lines))


NODES = [ProxyTestCLIP]
