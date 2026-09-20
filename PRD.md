# Again ? Product Requirements Document

**Promise:** Paste an error. Recover what you tried. Take the next step.

**Tagline:** Stop repeating failed fixes.

**Build snapshot:** deadline MVP specification aligned to the current implementation contract. Final acceptance observations and deployment links are tracked in [SUBMISSION_READY.md](SUBMISSION_READY.md); pending checks are not represented as passed.

## User and problem

A solo developer repeatedly encounters failures whose useful context is scattered across terminal output and old conversations. Similar error strings hide different stages and conditions. A fresh assistant can recommend an already failed attempt or confuse a partial repair with a completed resolution.

Again makes those prior outcomes available at the moment of troubleshooting. It remembers what was tried, checks whether the current conditions fit, and shows one next step with evidence.

## Required experience

The first screen has a paste box, **Recall a fix**, **Try a real incident**, and a live readiness indicator. It needs no judge login. Near-black green, warm white and restrained lime accents keep the action and evidence readable. Keyboard operation, visible focus and a narrow-screen layout are required. Outcome badges use words as well as color.

After recall, show:

- **Next step:** one recorded action, one clarification, or an explicit no-applicable-memory result.
- **What matches:** the current stage and conditions supported by retrieved evidence.
- **What was already tried:** failed actions actually recorded for those conditions.
- **Evidence:** clickable excerpts with their source labels and outcome status.
- **Live details:** actual native query timing and retrieved IDs, API time and browser round-trip time in an expandable panel.

Example buttons only populate the form. Genuine Moss retrieval must run when the user submits with memory enabled.

## Acceptance cases

| Case | Required behavior |
|---|---|
| Elevated helper-launch failure | Retrieve the recorded `unelevated_worker_ready` case, recognize that administrator preflight passed, and avoid another elevation retry as the remedy. |
| Non-admin preflight failure | Retrieve the different controller-token case and propose checking/elevating only the separate controller. |
| Ambiguous ?Access is denied? | Ask which stage failed; do not infer an applicable remedy from similarity alone. |
| Unrelated input | Show no applicable memory or relevant evidence with an explicit unresolved applicability question. |
| Previous failure | Show the actual failed action and its outcome; do not invent prior attempts. |
| Partial repair | Say that ordinary-worker startup was repaired while the later trace remained unresolved. |
| Teach then paraphrase | Index a user-reported outcome through genuine Moss and recall it in the same visitor session with different wording. |
| Visitor separation | A second visitor cannot retrieve or inspect the first visitor's additions. |
| Forget | Remove the current visitor's taught records from the private index and local store. |
| Memory off | Do not invoke retrieval; say that prior history is unavailable. |

Tests must exercise these actual critical flows. This app cannot inherit research test counts or inference benchmarks.

## Retrieval and applicability

Moss `moss-minilm` provides built-in text embeddings and live incident retrieval. Seven public-safe historical records are immutable seeds. The separate fictional teaching template is not pre-indexed as a verified incident. Each incident contains a stage, current-condition requirements, observations, recorded failed actions, one next step, limitations and source excerpts.

A bounded, explicit policy examines records returned by Moss. Data-defined stage aliases and condition signals establish applicability; missing or contradictory facts lead to clarification. Explicit current stage takes precedence over inferred wording. A vector score is a retrieval signal, not a calibrated probability that a remedy is correct. The policy does not return hardcoded answers for example-button text.

Resolved-in-recorded-environment, diagnosed, partially resolved, unresolved and user-reported are distinct outcomes. An unchanged error in an already elevated controller is not evidence that elevation failed. A startup timeout does not prove that a UAC prompt was refused or even visible.

## Scope, limits and privacy

Included: sanitized seeds, free-text recall, recorded attempts, source excerpts, live retrieval inspection, visitor-isolated teaching, forgetting, and memory on/off. A generative model is not a deployment dependency.

Excluded: command execution, automatic repair, uploads, accounts, integrations, general chat, training, new inference experiments, tracing, or claims of SSD/inference acceleration.

Public-demo input goes to its server. Self-hosting runs application processing on the user's host; Moss startup can authenticate or download a model. No full-offline claim is made. New records are session-local RAM state with a 60-minute expiry, five-addition limit and a maximum of 100 visitor sessions. They do not persist across restarts. The app does not log pasted query text.

The API bounds request bodies, text lengths and queued work. These measures keep a small public demonstration manageable; they are not a claim of production security or comprehensive debugging intelligence.

## Success and shipping gate

Verify at least three paraphrases, stage disambiguation, ambiguity, unrelated input, genuine teach/recall, visitor separation, and memory-off behavior. Record the actual shipped build's query/API/browser timings, readiness and retrieved incident IDs. Do not invent a latency target or optimize around a scripted answer.

Submission requires a working public agent URL, standalone source repository, this PRD, the architecture image and a real demonstration video. A temporary tunnel must be disclosed and kept alive. Freeze features thirty minutes before the submission deadline, then prioritize working links and the recording.
