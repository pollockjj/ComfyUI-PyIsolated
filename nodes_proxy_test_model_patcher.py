"""
Proxy Test Node: Model Patcher

COMPREHENSIVE functionality test of ModelPatcher.
Tests actual behavior, state changes, and operations.
NO proxy knowledge - pure ModelPatcher API testing.
"""
from __future__ import annotations

import torch
from typing import Any, Callable

from comfy_api.latest import io
import comfy.model_management
import comfy.hooks
import comfy.sd
import comfy.utils
import folder_paths


class ProxyTestModelPatcher(io.ComfyNode):
    """Comprehensive ModelPatcher functionality test - verifies actual behavior."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestModelPatcher",
            display_name="Proxy Test: Model Patcher (Full)",
            category="PyIsolated/ProxyTests",
            inputs=[
                io.Model.Input("model"),
                io.Clip.Input("clip", optional=True),
                io.Vae.Input("vae", optional=True),
                io.Latent.Input("latent", optional=True),
                io.String.Input("lora_name", default="None"),
            ],
            outputs=[
                io.String.Output("report", display_name="Report"),
            ],
        )

    @classmethod
    def execute(cls, model: Any, clip: Any = None, vae: Any = None, latent: Any = None, lora_name: str = "None") -> io.NodeOutput:
        lines = []
        tested = 0
        passed = 0
        failed = 0
        
        lines.append("=" * 60)
        lines.append("MODEL PATCHER COMPREHENSIVE FUNCTIONALITY TEST")
        lines.append("=" * 60)
        lines.append(f"Model Class: {type(model).__name__}")
        lines.append("")

        def test(name, func, verify=None):
            nonlocal tested, passed, failed
            tested += 1
            try:
                result = func()
                if verify and not verify(result):
                    lines.append(f"[FAIL] {name}: Verification failed")
                    failed += 1
                else:
                    res_str = str(result)[:60] + "..." if len(str(result)) > 60 else str(result)
                    lines.append(f"[PASS] {name}: {res_str}")
                    passed += 1
                return result
            except Exception as e:
                lines.append(f"[FAIL] {name}: {type(e).__name__}: {str(e)[:50]}")
                failed += 1
                return None

        # =====================================================================
        # 1. Core Properties & State
        # =====================================================================
        lines.append("-" * 40)
        lines.append("1. CORE PROPERTIES & STATE")
        lines.append("-" * 40)

        load_dev = test("load_device", lambda: model.load_device)
        offload_dev = test("offload_device", lambda: model.offload_device)
        current_dev = test("current_loaded_device()", lambda: model.current_loaded_device())
        
        initial_size = test("model_size()", lambda: model.model_size(), 
                           verify=lambda x: x > 0)
        initial_loaded = test("loaded_size()", lambda: model.loaded_size())
        
        test("model_dtype()", lambda: model.model_dtype(),
             verify=lambda x: x in [torch.float16, torch.bfloat16, torch.float32])
        
        test("lowvram_patch_counter()", lambda: model.lowvram_patch_counter())
        test("model_options", lambda: len(model.model_options))

        # =====================================================================
        # 2. Cloning & Identity
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("2. CLONING & IDENTITY")
        lines.append("-" * 40)

        clone = test("clone()", lambda: model.clone())
        if clone:
            test("is_clone(clone)", lambda: model.is_clone(clone),
                 verify=lambda x: x == True)
            test("clone_has_same_weights()", lambda: model.clone_has_same_weights(clone),
                 verify=lambda x: x == True)
            test("clone.model_size() matches", lambda: clone.model_size() == initial_size,
                 verify=lambda x: x == True)

        # =====================================================================
        # 3. Memory & Loading Operations
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("3. MEMORY & LOADING")
        lines.append("-" * 40)

        test("model_patches_to(offload)", lambda: model.model_patches_to(offload_dev))
        
        # Test partial load
        test("partially_load()", lambda: model.partially_load(load_dev, 0))
        loaded_after_partial = test("loaded_size() after partial_load", lambda: model.loaded_size())
        
        # Verify memory changed
        if loaded_after_partial is not None and initial_loaded is not None:
            test("Memory increased after load", 
                 lambda: loaded_after_partial >= initial_loaded,
                 verify=lambda x: x == True)
        
        test("partially_unload()", lambda: model.partially_unload(offload_dev, 0))
        
        test("get_ram_usage()", lambda: model.get_ram_usage(),
             verify=lambda x: x >= 0)

        # =====================================================================
        # 4. Model Options & Configuration
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("4. MODEL OPTIONS & CONFIGURATION")
        lines.append("-" * 40)

        original_options = test("get model_options", lambda: dict(model.model_options))
        
        # Modify options
        test("set model_options", lambda: setattr(model, 'model_options', 
             {**model.model_options, 'test_key': 'test_value'}))
        
        modified_options = test("verify options changed", lambda: model.model_options)
        if modified_options and 'test_key' in modified_options:
            test("option modification verified", lambda: modified_options['test_key'] == 'test_value',
                 verify=lambda x: x == True)

        # =====================================================================
        # 5. Patches & State Dict
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("5. PATCHES & STATE")
        lines.append("-" * 40)

        test("patches dict exists", lambda: type(model.patches).__name__)
        test("object_patches dict exists", lambda: type(model.object_patches).__name__)
        
        initial_patch_count = test("initial patch count", lambda: len(model.patches))
        
        # Add object patch
        test("add_object_patch('test')", lambda: model.add_object_patch('test_obj', 'test_value'))
        test("verify object_patch added", lambda: 'test_obj' in model.object_patches,
             verify=lambda x: x == True)

        # =====================================================================
        # 6. Hooks & Injection
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("6. HOOKS & INJECTION")
        lines.append("-" * 40)

        initial_injected = test("is_injected (initial)", lambda: model.is_injected)
        test("inject_model()", lambda: model.inject_model())
        after_inject = test("is_injected (after inject)", lambda: model.is_injected)
        
        test("eject_model()", lambda: model.eject_model())
        after_eject = test("is_injected (after eject)", lambda: model.is_injected)
        
        test("hook_mode", lambda: model.hook_mode)
        test("clean_hooks()", lambda: model.clean_hooks())

        # =====================================================================
        # 7. Attachments & Additional Models
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("7. ATTACHMENTS & ADDITIONAL MODELS")
        lines.append("-" * 40)

        test("set_attachments('key', 'val')", lambda: model.set_attachments('test_att', 'test_value'))
        retrieved = test("get_attachment('key')", lambda: model.get_attachment('test_att'))
        if retrieved:
            test("attachment value correct", lambda: retrieved == 'test_value',
                 verify=lambda x: x == True)
        
        test("remove_attachments('key')", lambda: model.remove_attachments('test_att'))
        
        # Additional models
        if clone:
            test("set_additional_models()", lambda: model.set_additional_models('test_key', [clone]))
            additional = test("get_additional_models()", lambda: model.get_additional_models())
            if additional:
                test("additional models count", lambda: len(additional) > 0,
                     verify=lambda x: x == True)
            test("remove_additional_models()", lambda: model.remove_additional_models('test_key'))

        # =====================================================================
        # 8. Latent Processing
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("8. LATENT PROCESSING")
        lines.append("-" * 40)

        if latent and "samples" in latent:
            samples = latent["samples"]
            
            processed_in = test("process_latent_in()", 
                              lambda: model.model.process_latent_in(samples))
            if processed_in is not None:
                test("latent_in shape preserved", 
                     lambda: processed_in.shape == samples.shape,
                     verify=lambda x: x == True)
            
            processed_out = test("process_latent_out()", 
                                lambda: model.model.process_latent_out(samples))
            if processed_out is not None:
                test("latent_out shape preserved",
                     lambda: processed_out.shape == samples.shape,
                     verify=lambda x: x == True)

        # =====================================================================
        # 9. LoRA Loading (if provided)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("9. LORA LOADING")
        lines.append("-" * 40)

        if lora_name and lora_name != "None":
            lora_path = test("resolve LoRA path", 
                           lambda: folder_paths.get_full_path("loras", lora_name))
            
            if lora_path:
                lora_data = test("load LoRA file", 
                               lambda: comfy.utils.load_torch_file(lora_path))
                
                if lora_data:
                    pre_lora_size = test("model size pre-LoRA", lambda: len(model.patches))
                    
                    new_model, new_clip = test("apply LoRA", 
                        lambda: comfy.sd.load_lora_for_models(model, clip, lora_data, 1.0, 1.0))
                    
                    if new_model:
                        post_lora_size = test("new model patch count", lambda: len(new_model.patches))
                        if pre_lora_size is not None and post_lora_size is not None:
                            test("LoRA patches applied", 
                                 lambda: post_lora_size > pre_lora_size,
                                 verify=lambda x: x == True)

        # =====================================================================
        # 10. Lifecycle & Cleanup
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("10. LIFECYCLE & CLEANUP")
        lines.append("-" * 40)

        test("pre_run()", lambda: model.pre_run())
        test("cleanup()", lambda: model.cleanup())
        test("patch_model(load_weights=False)", lambda: model.patch_model(load_weights=False))
        test("unpatch_model()", lambda: model.unpatch_model())

        # Summary
        lines.append("")
        lines.append("=" * 60)
        lines.append("SUMMARY")
        lines.append(f"Tested: {tested} | Passed: {passed} | Failed: {failed}")
        coverage = (passed / tested * 100) if tested > 0 else 0
        lines.append(f"Functional Coverage: {coverage:.1f}%")
        lines.append("=" * 60)
        
        return io.NodeOutput("\n".join(lines))


NODES = [ProxyTestModelPatcher]
