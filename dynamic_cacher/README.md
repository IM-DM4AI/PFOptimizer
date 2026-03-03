# Dynamic Cache (`dycacher`)

`dycacher` is the runtime inference-context reuse cache used by PFOptimizer.
It targets prediction functions (UDFs) that repeatedly load model artifacts or
build inference sessions across many row-level calls.

## Overview

For each prediction function, `dycacher` binds a dynamic cache composed of:

1. `ML API detector`: identifies framework APIs used for inference-context setup.
2. `Inference context object-store`: caches and reuses setup results by API plus
   runtime arguments.

To automate reuse without user perception, `dycacher` dynamically injects reuse
checking logic into target ML APIs and substitutes the original API at runtime.

When a setup API is called, `dycacher` checks whether the same API call has
already appeared with equivalent arguments. If yes, it returns the cached
context object instead of rebuilding it.

## Design Rationale (from the paper)

### Challenge 1: Diverse UDF code, but limited setup APIs

- User Python code can be complex, but inference setup APIs are usually limited
  and deterministic in major ML frameworks.
- Instead of analyzing the whole UDF statically, `dycacher` only marks and
  intercepts a small set of setup APIs.
- This keeps overhead low while covering common production patterns.

### Challenge 2: Runtime values are required for accurate reuse

- In Python, precise types/values are often ambiguous before execution.
- `dycacher` performs reuse checking exactly at API call time, when concrete
  argument values are available.
- This allows robust cache key construction (for example file handlers passed
  to `pickle.load`).

## Automatic Reuse Procedure

The runtime flow follows the paper algorithm:

1. Python startup initializes an inference-context object store as a hash table.
2. The store is a key-value map conceptually indexed by `called_func` and
   `called_args`, with cached `context` objects as values.
3. Importing `dycacher` installs an import hook (`sys.meta_path`).
4. The ML API detector applies detection rules, injects a reuse callback into
   target APIs, and performs runtime substitution via monkey patching.
5. Whenever a target API is called, the callback looks up the store using:
   - `called_func` comparator (function identity)
   - `called_args` comparator (argument value equivalence)
6. Cache miss path:
   - Execute original API with runtime arguments.
   - Store returned context.
   - Return the newly created context.
7. Cache hit path:
   - Return cached context directly.

## Key and Equality Semantics

- `called_func`: compared by identity (`is`) at the design level; each ML API
  setup function/method is treated as a unique callable target.
- `called_args`: compared by value (`==`) so equivalent runtime values map to
  the same cached context even if argument object references differ.
- File objects: normalized into comparable keys (for example, path-based
  matching in the paper example for `pickle.load`; the current implementation
  also tracks the current file offset).
- ONNX Runtime option objects: design intent is attribute-based equivalence
  across option instances. The implementation wraps `SessionOptions` into a
  comparable object for stable lookup behavior.

## Supported APIs

Current rules are defined in `dycacher/api_rules.py`:

- `pickle.load`
- `joblib.load`
- `onnxruntime.InferenceSession`
- `onnxruntime.SessionOptions` (wrapped for comparable cache keys)
- `xgboost.Booster` and `xgboost.Booster.load_model`
- `lightgbm.Booster`
- `tensorflow.keras.models.load_model`
- `torch.load`

## Installation

From local wheel:

```bash
pip install dynamic_cacher/release/dycacher-0.98.8-py3-none-any.whl
```

Or from source:

```bash
pip install -e dynamic_cacher
```

## Quick Start (Python)

Import `dycacher` before your prediction function imports/uses ML frameworks.

```python
import dycacher

def predict(row):
    import pickle
    import onnxruntime as ort

    with open("scaler.pkl", "rb") as f:
        scaler = pickle.load(f)  # cached after first call

    session = ort.InferenceSession("model.onnx")  # cached after first call
    return session.run(...)
```

Optional cleanup when query execution ends:

```python
dycacher.reset_cache()
```

## Embedded Python (C/C++)

If prediction UDFs are invoked from embedded Python, pre-import `dycacher`
once before loading UDF modules. See:

- `dynamic_cacher/examples/cpp/cpp_import_example.cpp`
- `dynamic_cacher/examples/cpp/cpp_basic_example.cpp`

The `cpp_import_example.cpp` path shows the intended integration point where
cache is enabled before iterative UDF calls.

## Cache Lifecycle APIs

In addition to `reset_cache()`, `dycacher` exposes shared-memory helpers:

- `write_to_shm()`: serialize current cache to shared memory.
- `load_from_shm()`: load cache from shared memory.
- `try_to_load_cache()`: no-op if local cache already exists; otherwise try SHM.
- `close_shm()`: release/unlink shared memory segment.

These APIs are useful when coordinating cache reuse across Python runtimes in
the same host.

## Extending API Rules

Rules are extensible by framework/API pattern:

```python
from dycacher.import_hook import when_imported, reuse_checking

@when_imported("my_framework")
def rule_my_framework(mod):
    mod.load_model = reuse_checking(mod.load_model)
```

This follows the same runtime interception mechanism used by built-in rules.

## Correctness Assumptions

Safe reuse depends on two assumptions from the paper:

1. The setup API is deterministic for equivalent arguments.
2. The returned context object is not semantically mutated by subsequent UDF
   code in a way that invalidates reuse.

If either assumption is violated, disable that API rule or avoid caching for
that path.

## Repository Pointers

- Core hook/runtime logic: `dynamic_cacher/dycacher/import_hook.py`
- Built-in API rules: `dynamic_cacher/dycacher/api_rules.py`
- Comparable argument wrappers: `dynamic_cacher/dycacher/comparable.py`
- Smoke test: `dynamic_cacher/smoke_test.py`
