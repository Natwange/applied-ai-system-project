from src.models import Song, UserProfile
from src.scoring_modes import ScoringStrategy, DEFAULT_STRATEGY


def score_song(user: UserProfile, song: Song, strategy: ScoringStrategy = DEFAULT_STRATEGY) -> float:
    return strategy.score(user, song)


def recommend(
    user: UserProfile,
    songs: list[Song],
    strategy: ScoringStrategy = DEFAULT_STRATEGY,
    k: int = 5,
) -> list[tuple[Song, float]]:
    candidates = [
        s for s in songs
        if s.mood == user.favorite_mood or s.genre == user.favorite_genre
    ]
    if len(candidates) < k:
        candidates = songs

    scored = [(song, score_song(user, song, strategy)) for song in candidates]
    ranked = sorted(scored, key=lambda x: x[1], reverse=True)
    return ranked[:k]


def explain_recommendation(
    user: UserProfile,
    song: Song,
    strategy: ScoringStrategy = DEFAULT_STRATEGY,
    feedback_boosted: bool = False,
) -> str:
    reasons = []

    if song.mood == user.favorite_mood:
        reasons.append(f'mood matches "{song.mood}"')

    if song.genre == user.favorite_genre:
        reasons.append(f'genre matches "{song.genre}"')

    energy_diff = abs(song.energy - user.target_energy)
    if energy_diff <= 0.15:
        reasons.append(f"energy is very close to your target ({song.energy:.2f} vs {user.target_energy:.2f})")
    elif energy_diff <= 0.3:
        reasons.append(f"energy is near your target ({song.energy:.2f} vs {user.target_energy:.2f})")

    if user.likes_acoustic and song.acousticness >= 0.6:
        reasons.append(f"high acousticness fits your preference ({song.acousticness:.2f})")
    elif not user.likes_acoustic and song.acousticness <= 0.3:
        reasons.append(f"low acousticness fits your preference ({song.acousticness:.2f})")

    if feedback_boosted:
        reasons.append("ranked higher after your feedback")

    if not reasons:
        return f"Closest available match under {strategy.label} mode."

    return "Recommended because: " + ", ".join(reasons) + f" [{strategy.label}]"


class Recommender:
    """Thin wrapper kept for backwards compatibility with existing tests."""

    def __init__(self, songs: list[Song], strategy: ScoringStrategy = DEFAULT_STRATEGY):
        self.songs = songs
        self.strategy = strategy

    def recommend(self, user: UserProfile, k: int = 5) -> list[Song]:
        results = recommend(user, self.songs, self.strategy, k)
        return [song for song, _ in results]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        return explain_recommendation(user, song, self.strategy)
