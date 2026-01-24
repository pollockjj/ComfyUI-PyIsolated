# PyIsolate Architecture

Current fork:  https://github.com/pollockjj/pyisolate

A production-ready process isolation library for running untrusted code in sandboxed processes with secure, zero-copy tensor transfer.

## Purpose

PyIsolate enables running arbitrary Python modules in isolated child processes with:
- **Security**: Bubblewrap (bwrap) sandboxing with deny-by-default filesystem
- **Performance**: Zero-copy CUDA tensor transfer via undocumented PyTorch IPC primitives
- **Safety**: JSON-RPC (no pickle) prevents deserialization attacks from sandboxed processes
- **Extensibility**: Adapter pattern for application-specific integration (e.g., ComfyUI)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HOST PROCESS                                    │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐  │
│  │ Extension       │  │ SerializerRegistry│  │ IsolationAdapter          │  │
│  │ (host.py)       │  │ (custom types)    │  │ (app-specific hooks)      │  │
│  └────────┬────────┘  └────────┬─────────┘  └───────────┬────────────────┘  │
│           │                    │                         │                   │
│           └────────────────────┼─────────────────────────┘                   │
│                                │                                             │
│                    ┌───────────▼───────────┐                                 │
│                    │      AsyncRPC         │                                 │
│                    │  (rpc_protocol.py)    │                                 │
│                    └───────────┬───────────┘                                 │
│                                │                                             │
│                    ┌───────────▼───────────┐                                 │
│                    │  JSONSocketTransport  │  ← Length-prefixed JSON msgs   │
│                    │  (rpc_transports.py)  │                                 │
│                    └───────────┬───────────┘                                 │
│                                │                                             │
│                    ┌───────────▼───────────┐                                 │
│                    │   Unix Domain Socket  │  ← Or TCP (Windows fallback)   │
│                    └───────────┬───────────┘                                 │
└────────────────────────────────┼─────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────────────────────────┐
│                    CHILD PROCESS (bwrap sandbox)                             │
│                    ┌───────────▼───────────┐                                 │
│                    │   Unix Domain Socket  │                                 │
│                    └───────────┬───────────┘                                 │
│                                │                                             │
│                    ┌───────────▼───────────┐                                 │
│                    │  JSONSocketTransport  │                                 │
│                    └───────────┬───────────┘                                 │
│                                │                                             │
│                    ┌───────────▼───────────┐                                 │
│                    │      AsyncRPC         │                                 │
│                    └───────────┬───────────┘                                 │
│           ┌────────────────────┼─────────────────────┐                       │
│  ┌────────▼────────┐  ┌────────▼─────────┐  ┌───────▼────────┐              │
│  │ ExtensionBase   │  │ ProxiedSingleton │  │ Adapter APIs   │              │
│  │ (your code)     │  │ (remote proxies) │  │ (RPC services) │              │
│  └─────────────────┘  └──────────────────┘  └────────────────┘              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## File Reference

### Core Files (`pyisolate/_internal/`)

| File | Purpose |
|------|---------|
| `host.py` | **Extension manager**. Creates venv, launches sandboxed process, sets up RPC |
| `rpc_protocol.py` | **AsyncRPC engine**. Request/response dispatch, ProxiedSingleton pattern |
| `rpc_transports.py` | **Transport layer**. JSONSocketTransport (JSON-RPC over sockets) |
| `rpc_serialization.py` | **Serialization helpers**. Type wrappers, _prepare_for_rpc, _tensor_to_cuda |
| `tensor_serializer.py` | **Zero-copy tensors**. The secret sauce - torch.multiprocessing.reductions |
| `sandbox.py` | **Bwrap command builder**. Deny-by-default filesystem, GPU passthrough |
| `uds_client.py` | **Child entrypoint**. Launched as `python -m pyisolate._internal.uds_client` |
| `bootstrap.py` | **Child bootstrap**. Applies host snapshot, reconstructs sys.path |
| `serialization_registry.py` | **Custom serializers**. Plugin-registered type handlers |

### Public API (`pyisolate/`)

