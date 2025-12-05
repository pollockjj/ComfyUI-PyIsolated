from __future__ import annotations

from comfy_api.latest import io, ComfyExtension

class PyIsolatedTestNodeV1:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("message",)
    FUNCTION = "test_v1"
    CATEGORY = "pyisolated"

    def test(self):
        return ("PyIsolate is working!",)


NODE_CLASS_MAPPINGS = {"PyIsolatedTestNodeV1": PyIsolatedTestNodeV1,}

NODE_DISPLAY_NAME_MAPPINGS = {"PyIsolatedTestNodeV1": "PyIsolatedTestNodeV1",}