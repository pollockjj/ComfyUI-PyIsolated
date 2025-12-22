from __future__ import annotations

from comfy_api.latest import ComfyExtension

from .nodes import (
    PyIsolatedTestNodeV3,
    PyIsolatedExecuteV3,
    PyIsolatedExecuteAdvancedV3,
    ZeroCopyArange,
    TestCLIPProxy_APISO,
)
from .nodes_adversarial import AdversarialSummary
from .nodes_security_audit import SecurityAudit

class PyIsolatedExtension(ComfyExtension):
    async def get_node_list(self):
        return [
            PyIsolatedTestNodeV3,
            PyIsolatedExecuteV3,
            PyIsolatedExecuteAdvancedV3,
            ZeroCopyArange,
            TestCLIPProxy_APISO,
            AdversarialSummary,
            SecurityAudit,
        ]


async def comfy_entrypoint() -> PyIsolatedExtension:
    return PyIsolatedExtension()
