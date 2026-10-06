---
title: Nature Detective — the offline AI that sends my kids back outside
published: false
tags: devchallenge, hf26challenge, gemma, opensource
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

Last Sunday I watched my kids walk past a hundred fascinating things without seeing a single one.

We live in Mersch, in the middle of Luxembourg — fifteen minutes from forests that have more species per square meter than my phone has apps. And yet the walk was negotiations: five more minutes of screen, then we'll go. The screen is the destination. The forest is the commute.

So for this challenge I built the opposite deal: **the screen becomes the reason to go into the forest — and the forest stays the point.**

## What I Built

**Nature Detective** is an offline-first nature companion for kids aged 5-10.

A child photographs something alive — a plant, a beetle, a mushroom. An **open-weight vision model (Gemma 3 4B, running entirely on local hardware)** identifies the find, tells one true fun fact a seven-year-old would love, sets a safety rule, and then does the thing no engagement-optimized app would ever do: **it sends the kid back outside.**

> 🎯 *"Count how many different colored flowers you can spot before the next corner!"*

Every identification comes with a mission — count, find, compare, observe. Missions never involve the screen. The screen is the shortest part of the experience, by design.

Every discovery lands in a **field journal** on the device, with a detective rank that grows with real outdoor finds (🐣 → 🐾 → 🦊 → 🦉). No account, no ads, no streak anxiety — just a collection of afternoons.

**[Try the live demo](https://main-michael-stanford-myrtle.trycloudflare.com)** — it runs on my own machine, on Gemma 3, right now.

![The result screen: a bee identified, a safety badge, the next outdoor mission](https://raw.githubusercontent.com/jeffreyturov-dev/nature-detective/master/assets/shot2_result.png)

## Demo

The full flow, no signup, works from a phone browser:

1. Open the [live demo](https://main-michael-stanford-myrtle.trycloudflare.com)
2. Snap a discovery (or upload any plant/insect photo)
3. Get the identification, the fact, the safety badge — and your mission
4. Check the field journal

Fair warning: inference on a 24-core CPU takes ~15-60 seconds depending on load. Slow enough to look at the real thing while you wait — which, honestly, is also the point.

## Code

{% github jeffreyturov-dev/nature-detective %}

The whole stack, MIT licensed:

| Piece | Choice | Why |
|---|---|---|
| Vision + reasoning | Gemma 3 4B via Ollama (Q4_K_M) | open-weight, multimodal, runs on CPU |
| Backend | FastAPI + SQLite | one file, zero infra |
| Frontend | Vanilla JS PWA, zero external assets | the offline claim has to be true |
| Cost | €0 | no API key, no per-call fee, ever |

## How I Built It

One model call turns a photo into a strict JSON object: identification, kid fact, safety level, next mission, quiz question. Everything the screen shows, in a single pass — because a children's app in a forest cannot afford round trips, and mine literally has none to afford: it runs where there is no signal.

```
📱 phone camera ──► FastAPI ──► Gemma 3 (local vision) ──► strict JSON
                                                              │
        field journal (SQLite) ◄── safety net (code) ◄── verifier pass
```

The interesting part is not the pipeline. It's what the pipeline refuses to do.

## The part I'm most proud of: what it refuses to do

During testing, I fed the app an abstract watercolor — green and yellow blur, no living thing in it. A single-pass version of the app answered, with high confidence: **"Spiderweb, Araneae."**

It was a confident, detailed, completely fabricated answer. The most dangerous kind of wrong — the kind a child would believe, remember, and repeat at school.

An app that teaches nature to kids has one job that outranks every other: **never teach a lie.** So now every identification goes through a second pass — a verifier, running on the same local model, whose only job is to doubt the first answer. The trick that makes it actually work: the verifier **never sees the claim first**. It must describe what it objectively sees — *"The image is an abstract painting, not a living organism."* — and only then decide whether the claim matches its own independent observation. Ask it to judge the claim directly and it politely agrees with everything; make it commit to its own eyes first, and it catches the lie.

The abstract painting now gets the honest answer: *"A first guess said this might be a spiderweb, but my double-check disagreed — and a good detective never teaches a maybe as a fact. Ask a grown-up or a field guide!"*

Teaching a child that "I don't know" is a respectable answer might be the most valuable feature in the whole app.

Safety works the same way — enforced twice, because prompt rules are suggestions and **code rules are guarantees**. The model is instructed that mushrooms and berries are always *look, don't touch*. And then the backend overrides it in code anyway, every time, no matter what the model says. When I tested it with a fly agaric (*Amanita muscaria* — the red one with white dots, beautiful and toxic), it identified it correctly *and* refused any interaction with it, twice over.

## Why Does Open Innovation Matter?

This project doesn't just *use* open weights. **It only exists because of them.**

- **The forest has no bars.** The whole point is a place with no signal. A closed API is a product that stops working exactly where mine starts working. Local inference isn't an optimization here — it's the product.
- **I will never upload my kids' photos to someone else's server.** Not their faces, not their location, not their finds. With Gemma running on my own hardware, nothing ever leaves the device. That's not a privacy policy; it's physics.
- **€0, forever.** No API key, no subscription, no per-call cost — so it can run in a school, a scout group, a nature club with no budget, anywhere in the world.
- **Ownable and swappable.** Any open-weight vision model Ollama can serve drops in with a one-line change. When a better small multimodal model ships next month, every Nature Detective gets smarter for free. Try getting that guarantee from a deprecated API version.

A closed model would have made this easier to demo and impossible to believe in.

## Prize Categories

- **Best Use of Gemma** — Gemma 3 4B is the entire brain of the project: species identification, kid-level explanations, mission generation, and the self-verification pass, all running locally through Ollama.

---

This Sunday we're going back to the forest. My kids already asked if the detective is coming.

He's in my pocket. He knows nothing about engagement metrics. And his favorite sentence, by far, is: *"Now go look for yourself."* 🌿
