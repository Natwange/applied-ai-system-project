from src.models import Song, UserProfile, SessionState
from src.recommender import recommend, explain_recommendation
from src.feedback import parse_feedback, update_profile_from_feedback, ParsedFeedback
from src.validator import build_validated_profile, validate_acoustic, VALID_MOODS, VALID_GENRES
from src.scoring_modes import STRATEGIES, DEFAULT_STRATEGY, ScoringStrategy
import src.logger as log

MAX_FEEDBACK_RETRIES = 2


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

def _dispatch(name: str, fn, *args, **kwargs):
    result = fn(*args, **kwargs)
    summary = _summarize(name, result)
    log.log_tool_call(name, summary)
    return result


def _summarize(name: str, result) -> str:
    if name == "rerun_recommender" and isinstance(result, list) and result:
        return f"{len(result)} results, top score {result[0][1]:.2f}"
    if name == "update_profile" and isinstance(result, list):
        return f"{len(result)} change(s)"
    if name == "parse_feedback" and isinstance(result, ParsedFeedback):
        return f"energy_delta={result.energy_delta:+.2f}, mood={result.new_mood}, genre={result.new_genre}"
    if isinstance(result, list):
        return f"{len(result)} item(s)"
    return ""


# ---------------------------------------------------------------------------
# Input collection
# ---------------------------------------------------------------------------

def _prompt_energy() -> str:
    while True:
        raw = input("  Target energy (0.0 – 1.0): ").strip()
        try:
            float(raw)
            return raw
        except ValueError:
            print("  Please enter a number, e.g. 0.7")


def _prompt_acoustic() -> str:
    while True:
        raw = input("  Like acoustic music? (yes / no): ").strip()
        try:
            validate_acoustic(raw)
            return raw
        except ValueError as e:
            print(f"  {e}")


def collect_input() -> tuple[UserProfile, list[str]]:
    print("\n" + "=" * 50)
    print("  VibeFinder 2.0 — Tell us your preferences")
    print("=" * 50)
    genre   = input("  Favourite genre: ").strip()
    mood    = input("  Current mood: ").strip()
    energy  = _prompt_energy()
    acoustic = _prompt_acoustic()

    profile, warnings = build_validated_profile(genre, mood, energy, acoustic)
    return profile, warnings


# ---------------------------------------------------------------------------
# Mode selection
# ---------------------------------------------------------------------------

def select_mode() -> ScoringStrategy:
    print("\n  Select a scoring mode:")
    print("    [1] Mood-First      — prioritises mood match")
    print("    [2] Genre-First     — prioritises genre match")
    print("    [3] Energy-Focused  — prioritises energy proximity")
    print("    [4] Balanced        — equal weight across all dimensions")
    choice = input("  Enter 1–4 (default 1): ").strip()
    strategy = STRATEGIES.get(choice, DEFAULT_STRATEGY)
    print(f"  Using: {strategy.label}\n")
    return strategy


# ---------------------------------------------------------------------------
# Recommendation display
# ---------------------------------------------------------------------------

def _liked_genres_moods(profile: UserProfile, all_songs: list[Song]) -> tuple[set, set]:
    liked_songs = [s for s in all_songs if s.id in profile.liked_song_ids]
    return {s.genre for s in liked_songs}, {s.mood for s in liked_songs}


def print_recommendations(
    profile: UserProfile,
    results: list[tuple[Song, float]],
    strategy: ScoringStrategy,
    all_songs: list[Song],
    round_num: int,
) -> None:
    liked_genres, liked_moods = _liked_genres_moods(profile, all_songs)
    label = "Initial Recommendations" if round_num == 0 else f"Refined Recommendations (Round {round_num})"
    print(f"\n  --- {label} ---")
    for i, (song, score) in enumerate(results, start=1):
        boosted = bool(
            round_num > 0 and liked_genres | liked_moods
            and (song.genre in liked_genres or song.mood in liked_moods)
        )
        explanation = explain_recommendation(profile, song, strategy, feedback_boosted=boosted)
        print(f"\n  {i}. {song.title} — {song.artist}")
        print(f"     Genre: {song.genre}  |  Mood: {song.mood}  |  Energy: {song.energy:.2f}  |  Score: {score}")
        print(f"     {explanation}")


# ---------------------------------------------------------------------------
# Single recommendation round
# ---------------------------------------------------------------------------

def run_recommendation_round(
    session: SessionState,
    songs: list[Song],
    strategy: ScoringStrategy,
    round_num: int,
) -> list[tuple[Song, float]]:
    results = _dispatch("rerun_recommender", recommend, session.profile, songs, strategy)
    print_recommendations(session.profile, results, strategy, songs, round_num)
    log.log_round_complete(round_num, results[0][1] if results else 0.0)
    return results


