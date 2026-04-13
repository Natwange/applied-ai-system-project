# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch**

---

## 2. Goal / Task

VibeMatch suggests songs from a small catalog that match how a user is feeling and what kind of music they like. It takes in a user's favorite genre, current mood, preferred energy level, and whether they like acoustic music, then returns the top 5 songs that best fit that description.

This is a classroom simulation, not a production system. It is designed to help you understand how real recommenders like Spotify or YouTube Music work under the hood — not to replace them.

---

## 3. Data Used

- **Catalog size:** 18 songs stored in `data/songs.csv`
- **Features per song:** title, artist, genre, mood, energy (0.0–1.0), tempo (BPM), valence, danceability, acousticness, instrumentalness
- **Genres represented:** pop, rock, lofi, metal, jazz, blues, classical, hip-hop, r&b, reggae, country, ambient, synthwave, indie pop, afrobeats (15 genres total)
- **Moods represented:** happy, chill, intense, relaxed, moody, focused, energetic, romantic, melancholic, nostalgic, angry, sad, peaceful, uplifting (14 moods total)
- **Limits:** The catalog is hand-crafted and tiny. Most genres and moods appear on only one song. There is no real-world listening data, no user history, and no songs from non-Western music traditions. The dataset reflects a narrow slice of musical taste.

---

## 4. Algorithm Summary

The system works in three steps.

**Step 1 — Filter.** Before doing any scoring, the system throws out every song that does not share the user's mood or genre. This keeps the list manageable. If fewer than 5 songs survive the filter, it keeps all 18 to make sure it can always return a full list.

**Step 2 — Score.** Each surviving song is given a score starting at zero. Points are added based on three things:
- Does the song's mood match what the user said? If yes, **+4 points.** This is the biggest reward.
- Does the song's genre match? If yes, **+1.5 points.**
- How close is the song's energy to what the user wants? A perfect energy match adds **up to +4 points.** A big mismatch adds close to zero.

The maximum possible score is 9.5 (mood + genre + perfect energy match).

**Step 3 — Rank.** Songs are sorted from highest to lowest score. The top 5 are returned along with a plain-language explanation of why each one was chosen.

No code, no machine learning — just addition and comparison.

---

## 5. Strengths

- **Works well when preferences are consistent.** Users whose mood and genre point at the same kinds of songs get clean, sensible results. The chill acoustic user and the workout user both received top 5 lists that matched their stated taste every time.
- **Transparent explanations.** Every recommendation comes with a reason ("mood matches", "genre matches", "energy is close"). There are no hidden factors — you can always see exactly why a song ranked where it did.
- **Handles missing preferences gracefully.** If a user's mood or genre doesn't exist in the catalog, the system falls back to energy proximity rather than crashing or returning nothing.
- **Fast and simple.** Because the logic is just arithmetic, it runs instantly and is easy to reason about. You don't need to train a model or collect user data.

---

## 6. Observed Behavior / Biases

**Mood dominance creates a genre filter bubble.**
The scoring function awards +4.0 points for a mood match and only +1.5 for a genre match, meaning mood is always the strongest signal. During adversarial testing, a user who listed "pop" as their favorite genre but "sad" as their current mood received a blues song as their #1 recommendation — ahead of every pop song in the catalog — simply because it was the only sad-labeled track. The system never asked whether the user actually wanted blues; it just followed the math. This means users who describe a momentary emotional state get recommendations driven by that feeling rather than their deeper musical taste, which is likely the opposite of what they want.

**Single-song moods create a ceiling for underrepresented feelings.**
Eleven of the fourteen moods in the catalog appear on exactly one song each (6% of the catalog). If a user's preferred mood is "nostalgic", "romantic", or "melancholic", there is only one song that can ever earn the mood bonus. That song will rank first regardless of whether it matches any other preference, while the remaining 17 songs compete only on genre and energy. Users with rare moods effectively have no choice — the system is locked in before genre or energy even matter.

**The pre-filter can silently eliminate better matches.**
Before scoring starts, the system discards every song that does not match the user's mood or genre. A jazz song with near-perfect energy and valence is invisible to a hip-hop fan whose mood does not appear in any jazz track. This creates a filter bubble at the filtering step, not the scoring step — the user never sees these songs, and no explanation is generated to tell them they were excluded.

---

## 7. Evaluation Process

Seven user profiles were tested in total — three standard profiles and four adversarial edge cases — using the full 18-song catalog.

**Standard profiles tested:**

- **Chill Acoustic User** (lofi, chill mood, energy 0.35) — Tested whether the system could serve a user who wants calm, quiet music. Results were consistent: lofi and ambient songs dominated the top 5, and every result had a clear reason in the explanation. This profile worked as expected.
- **Workout User** (rock, intense mood, energy 0.92) — Tested the high-energy end of the catalog. The top result was always a high-energy song (energy ≥ 0.7). This profile also behaved as expected.
- **Melancholic Classical User** (classical, melancholic mood, energy 0.22) — Tested the low-energy, acoustic end. All top 3 results had energy ≤ 0.6. Worked as expected, though only one song in the catalog was actually classical, so the genre bonus fired just once.

**Adversarial profiles tested:**

