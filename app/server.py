"""Nature Detective — offline-first nature companion for kids.

Everything runs on this machine: an open-weight vision model (Gemma 3 via
Ollama) identifies what a child photographs, and invents the next outdoor
mission. No cloud, no account, no photo ever leaves the device/network.
"""
import base64
import json
import re
import sqlite3
import time
import urllib.request
from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import io

BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "journal.db"
DB.parent.mkdir(exist_ok=True)

OLLAMA = "http://localhost:11434/api/generate"
MODEL = "gemma3:4b"

PROMPT = """You are "Nature Detective", a kind nature guide for children aged 5-10,
on a family hike. A child just photographed something outdoors.

ABSOLUTE RULES (never break them):
- Never invent a species. If you are not reasonably sure what is in the photo,
  say so honestly ("I'm not sure — it looks like it could be...").
- NEVER encourage touching, picking or eating anything. Mushrooms and berries
  are ALWAYS "look-dont-touch", no exception.
- Everything you say must be true and verifiable. No made-up facts.

Answer ONLY with this JSON object, no markdown, no commentary:
{
  "identified": true or false,
  "common_name": "simple name a child understands",
  "latin_name": "scientific name or empty string",
  "type": "plant|flower|tree|insect|bird|mushroom|animal|other",
  "confidence": "high|medium|low",
  "kid_fact": "one true, amazing fact a 7-year-old would love (1-2 sentences)",
  "safety": "safe|look-dont-touch",
  "mission": "one fun OUTDOOR mission related to this find that gets the kid moving and observing (e.g. count, find, compare) — 1 sentence, no screen involved",
  "quiz_question": "one simple true/false question about this find",
  "quiz_answer": true or false
}"""


def get_db():
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS finds(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             ts REAL, common_name TEXT, latin_name TEXT, type TEXT,
             confidence TEXT, safety TEXT, kid_fact TEXT, mission TEXT,
             quiz_question TEXT, quiz_answer INTEGER, thumb TEXT)"""
    )
    return con


def ollama_vision(image_b64: str) -> dict:
    body = json.dumps({
        "model": MODEL,
        "prompt": PROMPT,
        "images": [image_b64],
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 450},
    }).encode()
    req = urllib.request.Request(
        OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = json.loads(r.read())["response"]
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"no JSON in model output: {raw[:300]}")
    data = json.loads(m.group(0))
    # Hard safety net — the model's rules are prompt-level; these are code-level.
    if str(data.get("type", "")).lower() in ("mushroom", "berry", "berries"):
        data["safety"] = "look-dont-touch"
    return data


app = FastAPI(title="Nature Detective")


@app.post("/api/identify")
async def identify(photo: UploadFile):
    raw = await photo.read()
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    im.thumbnail((640, 640))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=82)
    b64 = base64.b64encode(buf.getvalue()).decode()

    t0 = time.time()
    try:
        result = ollama_vision(b64)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)
    result["elapsed_s"] = round(time.time() - t0, 1)

    thumb = io.BytesIO()
    im.copy().resize((96, 96)).save(thumb, format="JPEG", quality=70)
    thumb_b64 = base64.b64encode(thumb.getvalue()).decode()

    con = get_db()
    cur = con.execute(
        """INSERT INTO finds(ts,common_name,latin_name,type,confidence,safety,
                             kid_fact,mission,quiz_question,quiz_answer,thumb)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (time.time(), result.get("common_name", ""), result.get("latin_name", ""),
         result.get("type", ""), result.get("confidence", ""),
         result.get("safety", ""), result.get("kid_fact", ""),
         result.get("mission", ""), result.get("quiz_question", ""),
         1 if result.get("quiz_answer") else 0, thumb_b64),
    )
    con.commit()
    result["find_id"] = cur.lastrowid
    con.close()
    return result


@app.get("/api/journal")
async def journal():
    con = get_db()
    rows = con.execute(
        """SELECT id,ts,common_name,latin_name,type,confidence,safety,
                  kid_fact,mission,quiz_question,quiz_answer,thumb
           FROM finds ORDER BY id DESC LIMIT 100"""
    ).fetchall()
    con.close()
    cols = ["id", "ts", "common_name", "latin_name", "type", "confidence",
            "safety", "kid_fact", "mission", "quiz_question", "quiz_answer", "thumb"]
    return [dict(zip(cols, r)) for r in rows]


@app.delete("/api/journal/{find_id}")
async def delete_find(find_id: int):
    con = get_db()
    con.execute("DELETE FROM finds WHERE id=?", (find_id,))
    con.commit()
    con.close()
    return {"deleted": find_id}


@app.get("/")
async def index():
    return FileResponse(BASE / "static" / "index.html")


app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8347)