# ---------------------------------------------------------------------------
# Feedback collection with retries
# ---------------------------------------------------------------------------

def collect_feedback(current_results: list[tuple[Song, float]]) -> ParsedFeedback | None:
    print("\n  Give feedback on these recommendations:")
    print("  Examples: 'too energetic', 'more chill', 'I liked song 2', 'less acoustic'")
    print("  (type 'done' to finish)\n")

    for attempt in range(MAX_FEEDBACK_RETRIES + 1):
        raw = input("  Your feedback: ").strip()
        if raw.lower() in ("done", "quit", "exit", ""):
            return None

        log.log_feedback(raw)
        parsed = _dispatch("parse_feedback", parse_feedback, raw, current_results)

        if parsed.has_changes():
            return parsed

        retries_left = MAX_FEEDBACK_RETRIES - attempt
        if retries_left > 0:
            print(f"  Feedback not recognised. Try again ({retries_left} attempt(s) left).")
        else:
            print("  Could not interpret feedback — skipping this round.")

    return None


# ---------------------------------------------------------------------------
# Session summary
# ---------------------------------------------------------------------------

def print_session_summary(session: SessionState, final_results: list[tuple[Song, float]]) -> None:
    print("\n" + "=" * 50)
    print("  SESSION SUMMARY")
    print("=" * 50)
    print(f"  Feedback rounds completed: {session.round_number}")
    print(f"  Final profile:")
    p = session.profile
    print(f"    Genre:   {p.favorite_genre}")
    print(f"    Mood:    {p.favorite_mood}")
    print(f"    Energy:  {p.target_energy:.2f}")
    print(f"    Acoustic: {p.likes_acoustic}")

    if session.profile_snapshots:
        print("\n  Profile changes across session:")
        first = session.profile_snapshots[0]
        if first.favorite_genre != p.favorite_genre:
            print(f"    genre:   {first.favorite_genre} -> {p.favorite_genre}")
        if first.favorite_mood != p.favorite_mood:
            print(f"    mood:    {first.favorite_mood} -> {p.favorite_mood}")
        if abs(first.target_energy - p.target_energy) >= 0.01:
            print(f"    energy:  {first.target_energy:.2f} -> {p.target_energy:.2f}")
        if first.likes_acoustic != p.likes_acoustic:
            print(f"    acoustic:{first.likes_acoustic} -> {p.likes_acoustic}")

    print("\n  Final top picks:")
    for i, (song, score) in enumerate(final_results[:3], start=1):
        print(f"    {i}. {song.title} — {song.artist} (score: {score})")
    print("=" * 50)


# ---------------------------------------------------------------------------
# Main session orchestrator
# ---------------------------------------------------------------------------

def run_session(songs: list[Song]) -> None:
    # --- Input ---
    log.log_tool_call("collect_input")
    profile, warnings = collect_input()

    for w in warnings:
        log.log_guardrail(w)
        print(f"\n  [!] {w}")

    strategy = _dispatch("select_mode", select_mode)
    log.log_session_start(strategy.label)

    session = SessionState(profile=profile)

    # --- Initial round ---
    log.log_agent_plan(["rerun_recommender", "generate_explanations"])
    results = run_recommendation_round(session, songs, strategy, round_num=0)

    # --- Feedback loop ---
    while not session.is_complete():
        parsed = collect_feedback(results)

        if parsed is None:
            break

        print("\n  Interpretation:")
        if parsed.new_mood:
            print(f"    detected mood change -> {parsed.new_mood}")
        if parsed.energy_delta != 0.0:
            direction = "down" if parsed.energy_delta < 0 else "up"
            print(f"    detected energy signal -> energy {direction} by {abs(parsed.energy_delta)}")
        if parsed.likes_acoustic is not None:
            print(f"    detected acoustic preference -> {parsed.likes_acoustic}")
        if parsed.new_genre:
            print(f"    detected genre signal -> {parsed.new_genre}")
        if parsed.liked_song_ids:
            print(f"    detected liked songs -> IDs {parsed.liked_song_ids}")
        if parsed.conflicts:
            log.log_conflicts(parsed.conflicts)
            for c in parsed.conflicts:
                print(f"    [!] {c}")

        session.snapshot()

        log.log_agent_plan(["update_profile", "rerun_recommender", "generate_explanations"])
        changes = _dispatch("update_profile", update_profile_from_feedback, session.profile, parsed, results)
        log.log_profile_updates(changes)

        if changes:
            print("\n  Profile updates:")
            for change in changes:
                print(f"    {change}")

        session.round_number += 1
        results = run_recommendation_round(session, songs, strategy, round_num=session.round_number)

    print_session_summary(session, results)
    log.log_session_end(session.round_number)
