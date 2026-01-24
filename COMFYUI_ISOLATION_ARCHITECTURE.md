# ComfyUI Isolation System Architecture

Current fork:  https://github.com/pollockjj/ComfyUI/tree/pyisolate

This document provides a rapid bootstrapping guide for understanding the ComfyUI process isolation framework built on `pyisolate`.

## Purpose

The isolation system allows **untrusted or resource-intensive custom nodes** to run in separate sandboxed (bwrap) processes while maintaining transparent communication with the main ComfyUI host process. Models and heavy objects stay on the host; nodes execute in sandboxed children.

## Key Principle: Proxy Pattern

Objects that cannot cross process boundaries (models, CLIP, VAE) are:
1. **Registered** in a host-side registry with a unique ID
2. **Serialized** as lightweight reference objects (`ModelPatcherRef`, `CLIPRef`, etc.)
3. **Deserialized** in the child as **proxy objects** that forward method calls via RPC

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        HOST PROCESS                              │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ ModelPatcher    │  │ CLIPRegistry     │  │ VAERegistry    │  │
│  │ Registry        │  │                  │  │                │  │
│  └────────┬────────┘  └────────┬─────────┘  └───────┬────────┘  │
│           │                    │                     │           │
│           └────────────────────┼─────────────────────┘           │
│                                │                                 │
│                    ┌───────────▼──────────┐                      │
│                    │  AsyncRPC / Socket   │                      │
│                    │  (JSON + Tensor IPC) │                      │
│                    └───────────┬──────────┘                      │
└────────────────────────────────┼─────────────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────────────┐
│                    CHILD PROCESS (bwrap sandbox)                 │
│                    ┌───────────▼──────────┐                      │
│                    │  RPC Bridge          │                      │
│                    └───────────┬──────────┘                      │
│           ┌────────────────────┼─────────────────────┐           │
│  ┌────────▼────────┐  ┌────────▼─────────┐  ┌───────▼────────┐  │
│  │ ModelPatcher    │  │ CLIPProxy        │  │ VAEProxy       │  │
│  │ Proxy           │  │                  │  │                │  │
│  └─────────────────┘  └──────────────────┘  └────────────────┘  │
│                                                                  │
│                    ┌──────────────────────┐                      │
│                    │ ComfyNodeExtension   │  ← Node execution    │
│                    └──────────────────────┘                      │
└──────────────────────────────────────────────────────────────────┘
```

## File Reference

All files live in `/ComfyUI/comfy/isolation/`.

### Core Files

| File | Purpose |
|------|---------|
| `adapter.py` | **Main integration point**. Implements `IsolationAdapter`, registers serializers, provides RPC services, patches ComfyUI modules |
| `extension_wrapper.py` | `ComfyNodeExtension` class that discovers and executes nodes in the child process |
| `extension_loader.py` | Loads extensions, reads `pyproject.toml` config, creates `ExtensionManager` instances |
| `rpc_bridge.py` | Async-to-sync helper for running coroutines in isolated processes |

### Policy & Initialization

| File | Purpose |
|------|---------|
| `host_policy.py` | Security policy from `pyproject.toml`: network access, writable/readonly paths, whitelist |
| `host_hooks.py` | Initializes host-side proxy registries when child connects |

### Proxy Classes

| File | Purpose |
|------|---------|
| `model_patcher_proxy.py` | Proxies `ModelPatcher` API via RPC. Key optimization: moves CPU→CUDA before RPC in `apply_model()` |
| `clip_proxy.py` | Proxies CLIP encoder access |
| `vae_proxy.py` | Proxies VAE encode/decode |
| `model_sampling_proxy.py` | Proxies model sampling configuration |

### Service Proxies (in `proxies/` subdirectory)

| File | Purpose |
|------|---------|
| `folder_paths_proxy.py` | Proxies `folder_paths` module functions |
| `model_management_proxy.py` | Proxies `comfy.model_management` functions |
| `prompt_server_impl.py` | Proxies PromptServer for route registration |
| `progress_proxy.py` | Proxies progress reporting |
| `utils_proxy.py` | Proxies `comfy.utils` functions |

## Serialization System

The `ComfyUIAdapter.register_serializers()` method (adapter.py:76-264) handles cross-process serialization:

### Object Type Mappings

| ComfyUI Type | Serialized As | Deserialized To (child) |
|--------------|---------------|-------------------------|
| `ModelPatcher` | `ModelPatcherRef` | `ModelPatcherProxy` |
| `CLIP` | `CLIPRef` | `CLIPProxy` |
| `VAE` | `VAERef` | `VAEProxy` |
| `ModelSampling*` | `ModelSamplingRef` | `ModelSamplingProxy` |
| `KSAMPLER` | `{sampler_name, extra_options, inpaint_options}` | Reconstructed `KSAMPLER` |
| `ndarray` | PyTorch tensor | (same) |

### Context-Aware Deserialization

Deserializers check `PYISOLATE_CHILD` env var:
- **Child process**: Creates proxy object
- **Host process**: Looks up real object from registry

```python
def deserialize_model_patcher_ref(data):
    if os.environ.get("PYISOLATE_CHILD") == "1":
        return ModelPatcherProxy(data["model_id"], ...)
    else:
        return ModelPatcherRegistry()._get_instance(data["model_id"])
