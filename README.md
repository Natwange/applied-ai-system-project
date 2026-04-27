# VibeFinder 2.0 — Feedback-Driven Music Recommendation

VibeFinder 2.0 is an interactive, agentic music recommendation system built in Python. It recommends songs based on your preferences, accepts natural-language feedback, updates its internal model of your taste, and reruns recommendations — all within a single CLI session.

---

## Original Project — VibeFinder 1.0

VibeFinder 1.0 (Modules 1–3) was a rule-based music recommender that took a static user profile (genre, mood, energy, acoustic preference) and returned a ranked list of 5 songs from an 18-song catalog using a hardcoded scoring function. It generated plain-language explanations for each recommendation but had no feedback loop, no input validation, and no way to refine results after the initial output. The project established the core data model and scoring architecture that VibeFinder 2.0 is built on.

---

## What VibeFinder 2.0 Adds

| Feature | 1.0 | 2.0 |
|---|---|---|
| Recommendation engine | One-shot | Iterative feedback loop (up to 3 rounds) |
| Input handling | No validation | Guardrails, fuzzy matching, clamping |
| Scoring | Fixed weights | 4 swappable scoring strategies |
| Acoustic scoring | Stored, not used | Active scoring dimension |
| Feedback | None | Natural-language → profile updates |
| Observability | Print statements | Structured tool-call trace + session log |
| Song catalog | 18 songs | 48 songs across 15 genres and 14 moods |
| Evaluation | Manual | 16-scenario automated harness |

---

## Architecture Overview

```
User / CLI
    │
    ▼
Input Validator ──(fuzzy match, clamp, warn)──► Profile Builder
    │
    ▼
Scoring Mode Selector  [Mood-First | Genre-First | Energy-Focused | Balanced]
    │
    ▼
Agent Orchestrator  ◄────────────────────────────────────┐
    │  plan_round() → dispatch_tool()                     │
    ▼                                                     │
Recommendation Engine                           Profile Updater
    │  score_song() × 48 songs                           │
    ▼                                                     │
Explanation Engine                             Feedback Interpreter
    │                                                     │
    ▼                                                     │
Top-5 Results + Explanations ──► Human ──► Feedback ─────┘
    │
    ▼
Session Summary + Log File
    │
    ▼
Evaluation Harness  [16 pass/fail scenarios → optional Markdown report]
```

The **Agent Orchestrator** is the core of the system. Rather than executing steps silently, it names each action as a tool call before dispatching it — `parse_feedback()`, `update_profile()`, `rerun_recommender()` — and logs every step to both the console and a timestamped session file. This makes the reasoning observable at runtime and auditable after the fact.

The **Scoring Strategy** pattern means the four ranking modes are interchangeable objects. Swapping from Mood-First to Energy-Focused changes which dimension dominates without touching the scoring logic itself.

---

## Setup

**Requirements:** Python 3.12+

```bash
# 1. Clone the repository
git clone <repo-url>
cd applied-ai-system-project

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python -m src.main

# 5. Run the evaluation harness
python -m scripts.evaluate

# 6. Save an evaluation report
python -m scripts.evaluate --save

# 7. Run tests
pytest
```

No API keys or external services required. Everything runs locally.

---

## Sample Interactions

### Demo 1 — Normal case with energy feedback

```
==================================================
  VibeFinder 2.0 — Tell us your preferences
==================================================
  Favourite genre: pop
  Current mood: happy
  Target energy (0.0 – 1.0): 0.8
  Like acoustic music? (yes / no): no

  Select a scoring mode:
    [1] Mood-First      [2] Genre-First
    [3] Energy-Focused  [4] Balanced
  Enter 1–4 (default 1): 1
  Using: Mood-First

  --- Initial Recommendations ---

  1. Sunrise City — Neon Echo
     Genre: pop  |  Mood: happy  |  Energy: 0.82  |  Score: 9.69
     Recommended because: mood matches "happy", genre matches "pop",
     energy is very close to your target (0.82 vs 0.80) [Mood-First]

  2. Rooftop Lights — Indigo Parade
     Genre: indie pop  |  Mood: happy  |  Energy: 0.76  |  Score: 7.82
     Recommended because: mood matches "happy",
     energy is near your target (0.76 vs 0.80) [Mood-First]

  ...

  Your feedback: too energetic

  Interpretation:
    detected energy signal → energy down by 0.15

  [TOOL]  parse_feedback()   → energy_delta=-0.15, mood=None, genre=None
  [TOOL]  update_profile()   → 1 change(s)
  [PROFILE] target_energy: 0.80 → 0.65
  [TOOL]  rerun_recommender() → 5 results, top score 8.94

  Profile updates:
    target_energy: 0.80 → 0.65

  --- Refined Recommendations (Round 1) ---

  1. Sunrise City — Neon Echo
     Genre: pop  |  Mood: happy  |  Energy: 0.82  |  Score: 8.35
     Recommended because: mood matches "happy", genre matches "pop" [Mood-First]

  2. Block Party — Kenzo Floe
     Genre: hip-hop  |  Mood: uplifting  |  Energy: 0.79  |  Score: 5.81
     ...
```

