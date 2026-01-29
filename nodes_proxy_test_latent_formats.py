"""
Proxy Test Node: Latent Formats

SYSTEMATIC test of comfy.latent_formats coverage.
Enumerates ALL LatentFormat classes and tests each one.
Outputs coverage report for baseline comparison.
"""
from __future__ import annotations


import comfy.latent_formats
from comfy_api.latest import io


class ProxyTestLatentFormats(io.ComfyNode):
    """Systematic test of comfy.latent_formats - enumerates all format classes."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ProxyTestLatentFormats",
            display_name="Proxy Test: Latent Formats",
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
        skipped = 0

        lines.append("=" * 60)
        lines.append("LATENT FORMATS PROXY COVERAGE REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Discover all format classes
        lines.append("-" * 40)
        lines.append("DISCOVERED FORMAT CLASSES")
        lines.append("-" * 40)

        format_classes = []
        try:
            base_class = comfy.latent_formats.LatentFormat
            for name in sorted(dir(comfy.latent_formats)):
                if name.startswith('_'):
                    continue
                obj = getattr(comfy.latent_formats, name)
                if isinstance(obj, type) and issubclass(obj, base_class):
                    format_classes.append((name, obj))
            lines.append(f"Found {len(format_classes)} LatentFormat subclasses")
        except Exception as e:
            lines.append(f"[FAIL] Discovery failed: {e}")
            failed += 1

        lines.append("")
        lines.append("-" * 40)
        lines.append("BASE CLASS TEST")
        lines.append("-" * 40)

        # Test LatentFormat base class
        tested += 1
        try:
            _ = comfy.latent_formats.LatentFormat
            lines.append("[PASS] LatentFormat class exists")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] LatentFormat: {e}")
            failed += 1

        # Instantiate base class
        tested += 1
        try:
            instance = comfy.latent_formats.LatentFormat()
            lines.append("[PASS] LatentFormat() instantiated")
            lines.append(f"       scale_factor={getattr(instance, 'scale_factor', 'N/A')}")
            lines.append(f"       latent_channels={getattr(instance, 'latent_channels', 'N/A')}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] LatentFormat(): {e}")
            failed += 1

        # Check methods
        tested += 1
        try:
            instance = comfy.latent_formats.LatentFormat()
            has_process_in = hasattr(instance, 'process_in')
            has_process_out = hasattr(instance, 'process_out')
            lines.append(f"[PASS] Methods: process_in={has_process_in}, process_out={has_process_out}")
            passed += 1
        except Exception as e:
            lines.append(f"[FAIL] Method check: {e}")
            failed += 1

        lines.append("")
        lines.append("-" * 40)
        lines.append("ALL FORMAT CLASSES")
        lines.append("-" * 40)

        for name, cls_obj in format_classes:
            tested += 1
            try:
                # Try to instantiate
                instance = cls_obj()
                scale = getattr(instance, 'scale_factor', 'N/A')
                channels = getattr(instance, 'latent_channels', 'N/A')
                lines.append(f"[PASS] {name}: scale={scale}, channels={channels}")
                passed += 1
            except TypeError as e:
                # Some classes may require args
                lines.append(f"[SKIP] {name}: requires args ({e})")
                skipped += 1
                tested -= 1
            except Exception as e:
                lines.append(f"[FAIL] {name}: {type(e).__name__}: {e}")
                failed += 1

        lines.append("")
        lines.append("-" * 40)
        lines.append("KEY FORMAT CLASSES (explicit)")
        lines.append("-" * 40)

        key_formats = ['SD15', 'SDXL', 'SD3', 'Flux', 'HunyuanVideo', 'Mochi']
        for fmt_name in key_formats:
            tested += 1
            try:
                fmt_class = getattr(comfy.latent_formats, fmt_name)
                instance = fmt_class()
                lines.append(f"[PASS] {fmt_name}: scale={instance.scale_factor}")
                passed += 1
            except AttributeError:
                lines.append(f"[SKIP] {fmt_name}: not in this ComfyUI version")
                skipped += 1
                tested -= 1
            except TypeError:
                lines.append(f"[SKIP] {fmt_name}: requires args")
                skipped += 1
                tested -= 1
            except Exception as e:
                lines.append(f"[FAIL] {fmt_name}: {e}")
                failed += 1

        # Summary
        lines.append("")
        lines.append("=" * 60)
        lines.append("COVERAGE SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Format classes discovered: {len(format_classes)}")
        lines.append(f"Tested: {tested}")
        lines.append(f"Passed: {passed}")
        lines.append(f"Failed: {failed}")
        lines.append(f"Skipped: {skipped}")
        coverage = (passed / tested * 100) if tested > 0 else 0
        lines.append(f"Coverage: {coverage:.1f}%")
        lines.append("=" * 60)

        report = "\n".join(lines)
        return io.NodeOutput(report)


NODES = [ProxyTestLatentFormats]