```

## RPC Services

`ComfyUIAdapter.provide_rpc_services()` returns singleton services available for RPC:

- `PromptServerService` - HTTP route registration
- `FolderPathsProxy` - Path resolution
- `ModelManagementProxy` - Model loading/unloading, VRAM management
- `UtilsProxy` - Utility functions
- `ProgressProxy` - Progress callbacks
- `VAERegistry`, `CLIPRegistry`, `ModelPatcherRegistry`, `ModelSamplingRegistry`, `FirstStageModelRegistry` - Object registries

## Extension Configuration

Extensions declare isolation support in `pyproject.toml`:

```toml
[tool.comfy.isolation]
can_isolate = true    # Extension supports isolation
share_torch = true    # Share CUDA IPC for tensors
```

Environment variables control enforcement:
- `PYISOLATE_ENFORCE_ISOLATED` - Force all extensions to isolate
- `PYISOLATE_ENFORCE_SANDBOX` - Force bwrap sandboxing

## Key Implementation Details

### 1. Shared Memory (adapter.py:27-34)

bwrap makes `/tmp` private, so TMPDIR is forced to `/dev/shm` for shared memory IPC:

```python
if os.path.exists("/dev/shm"):
    os.environ["TMPDIR"] = "/dev/shm"
```

### 2. Model Tensor Optimization (model_patcher_proxy.py:214-234)

Before RPC calls, CPU tensors are moved to CUDA to use fast CUDA IPC instead of slow tensor serialization:

```python
def apply_model(self, x, t, c_concat=None, ...):
    # Move CPU tensors to CUDA before RPC
    if x.device.type == "cpu":
        x = x.cuda()
    # ... RPC call with CUDA tensors uses IPC
```

### 3. Remote Object Handles (extension_wrapper.py:287-336)

Objects that can't be serialized get wrapped in `RemoteObjectHandle`:

```python
class RemoteObjectHandle:
    def __init__(self, handle_id, type_name):
        self.handle_id = handle_id
        self.type_name = type_name
```

### 4. Event Loop Handling (rpc_bridge.py)

Handles nested event loop scenarios:
- No loop running: `asyncio.run()`
- Loop already running: Spawns new thread with dedicated loop

### 5. Module Patching (adapter.py:280-382)

`handle_api_registration()` replaces ComfyUI module functions with proxy methods:

```python
# folder_paths.get_folder_paths() → FolderPathsProxy.get_folder_paths()
for name in dir(instance):
    if not name.startswith("_"):
        setattr(folder_paths, name, getattr(instance, name))
```

## Debugging Tips

1. **Check process context**: `os.environ.get("PYISOLATE_CHILD") == "1"` indicates child process
2. **Registry lookups**: Use `Registry()._get_instance(id)` to inspect registered objects
3. **RPC tracing**: Enable pyisolate debug logging to see RPC traffic
4. **Sandbox issues**: Check `/dev/shm` permissions and bwrap availability

## Related pyisolate Components

- `pyisolate.interfaces.IsolationAdapter` - Base adapter interface
- `pyisolate._internal.rpc_protocol.AsyncRPC` - RPC implementation
- `pyisolate._internal.rpc_protocol.ProxiedSingleton` - Base for RPC services
- `ExtensionBase` - Base class for `ComfyNodeExtension`
- `ExtensionManager` - Manages extension lifecycle

## Quick Reference: Adding a New Proxy Type

1. Create registry class extending appropriate base in `comfy/isolation/`
2. Create proxy class that forwards calls via RPC
3. Add serializer/deserializer in `adapter.py:register_serializers()`
4. Add registry to `provide_rpc_services()` if needed
5. Handle in `extension_wrapper.py` if special deserialization needed

---

## Essential Files to Read (in order)

For full context on the isolation system, read these files:

| Priority | File | Why |
|----------|------|-----|
| 1 | `/ComfyUI/comfy/model_management.py` | **THE** VRAM management chokepoint. `load_models_gpu`, `current_loaded_models`, `LoadedModel` class |
| 2 | `/ComfyUI/comfy/isolation/adapter.py` | Main integration: serializers, RPC services, module patching |
| 3 | `/ComfyUI/comfy/isolation/model_patcher_proxy.py` | ModelPatcher proxy - the `manage_lifecycle` decision lives here |
| 4 | `/ComfyUI/comfy/isolation/proxies/base.py` | `BaseRegistry` and `BaseProxy` - lifecycle management infrastructure |
| 5 | `/ComfyUI/comfy/isolation/extension_wrapper.py` | Node execution in child, RemoteObjectHandle |
| 6 | `/ComfyUI/comfy/isolation/clip_proxy.py` | CLIP proxy pattern (similar to model_patcher_proxy) |
| 7 | `/ComfyUI/comfy/isolation/vae_proxy.py` | VAE proxy pattern |
| 8 | `/ComfyUI/comfy/isolation/host_hooks.py` | Host-side initialization when child connects |
| 9 | `/ComfyUI/comfy/isolation/extension_loader.py` | Extension discovery, pyproject.toml parsing |
| 10 | `/ComfyUI/comfy/model_patcher.py` | The real ModelPatcher class being proxied |