| File | Purpose |
|------|---------|
| `interfaces.py` | **IsolationAdapter protocol**. Contract for application adapters |
| `shared.py` | **ExtensionBase**. Base class for isolated code |
| `config.py` | **ExtensionConfig**. Configuration schema |
| `host.py` | **Public Extension class**. Main entry point for creating isolated extensions |

---

## JSON-RPC Protocol

PyIsolate uses JSON-RPC over Unix Domain Sockets instead of pickle to prevent **deserialization attacks** from sandboxed code. A malicious child process cannot escape the sandbox via crafted pickle payloads.

### Message Format

All messages are length-prefixed JSON:

```
┌──────────────┬─────────────────────────────────────┐
│ 4 bytes (BE) │ JSON payload (UTF-8)                │
│ message len  │                                     │
└──────────────┴─────────────────────────────────────┘
```

### Message Types

```python
# Request (host → child or child → host)
{
    "kind": "call",
    "object_id": "extension",       # Target object ID
    "call_id": 42,                  # Request correlation ID
    "parent_call_id": null,         # For nested calls
    "method": "execute",            # Method name
    "args": [...],                  # Positional args (JSON)
    "kwargs": {...}                 # Keyword args (JSON)
}

# Callback (reverse RPC)
{
    "kind": "callback",
    "callback_id": "uuid-...",
    "call_id": 43,
    "parent_call_id": 42,
    "args": [...],
    "kwargs": {...}
}

# Response
{
    "kind": "response",
    "call_id": 42,
    "result": {...},                # Serialized result
    "error": null                   # Or error string
}
```

### Custom Type Serialization

Non-JSON types are serialized via `SerializerRegistry`:

```python
# Registration (in adapter)
registry.register(
    "ModelPatcher",
    serialize_model_patcher,    # obj → dict with __type__
    deserialize_model_patcher   # dict → proxy or real object
)

# Serialized form
{
    "__type__": "ModelPatcher",
    "model_id": "uuid-...",
    # ... other fields
}
```

---

## Bubblewrap Sandbox

