from src.models import UserProfile, Song
from src.feedback import parse_feedback, update_profile_from_feedback


def _make_results() -> list[tuple[Song, float]]:
    songs = [
        Song(1, "Track One",   "Artist A", "pop",  "happy",     0.82, 118, 0.84, 0.79, 0.18),
        Song(2, "Track Two",   "Artist B", "lofi", "chill",     0.35, 72,  0.60, 0.58, 0.86),
        Song(3, "Track Three", "Artist C", "rock", "intense",   0.91, 152, 0.48, 0.66, 0.10),
        Song(4, "Track Four",  "Artist D", "jazz", "relaxed",   0.37, 90,  0.71, 0.54, 0.89),
        Song(5, "Track Five",  "Artist E", "r&b",  "romantic",  0.55, 85,  0.78, 0.68, 0.44),
    ]
    return [(s, float(5 - i)) for i, s in enumerate(songs)]


def _make_profile() -> UserProfile:
    return UserProfile("pop", "happy", 0.8, False)


# --- Energy ---

def test_parse_feedback_energy_down():
    parsed = parse_feedback("too energetic", _make_results())
    assert parsed.energy_delta < 0


def test_parse_feedback_energy_up():
    parsed = parse_feedback("more energetic", _make_results())
    assert parsed.energy_delta > 0


def test_conflicting_energy_signals_cancel():
    parsed = parse_feedback("too energetic more energy", _make_results())
    assert parsed.energy_delta == 0.0
    assert len(parsed.conflicts) > 0


def test_update_profile_applies_energy_delta():
    profile = _make_profile()
    results = _make_results()
    parsed = parse_feedback("too energetic", results)
    update_profile_from_feedback(profile, parsed, results)
    assert profile.target_energy < 0.8


def test_energy_clamped_at_zero():
    profile = UserProfile("pop", "happy", 0.05, False)
    results = _make_results()
    parsed = parse_feedback("too energetic", results)
    update_profile_from_feedback(profile, parsed, results)
    assert profile.target_energy >= 0.0


def test_energy_clamped_at_one():
    profile = UserProfile("pop", "happy", 0.95, False)
    results = _make_results()
    parsed = parse_feedback("more energetic", results)
    update_profile_from_feedback(profile, parsed, results)
    assert profile.target_energy <= 1.0


# --- Acoustic ---

def test_parse_feedback_less_acoustic():
    parsed = parse_feedback("less acoustic", _make_results())
    assert parsed.likes_acoustic is False


def test_parse_feedback_more_acoustic():
    parsed = parse_feedback("more acoustic", _make_results())
    assert parsed.likes_acoustic is True


# --- Mood ---

def test_parse_feedback_mood_change():
    parsed = parse_feedback("more chill", _make_results())
    assert parsed.new_mood == "chill"


def test_update_profile_changes_mood():
    profile = _make_profile()
    results = _make_results()
    parsed = parse_feedback("more chill", results)
    update_profile_from_feedback(profile, parsed, results)
    assert profile.favorite_mood == "chill"


# --- Genre ---

def test_parse_feedback_genre_change():
    parsed = parse_feedback("more rock", _make_results())
    assert parsed.new_genre == "rock"


# --- Liked song ---

def test_parse_feedback_liked_song_extracts_id():
    results = _make_results()
    parsed = parse_feedback("I liked song 2", results)
    assert results[1][0].id in parsed.liked_song_ids


def test_liked_song_tracked_in_profile():
    profile = _make_profile()
    results = _make_results()
    parsed = parse_feedback("I liked song 1", results)
    update_profile_from_feedback(profile, parsed, results)
    assert results[0][0].id in profile.liked_song_ids


def test_liked_song_nudges_energy():
    profile = _make_profile()        # target_energy = 0.8
    results = _make_results()        # song 3 has energy = 0.91, gap = 0.11, nudge = 0.011
    original_energy = profile.target_energy
    parsed = parse_feedback("I liked song 3", results)
    update_profile_from_feedback(profile, parsed, results)
    liked_song = results[2][0]
    expected = round(original_energy + 0.1 * (liked_song.energy - original_energy), 2)
    assert profile.target_energy == expected


# --- No changes ---

def test_unrecognised_feedback_has_no_changes():
    parsed = parse_feedback("xyzzy gibberish !!!!", _make_results())
    assert not parsed.has_changes()


# --- Feedback history ---

def test_feedback_history_recorded():
    profile = _make_profile()
    results = _make_results()
    parsed = parse_feedback("too energetic", results)
    update_profile_from_feedback(profile, parsed, results)
    assert "too energetic" in profile.feedback_history
