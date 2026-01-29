"""Free Memory Node - Triggers VRAM cleanup while passing through an image."""

from __future__ import annotations

from comfy_api.latest import io
import comfy.model_management as model_management


class FreeMemoryImagePassthrough(io.ComfyNode):
    """Passes through an image while calling free_memory at 95% device VRAM."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="FreeMemoryImagePassthrough",
            category="PyIsolate/Debug",
            display_name="Free Memory (Image Passthrough)",
            inputs=[
                io.Image.Input("image", display_name="Image"),
            ],
            outputs=[
                io.Image.Output("image", display_name="Image"),
            ],
        )

    @classmethod
    def execute(cls, image) -> io.NodeOutput:
        device = model_management.get_torch_device()
        total_memory = model_management.get_total_memory(device)
        target = int(total_memory * 0.95)
        model_management.free_memory(target, device)
        model_management.soft_empty_cache()
        return io.NodeOutput(image)
