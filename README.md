# CompAIler

**CPU-only AI-assisted C repair and compilation.** A local quantized model proposes complete-function repairs. Compiler diagnostics, behavioral tests, expression search, and dependency transactions decide what is accepted. Humans specify intended behavior and validate it with tests; CompAIler emits reviewable corrected source and a compiled artifact only when all supplied tests pass.

## Install

Supported release platform: **Linux x86-64**, Python 3.10–3.12, with approximately 16 GB RAM and at least 8 GB free disk space for installation, model, and work files. Other operating systems can use Docker or WSL2. CPU inference only; no GPU or model API account is needed.

Extract this archive, open a terminal in this directory, and run:

```bash
bash scripts/install-linux.sh
source .venv/bin/activate
compailer model download
```

The installer uses sudo for Debian/Ubuntu packages. It installs Clang/WASI, TinyCC, bubblewrap, Python dependencies, and the local CLI. The model is **Qwen2.5-Coder-7B-Instruct Q4_K_M**, a 4.68 GB download from the official public repository, pinned to a commit and SHA-256. It is not bundled in the ZIP. Model weights are cached in `~/.cache/compailer`; set `COMPAILER_MODEL_DIR` to change that directory. Inference sets `n_gpu_layers=0`.

For manual installation, install the system dependencies listed in the script, then:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
CMAKE_ARGS='-DGGML_CUDA=OFF -DGGML_NATIVE=OFF' python -m pip install llama-cpp-python==0.3.36 --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
compailer doctor
```

The installer tries a CPU wheel and can build on CPU if necessary. A C++ toolchain is included among its prerequisites.

## Compile imperfect C

```bash
compailer examples/sum/program.c \
  --spec examples/sum/intent.txt \
  --tests examples/sum/tests.json \
  --work-dir runs/sum -o sum.wasm
```

Default output is a WASI WebAssembly module. For a native Linux executable using TinyCC (or GCC fallback):

```bash
compailer examples/sum/program.c \
  --spec examples/sum/intent.txt --tests examples/sum/tests.json \
  --backend native --work-dir runs/sum-native -o sum
printf '5\n' | ./sum
```

Native test execution requires working unprivileged bubblewrap namespaces and libseccomp. Restricted containers may disable these; use the default WASI backend or the supplied Docker setup in that case. WASI test execution does not require user namespaces.

The work directory contains `original.c`, `candidate.c`, `input_manifest.json`, and `report.json`, plus model and search traces when repair was needed. A passing result also contains `corrected.c` and `program.wasm` (or native `program`). On failure, the candidate remains available for diagnosis, but no corrected-source or binary success artifact is released. Exit codes: 0 all supplied tests passed; 1 attempted repair failed validation; 2 invalid input, setup, or runtime error. Existing binary output paths are refused to prevent confusion with older builds. Use a fresh work directory for changed inputs or configuration.

Test format:

```json
[
  {"input": "5\n", "output": "15\n"},
  {"input": "0\n", "output": "0\n"}
]
```

Tests compare stdout after stripping leading/trailing whitespace and require exit status zero. They should cover boundaries and intended semantics, not just compiler acceptance. `--extra-tests additional.json` adds further validation/search scenarios. All supplied tests are visible to the repair/search process; do not report them as independent held-out evaluation.

## Engine

1. Check the original program; return passing inputs unchanged.
2. Extract functions and their dependency context using tolerant lexical boundaries.
3. Run the local CPU model on individual complete functions, expanding neighbor context on retries; preserve signatures and already-passing scenarios.
4. Search generic expression changes and model function crossovers.
5. Search transactions involving dependencies and callers.
6. Recompile and rerun every supplied test before releasing corrected C and an artifact.

The model uses 8,192 context tokens, temperature zero, and four CPU threads by default. Set `COMPAILER_THREADS` and `COMPAILER_WORKERS` before launching to configure CPU usage. There is no training, GPU inference, cloud model call, or benchmark-specific source lookup in the runtime.

`--model /path/model.gguf` uses an existing local model. `--proposal-cache directory` is an explicit reproducibility mode: it replays prior model proposals for matching original source and requirement, rather than making fresh model calls. Reports label this mode. It is not enabled in the ordinary CLI or Space.

## Scope and evidence

This initial release supports a restricted single-file console-C subset; see [supported C](docs/SUPPORTED_C.md). It does not repair every possible malformed C file or infer unspecified intent. Test success is not a universal proof of correctness.

The prior constructed benchmark comprised six faulty 179–210-line programs with 43 injected faults, plus two correct controls. The recorded final verification passed 1,248/1,248 executions across TinyCC and GCC/UBSan. That final search reused 86 recorded CPU-model proposals. These are the earlier experiment results, not a claim that this newly packaged WASI release was rerun on an uncached complete suite. See [benchmark evidence](benchmarks/README.md) and [release validation](VALIDATION.md) for the distinction and actual package checks.

## Development and distribution

```bash
python -m pip install '.[test]'
python -m pytest -q
python -m build
```

CI exercises package creation, source guards, WASI execution, failure withholding, and input isolation without downloading model weights. To publish on GitHub, upload this project's contents (including `.github`) to a new repository. Consumers can clone/download it and run the installer. `dist/` contains an installable wheel and source distribution; neither is published to PyPI by this archive.

A Dockerfile is included for an alternative CPU-only CLI environment. A separate complete Hugging Face Space ZIP provides the browser interface.

License: Apache-2.0 for original project code. See [third-party notices](THIRD_PARTY_NOTICES.md).
