# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

### System Flow

```
Input (UserProfile) → Load all songs → Pre-filter candidates → Score each candidate → Rank by score → Explain → Output
```

### What Each Song Stores

Each `Song` tracks: `genre`, `mood`, `energy`, `tempo_bpm`, `valence`, `danceability`, `acousticness`, and `instrumentalness`.

The three features actively used in scoring are **mood**, **genre**, and **energy**. The rest are stored but not yet scored — available for future improvements.

### What the UserProfile Stores

`favorite_genre`, `favorite_mood`, `target_energy`, and `likes_acoustic`.

### Algorithm Recipe

1. **Load** — Read all songs from `songs.csv` into memory as `Song` objects.
2. **Pre-filter** — Keep only songs that match the user's mood **or** genre. If fewer candidates than `k` remain, fall back to all songs so we always return a full list.
3. **Score** each candidate (starts at 0):
   - Mood match → **+4.0** (highest weight — mood drives listening context more than genre)
   - Genre match → **+3.0**
   - Energy closeness → `(1.0 - abs(song.energy - user.target_energy)) * 2.0` — max **+2.0**
4. **Rank** — Sort all scored candidates in descending order, return top `k`.
5. **Explain** — For each result, generate a plain-language reason based on which features matched.

### Filtering Approach: Context-Based

This system uses **context-based filtering** — it recommends songs similar to what the user says they like, based on features like mood and genre. It does not use **collaborative filtering** (what other users liked), which is the second layer real-world systems like Spotify add on top.

### Potential Biases

- **Mood dominance** — Mood carries the most weight (+4.0). A song that perfectly matches genre and energy but not mood will almost always rank below a mood-match, even if it's a better fit overall.
- **Pre-filter blind spots** — Songs that don't match on mood or genre are eliminated early. A great song that fits the user's energy perfectly but belongs to an unexpected genre will never be scored unless the fallback triggers.
- **Energy is the only numeric feature scored** — Tempo, danceability, and valence are ignored in scoring. A slow, low-danceability song can score the same as a high-energy dance track if genre and mood match.
- **No personalization over time** — Every recommendation starts fresh. The system has no memory of what the user skipped or replayed, so it can't improve from feedback.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

## Terminal Image
![alt text](terminal_image.png)