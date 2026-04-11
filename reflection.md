# Reflection: Comparing User Profile Outputs

## Chill Acoustic User vs. Workout User

The chill acoustic user (lofi, energy 0.35) and the workout user (rock, energy 0.92) sit at opposite ends of the energy scale, and the results look completely different. The chill user gets quiet lofi and ambient tracks — songs that feel like studying or sitting in a coffee shop. The workout user gets loud, fast tracks — metal, rock, afrobeats.

This makes sense because energy is a number. The system measures how far each song's energy is from what the user wants, so a loud metal track (energy 0.97) is very close to what the workout user asked for (0.92) and very far from what the chill user asked for (0.35). The two profiles are so different that they would never swap results.

---

## Chill Acoustic User vs. Melancholic Classical User

These two look similar on the surface — both want quiet, low-energy music — but they get slightly different results because their moods are different. The chill user's mood ("chill") appears on three songs in the catalog, so there are real options to choose from. The melancholic classical user's mood ("melancholic") appears on only one song, so that one song (Cold Window, classical piano) always ranks #1 no matter what.

The lesson here is that having a rare mood leaves you with almost no real choice. Once that single mood-match song takes the top spot, the rest of the list is just whatever has the closest energy — not necessarily what fits the user's taste. A user with a rare mood is getting a worse service than a user with a common mood, purely because of how the catalog is built.

---

## Workout User vs. Mood Overrides Genre User (pop + sad)

The workout user asked for something straightforward: intense, high-energy rock. The scoring logic agreed — every signal pointed at the same kinds of songs. The result felt right.

The "pop + sad" user is the opposite. They said they like pop music (a genre preference) but are feeling sad right now (an emotional state). These two things point at completely different songs in the catalog. The result was a blues song at #1 — Blue Harbor, which is slow, quiet, and not remotely pop. It won purely because it was the only sad song available, and the system gave sadness more points than it gave pop.

This is the clearest case where the system chose the user's mood over their musical taste. In a real app, you might want to ask: "Are you in the mood for something that matches how you feel, or something that fits your usual taste?" The current system has no way to ask that question — it just assumes mood always matters more.

---

## Why Does "Gym Hero" Keep Showing Up for Happy Pop Fans?

Gym Hero (by Max Pulse, genre: pop, mood: intense, energy: 0.93) appears in the top 3 for almost any user who likes pop, even users who want happy or relaxed music.

Here is why: the system gives +1.5 points for matching the user's genre (pop), and Gym Hero is one of only two pop songs in the entire catalog. So it almost always earns that genre bonus. On top of that, it has very high energy (0.93), which means it scores well for any user who wants medium-to-high energy music too.

But Gym Hero's mood is "intense" — not happy, not relaxed. A user who said they want happy pop is getting an intense gym track because the system counts the genre label ("pop") as a match, but does not penalize the system for the mood mismatch the way a human listener would.

In plain terms: the system sees the word "pop" and gives Gym Hero credit, even if the song would feel wrong to the actual person. This is what makes recommender systems hard to get right — a label like "pop" means many different things to different people, and the system treats it as a single fixed category.
