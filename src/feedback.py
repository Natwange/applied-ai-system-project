import re
from dataclasses import dataclass, field
from src.models import Song, UserProfile
from src.validator import VALID_MOODS, VALID_GENRES


ENERGY_DOWN = {"too energetic", "less energetic", "lower energy", "less energy", "too high energy", "tone it down", "calm it down"}
ENERGY_UP   = {"more energetic", "more energy", "higher energy", "more upbeat", "too calm", "not energetic enough"}
ACOUSTIC_UP = {"more acoustic", "too electric", "not acoustic enough"}
ACOUSTIC_DOWN = {"less acoustic", "too acoustic", "not acoustic", "more electric"}

ENERGY_DELTA = 0.15


@dataclass
class ParsedFeedback:
    energy_delta: float = 0.0
    likes_acoustic: bool | None = None
    new_mood: str | None = None
    new_genre: str | None = None
    liked_song_ids: list[int] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    raw: str = ""

    def has_changes(self) -> bool:
        return any([
            self.energy_delta != 0.0,
            self.likes_acoustic is not None,
            self.new_mood is not None,
            self.new_genre is not None,
            self.liked_song_ids,
        ])


def _extract_liked_positions(text: str) -> list[int]:
    """Pull song position numbers from phrases like 'liked song 2' or 'songs 1 and 3'."""
    return [int(n) for n in re.findall(r"\b([1-5])\b", text)]


def _detect_mood(text: str) -> str | None:
    for mood in VALID_MOODS:
        if mood in text:
            return mood
    return None


def _detect_genre(text: str) -> str | None:
    for genre in VALID_GENRES:
        if genre in text:
            return genre
    return None


def parse_feedback(
    raw: str,
    current_results: list[tuple[Song, float]],
) -> ParsedFeedback:
    text = raw.strip().lower()
    parsed = ParsedFeedback(raw=raw)

    # --- Liked song ---
    if any(kw in text for kw in ("liked song", "liked songs", "favourite", "favorite", "song")):
        positions = _extract_liked_positions(text)
        for pos in positions:
            if 1 <= pos <= len(current_results):
                parsed.liked_song_ids.append(current_results[pos - 1][0].id)

    # --- Energy ---
    energy_down = any(kw in text for kw in ENERGY_DOWN)
    energy_up   = any(kw in text for kw in ENERGY_UP)

    if energy_down and energy_up:
        parsed.conflicts.append("Conflicting energy signals detected — energy unchanged.")
    elif energy_down:
        parsed.energy_delta = -ENERGY_DELTA
    elif energy_up:
        parsed.energy_delta = +ENERGY_DELTA

    # --- Acoustic ---
    acoustic_up   = any(kw in text for kw in ACOUSTIC_UP)
    acoustic_down = any(kw in text for kw in ACOUSTIC_DOWN)

    if acoustic_up and acoustic_down:
        parsed.conflicts.append("Conflicting acoustic signals detected — acoustic preference unchanged.")
    elif acoustic_up:
        parsed.likes_acoustic = True
    elif acoustic_down:
        parsed.likes_acoustic = False

    # --- Mood (priority over energy if both detected) ---
    if any(kw in text for kw in ("more ", "less ")):
        mood = _detect_mood(text)
        if mood:
            parsed.new_mood = mood
            if parsed.energy_delta != 0.0:
                parsed.conflicts.append(
                    f'Mood signal ("{ mood }") takes priority — energy adjustment also applied.'
                )

    # --- Genre ---
    if any(kw in text for kw in ("more ", "less ", "not into")):
        genre = _detect_genre(text)
        if genre:
            parsed.new_genre = genre

    return parsed


def update_profile_from_feedback(
    profile: UserProfile,
    parsed: ParsedFeedback,
    current_results: list[tuple[Song, float]],
) -> list[str]:
    """Apply parsed feedback to profile in-place. Returns a human-readable list of changes."""
    changes: list[str] = []

    # --- Energy ---
    if parsed.energy_delta != 0.0:
        old = profile.target_energy
        profile.target_energy = round(max(0.0, min(1.0, old + parsed.energy_delta)), 2)
        changes.append(f"target_energy: {old:.2f} → {profile.target_energy:.2f}")

    # --- Acoustic ---
    if parsed.likes_acoustic is not None and parsed.likes_acoustic != profile.likes_acoustic:
        old = profile.likes_acoustic
        profile.likes_acoustic = parsed.likes_acoustic
        changes.append(f"likes_acoustic: {old} → {profile.likes_acoustic}")

    # --- Mood ---
    if parsed.new_mood and parsed.new_mood != profile.favorite_mood:
        old = profile.favorite_mood
        profile.favorite_mood = parsed.new_mood
        changes.append(f"favorite_mood: {old} → {profile.favorite_mood}")

    # --- Genre ---
    if parsed.new_genre and parsed.new_genre != profile.favorite_genre:
        old = profile.favorite_genre
        profile.favorite_genre = parsed.new_genre
        changes.append(f"favorite_genre: {old} → {profile.favorite_genre}")

    # --- Liked song inference ---
    for song_id in parsed.liked_song_ids:
        if song_id in profile.liked_song_ids:
            continue
        profile.liked_song_ids.append(song_id)
        liked_song = next((s for s, _ in current_results if s.id == song_id), None)
        if liked_song:
            old_energy = profile.target_energy
            nudge = round(0.1 * (liked_song.energy - profile.target_energy), 3)
            profile.target_energy = round(max(0.0, min(1.0, profile.target_energy + nudge)), 2)
            changes.append(
                f"liked song {song_id} ({liked_song.title}): "
                f"energy nudge {old_energy:.2f} → {profile.target_energy:.2f}"
            )

    profile.feedback_history.append(parsed.raw)
    return changes
