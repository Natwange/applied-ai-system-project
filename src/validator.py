import difflib
from src.models import UserProfile


VALID_GENRES = {
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave",
    "indie pop", "afrobeats", "r&b", "classical", "country",
    "metal", "blues", "reggae", "hip-hop",
}

VALID_MOODS = {
    "happy", "chill", "intense", "relaxed", "moody", "focused",
    "energetic", "romantic", "melancholic", "nostalgic", "angry",
    "sad", "peaceful", "uplifting",
}

ACOUSTIC_TRUE  = {"yes", "y", "true", "1"}
ACOUSTIC_FALSE = {"no", "n", "false", "0"}


def normalize_text(text: str) -> str:
    return text.strip().lower()


def _fuzzy_match(value: str, valid_set: set[str]) -> str | None:
    matches = difflib.get_close_matches(value, valid_set, n=1, cutoff=0.7)
    return matches[0] if matches else None


def validate_genre(raw: str) -> tuple[str, str | None]:
    """Return (genre, warning). Warning is None if input was exact."""
    value = normalize_text(raw)
    if value in VALID_GENRES:
        return value, None
    suggestion = _fuzzy_match(value, VALID_GENRES)
    if suggestion:
        return suggestion, f'Genre "{raw}" not recognised — using closest match "{suggestion}".'
    return value, f'Genre "{raw}" not found in catalog. Genre matching will be skipped.'


def validate_mood(raw: str) -> tuple[str, str | None]:
    """Return (mood, warning). Warning is None if input was exact."""
    value = normalize_text(raw)
    if value in VALID_MOODS:
        return value, None
    suggestion = _fuzzy_match(value, VALID_MOODS)
    if suggestion:
        return suggestion, f'Mood "{raw}" not recognised — using closest match "{suggestion}".'
    return value, f'Mood "{raw}" not found in catalog. Mood matching will be skipped, falling back to genre and energy.'


def validate_energy(raw: str) -> tuple[float, str | None]:
    """Return (energy, warning). Clamps silently to [0.0, 1.0] and warns."""
    try:
        value = float(raw.strip())
    except ValueError:
        raise ValueError(f'Energy must be a number between 0.0 and 1.0, got "{raw}".')

    if 0.0 <= value <= 1.0:
        return value, None

    clamped = max(0.0, min(1.0, value))
    return clamped, f"Energy {value} is out of range — clamped to {clamped}."


def validate_acoustic(raw: str) -> bool:
    """Return True/False. Raises ValueError on unrecognised input."""
    value = normalize_text(raw)
    if value in ACOUSTIC_TRUE:
        return True
    if value in ACOUSTIC_FALSE:
        return False
    raise ValueError(f'Acoustic preference must be yes/no, got "{raw}".')


def build_validated_profile(
    genre: str,
    mood: str,
    energy: str,
    acoustic: str,
) -> tuple[UserProfile, list[str]]:
    """Validate all inputs and return (UserProfile, warnings).
    Raises ValueError immediately on unrecoverable input (energy format, acoustic)."""
    warnings: list[str] = []

    validated_genre, genre_warn = validate_genre(genre)
    if genre_warn:
        warnings.append(genre_warn)

    validated_mood, mood_warn = validate_mood(mood)
    if mood_warn:
        warnings.append(mood_warn)

    validated_energy, energy_warn = validate_energy(energy)
    if energy_warn:
        warnings.append(energy_warn)

    validated_acoustic = validate_acoustic(acoustic)

    profile = UserProfile(
        favorite_genre=validated_genre,
        favorite_mood=validated_mood,
        target_energy=validated_energy,
        likes_acoustic=validated_acoustic,
    )
    return profile, warnings
