# Verified CPU repair results

**All six larger faulty programs pass every check in this suite. Both correct-code controls are unchanged and also pass.**

Inputs contain 179–210 physical lines, 11–15 functions and 7–8 simultaneous faults each (43 faults total). The nine-line toy examples are not used as acceptance evidence here.

| Program | Input lines | Injected faults | Visible + boundary | Original evaluation | Fresh seed 2402 | Final seed 2403 | Total per compiler |
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

The first search stage reached 6/6 and 144/144 original evaluation executions, but the additional cache eviction tests exposed unreclaimed pool slots. That failed intermediate result remains in search_results/quality_audit.json. Helper/caller transactions then fixed the problem. The 12 boundary tests are additional visible development tests, not held-out evidence.

The original evaluation group was inspected during method development; it must not be treated as an untouched holdout. Two 24-scenario groups provide additional verification, with only the final group explicitly generated after source selection. A final, third seed added 24 more scenarios per task, after all repairs were selected. This final set was never used for candidate selection. Python oracles were checked against clean reference implementations outside the repair layer.

This is 100% on the stated constructed suite, not a proof that every arbitrary C program can be repaired. This suite was used during method development; it is not an external benchmark.

## CPU and cost

The model remains Qwen2.5-Coder-7B-Instruct Q4_K_M, four CPU threads, zero GPU layers. This revision reused the 86 previously recorded CPU-model proposals rather than regenerating identical work. New model calls for the search revision: zero. Fresh use of the CLI runs that same small CPU model unless a compatible proposal cache is supplied.

The cached proposal stage originally took 44.5 minutes of CPU-only inference. The two new search stages took 7.10 minutes of additional wall time, using at most four CPU worker processes. These stages are reported separately; the search time does not include the earlier model inference.

## Evidence access and reproduction limits

The pinned public release contains selected benchmark fixtures, model proposal reports, corrected outputs, and summary audits. It does not contain the historical controller scripts and search journals referenced by the original prototype documentation. Do not attempt to rerun `run_search_trial.py`, `verify_perfect_suite.py`, or `audit_perfect_repair.py` from that release alone.

The separate `CompAIler_Historical_Evidence.zip` supplied with the revised manuscript preserves the available historical Python scripts, input fixtures, function-model records, cached-search journals, final verification reports, and manifests unchanged. Its README explains scope and external dependencies. The archive is available at [CompAIler_Historical_Evidence.zip](../CompAIler_Historical_Evidence.zip). The archive was assembled without rerunning experiments.

The installable release can independently revalidate the recorded final sources using the case validation JSONs, or perform a fresh CPU-model repair through the documented CLI. A new repair is a new run, not a replay of historical results. Supplying all 78 validation scenarios to search exposes verification outputs and does not preserve the historical repair-input separation.

## Precise scenario roles

Each `validation_tests.json` contains, in order:

| Python indices | Count | Role |
|---|---:|---|
| 0:4 | 4 | Original visible repair inputs |
| 4:6 | 2 | Adopted boundary/development inputs |
| 6:30 | 24 | Original evaluation checks, examined during development |
| 30:54 | 24 | Additional seed-2402 verification checks |
| 54:78 | 24 | Final seed-2403 checks generated after source selection |

The middle 48 are additional functional verification, not an untouched holdout. The final 24 provide the strongest independent post-selection evidence. All 78 remain part of the reported functional verification, with 624 successful executions per compiler and 1,248 across both compilers.

