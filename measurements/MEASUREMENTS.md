# Again measurements

The repaired Render Docker/Linux deployment passed **14/14 real API checks** on 20 September 2026 at 16:16 UTC. The source tested was [commit `99a098b`](https://github.com/AngRoy/again/tree/99a098b99733a2a99511b1407410fd9eaf02a1d8); later documentation/evidence commits do not imply another deployment. This is a small functional diagnostic, not a throughput benchmark or a broad debugging-accuracy evaluation.

## What passed

[Live evidence](live_checks.json) contains the actual responses, native-returned IDs, source scopes, states and times. It verifies the main worker-launch incident, distinct administrator-preflight stage, three paraphrases, ambiguous input, unrelated input, memory off, genuine indexing of a fictional note, recalling that note in different words, separation of a second visitor, unrelated input after teaching, and forgetting followed by a requery.

[47 automated app tests](app_tests.xml) passed with zero failures or errors. Those tests use isolated native fakes to exercise policy, bounds, ownership, expiry and cancellation; they do not replace the real Moss API run. No earlier research test totals or model-throughput measurements are counted here.

## Observed latency

All values below are milliseconds. Retrieval wraps real native query calls, including local text embedding and small result-assembly work. API time also includes the application's queue and policy work. HTTP round trip is measured by the validation client; it is not the browser's visible timer.

| Retrieval scope | Native calls/request | Samples | Retrieval median | Retrieval min-max | API median | HTTP median |
|---|---:|---:|---:|---:|---:|---:|
| Seed index only | 1 | 10 | 8.342 | 7.200-84.098 | 8.913 | 251.623 |
| Seed + visitor indexes | 2 | 2 | 27.530 | 12.776-42.285 | 28.416 | 452.931 |

The first checked seed-only request was also the slowest at 84.098 ms retrieval / 91.061 ms API / 763.573 ms HTTP. Its cause was not isolated. The two private-scope observations are too few for a latency distribution or percentile claim. Do not present their combined interval as the cost of one query. Native scores from separate sessions are not globally calibrated or converted to probabilities.

The fictional teaching request measured 282.242 ms indexing and 282.493 ms API time. Memory off made zero native queries and reported 0 ms retrieval; its client round trip was still 233.468 ms. These are individual observations, not promised service levels.

The validated build reported **11,049.379 ms application startup-to-ready**, including session initialization, indexing and a real warm query. The earlier initial deployment reported 12,399.906 ms in [first-readiness evidence](render_readiness.json). Neither is a measurement of a Render build, platform wake-up, or repeated cold starts.

Provider memory samples and deployment identity are recorded separately in [Render runtime evidence](render_runtime.json). The maximum of the two reported samples was 225,140,740 bytes, about 214.7 MiB. This is the provider's memory metric, not a measured RSS value or a bound on peak memory.

## Initial failure and repair

The preserved [initial API run](live_checks_initial.json) passed 11 of 13 checks. Visitor recall failed because the application passed shorthand metadata filtering that the real SDK rejected. The repair uses Moss's native `$and` / `field` / `$eq` filter, followed by an ownership check before any ID or excerpt reaches the response. The final live run above verifies the repaired path.

The [initial browser run](../tests/live_artifacts/live_ui_initial_failure.json) also found that the supplied `administrator_preflight says false` wording was not recognized. A data-defined signal now recognizes that canonical field; the final browser check and recording use the default example without adding conditions. The earlier explicit-condition workaround is not the final acceptance result.

A separate code review reproduced a canceled teaching operation that inserted a document before losing ownership bookkeeping. The repair shields the complete native mutation and bookkeeping transaction through repeated cancellation, validates the insertion count, and retains cleanup ownership for failed rollbacks. Focused regression tests cover this; it is not claimed as a real production incident.

## Reproduce

From the standalone repository root, install the app's development requirements into a virtual environment, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe scripts/check_live.py --base-url https://again-fl36.onrender.com --output measurements/live_checks_reproduced.json
```

The live checker uses only public seed queries and a clearly fictional teaching record in its own visitor session. It forgets that record after verification. Wait for `/api/ready` to return HTTP 200 before running it. To test a local instance, substitute `http://127.0.0.1:7860`. On Linux, use `.venv/bin/python`.

The [final default-input browser run](../tests/live_final_artifacts/live_ui_check.json) passed six checks with five real recall requests and no JavaScript errors, including the default preflight example and a 390-pixel mobile view. One desktop request visibly reported 14.1 ms retrieval, 14.7 ms API and 267.0 ms browser round trip. That is one browser observation, not the HTTP-client table or a browser latency distribution.

The [real recording](../demo/demo_recording.json) contains five API responses: lead recall, different preflight stage, memory off, fictional teaching and a paraphrase that retrieves the newly indexed ID. The [response evidence](../demo/demo_api_evidence.json) preserves that distinction. The original WebM is silent and captioned, 93.0 seconds at 1440 x 1000; [playback verification](../demo/video_validation.json) decoded the actual file at five asserted timestamps without recompression or retiming. The later narrated MP4 adds synthesized spoken explanation; original recording measurements and response evidence remain unchanged. See [submission links](../SUBMISSION_READY.md).

## Limits

Only seven historical incidents are seeded. Stage and fact checks use explicit patterns and can miss paraphrases or nuanced negation. Visitor notes use an additional conservative condition-word/technical-identifier check and always remain user-reported. The public app is a bounded anonymous demonstration with session limits, not authenticated production tenancy. Render Free may sleep after 15 idle minutes and can restart; visitor RAM is then lost. Startup/authentication, downloads and SDK usage telemetry prevent a claim of complete offline or network-silent operation.
