from __future__ import annotations

import logging
from typing import Dict

from comfy_api.latest import ComfyExtension, io

from .execution_wrapper import run_code_safe

logger = logging.getLogger(__name__)
LOG_PREFIX = ""


class PyIsolatedTestNodeV1:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("message",)
    FUNCTION = "test"
    CATEGORY = "PyIsolated"

    def test(self):
        return ("PyIsolated V1 Node is working!",)

class PyIsolatedExecuteV1:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "code": ("STRING", {
                    "multiline": True,
                    "default": "# Your code here\nresult = f'Hello, {input_text}!'\nprint(f'Processing: {input_text}')",
                }),
                "input_text": ("STRING", {"default": "World"}),
            },
            "optional": {
                "dependencies": ("STRING", {
                    "multiline": True,
                    "default": "# One package per line\n# numpy\n# requests",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("result", "stdout", "exit_code")
    FUNCTION = "execute"
    CATEGORY = "PyIsolated"

    def execute(self, code: str, input_text: str, dependencies: str = "") -> Tuple[str, str, int]:
        deps = [line.strip() for line in dependencies.split("\n") if line.strip() and not line.strip().startswith("#")]
        logger.info(f"{LOG_PREFIX}[V1] Executing with {len(deps)} dependencies")
        
        result, stdout, exit_code = run_code_safe(
            code=code,
            inputs={"input_text": input_text},
            dependencies=deps,
        )
        
        logger.info(f"{LOG_PREFIX}[V1] exit_code={exit_code}, result_len={len(result)}, stdout_len={len(stdout)}")
        return (result, stdout, exit_code)
class PyIsolatedExecuteAdvancedV1:
    """V1 advanced execution node: code + multi-type payloads + dependencies."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "code": ("STRING", {
                    "multiline": True,
                    "default": "# Access: text_payload, image_payload, latent_payload, mask_payload\nresult = f'Received text: {text_payload}'",
                }),
            },
            "optional": {
                "text_payload": ("STRING", {"default": ""}),
                "image_payload": ("IMAGE",),
                "latent_payload": ("LATENT",),
                "mask_payload": ("MASK",),
                "dependencies": ("STRING", {
                    "multiline": True,
                    "default": "",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "IMAGE", "LATENT", "STRING", "INT")
    RETURN_NAMES = ("result_text", "result_image", "result_latent", "stdout", "exit_code")
    FUNCTION = "execute"
    CATEGORY = "PyIsolated"

    def execute(
        self,
        code: str,
        text_payload: str = "",
        image_payload: Any = None,
        latent_payload: Any = None,
        mask_payload: Any = None,
        dependencies: str = "",
    ) -> Tuple[str, Any, Any, str, int]:
        deps = [line.strip() for line in dependencies.split("\n") if line.strip() and not line.strip().startswith("#")]
        logger.info(f"{LOG_PREFIX}[V1-ADV] Executing with {len(deps)} dependencies")
        
        inputs = {
            "text_payload": text_payload,
            "image_payload": image_payload,
            "latent_payload": latent_payload,
            "mask_payload": mask_payload,
        }
        
        result, stdout, exit_code = run_code_safe(
            code=code,
            inputs=inputs,
            dependencies=deps,
        )
        
        # Parse result - user code can return dict with typed outputs
        result_image = None
        result_latent = None
        if isinstance(result, dict):
            result_image = result.get("result_image")
            result_latent = result.get("result_latent")
            result_text = result.get("result_text", str(result))
        else:
            result_text = str(result)
        
        logger.info(f"{LOG_PREFIX}[V1-ADV] exit_code={exit_code}, result_text_len={len(result_text)}")
        return (result_text, result_image, result_latent, stdout, exit_code)

class PyIsolatedTestNodeV3(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PyIsolatedTestNodeV3",
            display_name="PyIsolatedTestNodeV3",
            category="PyIsolated",
            inputs=[],
            outputs=[
                io.String.Output("message", display_name="message"),
            ],
        )

    @classmethod
    def execute(cls) -> io.NodeOutput:
        return io.NodeOutput("PyIsolated V3 Node is working!")

class PyIsolatedExecuteV3(io.ComfyNode):
    """V3 basic execution node: code + input_text + dependencies."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PyIsolatedExecuteV3",
            display_name="PyIsolatedExecuteV3",
            category="PyIsolated",
            inputs=[
                io.String.Input(
                    "code",
                    multiline=True,
                    default="# Your code here\nresult = f'Hello, {input_text}!'\nprint(f'Processing: {input_text}')",
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
                io.String.Output("result"),
                io.String.Output("stdout"),
                io.Int.Output("exit_code"),
            ],
        )

    @classmethod
    def execute(cls, code: str, input_text: str, dependencies: str = "") -> io.NodeOutput:
        deps = [line.strip() for line in dependencies.split("\n") if line.strip() and not line.strip().startswith("#")]
        logger.info(f"{LOG_PREFIX}[V3] Executing with {len(deps)} dependencies")
        
        result, stdout, exit_code = run_code_safe(
            code=code,
            inputs={"input_text": input_text},
            dependencies=deps,
        )
        
        logger.info(f"{LOG_PREFIX}[V3] exit_code={exit_code}, result_len={len(result)}, stdout_len={len(stdout)}")
        return io.NodeOutput(result, stdout, exit_code)

class PyIsolatedExecuteAdvancedV3(io.ComfyNode):
    """V3 advanced execution node: code + multi-type payloads + dependencies."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PyIsolatedExecuteAdvancedV3",
            display_name="PyIsolatedExecuteAdvancedV3",
            category="PyIsolated",
            inputs=[
                io.String.Input(
                    "code",
                    multiline=True,
                    default="# Access: text_payload, image_payload, latent_payload, mask_payload\nresult = f'Received text: {text_payload}'",
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
                io.String.Output("result_text"),
                io.Image.Output("result_image"),
                io.Latent.Output("result_latent"),
                io.String.Output("stdout"),
                io.Int.Output("exit_code"),
            ],
        )

    @classmethod
    def execute(
        cls,
        code: str,
        text_payload: str = "",
        image_payload: Any = None,
        latent_payload: Any = None,
        mask_payload: Any = None,
        dependencies: str = "",
    ) -> io.NodeOutput:
        deps = [line.strip() for line in dependencies.split("\n") if line.strip() and not line.strip().startswith("#")]
        logger.info(f"{LOG_PREFIX}[V3-ADV] Executing with {len(deps)} dependencies")
        
        inputs = {
            "text_payload": text_payload,
            "image_payload": image_payload,
            "latent_payload": latent_payload,
            "mask_payload": mask_payload,
        }
        
        result, stdout, exit_code = run_code_safe(
            code=code,
            inputs=inputs,
            dependencies=deps,
        )
        
        # Parse result - user code can return dict with typed outputs
        result_image = None
        result_latent = None
        if isinstance(result, dict):
            result_image = result.get("result_image")
            result_latent = result.get("result_latent")
            result_text = result.get("result_text", str(result))
        else:
            result_text = str(result)
        
        logger.info(f"{LOG_PREFIX}[V3-ADV] exit_code={exit_code}, result_text_len={len(result_text)}")
        return io.NodeOutput(result_text, result_image, result_latent, stdout, exit_code)



class PyIsolatedExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [PyIsolatedTestNodeV3, PyIsolatedExecuteV3, PyIsolatedExecuteAdvancedV3]




NODE_CLASS_MAPPINGS = {"PyIsolatedTestNodeV1": PyIsolatedTestNodeV1, "PyIsolatedTestNodeV3": PyIsolatedTestNodeV3, "PyIsolatedExecuteV1": PyIsolatedExecuteV1, "PyIsolatedExecuteV3": PyIsolatedExecuteV3, "PyIsolatedExecuteAdvancedV1": PyIsolatedExecuteAdvancedV1, "PyIsolatedExecuteAdvancedV3": PyIsolatedExecuteAdvancedV3}

NODE_DISPLAY_NAME_MAPPINGS = {"PyIsolatedTestNodeV1": "PyIsolatedTestNodeV1", "PyIsolatedTestNodeV3": "PyIsolatedTestNodeV3", "PyIsolatedExecuteV1": "PyIsolatedExecuteV1", "PyIsolatedExecuteV3": "PyIsolatedExecuteV3", "PyIsolatedExecuteAdvancedV1": "PyIsolatedExecuteAdvancedV1", "PyIsolatedExecuteAdvancedV3": "PyIsolatedExecuteAdvancedV3"}