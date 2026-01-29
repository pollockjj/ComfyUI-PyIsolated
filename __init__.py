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
from .nodes_proxy_test_model_management import ProxyTestModelManagement
from .nodes_proxy_test_folder_paths import ProxyTestFolderPaths
from .nodes_proxy_test_utils import ProxyTestUtils
from .nodes_proxy_test_latent_formats import ProxyTestLatentFormats
from .nodes_proxy_test_model_patcher import ProxyTestModelPatcher
from .nodes_proxy_test_clip import ProxyTestCLIP
from .nodes_proxy_test_vae import ProxyTestVAE
from .nodes_proxy_test_model_sampler import ProxyTestModelSampler
from .nodes_gate import GateAny
from .nodes_free_memory import FreeMemoryImagePassthrough

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
            ProxyTestModelManagement,
            ProxyTestFolderPaths,
            ProxyTestUtils,
            ProxyTestLatentFormats,
            ProxyTestModelPatcher,
            ProxyTestCLIP,
            ProxyTestVAE,
            ProxyTestModelSampler,
            GateAny,
            FreeMemoryImagePassthrough,
        ]


async def comfy_entrypoint() -> PyIsolatedExtension:
    return PyIsolatedExtension()
