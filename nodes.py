from __future__ import annotations

from typing import Any

from comfy_api.latest import io

from .execution_wrapper import run_code_direct


class PyIsolatedTestNodeV3(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PyIsolatedTestNodeV3",
            display_name="PyIsolatedTestNodeV3",
            category="PyIsolated",
            inputs=[],
            outputs=[io.String.Output("message", display_name="message")],
        )

    @classmethod
    def execute(cls) -> io.NodeOutput:
        return io.NodeOutput("PyIsolated V3 Node is working!")


class PyIsolatedExecuteV3(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PyIsolatedExecuteV3",
            display_name="PyIsolatedExecuteV3",
            category="PyIsolated",
            inputs=[
                io.String.Input(
                    "code",
                    multiline=True,
                    default="result = f'Received text: {text_payload}'",
                ),
                io.String.Input("text_payload", optional=True),
                io.Image.Input("image_payload", optional=True),
                io.Latent.Input("latent_payload", optional=True),
                io.Mask.Input("mask_payload", optional=True),
            ],
            outputs=[
                io.String.Output("result_text", display_name="result_text"),
                io.Image.Output("result_image", display_name="result_image"),
                io.Latent.Output("result_latent", display_name="result_latent"),
                io.String.Output("stdout", display_name="stdout"),
                io.Int.Output("exit_code", display_name="exit_code"),
            ],
        )

    @classmethod
    def execute(
        cls,
        code: str,
        text_payload: str = "",
        image_payload: Any = None,
        latent_payload: Any = None,
        mask_payload: Any = None,
    ) -> io.NodeOutput:
        inputs = {
            "text_payload": text_payload,
            "image_payload": image_payload,
            "latent_payload": latent_payload,
            "mask_payload": mask_payload,
        }

        result, stdout, exit_code = run_code_direct(code=code, inputs=inputs)

        result_image = None
        result_latent = None
        if isinstance(result, dict):
            result_image = result.get("result_image")
            result_latent = result.get("result_latent")
            result_text = result.get("result_text", str(result))
        else:
            result_text = str(result)

        return io.NodeOutput(result_text, result_image, result_latent, stdout, exit_code)


class PyIsolatedExecuteAdvancedV3(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PyIsolatedExecuteAdvancedV3",
            display_name="PyIsolatedExecuteAdvancedV3",
            category="PyIsolated",
            inputs=[
                io.String.Input(
                    "code",
                    multiline=True,
                    default="result = f'Received text: {text_payload}'",
                ),
                io.String.Input("text_payload", optional=True),
                io.Image.Input("image_payload", optional=True),
                io.Latent.Input("latent_payload", optional=True),
                io.Mask.Input("mask_payload", optional=True),
                io.String.Input(
                    "dependencies",
                    multiline=True,
                    default="# One package per line",
                    optional=True,
                ),
            ],
            outputs=[
                io.String.Output("result_text", display_name="result_text"),
                io.Image.Output("result_image", display_name="result_image"),
                io.Latent.Output("result_latent", display_name="result_latent"),
                io.String.Output("stdout", display_name="stdout"),
                io.Int.Output("exit_code", display_name="exit_code"),
            ],
        )

    @classmethod
    def execute(
        cls,
        code: str,
        text_payload: str = "",
        image_payload: Any = None,
        latent_payload: Any = None,
        mask_payload: Any = None,
        dependencies: str = "",
    ) -> io.NodeOutput:
        deps = [
            line.strip()
            for line in dependencies.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        inputs = {
            "text_payload": text_payload,
            "image_payload": image_payload,
            "latent_payload": latent_payload,
            "mask_payload": mask_payload,
        }

        result, stdout, exit_code = run_code_direct(code=code, inputs=inputs, dependencies=deps)

        result_image = None
        result_latent = None
        if isinstance(result, dict):
            result_image = result.get("result_image")
            result_latent = result.get("result_latent")
            result_text = result.get("result_text", str(result))
        else:
            result_text = str(result)

        return io.NodeOutput(result_text, result_image, result_latent, stdout, exit_code)
