"""Gate Nodes - Forces deterministic execution order."""

from __future__ import annotations

from comfy_api.latest import io


class GateAny(io.ComfyNode):
    """Universal Gate - accepts any types for Gate and Source."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="GateAny",
            category="PyIsolate/Flow",
            display_name="Gate (Any)",
            inputs=[
                io.AnyType.Input("gate", display_name="Gate"),
                io.AnyType.Input("source", display_name="Source"),
            ],
            outputs=[
                io.AnyType.Output("gate_out", display_name="Gate"),
                io.AnyType.Output("drain", display_name="Drain"),
            ],
        )

    @classmethod
    def execute(cls, gate, source) -> io.NodeOutput:
        return io.NodeOutput(gate, source)


class GateCondClip(io.ComfyNode):
    """Gate: CONDITIONING in, CLIP passes through."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="GateCondClip",
            category="PyIsolate/Flow",
            display_name="Gate (Cond→Clip)",
            inputs=[
                io.Conditioning.Input("gate", display_name="Gate"),
                io.Clip.Input("source", display_name="Source"),
            ],
            outputs=[
                io.Conditioning.Output("gate_out", display_name="Gate"),
                io.Clip.Output("drain", display_name="Drain"),
            ],
        )

    @classmethod
    def execute(cls, gate, source) -> io.NodeOutput:
        return io.NodeOutput(gate, source)


class GateLatentModel(io.ComfyNode):
    """Gate: LATENT in, MODEL passes through."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="GateLatentModel",
            category="PyIsolate/Flow",
            display_name="Gate (Latent→Model)",
            inputs=[
                io.Latent.Input("gate", display_name="Gate"),
                io.Model.Input("source", display_name="Source"),
            ],
            outputs=[
                io.Latent.Output("gate_out", display_name="Gate"),
                io.Model.Output("drain", display_name="Drain"),
            ],
        )

    @classmethod
    def execute(cls, gate, source) -> io.NodeOutput:
        return io.NodeOutput(gate, source)
