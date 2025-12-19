from __future__ import annotations

from comfy_api.latest import ComfyExtension

from .nodes import (
    PyIsolatedTestNodeV3,
    PyIsolatedExecuteV3,
    PyIsolatedExecuteAdvancedV3,
    ZeroCopyArange,
    TestCLIPProxy_APISO,
)
from .nodes_adversarial import (
    AdversarialSummary,
    AdversarialFilesystemRead,
    AdversarialFilesystemWrite,
    AdversarialEnvLeak,
)

class PyIsolatedExtension(ComfyExtension):
    async def get_node_list(self):
        return [
            PyIsolatedTestNodeV3,
            PyIsolatedExecuteV3,
            PyIsolatedExecuteAdvancedV3,
            ZeroCopyArange,
            TestCLIPProxy_APISO,
            # Adversarial test nodes for sandbox verification
            AdversarialSummary,
            AdversarialFilesystemRead,
            AdversarialFilesystemWrite,
            AdversarialEnvLeak,
        ]


async def comfy_entrypoint() -> PyIsolatedExtension:
    return PyIsolatedExtension()
