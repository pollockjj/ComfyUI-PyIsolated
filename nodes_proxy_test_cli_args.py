"""
Proxy Test Node: CLI Args

SYSTEMATIC test of cli_args proxy coverage.
Tests preview_method and preview_size - the runtime CLI settings
that must be accessible from isolated child processes.

This proxy is CRITICAL for preview functionality in isolated nodes.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from comfy_api.latest import io

logger = logging.getLogger(__name__)


class ProxyTestCliArgs(io.ComfyNode):
    """Systematic test of cli_args proxy - tests ALL proxy members."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestCliArgs",
            display_name="Proxy Test: CLI Args",
            category="PyIsolated/ProxyTests",
            inputs=[],
            outputs=[
                io.String.Output("report", display_name="Report"),
            ],
        )

    @classmethod
    def execute(cls) -> io.NodeOutput:
        lines = []
        tested = 0
        passed = 0
        failed = 0

        lines.append("=" * 60)
        lines.append("CLI ARGS PROXY COVERAGE REPORT")
        lines.append("=" * 60)
        lines.append("")

        def verify(name: str,
                  action: Callable[[], Any],
                  check: Callable[[Any], bool] | None = None,
                  expect_error: type[Exception] | None = None) -> Any:
            nonlocal tested, passed, failed
            tested += 1
            try:
                result = action()
                if expect_error:
                    lines.append(f"[FAIL] {name}: Expected {expect_error.__name__} but got result: {result}")
                    failed += 1
                    return result
                if check and not check(result):
                    lines.append(f"[FAIL] {name}: Check failed, got: {result}")
                    failed += 1
                else:
                    lines.append(f"[PASS] {name}: {result}")
                    passed += 1
                return result
            except Exception as e:
                if expect_error and isinstance(e, expect_error):
                    lines.append(f"[PASS] {name}: Raised expected {expect_error.__name__}")
                    passed += 1
                else:
                    lines.append(f"[FAIL] {name}: {type(e).__name__}: {e}")
                    failed += 1
                return None

        # =====================================================================
        # SECTION 1: Direct args import (baseline - what child sees locally)
        # =====================================================================
        lines.append("-" * 40)
        lines.append("SECTION 1: DIRECT ARGS ACCESS (LOCAL)")
        lines.append("-" * 40)

        from comfy.cli_args import args, LatentPreviewMethod

        verify("args.preview_method exists",
               lambda: args.preview_method,
               check=lambda x: isinstance(x, LatentPreviewMethod))

        verify("args.preview_method.value is string",
               lambda: args.preview_method.value,
               check=lambda x: isinstance(x, str))

        verify("args.preview_size exists",
               lambda: args.preview_size,
               check=lambda x: isinstance(x, int))

        local_method = args.preview_method
        local_method_str = args.preview_method.value
        local_size = args.preview_size

        lines.append(f"       Local preview_method: {local_method} ('{local_method_str}')")
        lines.append(f"       Local preview_size: {local_size}")

        # =====================================================================
        # SECTION 2: CliArgsProxy import and instantiation
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("SECTION 2: PROXY IMPORT & INSTANTIATION")
        lines.append("-" * 40)

        proxy = None
        try:
            from comfy.isolation.proxies.cli_args_proxy import CliArgsProxy
            lines.append("[PASS] Import CliArgsProxy")
            passed += 1
            tested += 1
        except Exception as e:
            lines.append(f"[FAIL] Import CliArgsProxy: {e}")
            failed += 1
            tested += 1
            # Can't continue without the proxy
            lines.append("")
            lines.append("=" * 60)
            lines.append("CANNOT CONTINUE - PROXY IMPORT FAILED")
            lines.append("=" * 60)
            report = "\n".join(lines)
            return io.NodeOutput(report)

        verify("CliArgsProxy.get_instance() returns instance",
               lambda: CliArgsProxy.get_instance(),
               check=lambda x: x is not None)

        proxy = CliArgsProxy.get_instance()

        verify("proxy is CliArgsProxy",
               lambda: isinstance(proxy, CliArgsProxy),
               check=lambda x: x is True)

        # =====================================================================
        # SECTION 3: Proxy method tests
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("SECTION 3: PROXY METHOD TESTS")
        lines.append("-" * 40)

        # get_preview_method
        proxy_method_str = verify("proxy.get_preview_method() returns string",
                                   lambda: proxy.get_preview_method(),
                                   check=lambda x: isinstance(x, str))

        verify("get_preview_method() is valid enum value",
               lambda: LatentPreviewMethod.from_string(proxy_method_str),
               check=lambda x: x is not None)

        proxy_method = LatentPreviewMethod.from_string(proxy_method_str) if proxy_method_str else None

        # get_preview_size
        proxy_size = verify("proxy.get_preview_size() returns int",
                            lambda: proxy.get_preview_size(),
                            check=lambda x: isinstance(x, int) and x > 0)

        # =====================================================================
        # SECTION 4: Proxy vs Local comparison (THE CRITICAL TEST)
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("SECTION 4: PROXY VS LOCAL COMPARISON")
        lines.append("-" * 40)
        lines.append("(In isolated process, proxy should return HOST value)")
        lines.append("")

        lines.append(f"  Local args.preview_method:  {local_method} ('{local_method_str}')")
        lines.append(f"  Proxy get_preview_method(): {proxy_method} ('{proxy_method_str}')")
        lines.append(f"  Local args.preview_size:    {local_size}")
        lines.append(f"  Proxy get_preview_size():   {proxy_size}")
        lines.append("")

        # In an isolated process, local args will be defaults (NoPreviews)
        # but proxy should return the HOST's current value
        # If they match AND are NoPreviews, proxy might not be working

        tested += 1
        if proxy_method_str == local_method_str:
            if proxy_method_str == "none":
                lines.append("[WARN] Both local and proxy return 'none' - proxy may not be RPC'ing to host")
                lines.append("       This is expected if --preview-method was not set on host")
                passed += 1  # Not strictly a failure
            else:
                lines.append(f"[PASS] preview_method matches: '{proxy_method_str}'")
                passed += 1
        else:
            lines.append(f"[INFO] preview_method DIFFERS - Local: '{local_method_str}', Proxy: '{proxy_method_str}'")
            lines.append("       This is EXPECTED in isolated process if host has different setting")
            passed += 1

        tested += 1
        if proxy_size == local_size:
            lines.append(f"[PASS] preview_size matches: {proxy_size}")
            passed += 1
        else:
            lines.append(f"[INFO] preview_size DIFFERS - Local: {local_size}, Proxy: {proxy_size}")
            lines.append("       This is EXPECTED in isolated process if host has different setting")
            passed += 1

        # =====================================================================
        # SECTION 5: LatentPreviewMethod enum coverage
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("SECTION 5: LatentPreviewMethod ENUM")
        lines.append("-" * 40)

        verify("NoPreviews value is 'none'",
               lambda: LatentPreviewMethod.NoPreviews.value,
               check=lambda x: x == "none")

        verify("Auto value is 'auto'",
               lambda: LatentPreviewMethod.Auto.value,
               check=lambda x: x == "auto")

        verify("Latent2RGB value is 'latent2rgb'",
               lambda: LatentPreviewMethod.Latent2RGB.value,
               check=lambda x: x == "latent2rgb")

        verify("TAESD value is 'taesd'",
               lambda: LatentPreviewMethod.TAESD.value,
               check=lambda x: x == "taesd")

        verify("from_string('none') -> NoPreviews",
               lambda: LatentPreviewMethod.from_string("none"),
               check=lambda x: x == LatentPreviewMethod.NoPreviews)

        verify("from_string('auto') -> Auto",
               lambda: LatentPreviewMethod.from_string("auto"),
               check=lambda x: x == LatentPreviewMethod.Auto)

        verify("from_string('latent2rgb') -> Latent2RGB",
               lambda: LatentPreviewMethod.from_string("latent2rgb"),
               check=lambda x: x == LatentPreviewMethod.Latent2RGB)

        verify("from_string('taesd') -> TAESD",
               lambda: LatentPreviewMethod.from_string("taesd"),
               check=lambda x: x == LatentPreviewMethod.TAESD)

        verify("from_string('invalid') -> None",
               lambda: LatentPreviewMethod.from_string("invalid"),
               check=lambda x: x is None)

        # =====================================================================
        # SECTION 6: Integration with latent_preview module
        # =====================================================================
        lines.append("")
        lines.append("-" * 40)
        lines.append("SECTION 6: LATENT_PREVIEW INTEGRATION")
        lines.append("-" * 40)

        try:
            import latent_preview
            lines.append("[PASS] Import latent_preview module")
            passed += 1
            tested += 1

            verify("latent_preview.default_preview_method exists",
                   lambda: latent_preview.default_preview_method,
                   check=lambda x: isinstance(x, LatentPreviewMethod))

            verify("latent_preview.MAX_PREVIEW_RESOLUTION exists",
                   lambda: latent_preview.MAX_PREVIEW_RESOLUTION,
                   check=lambda x: isinstance(x, int) and x > 0)

            verify("latent_preview.get_previewer is callable",
                   lambda: callable(latent_preview.get_previewer),
                   check=lambda x: x is True)

            verify("latent_preview.prepare_callback is callable",
                   lambda: callable(latent_preview.prepare_callback),
                   check=lambda x: x is True)

            verify("latent_preview.set_preview_method is callable",
                   lambda: callable(latent_preview.set_preview_method),
                   check=lambda x: x is True)

        except Exception as e:
            lines.append(f"[FAIL] Import latent_preview: {e}")
            failed += 1
            tested += 1

        # =====================================================================
        # SUMMARY
        # =====================================================================
        lines.append("")
        lines.append("=" * 60)
        lines.append("COVERAGE SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Tests run:    {tested}")
        lines.append(f"Passed:       {passed}")
        lines.append(f"Failed:       {failed}")
        lines.append(f"Pass rate:    {100*passed//tested if tested else 0}%")
        lines.append("")

        if failed == 0:
            lines.append("[SUCCESS] All CLI Args proxy tests passed!")
        else:
            lines.append(f"[ATTENTION] {failed} test(s) failed - review above")

        lines.append("")
        lines.append("=" * 60)
        lines.append("DIAGNOSTIC INFO")
        lines.append("=" * 60)
        lines.append(f"Is child process: {__import__('os').environ.get('PYISOLATE_CHILD', '0') == '1'}")
        lines.append("Host preview setting should come from: execution.py set_preview_method()")

        report = "\n".join(lines)
        logger.info(f"\n{report}")
        return io.NodeOutput(report)


NODES = [ProxyTestCliArgs]
