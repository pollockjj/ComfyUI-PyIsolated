from __future__ import annotations

from comfy_api.latest import ComfyExtension

from .nodes import (
    PyIsolatedTestNodeV3,
    PyIsolatedExecuteV3,
    PyIsolatedExecuteAdvancedV3,
    ZeroCopyArange,
)

class PyIsolatedExtension(ComfyExtension):
    async def get_node_list(self):
        return [
            PyIsolatedTestNodeV3,
            PyIsolatedExecuteV3,
            PyIsolatedExecuteAdvancedV3,
            ZeroCopyArange,
        ]


async def comfy_entrypoint() -> PyIsolatedExtension:
    return PyIsolatedExtension()
