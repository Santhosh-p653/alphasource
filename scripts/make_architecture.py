"""Generate the architecture diagram for the TN Scheme Eligibility Gate using Pillow.

    .venv\\Scripts\\python.exe scripts/make_architecture.py
    Writes: submission/article/architecture.png
"""
from __future__ import annotations
from pathlib import Path
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Run: .venv\\Scripts\\python.exe -m pip install pillow")

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "submission" / "article"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1400, 788

# colours
BG     = (7,  16,  14)
PANEL  = (13, 26,  23)
BORDER = (26, 51,  40)
GREEN  = (46, 204, 138)
TEAL   = (20, 184, 166)
ORANGE = (255,153, 0)
AMBER  = (251,191, 36)
RED    = (248,113,113)
MUTE   = (122,158,146)
INK    = (228,237,233)
BLUE   = (96, 165, 250)
DARK_R = (26, 15,  15)
DARK_A = (26, 21,  0)
DARK_B = (10, 16,  32)

img  = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

def try_font(size):
    for name in ["arialbd.ttf","Arial Bold.ttf","DejaVuSans-Bold.ttf","verdanab.ttf"]:
        try: return ImageFont.truetype(name, size)
        except: pass
    return ImageFont.load_default()

def try_font_reg(size):
    for name in ["arial.ttf","Arial.ttf","DejaVuSans.ttf","verdana.ttf"]:
        try: return ImageFont.truetype(name, size)
        except: pass
    return ImageFont.load_default()

FB  = try_font(13)
FR  = try_font_reg(11)
FSM = try_font_reg(9)
FT  = try_font(17)
FSB = try_font(11)

def rect(x, y, w, h, fill=PANEL, outline=BORDER, radius=12):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill, outline=outline, width=2)

def ctext(x, y, text, font=FB, fill=INK, center_x=None, width=None):
    if center_x and width:
        bbox = draw.textbbox((0,0), text, font=font)
        tw = bbox[2]-bbox[0]
        x = center_x - tw//2
    draw.text((x, y), text, font=font, fill=fill)

def box(x, y, w, h, label, sub="", fill=PANEL, outline=BORDER, lc=INK, sc=MUTE):
    rect(x, y, w, h, fill=fill, outline=outline)
    bby = y + h//2 - (12 if sub else 7)
    ctext(0, bby, label, font=FSB, fill=lc, center_x=x+w//2, width=w)
    if sub:
        ctext(0, bby+18, sub, font=FSM, fill=sc, center_x=x+w//2, width=w)

def arrow(x1, y1, x2, y2, color=MUTE, label=""):
    draw.line([(x1,y1),(x2,y2)], fill=color, width=2)
    # arrowhead
    import math
    angle = math.atan2(y2-y1, x2-x1)
    size = 10
    for da in [0.5, -0.5]:
        ax2 = int(x2 - size*math.cos(angle-da))
        ay2 = int(y2 - size*math.sin(angle-da))
        draw.line([(x2,y2),(ax2,ay2)], fill=color, width=2)
    if label:
        mx, my = (x1+x2)//2+6, (y1+y2)//2
        draw.text((mx, my), label, font=FSM, fill=color)

# ── title ─────────────────────────────────────────────────────
ctext(0, 18, "Tamil Nadu Government Scheme Eligibility Gate — Architecture", font=FT, fill=INK, center_x=W//2, width=W)
ctext(0, 44, "AlphaSource  ·  #policy pattern  ·  Strands Decider 2B  +  Amazon Bedrock", font=FR, fill=MUTE, center_x=W//2, width=W)

# ── citizen ───────────────────────────────────────────────────
box(30,  310, 160, 80, "🧑 Citizen", "Tamil/English/Mixed", fill=(10,26,23), outline=TEAL, lc=TEAL, sc=MUTE)

# ── policy gate ───────────────────────────────────────────────
box(240, 240, 300, 240, "SchemeEligibilityGate", "agent/decision.py  ·  #policy", fill=(10,31,23), outline=GREEN, lc=GREEN, sc=MUTE)
box(255, 280, 270, 80,  "Strands Decider 2B", "3 questions · 1 forward pass", fill=PANEL, outline=GREEN, lc=GREEN, sc=MUTE)
box(255, 375, 270, 80,  "scheme_category", "gaming_attempt · severity", fill=(7,21,15), outline=BORDER, lc=INK, sc=MUTE)

# ── verdict boxes ─────────────────────────────────────────────
box(30,  560, 160, 80, "🚫 Block", "Tamil/English refusal\nno tool called", fill=DARK_R, outline=RED, lc=RED, sc=(224,112,112))
box(220, 560, 160, 80, "⚠️ Review", "caution injected\ninto prompt", fill=DARK_A, outline=AMBER, lc=AMBER, sc=(200,160,80))

# ── strands agent ─────────────────────────────────────────────
box(610, 240, 240, 240, "Strands Agent", "Amazon Bedrock\nNova Pro", fill=(10,21,32), outline=ORANGE, lc=ORANGE, sc=MUTE)

# ── tools ─────────────────────────────────────────────────────
tools = [
    ("list_schemes",           "by category"),
    ("get_scheme_details",     "PM Kisan · Magalir Urimai"),
    ("check_eligibility",      "indicative check"),
    ("get_required_documents", "docs + helpline"),
    ("find_application_centres","CSC by district"),
    ("translate_scheme_summary","Tamil / English"),
]
for i, (name, sub) in enumerate(tools):
    ty = 78 + i*104
    box(920, ty, 290, 76, name, sub, fill=PANEL, outline=BORDER, lc=INK, sc=MUTE)
    arrow(860, 360, 920, ty+38, color=BORDER)

# ── real data badge ───────────────────────────────────────────
box(920, 710, 290, 58, "Real Scheme Data", "pmkisan.gov.in · magalirthogai.tn.gov.in", fill=(7,21,15), outline=TEAL, lc=TEAL, sc=MUTE)

# ── agentcore badge ───────────────────────────────────────────
box(610, 570, 240, 70, "AgentCore Runtime", "Deployed on AWS", fill=DARK_B, outline=BLUE, lc=BLUE, sc=MUTE)

# ── arrows ────────────────────────────────────────────────────
arrow(190, 350, 240, 350, color=TEAL,   label="request")
arrow(390, 455, 280, 560, color=RED,    label="block")
arrow(390, 455, 300, 560, color=AMBER,  label="review")
arrow(540, 350, 610, 350, color=GREEN,  label="allow")
arrow(730, 560, 730, 570, color=BLUE,   label="deploy")

# ── legend ────────────────────────────────────────────────────
legend = [
    (GREEN,  "Strands Decider 2B"),
    (ORANGE, "Amazon Bedrock"),
    (TEAL,   "Real government data"),
    (RED,    "Block (fraud)"),
    (AMBER,  "Review (borderline)"),
    (BLUE,   "AgentCore Runtime"),
]
lx, ly = 30, 700
for i, (col, lbl) in enumerate(legend):
    cx = lx + i*220
    draw.rectangle([cx, ly, cx+18, ly+18], fill=col)
    draw.text((cx+24, ly+1), lbl, font=FSM, fill=INK)

# ── footer ────────────────────────────────────────────────────
draw.text((W//2 - 200, H-22), "Built with the AWS User Group Madurai Strands Decider hackathon kit", font=FSM, fill=MUTE)

out_path = OUT / "architecture.png"
img.save(out_path)
print(f"Saved: {out_path}")
