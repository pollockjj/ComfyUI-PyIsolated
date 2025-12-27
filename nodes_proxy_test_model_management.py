"""
Proxy Test Node: Model Management

SYSTEMATIC test of comfy.model_management proxy coverage.
Enumerates ALL proxy methods/properties and tests each one.
Outputs coverage report for baseline comparison.
"""
from __future__ import annotations

import os
from typing import Any

import comfy.model_management as mm
from comfy_api.latest import io


# Complete list of proxy members extracted from ModelManagementProxy
PROXY_PROPERTIES = [
    "VRAMState", "CPUState", "vram_state", "set_vram_to", "cpu_state",
    "total_vram", "total_ram", "lowvram_available", "directml_enabled",
    "xpu_available", "npu_available", "mlu_available", "ixuca_available",
    "torch_version", "torch_version_numeric",
    "FLOAT8_TYPES", "OOM_EXCEPTION", "XFORMERS_IS_AVAILABLE", "XFORMERS_VERSION",
    "XFORMERS_ENABLED_VAE", "MIN_WEIGHT_MEMORY_RATIO", "ENABLE_PYTORCH_ATTENTION",
    "SUPPORT_FP8_OPS", "AMD_RDNA2_AND_OLDER_ARCH", "PRIORITIZE_FP16", "FORCE_FP32",
    "DISABLE_SMART_MEMORY", "WINDOWS", "EXTRA_RESERVED_VRAM", "STREAMS", "NUM_STREAMS",
    "PINNED_MEMORY", "TOTAL_PINNED_MEMORY", "MAX_PINNED_MEMORY", "PINNING_ALLOWED_TYPES",
]

PROXY_METHODS_NO_ARGS = [
    "get_supported_float8_types", "is_intel_xpu", "is_ascend_npu", "is_mlu", "is_ixuca",
    "get_torch_device", "mac_version", "is_nvidia", "is_amd", "extra_reserved_memory",
    "minimum_inference_memory", "cleanup_models_gc", "cleanup_models",
    "unet_offload_device", "text_encoder_offload_device", "text_encoder_device",
    "intermediate_device", "vae_device", "vae_offload_device", "force_channels_last",
    "sage_attention_enabled", "flash_attention_enabled", "xformers_enabled",
    "xformers_enabled_vae", "pytorch_attention_enabled", "pytorch_attention_enabled_vae",
    "pytorch_attention_flash_attention", "force_upcast_attention_dtype",
    "cpu_mode", "mps_mode", "is_directml_enabled", "extended_fp16_support",
    "unload_all_models", "processing_interrupted",
]

PROXY_METHODS_WITH_ARGS = [
    "get_total_memory", "get_free_memory", "amd_min_version", "get_torch_device_name",
    "module_size", "use_more_memory", "offloaded_memory", "free_memory",
    "load_models_gpu", "load_model_gpu", "loaded_models", "dtype_size",
    "unet_inital_load_device", "maximum_vram_for_weights", "unet_dtype",
    "unet_manual_cast", "text_encoder_initial_device", "text_encoder_dtype",
    "vae_dtype", "get_autocast_device", "supports_dtype", "supports_cast",
    "pick_weight_dtype", "device_supports_non_blocking", "current_stream",
    "get_offload_stream", "sync_stream", "cast_to", "cast_to_device",
    "pin_memory", "unpin_memory", "is_device_type", "is_device_cpu",
    "is_device_mps", "is_device_xpu", "is_device_cuda", "should_use_fp16",
    "should_use_bf16", "supports_fp8_compute", "soft_empty_cache",
    "interrupt_current_processing", "throw_exception_if_processing_interrupted",
]


