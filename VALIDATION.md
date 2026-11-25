# Predeployment package validation — 24 November 2026

Performed on Linux x86-64 with Python 3.12, Clang/LLD 14, Debian Bookworm wasi-libc, Wasmtime 39.0.0, Gradio 5.49.1, and CPU llama-cpp-python 0.3.36.

- Fresh end-to-end CPU inference: included faulty sum program repaired with **three new model calls**, no proposal cache, four behavioral tests passing. Source changed and the validated WASI artifact was released. The model was the previously downloaded official Q4_K_M GGUF, not freshly downloaded for this check.
- Six previously corrected larger benchmark programs: **468/468 scenarios passing on WASI** (78 each). This checks compiler/runtime portability of recorded corrected sources; it is not a new end-to-end repair experiment on those six programs.
- Automated release checks: **17 tests passing**, covering C execution, absence of host filesystem access, fuel exhaustion, output limits, restricted preprocessing, signature preservation, required tests, output-directory isolation, actual subprocess expression-search repair, already-passing input preservation, and withholding successful artifacts on failed validation.
- Native TinyCC compilation and bubblewrap/seccomp execution of the corrected sum example: 4/4 tests passing.
- Gradio application constructed successfully; its real subprocess callback accepted a passing C source, ran compiler/test validation, and returned corrected-source and JSON downloads (4/4 tests).
- Wheel and source distribution built; wheel installed and CLI doctor/compilation exercised in a separate virtual environment. Installer shell syntax checked.

CPU model is loaded lazily and closed before process-pool search. Search workers use fresh spawned processes to avoid inheriting WebAssembly runtime threads. WASI stack is set to 8 MiB so the matrix benchmark's local arrays fit; remaining linear memory is limited to 256 MiB. Unused static helpers are permitted while other enabled warnings remain errors.

The Dockerfiles and Space upload layout are included. Docker is unavailable in this execution environment: **the Docker image and a live Hugging Face deployment had not yet been exercised in this predeployment validation environment**. Full model downloading was not repeated; the pinned upstream model metadata and checksums were verified against the official repository API. No public repository, package index, or Space has been created by preparing these files.

Historical native TinyCC/GCC experimental results are documented separately in `benchmarks/`. They should not be confused with this release's fresh CPU example or WASI source revalidation.

## Subsequent deployment validation

Later on 24 November 2026, the live CPU Basic Space was exercised successfully after the linker/runtime thread fix. This subsequent observation is distinct from the predeployment checks above. See `docs/LIVE_VALIDATION_2026-11-24.md` for outcomes, exact revisions, and evidence limits. The earlier statement concerns its original environment and stage, not the later state of the public service. This documentation update does not imply a local Docker image build was performed.

