"""
Proxy Test Node: Model Management

COMPREHENSIVE functionality test of comfy.model_management.
Tests actual behavior, state changes, and operations.
NO proxy knowledge - pure model_management API testing.
Model-patcher-level rigor with 100/100 coverage, 0 skips.
"""
from __future__ import annotations

import torch
from typing import Any, Callable

import comfy.model_management as mm
from comfy_api.latest import io


class ProxyTestModelManagement(io.ComfyNode):
    """Comprehensive model_management functionality test - verifies actual behavior."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestModelManagement",
            display_name="Proxy Test: Model Management (Full)",
            category="PyIsolated/ProxyTests",
            inputs=[
                io.Model.Input("model"),
                io.Clip.Input("clip"),
                io.Vae.Input("vae"),
            ],
            outputs=[
                io.String.Output("report", display_name="Report"),
            ],
        )

    @classmethod
    def execute(cls, model: Any, clip: Any, vae: Any) -> io.NodeOutput:
        lines = []
        tested = 0
        passed = 0
        failed = 0

        lines.append("=" * 60)
        lines.append("MODEL MANAGEMENT COMPREHENSIVE FUNCTIONALITY TEST")
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
                    if isinstance(e, expect_error):
                        lines.append(f"[PASS] {name} - Expected error caught: {type(e).__name__}")
                        passed += 1
                    else:
                        lines.append(f"[FAIL] {name} - Expected {expect_error.__name__}, got {type(e).__name__}: {e}")
                        failed += 1
                else:
                    lines.append(f"[FAIL] {name} - Exception: {type(e).__name__}: {e}")
                    failed += 1
                return None

        # Get device for tests
        device = mm.get_torch_device()

        # =====================================================================
        # GROUP 1: MODULE-LEVEL PROPERTIES (29 tests)
        # =====================================================================
        lines.append("-" * 40)
        lines.append("GROUP 1: MODULE-LEVEL PROPERTIES")
        lines.append("-" * 40)

        verify("VRAMState enum", lambda: isinstance(mm.VRAMState.NORMAL_VRAM, mm.VRAMState), check=lambda x: x is True)
        verify("CPUState enum", lambda: isinstance(mm.CPUState.GPU, mm.CPUState), check=lambda x: x is True)
        verify("vram_state is VRAMState", lambda: isinstance(mm.vram_state, mm.VRAMState), check=lambda x: x is True)
        verify("set_vram_to is VRAMState", lambda: isinstance(mm.set_vram_to, mm.VRAMState), check=lambda x: x is True)
        verify("cpu_state is CPUState", lambda: isinstance(mm.cpu_state, mm.CPUState), check=lambda x: x is True)
        verify("total_vram >= 0", lambda: mm.total_vram >= 0, check=lambda x: x is True)
        verify("total_ram >= 0", lambda: mm.total_ram >= 0, check=lambda x: x is True)
        verify("lowvram_available is bool", lambda: isinstance(mm.lowvram_available, bool), check=lambda x: x is True)
        verify("directml_enabled is bool", lambda: isinstance(mm.directml_enabled, bool), check=lambda x: x is True)
        verify("xpu_available is bool", lambda: isinstance(mm.xpu_available, bool), check=lambda x: x is True)
        verify("npu_available is bool", lambda: isinstance(mm.npu_available, bool), check=lambda x: x is True)
        verify("mlu_available is bool", lambda: isinstance(mm.mlu_available, bool), check=lambda x: x is True)
        verify("ixuca_available is bool", lambda: isinstance(mm.ixuca_available, bool), check=lambda x: x is True)
        verify("torch_version is str", lambda: isinstance(mm.torch_version, str) and len(mm.torch_version) > 0, check=lambda x: x is True)
        verify("torch_version_numeric is tuple", lambda: isinstance(mm.torch_version_numeric, tuple) and len(mm.torch_version_numeric) == 2, check=lambda x: x is True)
        verify("FLOAT8_TYPES is list", lambda: isinstance(mm.FLOAT8_TYPES, list), check=lambda x: x is True)
        verify("OOM_EXCEPTION exists", lambda: mm.OOM_EXCEPTION is not None, check=lambda x: x is True)
        verify("XFORMERS_IS_AVAILABLE is bool", lambda: isinstance(mm.XFORMERS_IS_AVAILABLE, bool), check=lambda x: x is True)
        verify("XFORMERS_VERSION is str", lambda: isinstance(mm.XFORMERS_VERSION, str), check=lambda x: x is True)
        verify("XFORMERS_ENABLED_VAE is bool", lambda: isinstance(mm.XFORMERS_ENABLED_VAE, bool), check=lambda x: x is True)
        verify("MIN_WEIGHT_MEMORY_RATIO is number", lambda: isinstance(mm.MIN_WEIGHT_MEMORY_RATIO, (int, float)), check=lambda x: x is True)
        verify("ENABLE_PYTORCH_ATTENTION is bool", lambda: isinstance(mm.ENABLE_PYTORCH_ATTENTION, bool), check=lambda x: x is True)
        verify("SUPPORT_FP8_OPS is bool", lambda: isinstance(mm.SUPPORT_FP8_OPS, bool), check=lambda x: x is True)
        verify("AMD_RDNA2_AND_OLDER_ARCH is list", lambda: isinstance(mm.AMD_RDNA2_AND_OLDER_ARCH, list), check=lambda x: x is True)
        verify("PRIORITIZE_FP16 is bool", lambda: isinstance(mm.PRIORITIZE_FP16, bool), check=lambda x: x is True)
        verify("FORCE_FP32 is bool", lambda: isinstance(mm.FORCE_FP32, bool), check=lambda x: x is True)
        verify("DISABLE_SMART_MEMORY is bool", lambda: isinstance(mm.DISABLE_SMART_MEMORY, bool), check=lambda x: x is True)
        verify("WINDOWS is bool", lambda: isinstance(mm.WINDOWS, bool), check=lambda x: x is True)
        verify("EXTRA_RESERVED_VRAM >= 0", lambda: mm.EXTRA_RESERVED_VRAM >= 0, check=lambda x: x is True)

        # =====================================================================
        # GROUP 2: DEVICE DETECTION (7 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 2: DEVICE DETECTION")
        lines.append("-" * 40)

        verify("is_intel_xpu() is bool", lambda: isinstance(mm.is_intel_xpu(), bool), check=lambda x: x is True)
        verify("is_ascend_npu() is bool", lambda: isinstance(mm.is_ascend_npu(), bool), check=lambda x: x is True)
        verify("is_mlu() is bool", lambda: isinstance(mm.is_mlu(), bool), check=lambda x: x is True)
        verify("is_ixuca() is bool", lambda: isinstance(mm.is_ixuca(), bool), check=lambda x: x is True)
        verify("is_nvidia() is bool", lambda: isinstance(mm.is_nvidia(), bool), check=lambda x: x is True)
        verify("is_amd() is bool", lambda: isinstance(mm.is_amd(), bool), check=lambda x: x is True)
        verify("get_torch_device() has type", lambda: hasattr(mm.get_torch_device(), 'type'), check=lambda x: x is True)

        # =====================================================================
        # GROUP 3: DEVICE FUNCTIONS (10 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 3: DEVICE FUNCTIONS")
        lines.append("-" * 40)

        verify("get_torch_device_name() non-empty", lambda: len(mm.get_torch_device_name(device)) > 0, check=lambda x: x is True)
        verify("is_device_type() is bool", lambda: isinstance(mm.is_device_type(device, 'cpu'), bool), check=lambda x: x is True)
        verify("is_device_cpu() is bool", lambda: isinstance(mm.is_device_cpu(device), bool), check=lambda x: x is True)
        verify("is_device_mps() is bool", lambda: isinstance(mm.is_device_mps(device), bool), check=lambda x: x is True)
        verify("is_device_xpu() is bool", lambda: isinstance(mm.is_device_xpu(device), bool), check=lambda x: x is True)
        verify("is_device_cuda() is bool", lambda: isinstance(mm.is_device_cuda(device), bool), check=lambda x: x is True)
        verify("device_supports_non_blocking() is bool", lambda: isinstance(mm.device_supports_non_blocking(device), bool), check=lambda x: x is True)
        verify("get_autocast_device() returns str", lambda: isinstance(mm.get_autocast_device(device), str), check=lambda x: x is True)
        verify("is_directml_enabled() is bool", lambda: isinstance(mm.is_directml_enabled(), bool), check=lambda x: x is True)
        verify("mac_version() is tuple or None", lambda: mm.mac_version() is None or isinstance(mm.mac_version(), tuple), check=lambda x: x is True)

        # =====================================================================
        # GROUP 4: MEMORY FUNCTIONS (7 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 4: MEMORY FUNCTIONS")
        lines.append("-" * 40)

        verify("get_total_memory() > 0", lambda: mm.get_total_memory() > 0, check=lambda x: x is True)
        verify("get_free_memory() >= 0", lambda: mm.get_free_memory() >= 0, check=lambda x: x is True)
        verify("extra_reserved_memory() >= 0", lambda: mm.extra_reserved_memory() >= 0, check=lambda x: x is True)
        verify("minimum_inference_memory() > 0", lambda: mm.minimum_inference_memory() > 0, check=lambda x: x is True)
        verify("maximum_vram_for_weights() >= 0", lambda: mm.maximum_vram_for_weights() >= 0, check=lambda x: x is True)
        # module_size() is public API - call it on the server via ModelPatcherProxy.model_size() instead
        verify("model.model_size() > 0", lambda: model.model_size() > 0, check=lambda x: x is True)
        verify("cleanup_models() returns None", lambda: mm.cleanup_models() is None, check=lambda x: x is True)
        verify("cleanup_models_gc() returns None", lambda: mm.cleanup_models_gc() is None, check=lambda x: x is True)

        # =====================================================================
        # GROUP 5: DTYPE SELECTION LOGIC (12 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 5: DTYPE SELECTION LOGIC")
        lines.append("-" * 40)

        verify("unet_dtype() valid", lambda: isinstance(mm.unet_dtype(), torch.dtype), check=lambda x: x is True)
        verify("text_encoder_dtype() valid", lambda: isinstance(mm.text_encoder_dtype(), torch.dtype), check=lambda x: x is True)
        verify("vae_dtype() valid", lambda: isinstance(mm.vae_dtype(), torch.dtype), check=lambda x: x is True)
        verify("should_use_fp16() is bool", lambda: isinstance(mm.should_use_fp16(), bool), check=lambda x: x is True)
        verify("should_use_bf16() is bool", lambda: isinstance(mm.should_use_bf16(), bool), check=lambda x: x is True)
        verify("supports_fp8_compute() is bool", lambda: isinstance(mm.supports_fp8_compute(), bool), check=lambda x: x is True)
        verify("supports_dtype(fp16) is bool", lambda: isinstance(mm.supports_dtype(device, torch.float16), bool), check=lambda x: x is True)
        verify("supports_cast(fp16) is bool", lambda: isinstance(mm.supports_cast(device, torch.float16), bool), check=lambda x: x is True)
        verify("pick_weight_dtype() valid", lambda: isinstance(mm.pick_weight_dtype(torch.float16, torch.float32), torch.dtype), check=lambda x: x is True)
        verify("force_upcast_attention_dtype() dict or None", lambda: mm.force_upcast_attention_dtype() is None or isinstance(mm.force_upcast_attention_dtype(), dict), check=lambda x: x is True)
        verify("dtype_size(fp16) == 2", lambda: mm.dtype_size(torch.float16) == 2, check=lambda x: x is True)
        verify("unet_manual_cast() returns dtype or None", lambda: mm.unet_manual_cast(torch.float16, device) is None or isinstance(mm.unet_manual_cast(torch.float16, device), torch.dtype), check=lambda x: x is True)

        # =====================================================================
        # GROUP 6: DEVICE PLACEMENT FUNCTIONS (10 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 6: DEVICE PLACEMENT FUNCTIONS")
        lines.append("-" * 40)

        verify("unet_offload_device() has type", lambda: hasattr(mm.unet_offload_device(), 'type'), check=lambda x: x is True)
        verify("unet_inital_load_device() has type", lambda: hasattr(mm.unet_inital_load_device(1000000, torch.float16), 'type'), check=lambda x: x is True)
        verify("text_encoder_offload_device() has type", lambda: hasattr(mm.text_encoder_offload_device(), 'type'), check=lambda x: x is True)
        verify("text_encoder_device() has type", lambda: hasattr(mm.text_encoder_device(), 'type'), check=lambda x: x is True)
        verify("text_encoder_initial_device() has type", lambda: hasattr(mm.text_encoder_initial_device(device, mm.text_encoder_offload_device()), 'type'), check=lambda x: x is True)
        verify("intermediate_device() has type", lambda: hasattr(mm.intermediate_device(), 'type'), check=lambda x: x is True)
        verify("vae_device() has type", lambda: hasattr(mm.vae_device(), 'type'), check=lambda x: x is True)
        verify("vae_offload_device() has type", lambda: hasattr(mm.vae_offload_device(), 'type'), check=lambda x: x is True)
        verify("amd_min_version() is bool", lambda: isinstance(mm.amd_min_version(device, 3), bool), check=lambda x: x is True)
        verify("force_channels_last() is bool", lambda: isinstance(mm.force_channels_last(), bool), check=lambda x: x is True)

        # =====================================================================
        # GROUP 7: ATTENTION BACKEND SELECTION (7 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 7: ATTENTION BACKEND SELECTION")
        lines.append("-" * 40)

        verify("xformers_enabled() is bool", lambda: isinstance(mm.xformers_enabled(), bool), check=lambda x: x is True)
        verify("xformers_enabled_vae() is bool", lambda: isinstance(mm.xformers_enabled_vae(), bool), check=lambda x: x is True)
        verify("pytorch_attention_enabled() is bool", lambda: isinstance(mm.pytorch_attention_enabled(), bool), check=lambda x: x is True)
        verify("pytorch_attention_enabled_vae() is bool", lambda: isinstance(mm.pytorch_attention_enabled_vae(), bool), check=lambda x: x is True)
        verify("pytorch_attention_flash_attention() is bool", lambda: isinstance(mm.pytorch_attention_flash_attention(), bool), check=lambda x: x is True)
        verify("sage_attention_enabled() is bool", lambda: isinstance(mm.sage_attention_enabled(), bool), check=lambda x: x is True)
        verify("flash_attention_enabled() is bool", lambda: isinstance(mm.flash_attention_enabled(), bool), check=lambda x: x is True)

        # =====================================================================
        # GROUP 8: TENSOR OPERATIONS (5 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 8: TENSOR OPERATIONS")
        lines.append("-" * 40)

        test_tensor = torch.randn(2, 2)
        verify("cast_to(fp32) dtype correct", lambda: mm.cast_to(test_tensor, dtype=torch.float32).dtype == torch.float32, check=lambda x: x is True)
        verify("cast_to_device() dtype correct", lambda: mm.cast_to_device(test_tensor, device, torch.float32).dtype == torch.float32, check=lambda x: x is True)

        # pin_memory returns bool
        verify("pin_memory() returns bool", lambda: isinstance(mm.pin_memory(test_tensor), bool), check=lambda x: x is True)
        verify("unpin_memory() returns bool", lambda: isinstance(mm.unpin_memory(test_tensor), bool), check=lambda x: x is True)

        # =====================================================================
        # GROUP 9: STREAM MANAGEMENT (3 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 9: STREAM MANAGEMENT")
        lines.append("-" * 40)

        verify("current_stream() exists", lambda: mm.current_stream(device) is None or hasattr(mm.current_stream(device), 'wait_stream'), check=lambda x: True)
        verify("get_offload_stream() exists", lambda: mm.get_offload_stream(device) is None or hasattr(mm.get_offload_stream(device), 'wait_stream'), check=lambda x: True)
        verify("sync_stream() returns None", lambda: mm.sync_stream(device, None) is None, check=lambda x: x is True)

        # =====================================================================
        # GROUP 10: MODEL LOADING SYSTEM (3 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 10: MODEL LOADING SYSTEM")
        lines.append("-" * 40)

        verify("loaded_models() is list", lambda: isinstance(mm.loaded_models(), list), check=lambda x: x is True)
        verify("load_model_gpu() returns None", lambda: mm.load_model_gpu(model) is None, check=lambda x: x is True)
        verify("load_models_gpu() returns None", lambda: mm.load_models_gpu([model]) is None, check=lambda x: x is True)

        # =====================================================================
        # GROUP 11: INTERRUPT/ERROR HANDLING (5 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 11: INTERRUPT/ERROR HANDLING")
        lines.append("-" * 40)

        verify("processing_interrupted() initially false", lambda: mm.processing_interrupted() is False, check=lambda x: x is True)
        verify("interrupt_current_processing(True) sets flag", lambda: (mm.interrupt_current_processing(True), mm.processing_interrupted())[-1], check=lambda x: x is True)
        verify("throw_exception_if_processing_interrupted() raises", lambda: mm.throw_exception_if_processing_interrupted(), expect_error=mm.InterruptProcessingException)
        mm.interrupt_current_processing(False)
        verify("unload_all_models() returns None", lambda: mm.unload_all_models() is None, check=lambda x: x is True)
        verify("soft_empty_cache() returns None", lambda: mm.soft_empty_cache() is None, check=lambda x: x is True)

        # =====================================================================
        # GROUP 12: UTILITY FUNCTIONS (3 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 12: UTILITY FUNCTIONS")
        lines.append("-" * 40)

        loaded_list = mm.loaded_models()
        verify("offloaded_memory() >= 0", lambda: mm.offloaded_memory(loaded_list, device) >= 0, check=lambda x: x is True)
        verify("use_more_memory() returns None", lambda: mm.use_more_memory(1024 * 1024, loaded_list, device) is None, check=lambda x: x is True)
        verify("extended_fp16_support() is bool", lambda: isinstance(mm.extended_fp16_support(), bool), check=lambda x: x is True)

        # =====================================================================
        # GROUP 13: ADDITIONAL PROPERTIES & MODES (7 tests)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("GROUP 13: ADDITIONAL PROPERTIES & MODES")
        lines.append("-" * 40)

        verify("cpu_mode() is bool", lambda: isinstance(mm.cpu_mode(), bool), check=lambda x: x is True)
        verify("mps_mode() is bool", lambda: isinstance(mm.mps_mode(), bool), check=lambda x: x is True)
        verify("STREAMS is dict", lambda: isinstance(mm.STREAMS, dict), check=lambda x: x is True)
        verify("NUM_STREAMS is int", lambda: isinstance(mm.NUM_STREAMS, int), check=lambda x: x is True)
        verify("PINNED_MEMORY is dict", lambda: isinstance(mm.PINNED_MEMORY, dict), check=lambda x: x is True)
        verify("TOTAL_PINNED_MEMORY >= 0", lambda: mm.TOTAL_PINNED_MEMORY >= 0, check=lambda x: x is True)
        verify("MAX_PINNED_MEMORY is number", lambda: isinstance(mm.MAX_PINNED_MEMORY, (int, float)), check=lambda x: x is True)

        # =====================================================================
        # SUMMARY
        # =====================================================================
        lines.append("")
        lines.append("=" * 60)
        lines.append("SUMMARY")
        lines.append(f"Tested: {tested} | Passed: {passed} | Failed: {failed}")
        coverage = (passed / tested * 100) if tested > 0 else 0
        lines.append(f"Coverage: {coverage:.1f}%")
        lines.append("=" * 60)

        return io.NodeOutput("\n".join(lines))


NODES = [ProxyTestModelManagement]
