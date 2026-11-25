# Subsequent live validation — 24 November 2026

This is a retrospective documentation record of the previously observed live-service checks described in the manuscript. It is not a newly executed experiment or an original timestamped server log. A complete raw live-job trace is not included with this retrospective documentation record.

- Service: https://huggingface.co/spaces/Angshul/CompAIler
- Tested live source revision: `637bfbf4e18efaaa47bc79bf0a0c14e1fd574b93`.
- Corresponding inspected GitHub release source/distributions: `5678ce91c1d3514c494637851924a555966e97c8`, software version 0.1.0.
- CPU Basic; Docker SDK, Gradio UI; CPU model inference.
- Three-function array program with three logic errors: omitted final sum element, zero-initialized maximum, and reversed maximum comparison.
- Observed fresh repair: four new CPU model calls, 9/9 supplied scenarios passing, approximately seven minutes. This is one latency observation, not a repeated performance benchmark.
- Returned source checked locally on 100 further seeded arrays (seed 20261124, lengths 1–32, signed 32-bit values); 100/100 passed against Python sum/max oracles. This was verification of the returned source, not another model repair.
- Corrected source resubmitted: unchanged, 9/9 passing, zero model calls.
- Corrected-source and JSON-report downloads were produced.
- Earlier deployment failure: linker thread creation reported `Resource temporarily unavailable`. Tested runtime uses `-Wl,--threads=1` and disables Wasmtime parallel compilation.

`VALIDATION.md` preserves earlier package checks. Its previous statement about untested live deployment applied before this subsequent service check. Local Docker image building was not thereby established. Historical native large-program repair results, package/WASI revalidation, and this separate live example must remain distinct.

