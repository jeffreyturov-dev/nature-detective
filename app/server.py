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
- Never invent a species. If the photo is blurry, abstract, shows a person, a
  manufactured object, or anything that is NOT clearly a living thing you
  recognize, you MUST answer with "identified": false. A wrong guess is the
  worst possible answer — saying "I'm not sure" is always better.
- If you hesitate between two species, or the photo shows only a small or
  unclear part of the organism, use "confidence": "low" and say what it COULD be.
- NEVER encourage touching, picking or eating anything. Mushrooms and berries
  are ALWAYS "look-dont-touch", no exception.
- Everything you say must be true and verifiable. No made-up facts.

Example for a photo that does not clearly show a recognizable living thing:
{"identified": false, "common_name": "", "latin_name": "", "type": "other",
 "confidence": "low", "kid_fact": "", "safety": "unknown",
 "mission": "one fun outdoor observation mission",
 "quiz_question": "", "quiz_answer": false}

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


VERIFY_PROMPT = """You are a fact-checker for a children's nature app.
Another model looked at this photo and claimed it shows: {claim}.

Do NOT judge the claim yet. Work in two steps, in this order:
1. First, describe in one sentence what you OBJECTIVELY see in the photo,
   as if nobody had told you anything about it. If the photo does not clearly
   show a recognizable living thing (abstract, blurry, object, person),
   your description must say so plainly.
2. Only then, decide: is the claim consistent with YOUR OWN description?
   - CONFIRM if your description independently matches the claimed organism
     (a correct common name or close relative is good enough for a nature walk).
   - REJECT if your description is of something else, or of nothing
     recognizable — a child must never be taught a guess as a fact.

Answer ONLY with this JSON, no markdown:
{{"seen": "your one-sentence independent description",
  "confirmed": true or false, "reason": "one short sentence"}}"""


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


def _ollama_call(prompt: str, image_b64: str, num_predict: int = 450) -> str:
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": num_predict},
    }).encode()
    req = urllib.request.Request(
        OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["response"]


def _extract_json(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"no JSON in model output: {raw[:300]}")
    return json.loads(m.group(0))


def ollama_vision(image_b64: str) -> dict:
    data = _extract_json(_ollama_call(PROMPT, image_b64))
    # Hard safety net — the model's rules are prompt-level; these are code-level.
    if str(data.get("type", "")).lower() in ("mushroom", "berry", "berries"):
        data["safety"] = "look-dont-touch"

    # Second pass: a verifier whose only job is to doubt the first answer.
    if data.get("identified"):
        claim = f"{data.get('common_name','')} ({data.get('latin_name','')})"
        try:
            check = _extract_json(_ollama_call(
                VERIFY_PROMPT.format(claim=claim), image_b64, num_predict=120))
            data["verified"] = bool(check.get("confirmed"))
            data["verify_reason"] = str(check.get("reason", ""))[:200]
            if not data["verified"]:
                data.update({
                    "identified": False,
                    "kid_fact": ("A first guess said this might be "
                                 + str(data.get("common_name", "something"))
                                 + ", but my double-check disagreed — and a good "
                                   "detective never teaches a maybe as a fact. "
                                   "Ask a grown-up or a field guide!"),
                    "common_name": "", "latin_name": "", "confidence": "low",
                    "safety": "look-dont-touch",
                    "quiz_question": "", "quiz_answer": False,
                })
        except Exception:
            data["verified"] = None  # verifier unreachable — keep 1st answer
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
