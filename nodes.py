from __future__ import annotations

import logging
from typing import Dict

from comfy_api.latest import io, ComfyExtension

from .execution_wrapper import run_code_safe

logger = logging.getLogger(__name__)
LOG_PREFIX = "🔒 [PyIsolated]"

class PyIsolatedTestNode(io.ComfyNode):
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
        return io.NodeOutput("PyIsolate is working!")


class PyIsolatedExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [PyIsolatedTestNode]


NODE_CLASS_MAPPINGS = {
    "PyIsolatedTest": PyIsolatedTestNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PyIsolatedTest": "PyIsolated Test",
}