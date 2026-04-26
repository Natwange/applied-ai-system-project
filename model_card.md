# Model Card: VibeFinder 2.0

## 1. Model Name and Version

**VibeFinder 2.0** (upgraded from VibeFinder 1.0 / VibeMatch)

VibeFinder 1.0 was a one-shot, rule-based music recommender that took a static user profile and returned a ranked list of 5 songs with no ability to refine results. VibeFinder 2.0 extends this into an interactive, feedback-driven system with an agentic workflow, input guardrails, swappable scoring strategies, and an automated evaluation harness.

---

## 2. Intended Use

VibeFinder 2.0 is a classroom demonstration of applied AI concepts — specifically content-based recommendation, agentic feedback loops, and reliability testing. It is designed to show how an AI system can update its internal model of user preferences based on natural-language feedback and produce different outputs as a result.

**Intended for:**
- Educational exploration of iterative AI systems and scoring strategies
- Demonstrating observable AI reasoning through tool-call traces and session logs
- Evaluating how guardrails and input validation affect system reliability

**Not intended for:**
- Real music discovery — the catalog is hand-crafted and limited to 48 songs
- Production or commercial use
- Recommending music to users with tastes outside the catalog's represented genres and moods

---

## 3. Data

- **Catalog size:** 48 songs in `data/songs.csv` (expanded from 18 in v1.0)
- **Features per song:** title, artist, genre, mood, energy (0.0–1.0), tempo (BPM), valence, danceability, acousticness, instrumentalness
- **Genres represented:** pop, rock, lofi, metal, jazz, blues, classical, hip-hop, r&b, reggae, country, ambient, synthwave, indie pop, afrobeats (15 genres, each with at least 2 songs)
- **Moods represented:** happy, chill, intense, relaxed, moody, focused, energetic, romantic, melancholic, nostalgic, angry, sad, peaceful, uplifting (14 moods, each with at least 2 songs)
- **Limits:** The catalog is hand-crafted with no real-world listening data, no user history, and no representation of non-Western music traditions. It reflects a narrow slice of musical taste chosen to support classroom evaluation scenarios.

---

## 4. Algorithm Summary

The system works in five stages.

**Stage 1 — Validate.** User input is validated and normalised before anything else. Genre and mood are fuzzy-matched against known values (e.g. "happ" → "happy"). Energy is clamped to [0.0, 1.0] if out of range. Unknown inputs trigger a warning and a fallback strategy rather than a crash.

**Stage 2 — Filter.** Songs that do not share the user's mood or genre are removed before scoring. If fewer than 5 candidates remain, the filter is lifted and all 48 songs are scored.

**Stage 3 — Score.** Each candidate song is scored using one of four interchangeable strategies:

| Strategy | Mood | Genre | Energy | Acoustic |
|---|---|---|---|---|
| Mood-First (default) | +5.0 | +1.5 | ×2.0 | ×1.5 |
| Genre-First | +2.0 | +5.0 | ×2.0 | ×1.5 |
| Energy-Focused | +1.5 | +1.0 | ×5.0 | ×1.5 |
| Balanced | +2.5 | +2.5 | ×2.5 | ×1.5 |

Acoustic alignment is now an active scoring dimension in all modes (it was stored but unused in v1.0).

**Stage 4 — Explain.** Each top-5 result receives a plain-language explanation citing which dimensions matched, how close the energy was, whether acousticness aligned, and whether the result was boosted by prior feedback.

**Stage 5 — Feedback loop.** The user provides natural-language feedback. The system parses it into structured adjustments (e.g. "too energetic" → `energy_target -= 0.15`), updates the internal user profile, and reruns stages 2–4. This repeats up to 3 times per session.

---

## 5. Strengths

- **Transparent reasoning.** Every recommendation comes with a cited reason. Every feedback interpretation is printed before it is applied. Every profile change is logged. Nothing is hidden.
- **Handles edge cases without crashing.** Unknown moods and genres fall back gracefully. Out-of-range energy is clamped. Unrecognised feedback prompts a retry rather than a silent failure.
- **Iterative refinement.** Unlike v1.0, the system improves its recommendations within a session based on what the user says. A user who starts with poor results can steer the system toward better ones through feedback.
- **Observable agentic behaviour.** The agent explicitly names and logs each tool call before executing it, making the decision chain readable at runtime and auditable after the session ends.

---

## 6. Limitations and Bias

**Mood dominance persists by design.**
In the default Mood-First strategy, mood carries a +5.0 bonus versus +1.5 for genre. A pop fan who is feeling melancholic will consistently receive results that match their mood over their declared genre preference. This is a documented design decision, not a bug — but it disadvantages users whose momentary emotional state differs regularly from their long-term musical taste.

**Keyword-dependent feedback interpreter.**
The feedback system uses keyword matching. Phrases that mean the same thing but use different words — "dial back the intensity", "something quieter", "not so in-your-face" — will not be detected. Users who do not phrase feedback in the expected vocabulary get no profile update and no explanation. The system moves on silently.

