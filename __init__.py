from __future__ import annotations

import logging
from typing import Dict

from comfy_api.latest import io, ComfyExtension

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
        return ("PyIsolate is working!",)


NODE_CLASS_MAPPINGS = {"PyIsolatedTestNodeV1": PyIsolatedTestNodeV1,}

NODE_DISPLAY_NAME_MAPPINGS = {"PyIsolatedTestNodeV1": "PyIsolatedTestNodeV1",}