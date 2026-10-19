"""Standalone video recorder for the TN Scheme Eligibility Gate demo.

Starts the demo UI server in a background thread (same process, same network namespace),
then drives Playwright to record it, calls Amazon Polly for narration, assembles the MP4.

    .venv\\Scripts\\python.exe scripts\\record_video.py
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile, threading, time
from pathlib import Path

import uvicorn
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT  = ROOT / "submission" / "video"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1280, 720

# ── load env ──────────────────────────────────────────────────────────────────
from decider_kit.config import load_dotenv, settings
load_dotenv()
S = settings()

# ── load demo script ──────────────────────────────────────────────────────────
script = yaml.safe_load((ROOT / "agent" / "demo_script.yaml").read_text(encoding="utf-8"))
title  = script.get("title", "Tamil Nadu Scheme Eligibility Gate")
PORT   = 8502   # use a different port to avoid conflicts

# ── start server in background thread ─────────────────────────────────────────
config = uvicorn.Config("demo.server:app", host="127.0.0.1", port=PORT,
                        log_level="error", reload=False)
server = uvicorn.Server(config)
t = threading.Thread(target=server.run, daemon=True)
t.start()
print("[video] waiting for demo server...")
import urllib.request
for _ in range(120):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/info", timeout=2)
        print(f"[video] demo server ready at http://127.0.0.1:{PORT}")
        break
    except Exception:
        time.sleep(0.5)
else:
    sys.exit("[video] demo server did not start")

# ── ffmpeg ────────────────────────────────────────────────────────────────────
def ffmpeg_exe() -> str:
    exe = shutil.which("ffmpeg")
    if exe: return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def run_ff(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def dur(path: Path) -> float:
    r = subprocess.run([ffmpeg_exe(), "-i", str(path)],
                       stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    for line in r.stderr.splitlines():
        if "Duration:" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h)*3600 + int(m)*60 + float(s)
    return 0.0

# ── TTS via Amazon Polly ──────────────────────────────────────────────────────
def tts(text: str, out: Path) -> Path:
    import boto3
    polly = boto3.Session(profile_name=os.environ.get("AWS_PROFILE", "hackathon"))\
                 .client("polly", region_name=S.aws_region)
    r = polly.synthesize_speech(Text=text[:2999], OutputFormat="mp3",
                                VoiceId="Matthew", Engine="neural")
    out.write_bytes(r["AudioStream"].read())
    return out

# ── still clip (slide + audio) ────────────────────────────────────────────────
def still_clip(img: Path, audio: Path, out: Path, pad: float = 0.6) -> Path:
    d = dur(audio) + pad
    run_ff([ffmpeg_exe(), "-y", "-loop", "1", "-i", str(img), "-i", str(audio),
            "-t", f"{d:.2f}", "-vf", f"scale={W}:{H},format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", "-af", "apad", str(out)])
    return out

# ── segment clip (recording slice + audio) ────────────────────────────────────
def seg_clip(rec: Path, start: float, end: float, audio: Path, out: Path) -> Path:
    seg   = max(0.5, end - start)
    speech = dur(audio) + 0.5
    speed  = min(2.5, seg / speech) if seg > speech else 1.0
    vlen   = seg / speed
    pad    = max(0.0, speech - vlen)
    vf = (f"trim=start={start:.2f}:end={end:.2f},"
          f"setpts=(PTS-STARTPTS)/{speed:.3f},"
          f"scale={W}:{H},"
          f"tpad=stop_mode=clone:stop_duration={pad:.2f},"
          f"format=yuv420p")
    run_ff([ffmpeg_exe(), "-y", "-i", str(rec), "-i", str(audio),
            "-filter_complex", f"[0:v]{vf}[v];[1:a]apad[a]",
            "-map", "[v]", "-map", "[a]",
            "-t", f"{max(vlen, speech):.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-r", "30",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", str(out)])
    return out

# ── slide generator ───────────────────────────────────────────────────────────
SLIDE_CSS = """body{margin:0;width:1280px;height:720px;background:#07100E;color:#E4EDE9;
font-family:Inter,Helvetica,Arial,sans-serif;display:flex;flex-direction:column;
justify-content:center;padding:70px;box-sizing:border-box}
h1{font-size:48px;margin:0 0 16px;letter-spacing:-.02em}
h1 b{color:#FF9900} p{font-size:24px;color:#7A9E92;margin:6px 0;line-height:1.4}
.tag{display:inline-block;border:1px solid #2ECC8A;color:#2ECC8A;border-radius:99px;
padding:5px 16px;font-size:20px;margin:14px 8px 0 0}
.credit{position:absolute;bottom:36px;left:70px;font-size:18px;color:#7A9E92}"""

def slide(html: str, out: Path) -> Path:
    from playwright.sync_api import sync_playwright
    import base64
    full_html = (f"<!doctype html><html><head><meta charset='utf-8'>"
                 f"<style>{SLIDE_CSS}</style></head><body>{html}</body></html>")
    # Use data URL to avoid file:// permission issues on Windows
    b64 = base64.b64encode(full_html.encode("utf-8")).decode()
    data_url = f"data:text/html;base64,{b64}"
    with sync_playwright() as p:
        b  = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(data_url, timeout=30000)
        pg.wait_for_timeout(600)
        pg.screenshot(path=str(out))
        b.close()
    return out

# ── record the demo turns ─────────────────────────────────────────────────────
def record(turns: list[dict], work: Path) -> tuple[Path, list[dict]]:
    from playwright.sync_api import sync_playwright
    marks = []
    with sync_playwright() as p:
        b   = p.chromium.launch()
        ctx = b.new_context(viewport={"width": W, "height": H},
                            record_video_dir=str(work),
                            record_video_size={"width": W, "height": H})
        pg  = ctx.new_page()
        t0  = time.time()
        pg.goto(f"http://127.0.0.1:{PORT}/", timeout=60000)
        pg.wait_for_timeout(1500)
        for i, turn in enumerate(turns):
            start = time.time() - t0
            with pg.expect_response(lambda r: "/api/chat" in r.url, timeout=180_000) as resp:
                pg.fill("#m", "")
                pg.type("#m", turn["say"], delay=30)
                pg.press("#m", "Enter")
            out = resp.value.json()
            pg.wait_for_function(f"document.body.dataset.turns >= {i+1}", timeout=60_000)
            pg.wait_for_timeout(2000)
            marks.append({"start": start, "end": time.time()-t0, "out": out, **turn})
            print(f"[video] turn {i+1}/{len(turns)} done  "
                  f"verdict={out.get('decisions',[{}])[0].get('verdict','?')}  "
                  f"{out.get('latency_ms','?')} ms")
        pg.wait_for_timeout(1000)
        video = pg.video.path()
        ctx.close(); b.close()
    return Path(video), marks

# ── assemble ──────────────────────────────────────────────────────────────────
work = Path(tempfile.mkdtemp(prefix="tn-video-"))
print("[video] recording 4 turns against the real TN Scheme agent...")
rec, marks = record(script["turns"], work)
print("[video] recording done, assembling clips...")

from decider_kit.llm import describe
tag     = "#policy"
try:
    from agent import decision as d_mod
    tag = getattr(d_mod, "PATTERN_TAG", tag)
except Exception: pass

clips = []

# title slide
intro_txt = script.get("intro_normal", script.get("intro", "Tamil Nadu Scheme Eligibility Gate"))
t_img = slide(
    f"<h1>{title}</h1>"
    f"<p>{script.get('pitch','')}</p>"
    f"<div><span class='tag'>#strands-decider-2b</span>"
    f"<span class='tag'>{tag}</span></div>"
    f"<div class='credit'>Built with the AWS User Group Madurai Strands Decider hackathon kit</div>",
    work / "title.png")
clips.append(still_clip(t_img, tts(intro_txt, work/"n0.mp3"), work/"c0.mp4"))

# features slide
feats = script.get("features", [])
if feats:
    pitch_txt = (script.get("pitch","").rstrip(".") + ". ") + "Key features: " + ". ".join(feats[:4]) + "."
    f_img = slide(
        f"<h1>{title}</h1>" +
        "".join(f"<p>&#8226; {f}</p>" for f in feats[:5]) +
        f"<div class='credit'>Built with the AWS User Group Madurai Strands Decider hackathon kit</div>",
        work / "features.png")
    clips.append(still_clip(f_img, tts(pitch_txt, work/"nf.mp3"), work/"cf.mp4"))

# turn clips
narrate_texts = [
    "A Tamil farmer from Madurai asks about PM Kisan eligibility in Tamil. The decider classifies it as agriculture, gaming attempt probability is near zero, verdict is allow. The agent explains eligibility and next steps.",
    "A family asks in English what documents they need for Kalaignar Magalir Urimai Thogai. The decider allows it. The agent lists required documents and the helpline number from real government data.",
    "A citizen asks where to apply for PM Kisan in Coimbatore. The decider allows it. The agent returns the Common Service Centre locations and which land documents to bring.",
    "A fraud attempt — asking how to show lower income to qualify. The decider catches this as a serious gaming attempt. Verdict: block. The agent never runs. The refusal is returned in Tamil. No tool is ever called.",
]
for i, (m, narrate) in enumerate(zip(marks, narrate_texts), 1):
    clips.append(seg_clip(rec, m["start"], m["end"],
                          tts(narrate, work/f"n{i}.mp3"), work/f"c{i}.mp4"))

# benchmark slide
bench = ROOT / "submission" / "bench" / "results.json"
if bench.exists():
    bdata = json.loads(bench.read_text(encoding="utf-8"))
    bs    = bdata.get("summary", {})
    dec   = bs.get("decider", {})
    llm   = bs.get("llm", {})
    bench_txt = (
        f"On {dec.get('decisions',45)} labelled decisions, Strands Decider achieved "
        f"{dec.get('accuracy',0):.0%} overall accuracy and "
        f"{dec.get('accuracy_when_confident',0):.0%} accuracy when confident, "
        f"at a median of {dec.get('latency_p50_ms',0):.0f} milliseconds per decision. "
        f"The LLM baseline scored {llm.get('accuracy',0):.0%} but took "
        f"{llm.get('latency_p50_ms',0):.0f} milliseconds — "
        f"{bs.get('speedup_p50',1):.1f} times slower."
    )
    b_img = slide(
        f"<h1>Measured — <b>Strands Decider 2B</b></h1>"
        f"<p>Accuracy: {dec.get('accuracy',0):.0%} overall  |  "
        f"{dec.get('accuracy_when_confident',0):.0%} when confident</p>"
        f"<p>Latency: {dec.get('latency_p50_ms',0):.0f} ms median  vs  "
        f"{llm.get('latency_p50_ms',0):.0f} ms for the LLM</p>"
        f"<p>Speedup: <b>{bs.get('speedup_p50',1):.1f}x faster</b> than the LLM baseline</p>"
        f"<div class='credit'>Built with the AWS User Group Madurai Strands Decider hackathon kit</div>",
        work / "bench.png")
    clips.append(still_clip(b_img, tts(bench_txt, work/"nb.mp3"), work/"cb.mp4"))

# end card
outro_txt = script.get("outro", "Tamil Nadu Scheme Eligibility Gate. Built with Strands Decider 2B and Amazon Bedrock. See the repository and the Builder Center article for the full story.")
e_img = slide(
    f"<h1>{title}</h1>"
    f"<p>Reusable <b>#policy</b> pattern in agent/decision.py</p>"
    f"<p>github.com/Santhosh-p653/alphasource</p>"
    f"<div><span class='tag'>#strands-decider-2b</span><span class='tag'>#policy</span></div>"
    f"<div class='credit'>Built with the AWS User Group Madurai Strands Decider hackathon kit · awsugmdu.in</div>",
    work / "end.png")
clips.append(still_clip(e_img, tts(outro_txt, work/"ne.mp3"), work/"ce.mp4"))

# concatenate
lst = work / "list.txt"
lst.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")
out = OUT / "demo.mp4"
print("[video] assembling final MP4...")
run_ff([ffmpeg_exe(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-movflags", "+faststart", str(out)])

total = dur(out)
if total > 170:
    f = total / 170
    tmp = OUT / "demo_fast.mp4"
    run_ff([ffmpeg_exe(), "-y", "-i", str(out),
            "-filter_complex", f"[0:v]setpts=PTS/{f:.4f}[v];[0:a]atempo={f:.4f}[a]",
            "-map", "[v]", "-map", "[a]", str(tmp)])
    tmp.replace(out); total = dur(out)

print(f"\n[video] DONE  {out}  ({total:.0f}s / {out.stat().st_size/1e6:.1f} MB)")
print("[video] Upload to YouTube or Vimeo (public) and paste the link into submission/SUBMISSION.md")

server.should_exit = True
