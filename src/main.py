"""
Command line runner for the Music Recommender Simulation.
"""

from recommender import load_songs, Recommender, UserProfile


def main() -> None:
    songs = load_songs("data/songs.csv")
    rec = Recommender(songs)

    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )

    recommendations = rec.recommend(user, k=5)

    print("\nTop recommendations:\n")
    for song in recommendations:
        explanation = rec.explain_recommendation(user, song)
        print(f"{song.title} by {song.artist} — Score: {song.energy}")
        print(f"Because: {explanation}")
        print()


if __name__ == "__main__":
    main()
