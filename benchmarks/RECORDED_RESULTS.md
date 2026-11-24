# Verified CPU repair results

**All six larger faulty programs pass every check in this suite. Both correct-code controls are unchanged and also pass.**

Inputs contain 179–210 physical lines, 11–15 functions and 7–8 simultaneous faults each (43 faults total). The nine-line toy examples are not used as acceptance evidence here.

| Program | Input lines | Injected faults | Training + boundary | Original held-out | Fresh seed 2402 | Final seed 2403 | Total per compiler |
|---|---:|---:|---:|---:|---:|---:|---:|
| inventory | 185 | 8 | 6/6 | 24/24 | 24/24 | 24/24 | 78/78 |
| gradebook | 179 | 7 | 6/6 | 24/24 | 24/24 | 24/24 | 78/78 |
| lru_cache | 210 | 7 | 6/6 | 24/24 | 24/24 | 24/24 | 78/78 |
| graph_engine | 205 | 7 | 6/6 | 24/24 | 24/24 | 24/24 | 78/78 |
| expression_parser | 185 | 7 | 6/6 | 24/24 | 24/24 | 24/24 | 78/78 |
| sparse_matrix | 201 | 7 | 6/6 | 24/24 | 24/24 | 24/24 | 78/78 |
| inventory_correct_control | 185 | 0 | 6/6 | 24/24 | 24/24 | 24/24 | 78/78 |
| expression_parser_correct_control | 185 | 0 | 6/6 | 24/24 | 24/24 | 24/24 | 78/78 |

Final checks: **624/624 per compiler**, using TinyCC and GCC -O2 with undefined-behavior sanitization. Across both compilers: **1248/1248 executions passed**.

The six faulty applications account for 468 program/scenario pairs per compiler; controls add 156. Inputs intentionally repeat between each clean control and its corresponding faulty task, so execution counts are not counts of globally distinct inputs.

## Method

The small CPU model proposes complete functions. The revised deterministic layer retains those proposals and the original function versions, explores general C operator/field/coefficient edits and function substitutions, compiles candidates, and ranks their visible-test behavior. It does not replace output strings with expected answers or insert values extracted from expected output.

A second search stage treats a helper and its callers as one transaction. It can restore caller implementations while selecting a compatible model-proposed helper, then test a local field edit. This resolves coupled state updates that independent function replacements missed.

The repair API receives only input source, candidate functions, compiler and visible tests. It never receives clean reference C or mutation descriptions. No final C changes were manually written. The source audit reconstructs every result from recorded CPU-model output and search transformations and checks that function interfaces remain unchanged.

The first search stage reached 6/6 and 144/144 original held-out executions, but the additional cache eviction tests exposed unreclaimed pool slots. That failed intermediate result remains in search_results/quality_audit.json. Helper/caller transactions then fixed the problem. The 12 boundary tests are additional visible development tests, not held-out evidence.

After repair, 24 original held-out and 24 separately seeded scenarios per task were evaluated without feeding them back into search. A final, third seed added 24 more scenarios per task, after all repairs were selected. This final set was never used for candidate selection. Python oracles were checked against clean reference implementations outside the repair layer.

This is 100% on the stated constructed suite, not a proof that every arbitrary C program can be repaired. This suite was used during method development; it is not an external benchmark.

## CPU and cost

The model remains Qwen2.5-Coder-7B-Instruct Q4_K_M, four CPU threads, zero GPU layers. This revision reused the 86 previously recorded CPU-model proposals rather than regenerating identical work. New model calls for the search revision: zero. Fresh use of the CLI runs that same small CPU model unless a compatible proposal cache is supplied.

The cached proposal stage originally took 44.5 minutes of CPU-only inference. The two new search stages took 7.10 minutes of additional wall time, using at most four CPU worker processes. These stages are reported separately; the search time does not include the earlier model inference.

## Use and reproduce

`ai_compile_verified.py` is the current entry point. It requires behavioral tests. It publishes output_directory/program only after every supplied check passes and returns a nonzero status on failure. Source and failure reports are retained for review.

```bash
python ai_compile_verified.py source.c \
  --requirement-file requirement.txt --tests visible_tests.json \
  --extra-tests boundary_tests.json --output result
```

To reuse a compatible prior run, add `--llm-cache function_results/<program>`. The source and requirement must match. The optional extra tests are supplied only to the final dependency search and release gate.

For this archived trial, run `run_search_trial.py`, `build_quality_checks.py`, `run_transaction_trial.py`, `verify_perfect_suite.py`, `audit_perfect_repair.py`, and `report_verified_results.py` in order. Model, compiler and sandbox dependencies are described in README.md; weights are excluded from the archive.

Controllers and input fixture hashes are retained in stage manifests. The transaction manifest’s base-selection description mentions the four original scenarios; its extra_visible_tests field and actual six-test reports record the two boundary checks as well. The old manifest is retained unchanged as historical evidence.

Final sources and gated executables are in transaction_results/<program>/. Full compiler output, every selected transformation, candidate evaluation journals, rejected intermediate results and independent verification reports remain included.
