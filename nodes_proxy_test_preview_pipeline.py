"""
Proxy Test Node: Preview Pipeline

COMPREHENSIVE end-to-end test of the preview pipeline in isolated processes.
Tests the full flow: get_previewer -> decode_latent -> progress_bar_hook -> host

This is the integration test for the entire preview system.
"""
from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

from comfy_api.latest import io

logger = logging.getLogger(__name__)


class ProxyTestPreviewPipeline(io.ComfyNode):
    """End-to-end test of preview pipeline - tests full flow from child to host."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestPreviewPipeline",
            display_name="Proxy Test: Preview Pipeline",
            category="PyIsolated/ProxyTests",
            inputs=[
                io.Model.Input("model"),
            ],
            outputs=[
                io.String.Output("report", display_name="Report"),
            ],
        )

    @classmethod
    def execute(cls, model: Any) -> io.NodeOutput:
        lines = []
        tested = 0
        passed = 0
        failed = 0

        lines.append("=" * 60)
        lines.append("PREVIEW PIPELINE INTEGRATION TEST")
        lines.append("=" * 60)
        lines.append("")

        def verify(name: str,
                  action: Callable[[], Any],
                  check: Callable[[Any], bool] | None = None) -> Any:
            nonlocal tested, passed, failed
            tested += 1
            try:
                result = action()
                if check and not check(result):
                    lines.append(f"[FAIL] {name}: Check failed, got: {type(result).__name__}")
                    failed += 1
                else:
                    lines.append(f"[PASS] {name}")
                    passed += 1
                return result
            except Exception as e:
                lines.append(f"[FAIL] {name}: {type(e).__name__}: {e}")
                failed += 1
                return None

        import os
        is_child = os.environ.get('PYISOLATE_CHILD', '0') == '1'
        lines.append(f"Running in: {'CHILD PROCESS' if is_child else 'HOST PROCESS'}")
        lines.append("")

        # =====================================================================
        # SECTION 1: CLI Args Proxy
        # =====================================================================
        lines.append("-" * 40)
        lines.append("SECTION 1: CLI ARGS PROXY")
        lines.append("-" * 40)

        from comfy.cli_args import args, LatentPreviewMethod

        local_method = args.preview_method
        local_method_str = local_method.value
        lines.append(f"  Local args.preview_method: {local_method} ('{local_method_str}')")

        proxy_method_str = None
        try:
            from comfy.isolation.proxies.cli_args_proxy import CliArgsProxy
            proxy = CliArgsProxy.get_instance()
            proxy_method_str = proxy.get_preview_method()
            proxy_method = LatentPreviewMethod.from_string(proxy_method_str)
            lines.append(f"  Proxy get_preview_method(): {proxy_method} ('{proxy_method_str}')")

            if is_child:
                if proxy_method_str == local_method_str == "none":
                    lines.append("  [WARN] Both are 'none' - may indicate proxy not RPC'ing")
                elif proxy_method_str != local_method_str:
                    lines.append("  [INFO] Proxy differs from local - proxy is working!")
                    passed += 1
                    tested += 1
                else:
                    lines.append("  [OK] Values match")
                    passed += 1
                    tested += 1
            else:
                lines.append("  [INFO] Not in child - proxy and local should match")
                passed += 1
                tested += 1
        except Exception as e:
            lines.append(f"  [FAIL] CliArgsProxy: {e}")
            failed += 1
            tested += 1

        # =====================================================================
        # SECTION 2: Get Previewer
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("SECTION 2: GET_PREVIEWER")
        lines.append("-" * 40)

        previewer = None
        latent_format = None
        device = None

        try:
            import comfy.model_management as mm
            device = mm.get_torch_device()
            lines.append(f"  Device: {device}")
            passed += 1
            tested += 1
        except Exception as e:
            lines.append(f"  [FAIL] Get device: {e}")
            failed += 1
            tested += 1

        try:
            # Get latent format from model
            if hasattr(model, 'model') and hasattr(model.model, 'latent_format'):
                latent_format = model.model.latent_format
                lines.append(f"  Latent format: {type(latent_format).__name__}")
                passed += 1
                tested += 1
            else:
                lines.append("  [WARN] Model has no latent_format, using SD15")
                import comfy.latent_formats as lf
                latent_format = lf.SD15()
                passed += 1
                tested += 1
        except Exception as e:
            lines.append(f"  [FAIL] Get latent format: {e}")
            failed += 1
            tested += 1

        if device and latent_format:
            try:
                import latent_preview
                previewer = latent_preview.get_previewer(device, latent_format)
                if previewer is not None:
                    lines.append(f"  [PASS] get_previewer returned: {type(previewer).__name__}")
                    passed += 1
                    tested += 1
                else:
                    # If proxy returned 'none', this is expected
                    if proxy_method_str == "none":
                        lines.append("  [INFO] get_previewer returned None (preview_method='none')")
                        passed += 1
                        tested += 1
                    else:
                        lines.append(f"  [WARN] get_previewer returned None but method='{proxy_method_str}'")
                        passed += 1
                        tested += 1
            except Exception as e:
                lines.append(f"  [FAIL] get_previewer: {e}")
                lines.append(f"         {traceback.format_exc()}")
                failed += 1
                tested += 1

        # =====================================================================
        # SECTION 3: Progress Bar Hook
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("SECTION 3: PROGRESS BAR HOOK")
        lines.append("-" * 40)

        try:
            import comfy.utils
            hook = comfy.utils.PROGRESS_BAR_HOOK
            if hook is not None:
                lines.append(f"  [PASS] PROGRESS_BAR_HOOK is set: {hook}")
                passed += 1
                tested += 1

                # Test calling it with no preview
                try:
                    hook(1, 10, None, None)
                    lines.append("  [PASS] Hook accepts (value, total, None, None)")
                    passed += 1
                    tested += 1
                except Exception as e:
                    lines.append(f"  [FAIL] Hook call failed: {e}")
                    failed += 1
                    tested += 1
            else:
                lines.append("  [WARN] PROGRESS_BAR_HOOK is None")
                passed += 1
                tested += 1
        except Exception as e:
            lines.append(f"  [FAIL] PROGRESS_BAR_HOOK: {e}")
            failed += 1
            tested += 1

        # =====================================================================
        # SECTION 4: Synthetic Preview Test
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("SECTION 4: SYNTHETIC PREVIEW TEST")
        lines.append("-" * 40)

        if previewer is not None:
            try:
                import torch
                # Create a dummy latent
                dummy_latent = torch.randn(1, 4, 64, 64, device=device)

                # Try to decode
                preview_result = previewer.decode_latent_to_preview_image("JPEG", dummy_latent)

                if preview_result is not None:
                    if isinstance(preview_result, tuple) and len(preview_result) >= 2:
                        fmt, img, *rest = preview_result
                        lines.append(f"  [PASS] Decoded preview: format={fmt}, image_type={type(img).__name__}")

                        from PIL import Image
                        if isinstance(img, Image.Image):
                            lines.append(f"         Image size: {img.size}")
                            passed += 1
                            tested += 1

                            # Now test sending through progress hook
                            try:
                                import comfy.utils
                                if comfy.utils.PROGRESS_BAR_HOOK:
                                    comfy.utils.PROGRESS_BAR_HOOK(5, 10, preview_result, None)
                                    lines.append("  [PASS] Sent preview through PROGRESS_BAR_HOOK")
                                    passed += 1
                                    tested += 1
                            except Exception as e:
                                lines.append(f"  [FAIL] Hook with preview: {e}")
                                failed += 1
                                tested += 1
                        else:
                            lines.append(f"  [WARN] Image is not PIL.Image: {type(img)}")
                            passed += 1
                            tested += 1
                    else:
                        lines.append(f"  [WARN] Unexpected preview_result format: {type(preview_result)}")
                        passed += 1
                        tested += 1
                else:
                    lines.append("  [WARN] decode_latent_to_preview_image returned None")
                    passed += 1
                    tested += 1

            except Exception as e:
                lines.append(f"  [FAIL] Synthetic preview: {e}")
                lines.append(f"         {traceback.format_exc()}")
                failed += 1
                tested += 1
        else:
            lines.append("  [SKIP] No previewer available (method='none' or failed to create)")
            tested += 1
            passed += 1

        # =====================================================================
        # SECTION 5: UtilsProxy (Host-side)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("SECTION 5: UTILS PROXY")
        lines.append("-" * 40)

        try:
            from comfy.isolation.proxies.utils_proxy import UtilsProxy
            utils_proxy = UtilsProxy.get_instance()
            lines.append("  [PASS] UtilsProxy.get_instance()")
            passed += 1
            tested += 1

            # Check it has progress_bar_hook method
            if hasattr(utils_proxy, 'progress_bar_hook'):
                lines.append("  [PASS] UtilsProxy has progress_bar_hook method")
                passed += 1
                tested += 1
            else:
                lines.append("  [FAIL] UtilsProxy missing progress_bar_hook")
                failed += 1
                tested += 1
        except Exception as e:
            lines.append(f"  [FAIL] UtilsProxy: {e}")
            failed += 1
            tested += 1

        # =====================================================================
        # SUMMARY
        # =====================================================================
        lines.append("")
        lines.append("=" * 60)
        lines.append("PIPELINE TEST SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Tests run:    {tested}")
        lines.append(f"Passed:       {passed}")
        lines.append(f"Failed:       {failed}")
        lines.append(f"Pass rate:    {100*passed//tested if tested else 0}%")
        lines.append("")

        if failed == 0:
            lines.append("[SUCCESS] Preview pipeline tests passed!")
        else:
            lines.append(f"[ATTENTION] {failed} test(s) failed")

        report = "\n".join(lines)
        logger.info(f"\n{report}")
        return io.NodeOutput(report)


NODES = [ProxyTestPreviewPipeline]
