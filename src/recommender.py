import csv
from typing import List
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
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
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Pre-filter songs by mood or genre, score each, and return the top k ranked results."""
        # Pre-filter: only score songs that match on mood OR genre
        candidates = [
            s for s in self.songs
            if s.mood == user.favorite_mood or s.genre == user.favorite_genre
        ]

        # Fallback: if not enough candidates to fill k, score everything
        if len(candidates) < k:
            candidates = self.songs

        scored = [(song, score_song(user, song)) for song in candidates]
        ranked = sorted(scored, key=lambda x: x[1], reverse=True)
        return [song for song, _ in ranked[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language string explaining why a song was recommended."""
        reasons = []

        if song.mood == user.favorite_mood:
            reasons.append(f"mood matches ({song.mood})")
        if song.genre == user.favorite_genre:
            reasons.append(f"genre matches ({song.genre})")

        energy_diff = abs(song.energy - user.target_energy)
        if energy_diff <= 0.2:
            reasons.append(f"energy is close ({song.energy})")

        return "Recommended because: " + ", ".join(reasons) if reasons else "Low match"


def load_songs(csv_path: str) -> List[Song]:
    """
    Loads all songs from a CSV file and returns a list of Song objects.
    Required by src/main.py
    """
    print(f"Loading songs from {csv_path}...")
    songs = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append(Song(
                id=int(row["id"]),
                title=row["title"],
                artist=row["artist"],
                genre=row["genre"],
                mood=row["mood"],
                energy=float(row["energy"]),
                tempo_bpm=float(row["tempo_bpm"]),
                valence=float(row["valence"]),
                danceability=float(row["danceability"]),
                acousticness=float(row["acousticness"]),
                instrumentalness=float(row["instrumentalness"]),
            ))
    return songs


def score_song(user: UserProfile, song: Song) -> float:
    """Score a song against a user profile based on mood, genre, and energy proximity."""
    score = 0.0

    # Mood — highest weight (context beats genre)
    if song.mood == user.favorite_mood:
        score += 4.0

    # Genre — halved weight (experiment: energy matters more than genre label)
    if song.genre == user.favorite_genre:
        score += 1.5

    # Energy — doubled weight (experiment: numeric closeness, max +4.0)
    energy_diff = abs(song.energy - user.target_energy)
    score += (1.0 - energy_diff) * 4.0

    return round(score, 2)
