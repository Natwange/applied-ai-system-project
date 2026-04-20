from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Song:
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    instrumentalness: float = 0.0


@dataclass
class UserProfile:
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    genre_weight: float = 1.5
    mood_weight: float = 4.0
    energy_weight: float = 4.0
    acoustic_weight: float = 1.5
    liked_song_ids: list = field(default_factory=list)
    feedback_history: list = field(default_factory=list)

    def copy(self) -> "UserProfile":
        return UserProfile(
            favorite_genre=self.favorite_genre,
            favorite_mood=self.favorite_mood,
            target_energy=self.target_energy,
            likes_acoustic=self.likes_acoustic,
            genre_weight=self.genre_weight,
            mood_weight=self.mood_weight,
            energy_weight=self.energy_weight,
            acoustic_weight=self.acoustic_weight,
            liked_song_ids=list(self.liked_song_ids),
            feedback_history=list(self.feedback_history),
        )


@dataclass
class SessionState:
    profile: UserProfile
    round_number: int = 0
    max_rounds: int = 3
    profile_snapshots: list = field(default_factory=list)

    def snapshot(self) -> None:
        self.profile_snapshots.append(self.profile.copy())

    def rounds_remaining(self) -> int:
        return self.max_rounds - self.round_number

    def is_complete(self) -> bool:
        return self.round_number >= self.max_rounds
