# Again - 90-second demo and submission

The [finished 93-second video](https://github.com/AngRoy/again/releases/download/v1.0.0/again-demo.webm) is a silent captioned recording of the real deployed app. [Repository video](https://github.com/AngRoy/again/blob/main/demo/again-demo.webm) / [raw download](https://raw.githubusercontent.com/AngRoy/again/main/demo/again-demo.webm). Playback and five decoded timestamps passed. The optional narration below follows the actual interaction sequence; the supplied WebM contains no spoken audio.

## What the live recording shows

The main recording is a silent, captioned walkthrough of genuine public-browser requests. It has no spoken audio, mocked results, edited latency, or playback retiming. The planned interaction timeline is 90 seconds; the actual media duration is 93.0 seconds, verified from the WebM. [Playback evidence](demo/video_validation.json).

| Planned time | Action and optional spoken narration |
|---|---|
| 0-12 s | Open the live app and click **Try a real incident**. "Again remembers what happened, so a familiar error does not send you back to a failed fix." |
| 12-30 s | Recall the elevated worker-launch incident and open its source excerpt. "The administrator check passed, but the ordinary worker could not launch. Both recorded attempts failed at that stage. Starting the worker directly repaired startup; the later trace stayed unresolved." |
| 30-39 s | Select the non-admin preflight example and recall. "The same error at a different stage calls for a different action. A System32 prompt does not establish administrator privileges." |
| 39-47 s | Turn memory off, recall and show the timing panel. "With memory off, Again makes zero retrieval queries and says that history is unavailable." |
| 47-65 s | Fill and save the fictional port-mismatch teaching card. "This is a fictional, user-reported outcome, indexed now for this browser session. It is not promoted to verified history." |
| 65-79 s | Recall the newly taught outcome in different words. "A genuine Moss query recovers the new memory. Again asks whether its recorded conditions apply." |
| 79-90 s | Show the live returned IDs and timings, then return to the title. "Retrieval including embedding, API time and browser time stay separate. Again: stop repeating failed fixes." |

The video contains five real API responses: two historical recalls, memory off, teaching, and the taught-memory paraphrase. Ambiguous `Access is denied` and unrelated input are separately tested flows; they are not claimed as scenes in this recording. The architecture is a separate submission artifact.

Both historical worker-launch attempts were elevated; only one is documented as an explicit RunAs retry. Do not call them two RunAs attempts. Worker readiness is verified; successful trace completion is not.

## Fictional teaching card

Use the form's **fictional example** label. Do not preload or present this as a measured project incident.

- **Symptom:** The browser refuses the connection at localhost:3000.
- **Conditions:** The terminal says the development server is ready at localhost:3001.
- **Attempted action:** Refreshing the old localhost:3000 tab did not help. I opened the terminal's reported localhost:3001 URL.
- **User-reported outcome:** Fictional demonstration: the page loaded at localhost:3001.
- **Paraphrase to recall:** My server says it is running, but an old browser tab refuses the connection.

These are the supplied example fields. Expand **Make the next time easier**, fill the fictional example, then click **Save to my memory**. The taught outcome remains explicitly user-reported.

The deployed API's genuine teaching, recall and isolation checks passed. If recording in a new browser/profile, teach the fictional card again in that same session.

## Reproduce the captioned recording

After installing `requirements-dev.txt`, use an installed Google Chrome browser and Playwright's FFmpeg helper. From the repository root on Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install ffmpeg
.\.venv\Scripts\python.exe scripts/record_demo.py --url https://again-fl36.onrender.com --output demo/reproduced
.\.venv\Scripts\python.exe scripts/check_video.py demo/reproduced/again-demo.webm --output demo/reproduced/video_validation.json
```

The script defaults to Chrome's standard Windows installation path. Supply `--chrome` with the actual browser executable on another setup. Wait for `/api/ready` first. The script uses only public examples and a fictional teaching record, and writes the WebM, screenshots, response evidence and recording metadata. Require playback verification to report `status: passed` with decoded positions matching the requested seek times. Check the resulting media before uploading; recording completion alone is not proof of playability.

For a spoken submission video, record the optional narration above while demonstrating the same verified flow. Do not imply that the captioned artifact already contains narration.

## Screenshots

[Historical evidence](demo/again-live-evidence.png) | [Newly taught memory](demo/again-live-taught-memory.png) | [Actual timing panel](demo/again-live-teach-recall.png). These are from the real recording, not mocked UI tests.

## Submission description

**Again - Stop repeating failed fixes** is a troubleshooting-memory agent for developers. Paste an error and genuine Moss retrieval recovers relevant past attempts. An explicit policy checks whether their stage and conditions apply, then returns one next step with readable evidence. It preserves failed attempts and distinguishes resolved, diagnosed, partially resolved, unresolved and user-reported outcomes.

The sample corpus contains seven sanitized real incidents. A clearly fictional teaching card demonstrates adding a session-local outcome and finding it through different wording. The public demo sends input to its backend; local self-hosting runs the application on the user's host. No generative LLM, shell execution, inference-acceleration claim or universal debugging guarantee is involved.

The app is deployed on Render Free with genuine Linux Moss readiness and 14/14 real API checks. The earlier Windows diagnostic is not presented as deployed performance.

## Submission checklist

- Verify the public [repository](https://github.com/AngRoy/again) contains only this standalone sanitized app and that its latest app commit is visible.
- Open the actual live URL in a fresh browser and perform a genuine recall. Confirm that health reflects a completed real warm query.
- Link the final [PRD](PRD.md), [architecture document](ARCHITECTURE.md), and [architecture image](architecture.png).
- Record the interaction above, with no credential values, private terminal paths or unrelated browser tabs visible.
- Use the verified release video link, or upload that file to a separate host if the submission form requires it. Verify viewing permissions.
- Copy the exact verified repository/live/video links into [SUBMISSION_READY.md](SUBMISSION_READY.md) and the submission form.
- Confirm the cloud app remains healthy after submitting. Features were frozen at 16:16 UTC; submit before 18:29 UTC on 20 September 2026.

The video upload and final submission may require the owner's account interaction. Preserve at least thirty minutes for that step.