- **Nonexistent Mood (pop + anxious, energy 0.9)** — "Anxious" does not exist as a mood in the catalog. Expected the system to fall back on genre. It did — pop songs ranked #1 and #2 — but the scores were noticeably weaker (4.9 vs the 9.4 you get when mood also matches). This revealed how much scoring power mood normally carries.
- **Conflicting Genre + Mood (metal + chill, energy 0.4)** — The user said they like metal but are currently feeling chill. Surprisingly, zero metal songs appeared in the top 3. Three lofi songs ranked ahead of the lone metal track because mood weight (4.0) beat genre weight (1.5). The system followed the math correctly but the result would likely frustrate a real metal fan.
- **Both Unknown (bossa nova + anxious, energy 0.5)** — Neither genre nor mood exist in the catalog. The system degraded entirely to energy proximity, returning five songs from completely different genres with scores clustered between 1.80–1.96. This is the floor behavior — the system technically works but has no real taste signal to follow.
- **Mood Overrides Genre (pop + sad, energy 0.9)** — The most surprising result. A user who listed pop as their favorite genre but sad as their mood received a blues song at #1. The single sad song in the catalog (Blue Harbor, energy 0.44) outscored every pop song despite being quiet, slow, and in a completely different genre. This was the clearest proof that mood dominance can override the user's stated long-term preference.

**What surprised me most:** The system behaved predictably when a user's preferences were consistent, but broke down in interesting ways when they conflicted. The scoring weights were designed for users whose mood and genre reinforce each other — they were never stress-tested against a user whose emotional state and musical taste point in different directions.

---

## 8. Intended Use and Non-Intended Use

**This system is intended for:**
- Classroom exploration of how content-based recommenders work
- Learning how scoring weights shape the output of a simple AI system
- Demonstrating the difference between collaborative filtering and content-based filtering

**This system is NOT intended for:**
- Real music discovery by actual users — the catalog is too small and too narrow
- Any commercial or production use
- Recommending music to users with diverse tastes outside of Western pop, rock, or lofi genres
- Making decisions that affect real people, since the system has no way to verify whether its output is actually good for someone

---

## 9. Ideas for Improvement

1. **Balance the mood and genre weights.** The current gap between mood (+4.0) and genre (+1.5) is too wide. A user's genre preference represents their long-term taste while mood is a short-term state. One approach: give the user a "context mode" toggle — "match my mood" vs "match my usual taste" — and adjust the weights accordingly.

2. **Expand the catalog and reduce single-song moods.** Most moods and genres appear on only one song. Adding 5–10 songs per mood category would give the scoring function real options to choose between, instead of locking in the only available match. The system cannot be meaningfully evaluated on diversity until there are at least a few songs per mood.

3. **Score more features.** Tempo, danceability, valence, and acousticness are stored in the data but completely ignored during scoring. A user who likes acoustic music (`likes_acoustic=True`) currently gets no benefit from that preference. Wiring these features into the score — even with small weights — would make the system more expressive and more personal.

---

## 10. Personal Reflection

**What was my biggest learning moment?**

The biggest moment was running the "pop + sad" adversarial profile and watching a blues song rank #1 ahead of every pop song. I had written the scoring weights myself — mood +4.0, genre +1.5 — so I knew what they were. But knowing the numbers and seeing the consequence are different things. A user who calls themselves a pop fan gets a slow blues track because they admitted they are sad right now. The system did exactly what I told it to do, and it was still wrong. That gap between "correct math" and "useful result" was the clearest thing this project taught me.

**How did using AI tools help, and when did I need to double-check?**

AI tools helped most during the adversarial profile design phase — prompting me to think about what inputs would stress-test the logic rather than confirm it. It is easy to only test cases you expect to pass. The suggestions around conflicting preferences (a metal fan who is chill, a pop fan who is sad) pushed the testing toward the edges where the system actually breaks.

Where I had to double-check: the first version of the adversarial tests assumed "sad" was not in the catalog, which was wrong — it appears on one song. The tests were written before the catalog was verified, so two of them failed with misleading error messages. The lesson was that AI-suggested test cases need to be grounded in what the data actually contains, not what you assume it contains. Running the catalog analysis first (`moods`, `genres`, counts) was what caught this.

**What surprised me about how simple algorithms can still "feel" like recommendations?**

The explanation feature surprised me the most. Once each result came with a reason — "mood matches (happy)", "genre matches (pop)", "energy is close (0.82)" — the output stopped feeling like a list of numbers and started feeling like a suggestion someone made. The underlying math is just addition, but wrapping it in a sentence that says "because" makes it feel intentional. That is probably doing a lot of work in real apps too: the explanation makes the recommendation feel trustworthy even when the logic behind it is simple.

**What would I try next?**

The most interesting next step would be adding a second dimension to the user profile: separating long-term taste from current context. Right now the system treats "my favorite genre is pop" and "I am feeling sad" as two inputs feeding the same scoring function, which is why mood can override genre. A better design would score genre and mood on separate tracks — "here are songs that fit your taste" vs "here are songs that fit your current mood" — and let the user decide which list they want. That one change would fix the biggest bias this project exposed without requiring any new data.
