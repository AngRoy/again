# Again - 90-second demo and submission

Record the real app after readiness is verified. Use only values visible in the live timing panel. If a feature is absent or failing, disclose or omit it; do not narrate a planned result as completed.

## What to click and say

| Time | Action and narration |
|---|---|
| 0-10 s | Open the live app. Click **Try a real incident**, then **Recall a fix**. "This error already cost us two failed attempts. Again remembers what happened so we can stop repeating the same fix." |
| 10-30 s | Show `LaunchUnelevated: Access is denied` with administrator preflight passed. Open its evidence. "Both attempts had passed the administrator check. The failure was launching the ordinary worker. Moss retrieves the matching incident and the recorded attempts. Starting the worker directly fixed that stage; the later trace stayed unresolved." |
| 30-45 s | Change to the non-admin preflight example, then try ambiguous `Access is denied` without a stage. "The same words can need a different next step. When conditions are missing, Again asks instead of recycling the wrong fix." |
| 45-65 s | Teach the fictional port card below, clearly marking it synthetic. Recall it with different wording. "This is a new user-reported memory, indexed during this visitor session. I can find it without repeating the exact error text." |
| 65-80 s | Expand the live details. "Moss supplies semantic retrieval. A bounded policy checks the returned conditions and outcomes. These are real query, API and browser timings; the query can include local embedding." |
| 80-90 s | Briefly show the architecture, then return to the result. "Again is a small debugging memory you can run yourself. This public demo sends samples to its backend. Recover what you learned, and stop repeating failed fixes." |

Both historical worker-launch attempts were elevated; only one is documented as an explicit RunAs retry. Do not call them two RunAs attempts. Worker readiness is verified; successful trace completion is not.

## Fictional teaching card

Use the form's **fictional example** label. Do not preload or present this as a measured project incident.

- **Symptom:** My browser says connection refused when I reopen yesterday's local dev-server tab.
- **Conditions:** The browser is at localhost:3000; the terminal says the server is Ready at localhost:3001.
- **Attempted action:** I refreshed the old port-3000 tab; it still failed.
- **User-reported outcome:** Opening the Ready URL on port 3001 loaded the page.
- **Paraphrase to recall:** The local server is healthy on a new port, but my old browser bookmark cannot connect. What did I do last time?

If teaching has not passed genuine indexing/recall and isolation checks, replace that segment with a second real paraphrase and disclose the cut. Do not fake a saved record. If using a fresh browser/profile for recording, teach the card again in that same session.

## Submission description

**Again - Stop repeating failed fixes** is a troubleshooting-memory agent for developers. Paste an error and genuine Moss retrieval recovers relevant past attempts. An explicit policy checks whether their stage and conditions apply, then returns one next step with readable evidence. It preserves failed attempts and distinguishes resolved, diagnosed, partially resolved, unresolved and user-reported outcomes.

The sample corpus contains seven sanitized real incidents. A clearly fictional teaching card demonstrates adding a session-local outcome and finding it through different wording. The public demo sends input to its backend; local self-hosting runs the application on the user's host. No generative LLM, shell execution, inference-acceleration claim or universal debugging guarantee is involved.

Keep the teaching sentence only after that feature passes. State the actual cloud deployment used, after a remotely verified recall. Do not present the earlier Windows diagnostic as deployed performance.

## Submission checklist

- Verify the public [repository](https://github.com/AngRoy/again) contains only this standalone sanitized app and that its latest app commit is visible.
- Open the actual live URL in a fresh browser and perform a genuine recall. Confirm that health reflects a completed real warm query.
- Link the final [PRD](PRD.md), [architecture document](ARCHITECTURE.md), and [architecture image](architecture.png).
- Record the interaction above, with no credential values, private terminal paths or unrelated browser tabs visible.
- Upload the video to the submission platform's accepted host and verify viewing permissions. Do not invent a video URL.
- Copy the exact verified repository/live/video links into [SUBMISSION_READY.md](SUBMISSION_READY.md) and the submission form.
- Confirm the cloud app remains healthy after submitting. Freeze features at 17:59 UTC; submit before 18:29 UTC on 20 September 2026.

The video upload and final submission may require the owner's account interaction. Preserve at least thirty minutes for that step.
