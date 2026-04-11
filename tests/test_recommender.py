import os
import pytest
from src.recommender import Song, UserProfile, Recommender, load_songs

# ---------------------------------------------------------------------------
# System evaluation fixture — loads real song catalog
# ---------------------------------------------------------------------------

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")

@pytest.fixture(scope="module")
def full_recommender() -> Recommender:
    songs = load_songs(DATA_PATH)
    return Recommender(songs)


# ---------------------------------------------------------------------------
# Three distinct user preference profiles for system evaluation
# ---------------------------------------------------------------------------

CHILL_ACOUSTIC_USER = UserProfile(
    favorite_genre="lofi",
    favorite_mood="chill",
    target_energy=0.35,
    likes_acoustic=True,
)

WORKOUT_USER = UserProfile(
    favorite_genre="rock",
    favorite_mood="intense",
    target_energy=0.92,
    likes_acoustic=False,
)

MELANCHOLIC_CLASSICAL_USER = UserProfile(
    favorite_genre="classical",
    favorite_mood="melancholic",
    target_energy=0.22,
    likes_acoustic=True,
)

# ---------------------------------------------------------------------------
# Adversarial / edge-case profiles
# ---------------------------------------------------------------------------

# Edge case 1: mood that does not exist in the catalog ("anxious" → no song
# ever matches on mood), so only genre + energy drive scoring.  A pop fan
# asking for "anxious" music should still get pop songs, but the mood bonus
# is never earned — tests whether genre weight alone produces sensible results.
NONEXISTENT_MOOD_USER = UserProfile(
    favorite_genre="pop",
    favorite_mood="anxious",      # not in catalog
    target_energy=0.9,
    likes_acoustic=False,
)

# Edge case 2: genre and mood that pull in opposite directions.  "Metal"
# implies high energy and aggression; "chill" implies low energy and calm.
# With target_energy=0.4 the mood weight (4.0) dominates the genre weight
# (3.0), so lofi/ambient songs may beat the lone metal song.
CONFLICTING_GENRE_MOOD_USER = UserProfile(
    favorite_genre="metal",
    favorite_mood="chill",
    target_energy=0.4,
    likes_acoustic=False,
)

# Edge case 3: both genre and mood are absent from the catalog, so neither
# bonus is ever awarded.  The recommender degrades to a pure energy-proximity
# sorter — tests the floor behavior of the scoring function.
BOTH_UNKNOWN_USER = UserProfile(
    favorite_genre="bossa nova",  # not in catalog
    favorite_mood="anxious",      # not in catalog
    target_energy=0.5,
    likes_acoustic=True,
)

# Edge case 4 (adversarial surprise): the user's genre (pop) and mood (sad)
# both exist but belong to completely different songs.  Because mood weight
# (4.0) > genre weight (3.0), the lone "sad" blues song beats pop songs even
# though this user declared a preference for pop.  Captures the scoring
# imbalance between mood and genre.
MOOD_OVERRIDES_GENRE_USER = UserProfile(
    favorite_genre="pop",
    favorite_mood="sad",
    target_energy=0.9,
    likes_acoustic=False,
)


def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# System evaluation tests — run against the full catalog
# ---------------------------------------------------------------------------

def test_chill_acoustic_user_top_result_matches_mood_or_genre(full_recommender):
    results = full_recommender.recommend(CHILL_ACOUSTIC_USER, k=5)
    assert len(results) == 5
    top = results[0]
    assert top.mood == "chill" or top.genre == "lofi", (
        f"Expected top result to match mood 'chill' or genre 'lofi', got mood={top.mood}, genre={top.genre}"
    )


def test_workout_user_top_result_is_high_energy(full_recommender):
    results = full_recommender.recommend(WORKOUT_USER, k=5)
    assert len(results) == 5
    top = results[0]
    assert top.energy >= 0.7, (
        f"Expected top result to have energy >= 0.7 for workout user, got {top.energy}"
    )


