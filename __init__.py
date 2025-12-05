from __future__ import annotations

import logging
from typing import Dict

from comfy_api.latest import ComfyExtension, io

from .execution_wrapper import run_code_safe

logger = logging.getLogger(__name__)
LOG_PREFIX = "🔒 [PyIsolated]"


class PyIsolatedTestNodeV1:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("message",)
    FUNCTION = "test"
    CATEGORY = "pyisolated"

    def test(self):
        return ("PyIsolate V1 Node is working!",)


class PyIsolatedTestNodeV3(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PyIsolatedTest",
            display_name="PyIsolated Test",
            category="pyisolated",
            inputs=[],
            outputs=[
                io.String.Output("message", display_name="message"),
            ],
        )

    @classmethod
    def execute(cls) -> io.NodeOutput:
        return io.NodeOutput("PyIsolate V3 Node is working!")


class PyIsolatedExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [PyIsolatedTestNodeV3]




NODE_CLASS_MAPPINGS = {"PyIsolatedTestNodeV1": PyIsolatedTestNodeV1, "PyIsolatedTestNodeV3": PyIsolatedTestNodeV3}

NODE_DISPLAY_NAME_MAPPINGS = {"PyIsolatedTestNodeV1": "PyIsolatedTestNodeV1", "PyIsolatedTestNodeV3": "PyIsolatedTestNodeV3"}