---

### Demo 2 — Edge case: unknown mood with fallback

```
  Favourite genre: bossa nova
  Current mood: anxious
  Target energy (0.0 – 1.0): 0.4
  Like acoustic music? (yes / no): yes

  [!] Genre "bossa nova" not found in catalog. Genre matching will be skipped.
  [!] Mood "anxious" not found in catalog. Mood matching will be skipped,
      falling back to genre and energy.

  [GUARDRAIL] Genre "bossa nova" not found in catalog.
  [GUARDRAIL] Mood "anxious" not found in catalog.

  --- Initial Recommendations ---

  1. Library Rain — Paper Lanterns
     Genre: lofi  |  Mood: chill  |  Energy: 0.35  |  Score: 3.41
     Closest available match under Mood-First mode.
  ...
```

The system does not crash. It warns the user, falls back gracefully, and still returns 5 results ranked by energy proximity and acoustic alignment.

---

### Demo 3 — Liked song inference

```
  Your feedback: I liked song 2

  Interpretation:
    detected liked songs → IDs [4]

  [TOOL]  parse_feedback()     → energy_delta=+0.00, mood=None, genre=None
  [TOOL]  update_profile()     → 1 change(s)
  [PROFILE] liked song 4 (Library Rain): energy nudge 0.80 → 0.79

  Profile updates:
    liked song 4 (Library Rain): energy nudge 0.80 → 0.79
```

The system extracts the features of the liked song and gently nudges `target_energy` toward it. Future recommendations for songs similar in genre or mood to the liked song are flagged as `ranked higher after your feedback` in the explanation.

---

## Design Decisions

**Rule-based feedback interpreter, not an LLM.**
Using Claude or GPT to parse feedback would make the system harder to test, less predictable, and would hide the reasoning inside a model call. A rule-based interpreter is fully transparent — you can read exactly how `"too energetic"` becomes `energy_delta = -0.15`. This was the right trade-off for a system where observability and reliability were explicit goals.

**Strategy pattern for scoring modes.**
Hardcoding four sets of weights into one function would have made the code fragile and the modes invisible to the user. The Strategy pattern keeps each mode as a standalone object and makes the active mode part of the session trace. Adding a fifth mode later is a one-file change.

**Fuzzy matching over hard rejection.**
When a user types `"happ"` or `"lofy"`, rejecting the input outright is a bad experience. Using Python's built-in `difflib` to suggest the closest valid value and warn — rather than crash — makes the system usable without sacrificing correctness. Hard rejection is reserved only for inputs that can't be recovered (non-numeric energy, non-yes/no acoustic).

**Liked-song inference as a partial nudge, not an override.**
When you say you liked a song, its energy is not immediately adopted as your new target. Instead, `target_energy` moves 10% of the distance toward the liked song's energy. This prevents a single feedback signal from completely overriding the user's stated preference, which is the behaviour you'd want from a real system.

---

## Testing Summary

**44 unit tests across 3 files — all passing.**

| File | Tests | What it covers |
|---|---|---|
| `test_recommender.py` | 12 | Scoring, ranking, explanations, adversarial profiles |
| `test_validator.py` | 16 | Input validation, fuzzy matching, edge cases |
| `test_feedback.py` | 16 | Feedback parsing, profile updates, energy clamping |

**16-scenario evaluation harness** covering normal users, adversarial inputs, and feedback refinement loops.

**What worked well:** The modular design meant each component could be tested independently. Validator and feedback tests were straightforward to write because the functions have clear inputs and outputs. The evaluation harness caught a real issue early — the energy nudge from liked-song inference was too small (0.002) to survive rounding at 2 decimal places with songs that were very close in energy to the target.

**What was harder:** Testing the agent's tool-dispatch loop required simulating the feedback cycle programmatically rather than interactively. The evaluation script handles this by calling `parse_feedback` and `update_profile_from_feedback` directly, bypassing the CLI.

**Known limitation:** The feedback interpreter is keyword-based, so phrasing like `"dial back the intensity"` won't be detected even though it means the same thing as `"too energetic"`. A more robust system would use embeddings or a small classification model.

---

## Reflection

Building VibeFinder 2.0 clarified something that isn't obvious from reading about AI systems: the hardest part is not the algorithm, it is the edges. The scoring function took an afternoon. The guardrails, feedback conflict resolution, and energy-nudge rounding took longer — because that is where the system either handles reality gracefully or silently fails.

