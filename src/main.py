import os
import sys

from src.data_loader import load_songs
from src.agent import run_session

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")


def main() -> None:
    try:
        songs = load_songs(DATA_PATH)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] Could not load song catalog: {e}")
        sys.exit(1)

    try:
        run_session(songs)
    except KeyboardInterrupt:
        print("\n\n  Session interrupted. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
