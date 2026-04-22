import pytest
from src.validator import (
    normalize_text,
    validate_genre,
    validate_mood,
    validate_energy,
    validate_acoustic,
    build_validated_profile,
)


def test_normalize_text_strips_and_lowercases():
    assert normalize_text("  Pop  ") == "pop"
    assert normalize_text("HAPPY") == "happy"


def test_validate_genre_exact_match():
    genre, warning = validate_genre("pop")
    assert genre == "pop"
    assert warning is None


def test_validate_genre_fuzzy_match():
    genre, warning = validate_genre("poop")
    assert genre == "pop"
    assert warning is not None
    assert "closest match" in warning


def test_validate_genre_unknown_returns_warning():
    genre, warning = validate_genre("bossa nova")
    assert genre == "bossa nova"
    assert warning is not None
    assert "not found" in warning.lower()


def test_validate_mood_exact_match():
    mood, warning = validate_mood("chill")
    assert mood == "chill"
    assert warning is None


def test_validate_mood_unknown_triggers_fallback_warning():
    mood, warning = validate_mood("anxious")
    assert mood == "anxious"
    assert "falling back" in warning.lower()


def test_validate_energy_valid():
    energy, warning = validate_energy("0.7")
    assert energy == 0.7
    assert warning is None


def test_validate_energy_clamped_high():
    energy, warning = validate_energy("1.5")
    assert energy == 1.0
    assert "clamped" in warning.lower()


def test_validate_energy_clamped_low():
    energy, warning = validate_energy("-0.2")
    assert energy == 0.0
    assert "clamped" in warning.lower()


def test_validate_energy_non_numeric_raises():
    with pytest.raises(ValueError, match="number"):
        validate_energy("fast")


def test_validate_acoustic_true_variants():
    for val in ("yes", "y", "true", "1", "YES", "True"):
        assert validate_acoustic(val) is True


def test_validate_acoustic_false_variants():
    for val in ("no", "n", "false", "0", "NO"):
        assert validate_acoustic(val) is False


def test_validate_acoustic_invalid_raises():
    with pytest.raises(ValueError):
        validate_acoustic("maybe")


def test_build_validated_profile_clean_input():
    profile, warnings = build_validated_profile("pop", "happy", "0.8", "yes")
    assert profile.favorite_genre == "pop"
    assert profile.favorite_mood == "happy"
    assert profile.target_energy == 0.8
    assert profile.likes_acoustic is True
    assert not warnings


def test_build_validated_profile_collects_warnings():
    _, warnings = build_validated_profile("bossa nova", "anxious", "1.5", "no")
    assert len(warnings) == 3


def test_build_validated_profile_bad_energy_raises():
    with pytest.raises(ValueError):
        build_validated_profile("pop", "happy", "notanumber", "no")
