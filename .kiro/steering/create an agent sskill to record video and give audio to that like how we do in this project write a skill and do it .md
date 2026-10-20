---
inclusion: manual
---

# Skill: Record Demo Video with Audio Narration

This skill records the hackathon submission video for any agent in this kit. It mirrors what `scripts/record_video.py` does — start the demo UI, drive Playwright to capture browser interactions, synthesize narration with Amazon Polly, assemble everything with ffmpeg, and write `submission/video/demo.mp4`.

Trigger this skill when the participant says `/record`, "record the video", "make the video", or "run the video script".

---

## What this skill does

1. Reads `agent/demo_script.yaml` for the title, pitch, features, turns, and narration lines.
2. Reads `submission/bench/results.json` for real benchmark numbers (accuracy, latency, speedup).
3. Starts the demo UI server (`demo/server.py`) in a background thread on port 8502.
4. Uses Playwright (Chromium) to record browser interactions for each `turns[].say` entry.
5. Synthesizes MP3 narration for each segment using Amazon Polly (`Matthew`, neural engine, `AWS_PROFILE=hackathon`).
6. Combines recorded segments and slides into a single MP4 via ffmpeg.
7. Enforces a 170-second hard limit — speeds up the final video if it runs over.
8. Outputs `submission/video/demo.mp4`.

---

## Prerequisites the skill must verify before starting

- `agent/demo_script.yaml` exists and has `turns`, `title`, `pitch`, `intro_normal`, and `outro`.
- `agent/eval_cases.jsonl` exists (bench data needed for the benchmark slide).
- `submission/bench/results.json` exists — run `./kit bench` first if it does not.
- `submission/video/narration.md` exists with narration lines (one section per slide/turn).
- ffmpeg is on PATH or `imageio_ffmpeg` is installed in the venv.
- Playwright is installed: `playwright install chromium`.
- AWS credentials are configured under profile `hackathon` with Polly access.
- The `.venv` is active.

If any prerequisite is missing, tell the participant which one and how to fix it before proceeding.

---

## Video structure (fixed order)

| Clip | Source | Narration source |
|---|---|---|
| Title slide | Generated HTML → Playwright screenshot | `demo_script.yaml` → `intro_normal` |
| Features slide | Generated HTML → Playwright screenshot | `demo_script.yaml` → `pitch` + `features` |
| Turn 1…N | Playwright browser recording | `demo_script.yaml` → `turns[i].narrate` |
| Benchmark slide | Generated HTML → Playwright screenshot | Built from `submission/bench/results.json` |
| End card | Generated HTML → Playwright screenshot | `demo_script.yaml` → `outro` |

---

## Slide style (keep consistent with the kit)

All slides use the `SLIDE_CSS` block defined in `scripts/record_video.py`:

- Background `#07100E`, text `#E4EDE9`, accent `#FF9900`, tag border `#2ECC8A`.
- Canvas `1280×720`, font Inter/Helvetica/Arial.
- Every slide ends with: `Built with the AWS User Group Madurai Strands Decider hackathon kit` in the bottom-left credit div.
- Tags on the title and end card: `#strands-decider-2b` and the agent's `PATTERN_TAG` (read from `agent/decision.py`).

Do not change the colour scheme, credit line, or tag format.

---

## Audio narration rules

- Use Amazon Polly, voice `Matthew`, engine `neural`.
- Truncate text to 2999 characters per Polly call (hard API limit).
- Use `AWS_PROFILE` from the environment (defaults to `hackathon`) and `AWS_REGION` from `settings()`.
- Each clip gets its own MP3 in the temp working directory; never reuse audio across clips.
- Narration text comes from `demo_script.yaml` fields, not from `submission/video/narration.md`. The narration markdown is the human-readable reference; the YAML drives the script.

---

## ffmpeg assembly rules

- All clips must be `libx264`, `yuv420p`, 30 fps, `1280×720`, `aac` audio at 44100 Hz, 2 channels.
- Still clips (slides): loop the image for `audio_duration + 0.6 s` padding.
- Turn clips: if the recording segment is longer than the audio, speed up video (max 2.5×) to match. If shorter, pad with a cloned last frame.
- Concatenate with `-f concat -safe 0`.
- If final duration exceeds 170 s, re-encode with `setpts` and `atempo` to fit.
- Write the final file to `submission/video/demo.mp4`.

---

## How to run it

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\python.exe scripts\record_video.py
```

**macOS / Linux:**
```bash
.venv/bin/python scripts/record_video.py
```

Or via the kit command (which calls the same script):
```
.\kit.cmd video --target agentcore   # Windows
./kit video --target agentcore       # macOS/Linux
```

The `--target agentcore` flag points the demo server at the deployed AgentCore runtime. Omit it to record against the local agent.

---

## After recording

1. Verify `submission/video/demo.mp4` plays and is under 3 minutes.
2. Upload to YouTube or Vimeo as **public** (no third-party music, no trademarks).
3. Paste the public URL into `submission/SUBMISSION.md`.
4. The video end card must include the `Built with the AWS User Group Madurai Strands Decider hackathon kit` credit line — verify it is visible.

---

## Rules for the AI assistant executing this skill

- Never invent narration text. Use only the text from `demo_script.yaml` and the numbers from `submission/bench/results.json`.
- Never remove or alter the kit credit line from any slide.
- Do not modify `scripts/record_video.py` unless fixing a bug. This is kit infrastructure.
- Do not modify `agent/demo_script.yaml` narration lines to inflate or misrepresent results.
- If the benchmark slide data shows weak results, report them as-is. Do not suppress the benchmark slide.
- The deployed video must be recorded against the real agent (`./kit video --target agentcore`), not mocked data. Never describe a local model run as Amazon Bedrock in the video narration.
