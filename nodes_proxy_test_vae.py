"""
Proxy Test Node: VAE

COMPREHENSIVE functionality test of VAE.
Tests actual behavior, state changes, and operations.
NO proxy knowledge - pure VAE API testing.
"""
from __future__ import annotations

import torch
from typing import Any, Callable

from comfy_api.latest import io

class ProxyTestVAE(io.ComfyNode):
    """Comprehensive VAE functionality test - verifies actual behavior."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestVAE",
            display_name="Proxy Test: VAE (Full)",
            category="PyIsolated/ProxyTests",
            inputs=[
                io.Vae.Input("vae"),
            ],
            outputs=[
                io.String.Output("report", display_name="Report"),
            ],
        )

    @classmethod
    def execute(cls, vae: Any) -> io.NodeOutput:
        # Note: VAE doesn't have clone() usually, but we treat it as read-only or copy if needed.
        # VAE methods are mostly functional (encode/decode), state is configs.

        lines = []
        tested = 0
        passed = 0
        failed = 0

        lines.append("=" * 60)
        lines.append("VAE COMPREHENSIVE FUNCTIONALITY TEST")
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
        # 1. CORE PROPERTIES
        # =====================================================================
        lines.append("-" * 40)
        lines.append("1. CORE PROPERTIES")
        lines.append("-" * 40)

        verify("latent_dim", lambda: vae.latent_dim, check=lambda x: isinstance(x, int))
        verify("latent_channels", lambda: vae.latent_channels, check=lambda x: isinstance(x, int))
        verify("output_channels", lambda: vae.output_channels, check=lambda x: isinstance(x, int))

        # downscale/upscale ratio can be int or callable/tuple logic. Just check access.
        verify("downscale_ratio_access", lambda: vae.downscale_ratio, check=lambda x: True)
        verify("upscale_ratio_access", lambda: vae.upscale_ratio, check=lambda x: True)

        verify("working_dtypes", lambda: vae.working_dtypes, check=lambda x: isinstance(x, list))

        # =====================================================================
        # 1a. INTERNAL STRUCTURE (Isolation Critical)
        # =====================================================================
        lines.append("-" * 40)
        lines.append("1a. INTERNAL STRUCTURE")
        lines.append("-" * 40)

        verify("device", lambda: vae.device, check=lambda x: str(x).startswith("cuda") or str(x).startswith("cpu"))
        verify("vae_dtype", lambda: vae.vae_dtype, check=lambda x: x is not None)

        # These access internal structure via Proxies in isolation
        verify("patcher_access", lambda: vae.patcher, check=lambda x: x is not None)

        # first_stage_model: Should check basic attribute access to ensure proxy works
        def check_fsm():
             return hasattr(vae.first_stage_model, "encode") or hasattr(vae.first_stage_model, "decode")
        verify("first_stage_model_access", check_fsm, check=lambda x: x is True)

        # =====================================================================
        # 2. MEMORY AND PROCESSING
        # =====================================================================
        lines.append("-" * 40)
        lines.append("2. MEMORY & PROCESSING")
        lines.append("-" * 40)

        # Test memory estimation lambdas
        dummy_shape = (1, 3, 512, 512)
        dummy_dtype = torch.float16
        verify("memory_used_encode",
               lambda: vae.memory_used_encode(dummy_shape, dummy_dtype),
               check=lambda x: isinstance(x, (int, float)))

        verify("memory_used_decode",
               lambda: vae.memory_used_decode(dummy_shape, dummy_dtype),
               check=lambda x: isinstance(x, (int, float)))

        # Test processing wrappers (expect tensors back normally, or modified tensors)
        dummy_img = torch.zeros((1, 512, 512, 3))
        verify("process_input",
               lambda: vae.process_input(dummy_img),
               check=lambda x: isinstance(x, torch.Tensor))

        # =====================================================================
        # 3. ENCODE / DECODE OPERATIONS
        # =====================================================================
        lines.append("-" * 40)
        lines.append("3. ENCODE / DECODE")
        lines.append("-" * 40)

        # We need a dummy input suitable for encoding.
        # Usually process_input expects NHWC or NCHW depending on context, but VAE usually takes (B, H, W, C) or (B, C, H, W)
        # ComfyUI VAE encode takes (B, H, W, 3) images normalized 0-1 usually.

        test_image = torch.rand((1, 64, 64, 3)) # Small image for speed

        # Encode
        latent = verify("encode",
               lambda: vae.encode(test_image),
               check=lambda x: isinstance(x, torch.Tensor))

        if latent is not None:
             # Decode
             verify("decode",
                    lambda: vae.decode(latent),
                    check=lambda x: isinstance(x, torch.Tensor))

             # Encode Tiled (if supported, might just call encode for small img)
             verify("encode_tiled",
                    lambda: vae.encode_tiled(test_image, tile_x=64, tile_y=64),
                    check=lambda x: isinstance(x, torch.Tensor))

             # Decode Tiled
             verify("decode_tiled",
                    lambda: vae.decode_tiled(latent, tile_x=64, tile_y=64),
                    check=lambda x: isinstance(x, torch.Tensor))

        # =====================================================================
        # 4. STATE DICT
        # =====================================================================
        lines.append("-" * 40)
        lines.append("4. STATE DICT")
        lines.append("-" * 40)

        verify("get_sd", lambda: vae.get_sd(), check=lambda x: isinstance(x, dict))

        lines.append("")
        lines.append("=" * 60)
        lines.append("SUMMARY")
        lines.append(f"Tested: {tested} | Passed: {passed} | Failed: {failed}")
        coverage = (passed / tested * 100) if tested > 0 else 0
        lines.append(f"Functional Coverage: {coverage:.1f}%")
        lines.append("=" * 60)

        return io.NodeOutput("\n".join(lines))


NODES = [ProxyTestVAE]
