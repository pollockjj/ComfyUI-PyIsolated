from __future__ import annotations

from comfy_api.latest import ComfyExtension

from .nodes import (
    PyIsolatedTestNodeV3,
    PyIsolatedExecuteV3,
    PyIsolatedExecuteAdvancedV3,
)

class PyIsolatedExtension(ComfyExtension):
    async def get_node_list(self):
        return [PyIsolatedTestNodeV3, PyIsolatedExecuteV3, PyIsolatedExecuteAdvancedV3]


async def comfy_entrypoint() -> PyIsolatedExtension:
    return PyIsolatedExtension()