The decision to keep the feedback interpreter rule-based taught me something about the trade-off between capability and trustworthiness. An LLM-based interpreter would understand more phrases. But it would also be harder to test, slower to explain, and dependent on an external service. For a system where the whole point is observable reasoning, adding a black box in the middle would undermine the thing that makes it interesting.

The agentic loop — where the system plans which tools to call, calls them, logs each one, and shows the user what changed — also shifted how I think about what "AI" means in a product. The intelligence here is not in any single function. It is in the structure: the feedback-update-rerank cycle, the conflict resolution rules, the session trace. That is the part that makes the system feel like it reasons, even though every decision is deterministic and readable.

### Limitations and Bias

The most persistent bias is mood dominance. Because mood carries the highest scoring weight, a user who declares a genre preference but is currently in a different emotional state will consistently receive results that match their mood over their genre. A pop fan who is feeling melancholic gets blues and classical songs ahead of pop — every single time, by design. This is not a bug, but it would disadvantage users whose emotional state regularly differs from their stated taste.

The feedback interpreter is keyword-dependent. Phrases like "dial back the energy" or "something more laid-back" will not be detected, even though they clearly mean the same thing as "less energetic." A user who does not phrase feedback in the expected keywords gets no profile update and no explanation — the system just moves on silently.

### Could This Be Misused?

A music recommender is low-stakes, but the underlying pattern — collecting preference signals, updating an internal user model, and adjusting outputs accordingly — is exactly the same pattern used in systems with higher consequences (news feeds, ad targeting, hiring tools). The risk in those contexts is that iterative feedback loops can create filter bubbles or reinforce existing biases in the data rather than expanding what the user is exposed to. In VibeFinder, the nudge system deliberately limits how far a single feedback signal can shift the profile (10% of the gap, not a full override) as a small guard against this. In a production system, that kind of dampening and diversity injection would need to be much more deliberate.

### What Surprised Me During Testing

The most surprising failure was the energy nudge rounding issue. When a user likes a song whose energy is very close to their current target (e.g., 0.82 vs a target of 0.80), the nudge — 10% of a 0.02 gap — is 0.002. After rounding to two decimal places, that disappears entirely. The profile records the song as liked, but the energy value does not visibly change. The system behaved exactly as coded, but the result felt wrong: the user liked a song and nothing seemed to happen. This is the kind of failure that only appears when you run the system on real data with real numbers, not when you reason about the logic abstractly.

### Collaboration with AI During This Project

AI was used throughout the planning and implementation of VibeFinder 2.0.

**One instance where it was genuinely helpful:** AI proposed using the Strategy pattern for the scoring modes early in the design phase. Rather than hardcoding four sets of weights into a single function with conditional branches, it suggested making each mode a standalone object that the recommender accepts as a parameter. That recommendation made the modes testable in isolation, made the active mode visible in the session trace, and would make adding a fifth mode later a one-file change. It was the right architectural call and I would not have framed it that way on my own.

**One instance where its suggestion was flawed:** AI initially suggested using an LLM API (Claude or GPT) to interpret the user's natural-language feedback. The reasoning was that it would handle a wider range of phrasings more gracefully than keyword matching. That is technically true, but the suggestion was wrong for this project. An LLM-based interpreter would make the feedback loop non-deterministic, much harder to test (you cannot write a unit test that reliably checks what an LLM will return), dependent on an external service with latency and cost, and fundamentally opaque — the exact opposite of the observable reasoning the system was designed to demonstrate. The rule-based approach was the right call, and the AI's suggestion to use an LLM had to be rejected on architectural grounds, not capability grounds.

---

## Project Structure

```
src/
  models.py         Song, UserProfile, SessionState
  data_loader.py    CSV loading with field validation
  scoring_modes.py  4 scoring strategies (Strategy pattern)
  recommender.py    Scoring, ranking, explanations
  validator.py      Input guardrails and fuzzy matching
  feedback.py       Natural-language feedback interpreter
  logger.py         Structured console + file logging
  agent.py          Session orchestrator and tool dispatch
  main.py           CLI entry point
scripts/
  evaluate.py       16-scenario evaluation harness
data/
  songs.csv         48 songs across 15 genres, 14 moods
tests/
  test_recommender.py
  test_validator.py
  test_feedback.py
logs/               Auto-generated session logs
reports/            Optional evaluation report output
```

---

## Model Card

See [model_card.md](model_card.md) for a full breakdown of intended use, limitations, bias analysis, and evaluation methodology.

Demo Video Link:
[click me!](https://www.loom.com/share/92e259fb10164af89b4647a459977b15)