On Linux, child processes run inside [bubblewrap](https://github.com/containers/bubblewrap) sandboxes with **deny-by-default** filesystem access.

### Security Properties

| Property | Implementation |
|----------|----------------|
| **Filesystem isolation** | Explicit allow-list only (no `/home`, `/root`, `/etc`) |
| **Read-only venv** | Prevents persistent malware infection |
| **Network isolation** | `--unshare-net` by default |
| **User namespace** | Unprivileged execution via `--unshare-user` |
| **PID namespace** | Process isolation via `--unshare-pid` |
| **Die with parent** | `--die-with-parent` prevents orphan processes |

### Default Allow-List

```python
SANDBOX_SYSTEM_PATHS = [
    "/usr",                    # System binaries/libraries
    "/lib", "/lib64", "/lib32",# Core libraries
    "/bin", "/sbin",           # Essential binaries
    "/etc/ssl",                # SSL certificates
    "/etc/resolv.conf",        # DNS (if network enabled)
    # ... (see sandbox.py for full list)
]
```

### GPU Passthrough

When `allow_gpu=True`:

```python
GPU_PASSTHROUGH_PATTERNS = [
    "nvidia*",          # GPU devices
    "nvidiactl",        # Control device
    "nvidia-uvm",       # Unified memory
    "nvidia-uvm-tools", # UVM tools
    "dri",              # Direct Rendering Infrastructure
]
```

### Shared Memory Requirement

`/dev/shm` **must be shared** between host and child for zero-copy tensor transfer:

```python
cmd.extend(["--bind", "/dev/shm", "/dev/shm"])
```

This is a documented security trade-off - shared memory enables potential side-channel attacks, but is unavoidable for performant tensor IPC.

### Bwrap Command Example

```bash
bwrap \
  --unshare-user --unshare-pid --unshare-net \
  --new-session --die-with-parent \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind /usr /usr \
  --ro-bind /lib /lib \
  --ro-bind /path/to/venv /path/to/venv \
  --ro-bind /path/to/module /path/to/module \
  --bind /dev/shm /dev/shm \
  --dev-bind /dev/nvidia0 /dev/nvidia0 \
  --setenv PYISOLATE_UDS_ADDRESS /tmp/ext_xxx.sock \
  --setenv PYISOLATE_CHILD 1 \
  /path/to/venv/bin/python -m pyisolate._internal.uds_client
```

---

## Zero-Copy Tensor Transfer (The Secret Sauce)

PyIsolate achieves zero-copy tensor transfer by using **undocumented PyTorch multiprocessing primitives** from `torch.multiprocessing.reductions`. These functions are internal to PyTorch and not documented anywhere publicly.

### Why This Matters

Without zero-copy, transferring a 2GB tensor requires:
1. Serialize tensor to bytes (~2GB memory allocation)
2. Send bytes over socket (~2GB network I/O)
3. Deserialize into new tensor (~2GB memory allocation)

**Total overhead: 6GB memory, full data copy**

With zero-copy via shared memory/CUDA IPC:
1. Share memory handle (a few bytes)
2. Remote process maps same memory

**Total overhead: ~0 bytes, no data copy**

### CPU Tensors: Shared Memory via `/dev/shm`

CPU tensors use PyTorch's `file_system` sharing strategy, which creates files in `/dev/shm` (tmpfs).

#### Serialization (`tensor_serializer.py:129-184`)

```python
def _serialize_cpu_tensor(t: torch.Tensor) -> dict[str, Any]:
    # Ensure tensor is in shared memory
    if not t.is_shared():
        t.share_memory_()

    # Get the underlying storage
    storage = t.untyped_storage()

    # Use PyTorch's internal reducer
    sfunc, sargs = reductions.reduce_storage(storage)

    # sfunc is rebuild_storage_filename
    # sargs is (cls, manager_path, storage_key, size)
    return {
        "__type__": "TensorRef",
        "device": "cpu",
        "strategy": "file_system",
        "manager_path": sargs[1].decode("utf-8"),  # /dev/shm path
        "storage_key": sargs[2].decode("utf-8"),   # Unique key
        "storage_size": sargs[3],
        "dtype": str(t.dtype),
        "tensor_size": list(t.size()),
        "tensor_stride": list(t.stride()),
        "tensor_offset": t.storage_offset(),
        "requires_grad": t.requires_grad,
    }
```

#### Deserialization (`tensor_serializer.py:258-291`)

```python
def _deserialize_legacy_tensor(data: dict[str, Any]) -> torch.Tensor:
    # Rebuild the shared storage from /dev/shm
    rebuilt_storage = reductions.rebuild_storage_filename(
        torch.UntypedStorage,
        data["manager_path"].encode("utf-8"),
        data["storage_key"].encode("utf-8"),
        data["storage_size"]
    )

    # Wrap in typed storage
    typed_storage = torch.storage.TypedStorage(
        wrap_storage=rebuilt_storage,
        dtype=dtype,
        _internal=True
    )

    # Rebuild tensor with metadata
    metadata = (
        data["tensor_offset"],
        tuple(data["tensor_size"]),
        tuple(data["tensor_stride"]),
        data["requires_grad"],
    )
    return reductions.rebuild_tensor(torch.Tensor, typed_storage, metadata)
```

### CUDA Tensors: CUDA IPC with 15 Undocumented Arguments

CUDA tensors use CUDA's Inter-Process Communication (IPC) to share GPU memory handles.

#### The `rebuild_cuda_tensor` Function

This function takes **15 arguments**, none of which are documented:

```python
reductions.rebuild_cuda_tensor(
    cls,                    # 0:  torch.Tensor
    tensor_size,            # 1:  tuple - Tensor dimensions
    tensor_stride,          # 2:  tuple - Memory strides
    tensor_offset,          # 3:  int - Offset into storage
    storage_type,           # 4:  torch.storage.TypedStorage
    dtype,                  # 5:  torch.dtype
    device_idx,             # 6:  int - CUDA device index (NOT torch.device!)
    handle,                 # 7:  bytes - CUDA IPC memory handle
    storage_size,           # 8:  int - Size of underlying storage
    storage_offset,         # 9:  int - Offset within storage
    requires_grad,          # 10: bool - Gradient tracking
    ref_counter_handle,     # 11: bytes - Shared reference counter handle
    ref_counter_offset,     # 12: int - Offset into ref counter
    event_handle,           # 13: bytes|None - CUDA event for sync
    event_sync_required     # 14: bool - Whether to sync on event
)
```

#### Argument Documentation

| Arg # | Name | Type | Description |
|-------|------|------|-------------|
| 0 | `cls` | `type` | The tensor class (always `torch.Tensor`) |
| 1 | `tensor_size` | `tuple[int, ...]` | Shape of the tensor (e.g., `(3, 224, 224)`) |
| 2 | `tensor_stride` | `tuple[int, ...]` | Memory strides for each dimension |
| 3 | `tensor_offset` | `int` | Element offset from start of storage |
| 4 | `storage_type` | `type` | Storage wrapper class (`torch.storage.TypedStorage`) |
| 5 | `dtype` | `torch.dtype` | Data type (e.g., `torch.float32`) |
| 6 | `device_idx` | `int` | CUDA device index (0, 1, ...). **Must be int, not torch.device** |
| 7 | `handle` | `bytes` | CUDA IPC memory handle from `cudaIpcGetMemHandle()` |
| 8 | `storage_size` | `int` | Total size of the storage in elements |
| 9 | `storage_offset` | `int` | Byte offset within the storage allocation |
| 10 | `requires_grad` | `bool` | Whether tensor tracks gradients |
| 11 | `ref_counter_handle` | `bytes` | Shared memory handle for cross-process reference counting |
| 12 | `ref_counter_offset` | `int` | Offset into the reference counter shared memory |
| 13 | `event_handle` | `bytes \| None` | CUDA event handle for synchronization (or None) |
| 14 | `event_sync_required` | `bool` | If True, receiver must sync on event before accessing |

#### Serialization (`tensor_serializer.py:187-237`)

```python
def _serialize_cuda_tensor(t: torch.Tensor) -> dict[str, Any]:
    try:
        func, args = reductions.reduce_tensor(t)
    except RuntimeError as e:
        if "received from another process" in str(e):
            # Tensor already from IPC - must clone
            t = t.clone()
            func, args = reductions.reduce_tensor(t)
        else:
            raise

    # Keep tensor alive until remote opens handle
    _tensor_keeper.keep(t)

    # args has 15 elements - serialize for JSON transport
    return {
        "__type__": "TensorRef",
        "device": "cuda",
        "device_idx": args[6],              # int device index
        "tensor_size": list(args[1]),
        "tensor_stride": list(args[2]),
        "tensor_offset": args[3],
        "dtype": str(args[5]),
        "handle": base64.b64encode(args[7]).decode("ascii"),
        "storage_size": args[8],
        "storage_offset": args[9],
        "requires_grad": args[10],
        "ref_counter_handle": base64.b64encode(args[11]).decode("ascii"),
        "ref_counter_offset": args[12],
        "event_handle": base64.b64encode(args[13]).decode("ascii") if args[13] else None,
        "event_sync_required": args[14],
    }
```

#### Deserialization (`tensor_serializer.py:293-316`)

```python
# Decode handles from base64
handle = base64.b64decode(data["handle"])
ref_counter_handle = base64.b64decode(data["ref_counter_handle"])
event_handle = base64.b64decode(data["event_handle"]) if data["event_handle"] else None

# Reconstruct CUDA tensor
cuda_tensor = reductions.rebuild_cuda_tensor(
    torch.Tensor,
    tuple(data["tensor_size"]),
    tuple(data["tensor_stride"]),
    data["tensor_offset"],
    torch.storage.TypedStorage,
    dtype,
    data["device_idx"],          # int, NOT torch.device
    handle,
    data["storage_size"],
    data["storage_offset"],
    data["requires_grad"],
    ref_counter_handle,
    data["ref_counter_offset"],
    event_handle,
    data["event_sync_required"],
)
```

### TensorKeeper: Preventing Premature GC

A critical race condition exists: the host might garbage-collect a tensor before the child opens the shared memory handle. `TensorKeeper` maintains strong references for a retention window:

```python
class TensorKeeper:
    def __init__(self, retention_seconds: float = 30.0):
        self._keeper: collections.deque = collections.deque()

    def keep(self, t: torch.Tensor) -> None:
        now = time.time()
        self._keeper.append((now, t))
        # Cleanup expired entries
        while self._keeper and now - self._keeper[0][0] > self.retention_seconds:
            self._keeper.popleft()
```

---

## Extension Lifecycle

### Host Side (`host.py`)

```python
# 1. Create Extension
ext = Extension(
    module_path="/path/to/custom_node",
    extension_type=MyExtension,
    config={
        "name": "my-extension",
        "dependencies": ["numpy>=1.20"],
        "share_torch": True,
        "share_cuda_ipc": True,
    },
    venv_root_path="/path/to/venvs"
)

# 2. Start Process
ext.ensure_process_started()
#    - Creates isolated venv
#    - Installs dependencies
#    - Launches bwrap subprocess
#    - Establishes RPC connection

# 3. Get Proxy
proxy = ext.get_proxy()

# 4. Call Remote Methods
result = await proxy.execute(tensor_input)

# 5. Cleanup
ext.stop()
```

### Child Side (`uds_client.py`)

```python
# Entry: python -m pyisolate._internal.uds_client

# 1. Connect to host via UDS
client_sock.connect(os.environ["PYISOLATE_UDS_ADDRESS"])
transport = JSONSocketTransport(client_sock)

# 2. Receive bootstrap data
bootstrap_data = transport.recv()

# 3. Apply host snapshot (sys.path, adapter)
bootstrap_child()

# 4. Create extension instance
extension = extension_type()
extension._initialize_rpc(rpc)

# 5. Load module
module_spec.loader.exec_module(module)
await extension.on_module_loaded(module)

# 6. Run RPC loop until stopped
await rpc.run_until_stopped()
```

---

## ProxiedSingleton Pattern

`ProxiedSingleton` enables transparent RPC proxying for service objects:

```python
class ModelRegistry(ProxiedSingleton):
    """Host-side registry; child gets proxy."""

    async def get_model(self, model_id: str) -> ModelRef:
        return self._models[model_id]

    async def register_model(self, model: Any) -> str:
        model_id = str(uuid.uuid4())
        self._models[model_id] = model
        return model_id

# Host side: registers real instance
registry = ModelRegistry()
registry._register(rpc)

# Child side: gets RPC proxy
ModelRegistry.use_remote(rpc)
proxy = ModelRegistry()  # Returns proxy, not real instance
model_ref = await proxy.get_model("uuid-...")  # RPC call
```

---

## Adapter Integration

Applications integrate via `IsolationAdapter`:

```python
class ComfyUIAdapter:
    @property
    def identifier(self) -> str:
        return "comfyui"

    def register_serializers(self, registry):
        registry.register("ModelPatcher", serialize_mp, deserialize_mp)
        registry.register("CLIP", serialize_clip, deserialize_clip)

    def provide_rpc_services(self) -> list[type[ProxiedSingleton]]:
        return [ModelRegistry, CLIPRegistry, VAERegistry]

    def get_sandbox_system_paths(self) -> list[str]:
        return ["/path/to/comfyui"]
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PYISOLATE_CHILD` | Set to `"1"` in child processes |
| `PYISOLATE_UDS_ADDRESS` | Unix socket path or `tcp://host:port` |
| `PYISOLATE_ENABLE_CUDA_IPC` | Set to `"1"` to enable CUDA IPC |
| `PYISOLATE_HOST_SNAPSHOT` | JSON snapshot of host environment |
| `PYISOLATE_DEBUG_RPC` | Set to `"1"` for verbose RPC logging |

---

## Quick Reference: Key Files to Read

| Priority | File | Why |
|----------|------|-----|
| 1 | `_internal/tensor_serializer.py` | Zero-copy tensor magic |
| 2 | `_internal/rpc_protocol.py` | AsyncRPC engine, ProxiedSingleton |
| 3 | `_internal/rpc_transports.py` | JSONSocketTransport, no-pickle |
| 4 | `_internal/sandbox.py` | Bwrap command construction |
| 5 | `_internal/host.py` | Extension lifecycle management |
| 6 | `_internal/uds_client.py` | Child process entrypoint |
| 7 | `interfaces.py` | IsolationAdapter protocol |
| 8 | `shared.py` | ExtensionBase |
