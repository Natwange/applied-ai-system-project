from typing import Protocol
from src.models import Song, UserProfile


class ScoringStrategy(Protocol):
    label: str

    def score(self, user: UserProfile, song: Song) -> float:
        ...


class MoodFirstStrategy:
    label = "Mood-First"

    def score(self, user: UserProfile, song: Song) -> float:
        score = 0.0
        if song.mood == user.favorite_mood:
            score += 5.0
        if song.genre == user.favorite_genre:
            score += 1.5
        energy_diff = abs(song.energy - user.target_energy)
        score += (1.0 - energy_diff) * 2.0
        if user.likes_acoustic:
            score += song.acousticness * 1.5
        else:
            score += (1.0 - song.acousticness) * 1.5
        return round(score, 2)


class GenreFirstStrategy:
    label = "Genre-First"

    def score(self, user: UserProfile, song: Song) -> float:
        score = 0.0
        if song.genre == user.favorite_genre:
            score += 5.0
        if song.mood == user.favorite_mood:
            score += 2.0
        energy_diff = abs(song.energy - user.target_energy)
        score += (1.0 - energy_diff) * 2.0
        if user.likes_acoustic:
            score += song.acousticness * 1.5
        else:
            score += (1.0 - song.acousticness) * 1.5
        return round(score, 2)


class EnergyFocusedStrategy:
    label = "Energy-Focused"

    def score(self, user: UserProfile, song: Song) -> float:
        score = 0.0
        energy_diff = abs(song.energy - user.target_energy)
        score += (1.0 - energy_diff) * 5.0
        if song.mood == user.favorite_mood:
            score += 1.5
        if song.genre == user.favorite_genre:
            score += 1.0
        if user.likes_acoustic:
            score += song.acousticness * 1.5
        else:
            score += (1.0 - song.acousticness) * 1.5
        return round(score, 2)


class BalancedStrategy:
    label = "Balanced"

    def score(self, user: UserProfile, song: Song) -> float:
        score = 0.0
        if song.mood == user.favorite_mood:
            score += 2.5
        if song.genre == user.favorite_genre:
            score += 2.5
        energy_diff = abs(song.energy - user.target_energy)
        score += (1.0 - energy_diff) * 2.5
        if user.likes_acoustic:
            score += song.acousticness * 1.5
        else:
            score += (1.0 - song.acousticness) * 1.5
        return round(score, 2)


STRATEGIES: dict[str, ScoringStrategy] = {
    "1": MoodFirstStrategy(),
    "2": GenreFirstStrategy(),
    "3": EnergyFocusedStrategy(),
    "4": BalancedStrategy(),
}

DEFAULT_STRATEGY = MoodFirstStrategy()
