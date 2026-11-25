# Recorded benchmark and reproduction inputs

These are the prototype's six multi-error cases and cached CPU proposals. `summary.json` records final eight-case, two-compiler verification, including two correct controls. `audit.json` records a historical source audit. See [recorded results](RECORDED_RESULTS.md) for test roles and limitations.

Each `cases/<name>` contains submitted input, intent, visible repair tests, 78 verification scenarios, and the recorded corrected source. `proposals/<name>` contains the original input, model-stage output, and earlier CPU model replies. The runtime does not automatically consult these benchmark assets.

## Revalidate recorded corrected source

```bash
compailer benchmarks/cases/inventory/recorded_corrected.c \
  --spec benchmarks/cases/inventory/requirement.txt \
  --tests benchmarks/cases/inventory/validation_tests.json \
  --work-dir runs/inventory-revalidation -o inventory.wasm
```

This checks the already corrected program using the released WASI backend. A passing original input returns unchanged without model inference. It is source revalidation, not a fresh repair experiment or replication of historical native search timing.

## Fresh repair and cached proposals

Use `source.c` and `visible_tests.json` for a fresh repair. The optional `--proposal-cache benchmarks/proposals/inventory` replays compatible recorded proposals; reports identify cache reuse. All supplied tests, including `--extra-tests`, are visible to search. Supplying the entire 78-scenario file to repair does not preserve an independent verification set. See the five-group ordering in [RECORDED_RESULTS.md](RECORDED_RESULTS.md).

## Frozen historical evidence

Download [CompAIler_Historical_Evidence.zip](../CompAIler_Historical_Evidence.zip). It preserves 466 available historical files unchanged: controllers, input fixtures, proposal records, local/dependency journals, and verification/audit records. `SHA256.json` maps paths relative to `ai_compiler/` to content digests. The archive README distinguishes cached historical evidence from portable fresh-run reproduction and identifies missing external dependencies and historical path assumptions. No experiments were rerun to assemble the archive.

The original pinned release commit `5678ce91c1d3514c494637851924a555966e97c8` omitted these historical scripts and journals; this documentation/evidence update adds them as a separate archive. Model weights and compiler binaries are not bundled. Clean reference sources inside the historical archive are verification oracles, not repair inputs. The prior 1,248/1,248 result applies to the documented constructed suite and does not establish correctness for arbitrary programs.

