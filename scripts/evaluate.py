"""
Evaluation harness for VibeFinder 2.0.
Usage:
    python -m scripts.evaluate
    python -m scripts.evaluate --save
"""
import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data_loader import load_songs
from src.models import UserProfile, Song
from src.recommender import recommend
from src.validator import build_validated_profile
from src.feedback import parse_feedback, update_profile_from_feedback
from src.scoring_modes import DEFAULT_STRATEGY, MoodFirstStrategy

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")


# ---------------------------------------------------------------------------
# Test result container
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name: str
    category: str
    passed: bool
    message: str


def _pass(name: str, category: str, msg: str) -> TestResult:
    return TestResult(name, category, True, msg)


def _fail(name: str, category: str, msg: str) -> TestResult:
    return TestResult(name, category, False, msg)


# ---------------------------------------------------------------------------
# A: Normal user scenarios
# ---------------------------------------------------------------------------

def test_chill_acoustic_user(songs: list[Song]) -> TestResult:
    name, cat = "Chill acoustic user", "normal"
    profile = UserProfile("lofi", "chill", 0.35, True)
    results = recommend(profile, songs, DEFAULT_STRATEGY)
    top = results[0][0]
    if top.mood == "chill" or top.genre == "lofi":
        return _pass(name, cat, f"Top result: {top.title} (mood={top.mood}, genre={top.genre})")
    return _fail(name, cat, f"Expected chill/lofi at top, got mood={top.mood}, genre={top.genre}")


def test_workout_user(songs: list[Song]) -> TestResult:
    name, cat = "Workout user", "normal"
    profile = UserProfile("rock", "intense", 0.92, False)
    results = recommend(profile, songs, DEFAULT_STRATEGY)
    top = results[0][0]
    if top.energy >= 0.7:
        return _pass(name, cat, f"Top result energy: {top.energy:.2f} (>= 0.70)")
    return _fail(name, cat, f"Expected energy >= 0.70, got {top.energy:.2f}")


def test_melancholic_classical_user(songs: list[Song]) -> TestResult:
    name, cat = "Melancholic classical user", "normal"
    profile = UserProfile("classical", "melancholic", 0.22, True)
    results = recommend(profile, songs, DEFAULT_STRATEGY, k=3)
    failures = [s for s, _ in results if s.energy > 0.6]
    if not failures:
        return _pass(name, cat, "All top-3 results have energy <= 0.60")
    return _fail(name, cat, f"{len(failures)} result(s) exceeded energy 0.60: {[s.title for s in failures]}")


def test_different_users_get_different_top_results(songs: list[Song]) -> TestResult:
    name, cat = "Distinct users get distinct top results", "normal"
    p1 = UserProfile("lofi", "chill", 0.35, True)
    p2 = UserProfile("rock", "intense", 0.92, False)
    p3 = UserProfile("classical", "melancholic", 0.22, True)
    tops = {recommend(p, songs, DEFAULT_STRATEGY, k=1)[0][0].id for p in (p1, p2, p3)}
    if len(tops) == 3:
        return _pass(name, cat, "3 distinct users → 3 distinct top songs")
    return _fail(name, cat, f"Expected 3 distinct top songs, got {len(tops)}")


# ---------------------------------------------------------------------------
# B: Adversarial / guardrail scenarios
# ---------------------------------------------------------------------------

def test_unknown_mood_fallback(songs: list[Song]) -> TestResult:
    name, cat = "Unknown mood falls back gracefully", "adversarial"
    _, warnings = build_validated_profile("pop", "anxious", "0.5", "no")
    profile = UserProfile("pop", "anxious", 0.5, False)
    results = recommend(profile, songs, DEFAULT_STRATEGY)
    has_warning = any("not found" in w.lower() or "fallback" in w.lower() for w in warnings)
    if len(results) == 5 and has_warning:
        return _pass(name, cat, f"Returned 5 results with fallback warning")
    return _fail(name, cat, f"results={len(results)}, warning_issued={has_warning}")


def test_unknown_genre_fallback(songs: list[Song]) -> TestResult:
    name, cat = "Unknown genre falls back gracefully", "adversarial"
    _, warnings = build_validated_profile("bossa nova", "happy", "0.5", "yes")
    profile = UserProfile("bossa nova", "happy", 0.5, True)
    results = recommend(profile, songs, DEFAULT_STRATEGY)
    has_warning = len(warnings) > 0
    if len(results) == 5 and has_warning:
        return _pass(name, cat, f"Warning: {warnings[0]}")
    return _fail(name, cat, f"results={len(results)}, warning_issued={has_warning}")