**Energy nudge rounding.**
When a user likes a song whose energy is very close to their current target, the 10% nudge can be too small to survive rounding to two decimal places. The profile records the song as liked, but the energy value appears unchanged. This is technically correct behaviour but feels like a non-response to the user.

**Small catalog limits diversity.**
48 songs across 15 genres and 14 moods means some combinations still have very few candidates. Evaluation results are cleaner than v1.0 but the system would behave differently at real catalog scale.

**No cross-session memory.**
Each session starts fresh. The system cannot learn from what a user skipped or replayed across multiple sessions.

---

## 7. Evaluation and Testing Results

### Unit Tests — 44/44 passing

| File | Tests | What it covers |
|---|---|---|
| `test_recommender.py` | 12 | Scoring, ranking, explanations, adversarial profiles |
| `test_validator.py` | 16 | Input validation, fuzzy matching, clamping, edge cases |
| `test_feedback.py` | 16 | Feedback parsing, profile updates, conflict handling, energy clamping |

Run with: `pytest`

### Evaluation Harness — 16/16 passing

Automated scenarios across three categories:

**Normal:** chill acoustic user, workout user, melancholic classical user, distinct users get distinct top results — all passed. The system consistently returns results that fit stated preferences when genre and mood are available in the catalog.

**Adversarial:** unknown mood fallback, unknown genre fallback, energy clamping, invalid energy raises error, invalid acoustic raises error, conflicting genre/mood (mood weight dominates) — all passed. Guardrails behave as designed across all edge cases.

**Feedback:** energy down, energy up, mood change, rerank shifts results, liked song nudges energy, unrecognised feedback produces no changes — all passed.

Run with: `python -m scripts.evaluate` or `python -m scripts.evaluate --save` for a Markdown report.

### What surprised me during testing

The most unexpected failure was the energy nudge rounding issue. When a user likes a song very close in energy to their current target (gap of 0.02), the nudge — 10% of that gap — is 0.002. After rounding to two decimal places, the profile's `target_energy` value does not visibly change. The song is correctly tracked as liked, but the energy field looks identical. The system behaved exactly as coded, and it still felt like it wasn't working. This only appeared by running the system on real catalog numbers, not by reasoning about the logic abstractly.

---

## 8. AI Collaboration

AI assistance (Claude) was used throughout the planning, architecture, and implementation of VibeFinder 2.0.

**One instance where AI was genuinely helpful:**
Early in the design phase, AI proposed using the Strategy pattern for the scoring modes. Rather than hardcoding four weight profiles into a single scoring function with conditional branches, it suggested making each mode a standalone object that the recommender accepts as a parameter. This made each mode independently testable, made the active mode visible in the session trace, and means adding a fifth mode later is a one-file change. It was the right architectural decision and one I would not have framed that way without the suggestion.

**One instance where AI's suggestion was flawed:**
AI initially recommended using a large language model API to interpret natural-language feedback, on the basis that it would handle a wider range of phrasings than keyword matching. This suggestion was rejected. An LLM-based interpreter would make the feedback loop non-deterministic, impossible to unit test reliably, dependent on an external service with latency and cost, and fundamentally opaque — the opposite of what this system is designed to demonstrate. The rule-based interpreter is more limited in vocabulary but fully transparent, testable, and self-contained. The AI's suggestion was technically capable but architecturally wrong for this project.

---

## 9. Ideas for Improvement

1. **Separate long-term taste from current mood.** The biggest bias in the system is that a momentary emotional state can override a user's declared genre preference. Scoring these on separate tracks — "songs that fit your taste" vs "songs that fit your current mood" — and letting the user choose would fix the most common failure case without requiring new data.

2. **Expand feedback vocabulary.** The keyword-based interpreter misses paraphrases. Embedding-based matching or a small intent classifier would let users express feedback more naturally without giving up testability.

3. **Add cross-session memory.** Saving a user's profile between sessions would let the system accumulate preference signals over time rather than starting fresh each run.

4. **Increase catalog size.** At 48 songs, some genre/mood combinations still have very few candidates. A catalog of 200–500 songs would give the scoring function real options to differentiate between, and make evaluation results more meaningful.

---

## 10. Personal Reflection

**What was the biggest learning moment?**

Running the adversarial profiles and watching the system behave correctly by the math but wrongly by intuition. A pop fan who says they are sad gets a blues song at #1. A metal fan who is feeling chill gets lofi at #1. The system did exactly what it was designed to do — and those results would frustrate real users. That gap between "the math is correct" and "the outcome is useful" is the most important thing this project taught me about AI system design. You cannot evaluate a recommender only by asking whether it follows its rules. You have to ask whether the rules produce results people actually want.

**What did this project teach me about AI and problem-solving?**

The parts that took the most time were not the algorithms — they were the edges. Input validation, conflict resolution, rounding behaviour, fallback strategies. These are the places where the system either handles reality gracefully or fails in ways that are hard to explain to a user. Building those parts well required thinking not about what the system should do when everything is correct, but about what it should do when something is wrong. That shift in perspective — from "make it work" to "make it fail safely" — is the most transferable thing I took from this project.
