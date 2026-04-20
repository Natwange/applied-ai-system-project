import csv
from src.models import Song


REQUIRED_FIELDS = {
    "id", "title", "artist", "genre", "mood",
    "energy", "tempo_bpm", "valence", "danceability",
    "acousticness", "instrumentalness",
}


def load_songs(csv_path: str) -> list[Song]:
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        missing = REQUIRED_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"songs.csv is missing required columns: {missing}")

        for i, row in enumerate(reader, start=2):
            try:
                songs.append(Song(
                    id=int(row["id"]),
                    title=row["title"].strip(),
                    artist=row["artist"].strip(),
                    genre=row["genre"].strip().lower(),
                    mood=row["mood"].strip().lower(),
                    energy=float(row["energy"]),
                    tempo_bpm=float(row["tempo_bpm"]),
                    valence=float(row["valence"]),
                    danceability=float(row["danceability"]),
                    acousticness=float(row["acousticness"]),
                    instrumentalness=float(row["instrumentalness"]),
                ))
            except (KeyError, ValueError) as e:
                raise ValueError(f"songs.csv row {i} is malformed: {e}") from e

    if not songs:
        raise ValueError(f"No songs loaded from {csv_path} — file may be empty.")

    return songs
