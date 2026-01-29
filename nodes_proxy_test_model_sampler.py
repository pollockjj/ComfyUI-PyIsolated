"""
Proxy Test Node: ModelSampler

COMPREHENSIVE functionality test of ModelSampler (ModelSampling).
Tests explicit implementation of all properties and methods.
"""
from __future__ import annotations

import torch
from typing import Any, Callable

from comfy_api.latest import io
import comfy.model_sampling
import comfy.model_patcher

class ProxyTestModelSampler(io.ComfyNode):
    """Comprehensive ModelSampler functionality test."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestModelSampler",
            display_name="Proxy Test: ModelSampler (Full)",
            category="PyIsolated/ProxyTests",
            inputs=[
                io.Model.Input("model"),
            ],
            outputs=[
                io.String.Output("report", display_name="Report"),
            ],
        )

    @classmethod
    def execute(cls, model: comfy.model_patcher.ModelPatcher) -> io.NodeOutput:
        # Get the model_sampling instance from the ModelPatcher
        # This will be a ModelSamplingProxy in isolated mode, or ModelSampling in standard
        sampler = model.get_model_object("model_sampling")

        lines = []
        tested = 0
        passed = 0
        failed = 0

        lines.append("=" * 60)
        lines.append("MODELSAMPLER COMPREHENSIVE FUNCTIONALITY TEST")
        lines.append(f"Type: {type(sampler).__name__}")
        lines.append("=" * 60)

        def verify(name: str,
                  action: Callable[[], Any],
                  check: Callable[[Any], bool] | None = None,
                  expect_error: type[Exception] | None = None) -> Any:
            nonlocal tested, passed, failed
            tested += 1
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
                        lines.append(f"[FAIL] {name} - Verification failed. Result: {res}")
                        failed += 1
                else:
                    lines.append(f"[PASS] {name}")
                    passed += 1
                return res
            except Exception as e:
                lines.append(f"[FAIL] {name} - Error: {e}")
                failed += 1
                return None

        # =====================================================================
        # 1. CORE PROPERTIES (Explicitly Proxied)
        # =====================================================================
        lines.append("-" * 40)
        lines.append("1. CORE PROPERTIES")
        lines.append("-" * 40)

        # sigma_min/max/data might be tensors or floats depending on the specific sampler implementation
        verify("sigma_min", lambda: sampler.sigma_min, check=lambda x: isinstance(x, (float, torch.Tensor)))
        verify("sigma_max", lambda: sampler.sigma_max, check=lambda x: isinstance(x, (float, torch.Tensor)))
        verify("sigma_data", lambda: sampler.sigma_data, check=lambda x: isinstance(x, (float, torch.Tensor)))
        verify("sigmas (buffer)", lambda: sampler.sigmas, check=lambda x: isinstance(x, torch.Tensor))

        # =====================================================================
        # 2. CALCULATION METHODS
        # =====================================================================
        lines.append("-" * 40)
        lines.append("2. CALCULATION METHODS")
        lines.append("-" * 40)

        dummy_sigma = torch.tensor(1.0)
        dummy_timestep = torch.tensor(500.0)

        verify("timestep",
               lambda: sampler.timestep(dummy_sigma),
               check=lambda x: isinstance(x, torch.Tensor))

        verify("sigma",
               lambda: sampler.sigma(dummy_timestep),
               check=lambda x: isinstance(x, torch.Tensor))

        verify("percent_to_sigma",
               lambda: sampler.percent_to_sigma(0.5),
               check=lambda x: isinstance(x, float))

        # =====================================================================
        # 3. NOISE OPERATIONS
        # =====================================================================
        lines.append("-" * 40)
        lines.append("3. NOISE OPERATIONS")
        lines.append("-" * 40)

        dummy_noise = torch.randn(1, 4, 32, 32)
        dummy_latent = torch.randn(1, 4, 32, 32)
        dummy_model_out = torch.randn(1, 4, 32, 32)
        dummy_model_in = torch.randn(1, 4, 32, 32)

        verify("calculate_input",
               lambda: sampler.calculate_input(dummy_sigma, dummy_noise),
               check=lambda x: isinstance(x, torch.Tensor) and x.shape == dummy_noise.shape)

        verify("calculate_denoised",
               lambda: sampler.calculate_denoised(dummy_sigma, dummy_model_out, dummy_model_in),
               check=lambda x: isinstance(x, torch.Tensor))

        verify("noise_scaling",
               lambda: sampler.noise_scaling(dummy_sigma, dummy_noise, dummy_latent),
               check=lambda x: isinstance(x, torch.Tensor))

        verify("inverse_noise_scaling",
               lambda: sampler.inverse_noise_scaling(dummy_sigma, dummy_latent),
               check=lambda x: isinstance(x, torch.Tensor))

        # =====================================================================
        # 4. STATE MODIFICATION (set_sigmas)
        # =====================================================================
        lines.append("-" * 40)
        lines.append("4. STATE MODIFICATION")
        lines.append("-" * 40)

        # Create new sigmas and verify state update
        new_sigmas = torch.linspace(0.1, 10.0, 10).float()
        expected_min = new_sigmas[0].item()
        expected_max = new_sigmas[-1].item()

        # Verify set_sigmas updates internal state (sigma_min/max should change)
        def check_set_sigmas():
            sampler.set_sigmas(new_sigmas)
            # Fetch new values to confirm update
            s_min = sampler.sigma_min
            s_max = sampler.sigma_max
            # Allow small float tolerance if needed, but linear space should be exact here
            return abs(s_min - expected_min) < 1e-5 and abs(s_max - expected_max) < 1e-5

        verify("set_sigmas (State Update)",
               check_set_sigmas,
               check=lambda x: bool(x))

        lines.append("")
        lines.append("=" * 60)
        lines.append("SUMMARY")
        lines.append(f"Tested: {tested} | Passed: {passed} | Failed: {failed}")
        coverage = (passed / tested * 100) if tested > 0 else 0
        lines.append(f"Functional Coverage: {coverage:.1f}%")
        lines.append("=" * 60)

        return io.NodeOutput("\n".join(lines))

NODES = [ProxyTestModelSampler]