def test_melancholic_classical_user_recommendations_are_low_energy(full_recommender):
    results = full_recommender.recommend(MELANCHOLIC_CLASSICAL_USER, k=3)
    assert len(results) == 3
    for song in results:
        assert song.energy <= 0.6, (
            f"Expected all recommendations to have energy <= 0.6, got {song.title} with energy={song.energy}"
        )


def test_all_profiles_return_unique_top_recommendations(full_recommender):
    """Verifies the system differentiates between very different user tastes."""
    chill_top = full_recommender.recommend(CHILL_ACOUSTIC_USER, k=1)[0]
    workout_top = full_recommender.recommend(WORKOUT_USER, k=1)[0]
    classical_top = full_recommender.recommend(MELANCHOLIC_CLASSICAL_USER, k=1)[0]

    top_ids = {chill_top.id, workout_top.id, classical_top.id}
    assert len(top_ids) == 3, (
        "Expected three distinct users to receive three different top recommendations"
    )


def test_explanations_reference_matched_attributes(full_recommender):
    """Each profile's top recommendation explanation should mention at least one matched attribute."""
    for user, label in [
        (CHILL_ACOUSTIC_USER, "chill acoustic"),
        (WORKOUT_USER, "workout"),
        (MELANCHOLIC_CLASSICAL_USER, "melancholic classical"),
    ]:
        top = full_recommender.recommend(user, k=1)[0]
        explanation = full_recommender.explain_recommendation(user, top)
        assert "Recommended because:" in explanation, (
            f"[{label}] Expected explanation to cite a reason, got: {explanation!r}"
        )


# ---------------------------------------------------------------------------
# Adversarial / edge-case tests
# ---------------------------------------------------------------------------

def test_nonexistent_mood_still_returns_k_results(full_recommender):
    """Mood 'sad' is not in the catalog; recommender must still return k songs."""
    results = full_recommender.recommend(NONEXISTENT_MOOD_USER, k=5)
    assert len(results) == 5


def test_nonexistent_mood_top_result_uses_genre_fallback(full_recommender):
    """With no mood match ever possible, the top result should match the genre ('pop')."""
    results = full_recommender.recommend(NONEXISTENT_MOOD_USER, k=5)
    top = results[0]
    assert top.genre == "pop", (
        f"Expected genre fallback to surface a pop song, got genre={top.genre}"
    )


def test_conflicting_genre_mood_mood_weight_dominates(full_recommender):
    """Mood weight (4.0) > genre weight (3.0): top song should match mood 'chill',
    not necessarily genre 'metal'."""
    results = full_recommender.recommend(CONFLICTING_GENRE_MOOD_USER, k=5)
    top = results[0]
    assert top.mood == "chill", (
        f"Expected mood weight to dominate: top song should be 'chill', got mood={top.mood}"
    )


def test_both_unknown_profile_rankings_are_energy_only(full_recommender):
    """With no genre or mood matches possible, all scores come from energy proximity alone.
    No result should have an explanation citing mood or genre."""
    results = full_recommender.recommend(BOTH_UNKNOWN_USER, k=5)
    for song in results:
        explanation = full_recommender.explain_recommendation(BOTH_UNKNOWN_USER, song)
        assert "mood matches" not in explanation
        assert "genre matches" not in explanation


def test_mood_overrides_genre_preference(full_recommender):
    """Adversarial surprise: a pop fan who wants 'sad' music gets a blues song at #1.
    Mood weight (4.0) is strong enough to beat genre weight (3.0), so the
    lone sad/blues track outscores all pop songs despite the user preferring pop."""
    results = full_recommender.recommend(MOOD_OVERRIDES_GENRE_USER, k=5)
    top = results[0]
    # The blues/sad song beats pop/happy songs — mood weight dominates
    assert top.mood == "sad", (
        f"Expected 'sad' mood match to dominate: got mood={top.mood}, genre={top.genre}"
    )
    assert top.genre != "pop", (
        "Expected top result to NOT be pop — mood weight should pull a blues song to #1"
    )