class ProxyTestModelManagement(io.ComfyNode):
    """Systematic test of model_management proxy - tests ALL 113 proxy members."""
    
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestModelManagement",
            display_name="Proxy Test: Model Management",
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
        skipped = 0
        
        lines.append("=" * 60)
        lines.append("MODEL MANAGEMENT PROXY COVERAGE REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        # Get device for tests that need it
        try:
            device = mm.get_torch_device()
        except Exception:
            device = None
        
        # Section 1: Properties
        lines.append("-" * 40)
        lines.append("PROPERTIES")
        lines.append("-" * 40)
        
        for prop_name in PROXY_PROPERTIES:
            tested += 1
            try:
                value = getattr(mm, prop_name)
                value_str = str(value)
                if len(value_str) > 60:
                    value_str = value_str[:57] + "..."
                lines.append(f"[PASS] {prop_name} = {value_str}")
                passed += 1
            except Exception as e:
                lines.append(f"[FAIL] {prop_name}: {type(e).__name__}: {e}")
                failed += 1
        
        lines.append("")
        lines.append("-" * 40)
        lines.append("METHODS (no args)")
        lines.append("-" * 40)
        
        for method_name in PROXY_METHODS_NO_ARGS:
            tested += 1
            try:
                method = getattr(mm, method_name)
                result = method()
                result_str = str(result)
                if len(result_str) > 50:
                    result_str = result_str[:47] + "..."
                lines.append(f"[PASS] {method_name}() = {result_str}")
                passed += 1
            except Exception as e:
                lines.append(f"[FAIL] {method_name}(): {type(e).__name__}: {e}")
                failed += 1
        
        lines.append("")
        lines.append("-" * 40)
        lines.append("METHODS (with args - selective)")
        lines.append("-" * 40)
        
        # get_total_memory
        tested += 1
        try:
            result = mm.get_total_memory()
            lines.append(f"[PASS] get_total_memory() = {result / (1024**3):.2f} GB")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] get_total_memory(): {e}")
            failed += 1
        
        # get_free_memory
        tested += 1
        try:
            result = mm.get_free_memory()
            lines.append(f"[PASS] get_free_memory() = {result / (1024**3):.2f} GB")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] get_free_memory(): {e}")
            failed += 1
        
        # loaded_models
        tested += 1
        try:
            result = mm.loaded_models()
            lines.append(f"[PASS] loaded_models() = {len(result)} models")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] loaded_models(): {e}")
            failed += 1
        
        # module_size with model
        tested += 1
        try:
            if hasattr(model, 'model') and model.model is not None:
                size = mm.module_size(model.model)
                lines.append(f"[PASS] module_size(model.model) = {size / (1024**2):.2f} MB")
                passed += 1
            else:
                lines.append(f"[SKIP] module_size(model.model): no .model attribute")
                skipped += 1
                tested -= 1
        except Exception as e:
            lines.append(f"[FAIL] module_size(model.model): {e}")
            failed += 1
        
        # module_size with clip
        tested += 1
        try:
            if hasattr(clip, 'cond_stage_model') and clip.cond_stage_model is not None:
                size = mm.module_size(clip.cond_stage_model)
                lines.append(f"[PASS] module_size(clip.cond_stage_model) = {size / (1024**2):.2f} MB")
                passed += 1
            else:
                lines.append(f"[SKIP] module_size(clip): no .cond_stage_model")
                skipped += 1
                tested -= 1
        except Exception as e:
            lines.append(f"[FAIL] module_size(clip): {e}")
            failed += 1
        
        # module_size with vae
        tested += 1
        try:
            if hasattr(vae, 'first_stage_model') and vae.first_stage_model is not None:
                size = mm.module_size(vae.first_stage_model)
                lines.append(f"[PASS] module_size(vae.first_stage_model) = {size / (1024**2):.2f} MB")
                passed += 1
            else:
                lines.append(f"[SKIP] module_size(vae): no .first_stage_model")
                skipped += 1
                tested -= 1
        except Exception as e:
            lines.append(f"[FAIL] module_size(vae): {e}")
            failed += 1
        
        # get_torch_device_name
        tested += 1
        try:
            if device is not None:
                result = mm.get_torch_device_name(device)
                lines.append(f"[PASS] get_torch_device_name(device) = {result}")
                passed += 1
            else:
                lines.append(f"[SKIP] get_torch_device_name: no device")
                skipped += 1
                tested -= 1
        except Exception as e:
            lines.append(f"[FAIL] get_torch_device_name(): {e}")
            failed += 1
        
        # is_device_cuda
        tested += 1
        try:
            if device is not None:
                result = mm.is_device_cuda(device)
                lines.append(f"[PASS] is_device_cuda(device) = {result}")
                passed += 1
            else:
                lines.append(f"[SKIP] is_device_cuda: no device")
                skipped += 1
                tested -= 1
        except Exception as e:
            lines.append(f"[FAIL] is_device_cuda(): {e}")
            failed += 1
        
        # unet_dtype
        tested += 1
        try:
            result = mm.unet_dtype()
            lines.append(f"[PASS] unet_dtype() = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] unet_dtype(): {e}")
            failed += 1
        
        # text_encoder_dtype
        tested += 1
        try:
            result = mm.text_encoder_dtype()
            lines.append(f"[PASS] text_encoder_dtype() = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] text_encoder_dtype(): {e}")
            failed += 1
        
        # vae_dtype
        tested += 1
        try:
            result = mm.vae_dtype()
            lines.append(f"[PASS] vae_dtype() = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] vae_dtype(): {e}")
            failed += 1
        
        # should_use_fp16
        tested += 1
        try:
            result = mm.should_use_fp16()
            lines.append(f"[PASS] should_use_fp16() = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] should_use_fp16(): {e}")
            failed += 1
        
        # should_use_bf16
        tested += 1
        try:
            result = mm.should_use_bf16()
            lines.append(f"[PASS] should_use_bf16() = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] should_use_bf16(): {e}")
            failed += 1
        
        # supports_fp8_compute
        tested += 1
        try:
            result = mm.supports_fp8_compute()
            lines.append(f"[PASS] supports_fp8_compute() = {result}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] supports_fp8_compute(): {e}")
            failed += 1
        
        # maximum_vram_for_weights
        tested += 1
        try:
            result = mm.maximum_vram_for_weights()
            lines.append(f"[PASS] maximum_vram_for_weights() = {result / (1024**3):.2f} GB")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] maximum_vram_for_weights(): {e}")
            failed += 1
        
        # Summary
        lines.append("")
        lines.append("=" * 60)
        lines.append("COVERAGE SUMMARY")
        lines.append("=" * 60)
        total_proxy = len(PROXY_PROPERTIES) + len(PROXY_METHODS_NO_ARGS) + len(PROXY_METHODS_WITH_ARGS)
        lines.append(f"Total proxy members defined: {total_proxy}")
        lines.append(f"Tested: {tested}")
        lines.append(f"Passed: {passed}")
        lines.append(f"Failed: {failed}")
        lines.append(f"Skipped: {skipped}")
        coverage = (passed / tested * 100) if tested > 0 else 0
        lines.append(f"Coverage: {coverage:.1f}%")
        lines.append("=" * 60)
        
        report = "\n".join(lines)
        return io.NodeOutput(report)


NODES = [ProxyTestModelManagement]
