# Again - submission status

**Working document. Cloud deployment is healthy; final feature acceptance and the demonstration video are pending.**

| Required item | Current verified status |
|---|---|
| GitHub | [AngRoy/again](https://github.com/AngRoy/again) - standalone app published; final documentation/validation refresh pending. |
| Live agent | [again-fl36.onrender.com](https://again-fl36.onrender.com) - Render Free Docker/Linux; remote native readiness verified. |
| PRD | [PRD.md](PRD.md) - implementation contract drafted; finalize against acceptance checks. |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md), [SVG](architecture.svg), [PNG](architecture.png) - SVG and PNG rendered and visually checked; document aligned to implemented boundaries. |
| Health | Remote `/api/health` and `/api/ready` returned HTTP 200, `ready=true`, seven seed records. |
| Measurements | First deployed cold-ready observation: 12,399.906 ms. [Readiness evidence](measurements/render_readiness.json). Query acceptance/timing table pending. |
| Video | Not recorded or uploaded. [Prepared narration](DEMO_AND_SUBMISSION.md). |

The verified diagnostic uses genuine Moss text embedding/retrieval. Its timing is one observation, not a deployed latency guarantee. The public app must pass recall/paraphrase, stage ambiguity, no-applicable-memory, teach/recall, visitor isolation and memory-off checks before this status becomes ready.

Required human-only completion, if not available to the engineer: record narration, upload a real demonstration video, verify sharing permissions and submit the form. Use the real links above only after they have been verified. Render Free can sleep after 15 idle minutes; verify a fresh recall before recording.

Feature freeze: 17:59 UTC. Submission deadline: 20 September 2026, 18:29 UTC (23:59 IST). Reserve the final thirty minutes for recording, uploads, link checks and submission.