def test_energy_out_of_range_clamped(songs: list[Song]) -> TestResult:
    name, cat = "Out-of-range energy is clamped", "adversarial"
    _, warnings = build_validated_profile("pop", "happy", "1.5", "no")
    has_warning = any("clamped" in w.lower() for w in warnings)
    profile, _ = build_validated_profile("pop", "happy", "1.5", "no")
    if profile.target_energy == 1.0 and has_warning:
        return _pass(name, cat, "Energy 1.5 clamped to 1.0 with warning")
    return _fail(name, cat, f"energy={profile.target_energy}, warning_issued={has_warning}")


def test_invalid_energy_raises(songs: list[Song]) -> TestResult:
    name, cat = "Non-numeric energy raises ValueError", "adversarial"
    try:
        build_validated_profile("pop", "happy", "abc", "no")
        return _fail(name, cat, "Expected ValueError but none was raised")
    except ValueError:
        return _pass(name, cat, "ValueError raised as expected")


def test_invalid_acoustic_raises(songs: list[Song]) -> TestResult:
    name, cat = "Invalid acoustic input raises ValueError", "adversarial"
    try:
        build_validated_profile("pop", "happy", "0.5", "maybe")
        return _fail(name, cat, "Expected ValueError but none was raised")
    except ValueError:
        return _pass(name, cat, "ValueError raised as expected")


def test_conflicting_genre_mood(songs: list[Song]) -> TestResult:
    name, cat = "Conflicting genre/mood — mood weight dominates", "adversarial"
    profile = UserProfile("metal", "chill", 0.4, False)
    results = recommend(profile, songs, MoodFirstStrategy())
    top = results[0][0]
    if top.mood == "chill":
        return _pass(name, cat, f"Top result mood='chill' as expected (genre={top.genre})")
    return _fail(name, cat, f"Expected mood='chill' to dominate, got mood={top.mood}")


# ---------------------------------------------------------------------------
# C: Feedback refinement scenarios
# ---------------------------------------------------------------------------

def test_feedback_energy_down(songs: list[Song]) -> TestResult:
    name, cat = "Feedback: 'too energetic' lowers target energy", "feedback"
    profile = UserProfile("pop", "happy", 0.8, False)
    initial_results = recommend(profile, songs, DEFAULT_STRATEGY)

    parsed = parse_feedback("too energetic", initial_results)
    changes = update_profile_from_feedback(profile, parsed, initial_results)

    if profile.target_energy < 0.8 and changes:
        return _pass(name, cat, f"Energy reduced: {changes[0]}")
    return _fail(name, cat, f"Expected energy < 0.80, got {profile.target_energy:.2f}")


def test_feedback_energy_up(songs: list[Song]) -> TestResult:
    name, cat = "Feedback: 'more energetic' raises target energy", "feedback"
    profile = UserProfile("lofi", "chill", 0.3, True)
    initial_results = recommend(profile, songs, DEFAULT_STRATEGY)

    parsed = parse_feedback("more energetic", initial_results)
    update_profile_from_feedback(profile, parsed, initial_results)

    if profile.target_energy > 0.3:
        return _pass(name, cat, f"Energy raised to {profile.target_energy:.2f}")
    return _fail(name, cat, f"Expected energy > 0.30, got {profile.target_energy:.2f}")


def test_feedback_mood_change(songs: list[Song]) -> TestResult:
    name, cat = "Feedback: 'more chill' updates mood", "feedback"
    profile = UserProfile("pop", "happy", 0.8, False)
    initial_results = recommend(profile, songs, DEFAULT_STRATEGY)

    parsed = parse_feedback("more chill", initial_results)
    update_profile_from_feedback(profile, parsed, initial_results)

    if profile.favorite_mood == "chill":
        return _pass(name, cat, "favorite_mood updated to 'chill'")
    return _fail(name, cat, f"Expected mood='chill', got '{profile.favorite_mood}'")


def test_feedback_rerank_changes_results(songs: list[Song]) -> TestResult:
    name, cat = "Feedback: rerank after 'too energetic' shifts results", "feedback"
    profile = UserProfile("pop", "happy", 0.8, False)
    initial_results = recommend(profile, songs, DEFAULT_STRATEGY)
    initial_top_id = initial_results[0][0].id

    parsed = parse_feedback("too energetic", initial_results)
    update_profile_from_feedback(profile, parsed, initial_results)
    new_results = recommend(profile, songs, DEFAULT_STRATEGY)

    initial_avg = sum(s.energy for s, _ in initial_results) / len(initial_results)
    new_avg     = sum(s.energy for s, _ in new_results) / len(new_results)

    if new_avg < initial_avg:
        return _pass(name, cat, f"Avg energy dropped: {initial_avg:.2f} → {new_avg:.2f}")
    return _fail(name, cat, f"Expected lower avg energy after feedback, got {initial_avg:.2f} → {new_avg:.2f}")


