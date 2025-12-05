from __future__ import annotations

import logging
from typing import Dict

from comfy_api.latest import io, ComfyExtension

from .execution_wrapper import run_code_safe

logger = logging.getLogger(__name__)
LOG_PREFIX = "🔒 [PyIsolated]"


class PyIsolatedExecuteNode(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PyIsolated",
            display_name="PyIsolated Execute",
            category="pyisolated",
            inputs=[
                io.String.Input(
                    "code",
                    multiline=True,
                    default="# Simple example\nresult = f'Hello, {input_text}!'\nprint(f'Processing: {input_text}')",
                ),
                io.String.Input("input_text", default="World"),
                io.String.Input(
                    "dependencies",
                    multiline=True,
                    default="# One package per line\n# numpy\n# requests",
                    optional=True,
                ),
            ],
            outputs=[
                io.String.Output("result", display_name="result"),
                io.String.Output("stdout", display_name="stdout"),
                io.Int.Output("exit_code", display_name="exit_code"),
            ],
        )

    @classmethod
    def execute(cls, code: str, input_text: str, dependencies: str = "") -> io.NodeOutput:
        deps = [line.strip() for line in dependencies.split("\n") if line.strip() and not line.strip().startswith("#")]
        try:
            result, stdout, exit_code = run_code_safe(
                code=code,
                inputs={"input_text": input_text},
                dependencies=deps,
            )
            logger.info(f"{LOG_PREFIX}[V3] exit_code={exit_code}, result_len={len(result)}, stdout_len={len(stdout)}")
            return io.NodeOutput(result, stdout, exit_code)
        except Exception as e:  # pragma: no cover
            logger.error(f"{LOG_PREFIX}[V3] error: {e}", exc_info=True)
            return io.NodeOutput(f"Fatal execution error: {e}", "", 1)


class PyIsolatedExecuteAdvancedNode(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PyIsolatedAdvanced",
            display_name="PyIsolated Execute Advanced",
            category="pyisolated",
            inputs=[
                io.String.Input(
                    "code",
                    multiline=True,
                    default="# Use image_payload / latent_payload / mask_payload / text_payload\nresult = 'ok'",
                ),
                io.String.Input("text_payload", default="", optional=True),
                io.Image.Input("image_payload", optional=True),
                io.Latent.Input("latent_payload", optional=True),
                io.Mask.Input("mask_payload", optional=True),
                io.String.Input(
                    "dependencies",
                    multiline=True,
                    default="",
                    optional=True,
                ),
            ],
            outputs=[
                io.String.Output("result_text", display_name="result_text"),
                io.Image.Output("result_image", display_name="result_image"),
                io.Latent.Output("result_latent", display_name="result_latent"),
                io.String.Output("stdout", display_name="stdout"),
                io.Int.Output("exit_code", display_name="exit_code"),
            ],
        )

    @classmethod
    def execute(
        cls,
        code: str,
        text_payload: str = "",
        image_payload=None,
        latent_payload=None,
        mask_payload=None,
        dependencies: str = "",
    ) -> io.NodeOutput:
        deps = [line.strip() for line in dependencies.split("\n") if line.strip() and not line.strip().startswith("#")]
        inputs = {
            "text_payload": text_payload,
            "image_payload": image_payload,
            "latent_payload": latent_payload,
            "mask_payload": mask_payload,
        }
        try:
            result, stdout, exit_code = run_code_safe(
                code=code,
                inputs=inputs,
                dependencies=deps,
            )
            # Allow user code to set result_image/result_latent via returned dict
            result_image = None
            result_latent = None
            if isinstance(result, dict):
                result_image = result.get("result_image")
                result_latent = result.get("result_latent")
                result_text = result.get("result_text", str(result))
            else:
                result_text = str(result)

            return io.NodeOutput(
                result_text,
                result_image,
                result_latent,
                stdout,
                exit_code,
            )
        except Exception as e:  # pragma: no cover
            logger.error(f"{LOG_PREFIX}[V3-ADV] error: {e}", exc_info=True)
            return io.NodeOutput(f"Fatal execution error: {e}", None, None, "", 1)


class PyIsolatedExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [PyIsolatedExecuteNode, PyIsolatedExecuteAdvancedNode]


NODE_CLASS_MAPPINGS = {
    "PyIsolated": PyIsolatedExecuteNode,
    "PyIsolatedAdvanced": PyIsolatedExecuteAdvancedNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PyIsolated": "PyIsolated Execute",
    "PyIsolatedAdvanced": "PyIsolated Execute Advanced",
}
