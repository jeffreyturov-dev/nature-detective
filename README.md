# 🔍 Nature Detective

**An offline-first nature companion that gets kids off the screen and into the woods.**
Built for the Hacktoberfest 2026 DEV Challenge — Week 1: *Touch Grass*.

**Live demo:** https://main-michael-stanford-myrtle.trycloudflare.com

A child on a hike photographs a plant, a bug, a mushroom. An **open-weight vision
model (Gemma 3 4B) running locally** identifies the find, tells one true fun fact,
sets a safety rule, and hands out the **next outdoor mission** — count, find,
compare. Every discovery lands in a field journal on the device.

No account. No cloud. No photo, no GPS coordinate, no child's data ever leaves
your own hardware. It runs where the forest has no bars — that's the whole point.

## Why open matters here

- **No internet, no problem.** Inference runs on a local machine (a laptop, or a
  Raspberry Pi in a backpack acting as a Wi-Fi hotspot). The forest has no 5G;
  the detective doesn't care.
- **Kids' photos stay home.** A closed API would mean uploading pictures of your
  children to someone else's server. Here, nothing ever leaves the device.
- **€0 to run.** Gemma 3 via Ollama — no API key, no subscription, no per-call cost.
- **Swappable.** Any open-weight vision model Ollama can serve drops in with a
  one-line change.

## Safety is a feature, not a disclaimer

- The model is instructed to **never invent a species** — if it's not sure, it
  says so and sends the child to a grown-up or a field guide. Honesty over
  confidence, always.
- Mushrooms and berries are **always** "look, don't touch" — enforced twice:
  in the prompt *and* in code (`server.py`), because prompt rules are suggestions
  and code rules are guarantees.
- Missions never involve touching, picking or eating anything.

## Stack

| Piece | Choice | Why |
|---|---|---|
| Vision + reasoning | Gemma 3 4B (Ollama, Q4_K_M) | open-weight, multimodal, runs on CPU |
| Backend | FastAPI + SQLite | single file, zero infra |
| Frontend | Vanilla JS PWA, zero external assets | works fully offline |
| Total cost | €0 | — |

## Run it yourself

```bash
# 1. Install Ollama and pull the model
ollama pull gemma3:4b

# 2. Start the app
pip install fastapi uvicorn pillow
python3 app/server.py

# 3. Open http://localhost:8347 on a phone on the same network
```

On a 24-core CPU, one identification takes ~30-40 s — slow enough to look at the
real thing while you wait. Which, honestly, is also the point.

## How it works

```
📱 phone camera ──► FastAPI ──► Gemma 3 (local vision) ──► strict JSON
                                                              │
        field journal (SQLite) ◄── safety net (code) ◄────────┘
```

One model call returns the identification, the kid fact, the safety badge, the
next mission and a quiz question — everything the screen shows, so the screen
stays the shortest part of the experience.

## License

MIT — take it to your own woods.
