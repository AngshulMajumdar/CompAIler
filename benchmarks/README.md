# Recorded benchmark and reproduction inputs

These are the earlier prototype's six multi-error cases and cached CPU proposals. `summary.json` records the final eight-case, two-compiler verification (including two correct controls). `audit.json` and `RECORDED_RESULTS.md` document its provenance. No model weights, executable binaries, or hidden reference-source dependency is included.

Each `cases/<name>` contains faulty input, intent, visible repair tests, the 78 final verification tests, and the previously validated corrected source. `proposals/<name>` contains the original input, model-stage output, and trace of earlier CPU model replies. These files are explicit benchmark assets, never automatically consulted by the runtime. The corrected source is for inspection and revalidation only.

Example reproduction using cached model proposals:

```bash
compailer benchmarks/cases/inventory/source.c \
  --spec benchmarks/cases/inventory/requirement.txt \
  --tests benchmarks/cases/inventory/visible_tests.json \
  --extra-tests benchmarks/cases/inventory/validation_tests.json \
  --proposal-cache benchmarks/proposals/inventory \
  --work-dir runs/inventory -o inventory.wasm
```

This command labels cache reuse in its report. Both supplied test files are visible to search; it is not an independent held-out evaluation. For new model inference, omit `--proposal-cache`. The default WASI backend differs from the earlier native TinyCC/GCC environment, so reproduce and report its own results separately. The historical 1,248/1,248 result does not establish correctness on arbitrary programs.
