# Again

**Stop repeating failed fixes.** Paste an error. Recover what you tried. Take the next step.

Again is a small troubleshooting-memory agent. Genuine Moss text retrieval finds relevant incident memories; an explicit policy checks their stage and conditions before showing one recorded next step, a clarifying question, or no applicable memory. Evidence includes failed attempts and the outcome's actual status.

[Repository](https://github.com/AngRoy/again) | [Product requirements](PRD.md) | [Architecture](ARCHITECTURE.md) | [Demo script](DEMO_AND_SUBMISSION.md) | [Submission status](SUBMISSION_READY.md) | [93-second demo](https://github.com/AngRoy/again/releases/download/v1.0.0/again-demo.webm)

**Live demo:** [again-fl36.onrender.com](https://again-fl36.onrender.com). The Linux cloud service passed 14/14 genuine API checks and 47 automated app tests. The default-input browser flow and the silent captioned video also passed their checks; see [submission status](SUBMISSION_READY.md). Render Free can sleep after 15 idle minutes, so first access may need a platform restart and Moss warmup. [Render Free limits](https://render.com/docs/free)

## Why Again

The same words can describe different failures. If administrator preflight failed, checking the actual token is relevant. If that check already passed and the normal-permission helper cannot launch, another elevation retry repeats the wrong intervention. Again retrieves the relevant history, keeps partial repairs separate from full resolution, and links its next step to readable evidence.

Seven sanitized historical incidents ship with the app. A separate fictional port-mismatch card demonstrates teaching; it is never presented as an independently verified historical incident. Full private reports and research artifacts are not served or included in this repository.

## Run locally

Use Python 3.11 or 3.12 (the cloud container uses 3.11). From this repository's root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env.local
```

Edit `.env.local` locally and enter the two Moss values named in the template. Do not put their values in commands, screenshots, browser input, or commits. Existing nonempty environment values take precedence. Start the app:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 7860
```

Open `http://127.0.0.1:7860`. Readiness requires successful genuine Moss startup and a real warm query. The first start may authenticate and download the embedding model. This application does not depend on Torch, Transformers, a generative LLM, or the earlier inference models.

On Linux, use `.venv/bin/python` for the same commands. The included Dockerfile has built successfully on Render Free, where the real Moss readiness query passed. The initial Windows diagnostic and deployed Linux measurements remain separate observations.

## Use it

1. Choose **Try a real incident**, or paste a short error without secrets.
2. Give the failure stage and current conditions when known. Click **Recall a fix**.
3. Read the next step, previous failed attempts, status and source excerpts. Expand the live timing panel for retrieved IDs and query/API/browser timing.
4. Expand **Make the next time easier** and use **Save to my memory** to store a session-local, explicitly user-reported result. Then describe it differently and recall it again.
5. Use **Clear my additions** to remove that session's additions. Turning memory off performs no retrieval and says that history is unavailable.

Examples only fill the input. They do not select an answer or inject saved search results. The decision policy consumes incident IDs actually returned by Moss.

## Data and privacy

The public demo sends pasted text to its backend. Use sample errors. This is not on-device processing in the browser. Self-hosting keeps application inputs on your own host, subject to Moss authentication, model downloads and SDK usage telemetry; complete offline or network-silent operation is not claimed.

Seed memory is shared and read-only. New outcomes use a separate private Moss index with a mandatory server-generated visitor filter and an ownership check after retrieval. An opaque HttpOnly, SameSite=Lax cookie identifies a visitor; there is no public listing of taught outcomes. Additions are held in RAM, expire after 60 minutes of inactivity, and disappear when the server restarts. At most 100 visitor sessions and five additions per visitor are allowed. Each visitor has a 30-request-per-minute limit. Forget deletes the current visitor's indexed additions. Expired indexed additions are deleted at the next memory operation.

Queries are not logged by application code. Hosting/network infrastructure may have its own operational logs. Credentials stay in server-side environment configuration. Inputs and excerpts are rendered as text; there is no shell, upload, filesystem-browser, or arbitrary-command endpoint.

Input bounds are 4,000 characters for a query, 1,200 for conditions, and a 16 KiB request body. Native operations are serialized with a bounded eight-second queue wait. These are demo limits, not a production abuse-prevention or multi-tenant security certification.

## What the evidence establishes

The deployed [source commit `99a098b`](https://github.com/AngRoy/again/tree/99a098b99733a2a99511b1407410fd9eaf02a1d8) passed 14/14 live API checks, including genuine teaching, visitor separation, deletion and memory off. Separately, 47 automated app tests passed. The ten seed-only requests observed an 8.342 ms median combined retrieval interval; two requests that searched both indexes observed 12.776 and 42.285 ms. These small functional samples include embedding and are not latency guarantees. [Measurements, limitations and reproduction](measurements/MEASUREMENTS.md).

Recall depends on the incident corpus, semantic retrieval, and the supplied conditions. A reported remedy can still be inapplicable. Diagnosed, partially resolved, unresolved and user-reported outcomes retain those labels. Again proposes a next step; it does not execute a fix or diagnose arbitrary errors. Visitor notes also require two meaningful shared condition terms or one specific shared technical identifier after semantic retrieval. This conservative check can miss valid paraphrases; it only enables a condition-check question, never a verified repair claim.

## API

- `POST /api/recall`: query, optional stage/conditions, and `memory_enabled`.
- `POST /api/teach`: symptom, conditions, attempted action, outcome, and `is_synthetic`.
- `POST /api/forget`: remove this visitor's additions.
- `GET /api/health`: public readiness and observed cold-ready time.
- `GET /api/ready`: HTTP 200 only after a real warm query; otherwise HTTP 503.
- `GET /api/examples`: sanitized sample input text.

All UI requests use ordinary JSON. The combined Moss retrieval interval includes local embedding and result assembly; one or two actual queries are counted. API time and browser round-trip time are separate. No artificial delay or recorded timing is presented as a live result.