def test_feedback_liked_song_nudges_energy(songs: list[Song]) -> TestResult:
    name, cat = "Feedback: liked song nudges target energy", "feedback"
    profile = UserProfile("pop", "happy", 0.8, False)
    initial_results = recommend(profile, songs, DEFAULT_STRATEGY)
    liked_song = initial_results[0][0]
    original_energy = profile.target_energy

    parsed = parse_feedback("I liked song 1", initial_results)
    update_profile_from_feedback(profile, parsed, initial_results)

    nudge = abs(liked_song.energy - original_energy) * 0.1
    energy_changed = abs(profile.target_energy - original_energy) > 0.001
    liked_tracked  = liked_song.id in profile.liked_song_ids

    if energy_changed and liked_tracked:
        return _pass(name, cat, f"Energy nudged to {profile.target_energy:.2f}, song ID tracked")
    return _fail(name, cat, f"energy_changed={energy_changed}, liked_tracked={liked_tracked}")


def test_unrecognised_feedback_has_no_changes(songs: list[Song]) -> TestResult:
    name, cat = "Unrecognised feedback produces no profile changes", "feedback"
    profile = UserProfile("pop", "happy", 0.8, False)
    initial_results = recommend(profile, songs, DEFAULT_STRATEGY)

    parsed = parse_feedback("xyzzy gibberish !!!!", initial_results)
    if not parsed.has_changes():
        return _pass(name, cat, "No changes detected from unrecognised input")
    return _fail(name, cat, f"Unexpected changes: energy_delta={parsed.energy_delta}, mood={parsed.new_mood}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

ALL_TESTS = [
    test_chill_acoustic_user,
    test_workout_user,
    test_melancholic_classical_user,
    test_different_users_get_different_top_results,
    test_unknown_mood_fallback,
    test_unknown_genre_fallback,
    test_energy_out_of_range_clamped,
    test_invalid_energy_raises,
    test_invalid_acoustic_raises,
    test_conflicting_genre_mood,
    test_feedback_energy_down,
    test_feedback_energy_up,
    test_feedback_mood_change,
    test_feedback_rerank_changes_results,
    test_feedback_liked_song_nudges_energy,
    test_unrecognised_feedback_has_no_changes,
]


def run_all(songs: list[Song]) -> list[TestResult]:
    results = []
    for test_fn in ALL_TESTS:
        try:
            results.append(test_fn(songs))
        except Exception as e:
            results.append(_fail(test_fn.__name__, "error", f"Unexpected exception: {e}"))
    return results


def print_report(results: list[TestResult]) -> None:
    categories = sorted({r.category for r in results})
    total = len(results)
    passed = sum(1 for r in results if r.passed)

    print("\n" + "=" * 60)
    print("  VibeFinder 2.0 — Evaluation Report")
    print("=" * 60)

    for cat in categories:
        group = [r for r in results if r.category == cat]
        print(f"\n  [{cat.upper()}]")
        for r in group:
            status = "PASS" if r.passed else "FAIL"
            print(f"    [{status}] {r.name}")
            print(f"           {r.message}")

    print("\n" + "-" * 60)
    print(f"  {passed}/{total} tests passed")
    if passed == total:
        print("  All tests passed.")
    else:
        failed = [r.name for r in results if not r.passed]
        print(f"  Failed: {', '.join(failed)}")
    print("=" * 60)


def save_report(results: list[TestResult], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    passed = sum(1 for r in results if r.passed)
    lines = [
        f"# VibeFinder 2.0 — Evaluation Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Result: {passed}/{len(results)} passed\n",
    ]
    for cat in sorted({r.category for r in results}):
        lines.append(f"## {cat.capitalize()}")
        for r in results:
            if r.category == cat:
                status = "PASS" if r.passed else "FAIL"
                lines.append(f"- [{status}] **{r.name}**: {r.message}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  Report saved to {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="VibeFinder 2.0 evaluation harness")
    parser.add_argument("--save", action="store_true", help="Save report to reports/")
    args = parser.parse_args()

    try:
        songs = load_songs(DATA_PATH)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(f"\n  Running {len(ALL_TESTS)} evaluation scenarios...")
    results = run_all(songs)
    print_report(results)

    if args.save:
        filename = f"eval_{datetime.now().strftime('%Y-%m-%d')}.md"
        save_report(results, os.path.join(REPORTS_DIR, filename))

    sys.exit(0 if all(r.passed for r in results) else 1)


if __name__ == "__main__":
    main()
