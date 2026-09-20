# Again - submission ready

**The five requested artifacts are prepared, and the cloud app, real API flow, default-input browser flow and recorded video have passed their checks. Final submission through the owner's form remains separate.**

## Submission links

1. **Live agent:** https://again-fl36.onrender.com
2. **Source repository:** https://github.com/AngRoy/again
3. **PRD:** https://github.com/AngRoy/again/blob/main/PRD.md
4. **Architecture image:** https://github.com/AngRoy/again/blob/main/architecture.png
5. **Video:** [Download the narrated MP4](https://github.com/AngRoy/again/releases/download/v1.0.0/again-demo-narrated.mp4). The [original silent 93-second WebM](https://github.com/AngRoy/again/releases/download/v1.0.0/again-demo.webm) remains available.

The primary video is a **narrated live walkthrough** with synthesized spoken audio over the real browser recording. The original silent WebM is retained: real public-browser requests, no mocked responses, no edited latency or playback retiming. If the submission form requires a separate video host, upload this verified file there and use the resulting viewable link. A local file or an unverified upload is not a submitted video.

## Verification

| Item | Evidence |
|---|---|
| Cloud runtime | Render Free Docker/Linux; the laptop can be switched off. [Runtime observations](measurements/render_runtime.json). Free-tier sleeping still applies. |
| Validated deployed source | [99a098b](https://github.com/AngRoy/again/tree/99a098b99733a2a99511b1407410fd9eaf02a1d8). Later documentation/evidence commits do not imply redeployment. |
| Automated app tests | 47 passed, zero failures/errors. [JUnit](measurements/app_tests.xml); isolated native fakes are separate from live checks. |
| Real API acceptance | 14/14 passed. [Raw responses and IDs](measurements/live_checks.json). Includes paraphrases, stages, ambiguity, no match, genuine teaching, visitor isolation, forgetting and memory off. |
| Default-input browser | Six checks / five real recall requests, no JavaScript errors. [Evidence](tests/live_final_artifacts/live_ui_check.json). The default preflight example passes with no extra condition. |
| Mobile | Real 390-pixel-wide initial and recall views have no horizontal overflow. [Screenshot](tests/live_final_artifacts/live_mobile_recall.png). |
| Health | `/api/health` and `/api/ready` returned HTTP 200, `ready=true`, seven seed records. |
| Timing | [Scope-separated observations and limits](measurements/MEASUREMENTS.md). Startup-to-ready: 11,049.379 ms; platform wake-up is separate. |
| Recording | [Metadata](demo/demo_recording.json) and [five genuine response records](demo/demo_api_evidence.json). Lead incident, different preflight stage, memory off, fictional teaching, taught-memory paraphrase. |
| Original WebM playback | [Verified metadata and five decoded seeks](demo/video_validation.json): 93.0 seconds, 1440 x 1000, 8,315,080 bytes. |
| Architecture | [Document](ARCHITECTURE.md), [SVG](architecture.svg), [PNG](architecture.png). |

Narrated MP4: **93 seconds**, 4,502,598 bytes. [Browser playback and audio-track checks](demo/narrated_video_validation.json) and [full decode/audio-level checks](demo/narrated_audio_validation.json) passed. SHA-256: `00cf537fe6fd0b97e344ed030b36e088cb3e6a20bea7bb25f9d330bedb165225`.

Original WebM SHA-256: `ad802e80f033ff8d214ea7fc2124428d8097f080422dee69c1651a5eb43fc39b`.

The [initial API failure](measurements/live_checks_initial.json) and [initial browser preflight mismatch](tests/live_artifacts/live_ui_initial_failure.json) are preserved with their actual limitations. They are failure history, not the final state. The native filter and data-defined preflight signals were repaired before the passing checks above. This app's claims do not use earlier research benchmarks or test totals.

## Remaining owner step

Open the live link and wait for readiness, watch the video, then paste the exact repository/live/PRD/architecture/video links into the submission form. Upload the verified video to another host only if the form requires it. Confirm viewing permissions and submit before the deadline. The artifact checks do not claim that an authenticated submission form has already been sent.

Render Free can sleep after 15 idle minutes and restart; first access can need a platform wake-up plus Moss readiness, and visitor additions disappear on restart. The stable cloud URL does not promise continuous warm availability.

Features froze at **16:16:06 UTC**, 132.89 minutes before the deadline. [Freeze record](measurements/feature_freeze.json). Submission deadline: **20 September 2026, 18:29 UTC (23:59 IST)**.
